#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

import decimal
import re
from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from dj_rql._dataclasses import FilterArgs, OptimizationArgs
from dj_rql.constants import DjangoLookups, FilterTypes, SUPPORTED_FIELD_TYPES
from dj_rql.fields import SelectField
from dj_rql.openapi import RQLFilterClassSpecification
from dj_rql.qs import Annotation, NPR, NSR
from dj_rql.transformer import RQLToDjangoORMTransformer

from django.db.models import ForeignKey, ManyToManyField, Model, OneToOneField, OneToOneRel, Q
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.functional import cached_property

from lark.exceptions import LarkError

from py_rql.constants import (
    ComparisonOperators,
    FilterLookups,
    ListOperators,
    RESERVED_FILTER_NAMES,
    RQL_ANY_SYMBOL,
    RQL_EMPTY,
    RQL_FALSE,
    RQL_MINUS,
    RQL_NULL,
    RQL_PLUS,
    RQL_SEARCH_PARAM,
    RQL_TRUE,
    SearchOperators,
)
from py_rql.exceptions import RQLFilterLookupError, RQLFilterParsingError, RQLFilterValueError
from py_rql.parser import RQLParser


iterable_types = (list, tuple)


class RQLFilterClass:
    """Base class for filter classes."""

    MODEL = None
    """The model this filter is for."""

    FILTERS = None
    """A list or tuple of filters definitions."""

    EXTENDED_SEARCH_ORM_ROUTES = ()

    DISTINCT = False
    """If True, a `SELECT DISTINCT` will always be executed."""

    SELECT = False
    """If True, this FilterClass supports the ``select`` operator."""

    OPENAPI_SPECIFICATION = RQLFilterClassSpecification
    """Class for OpenAPI specifications generation."""

    QUERIES_CACHE_BACKEND = None
    """Class for query caching."""

    QUERIES_CACHE_SIZE = 20
    """Default number of cached queries."""

    def __init__(self, queryset, instance=None):
        self.queryset = queryset
        self._is_distinct = self.DISTINCT
        self._request = None
        self._view = None
        self._applied_annotations = set()

        if instance:
            self._init_from_class(instance)
        else:
            self._validate_init()
            self._default_init(self._get_init_filters())

    def _validate_init(self):
        e = 'Django model must be set for Filter Class.'
        assert self.MODEL and issubclass(self.MODEL, Model), e

        e = 'Wrong filter settings type for Filter Class.'
        assert (self.FILTERS is None) or isinstance(self.FILTERS, iterable_types), e

        e = 'Extended search ORM routes must be iterable.'
        assert isinstance(self.EXTENDED_SEARCH_ORM_ROUTES, iterable_types), e

    def _get_init_filters(self):
        return self.FILTERS

    def _default_init(self, filters):
        e = 'At least one filter must be set for Filter Class.'
        assert filters, e

        self.filters = {}
        self.ordering_filters = set()
        self.search_filters = set()
        self.select_tree = {}
        self.default_exclusions = set()
        self.annotations = {}

        self._build_filters(filters)
        self._extend_annotations()

    def _init_from_class(self, instance):
        copied_attributes = (
            'filters',
            'ordering_filters',
            'search_filters',
            'select_tree',
            'default_exclusions',
            'annotations',
        )
        for attr in copied_attributes:
            setattr(self, attr, getattr(instance, attr))

    def build_q_for_custom_filter(self, data):
        """ Django Q() builder for custom filter.

        :param FilterArgs data: Prepared filter data for custom filtering.
        :rtype: django.db.models.Q
        """
        raise RQLFilterParsingError(details={
            'error': 'Filter logic is not implemented: {0}.'.format(data.filter_name),
        })

    def build_name_for_custom_ordering(self, filter_name):
        """ Builder for ordering name of custom filter.

        :param str filter_name: Full filter name (f.e. ns1.ns2.filter1)
        :return: Django field str path
        :rtype: str
        """
        raise RQLFilterParsingError(details={
            'error': 'Ordering logic is not implemented: {0}.'.format(filter_name),
        })

    def optimize_field(self, data):
        """ This method can be overridden to apply complex DB optimization logic.

        :param OptimizationArgs data:
        :return: Optimized queryset
        :rtype: django.db.models.QuerySet or None
        """
        pass

    @property
    def openapi_specification(self):
        return self.OPENAPI_SPECIFICATION.get(self)

    def apply_annotations(self, filter_names, queryset=None):
        """
        This method is used from RQL Transformer to apply annotations before filtering on queryset,
        but after it's understood which filters are used. Also, it's used to apply annotations
        for select() optimization.

        :param set of str filter_names: Set of filter names
        :param django.db.models.QuerySet or None queryset: Queryset for annotation
        """
        if queryset is None:
            qs = self.queryset.all()
        else:
            qs = queryset.all()

        if not self.SELECT:
            return qs

        for filter_name in filter_names:
            anno_list = self.annotations.get(filter_name)

            if not anno_list:
                continue

            for anno in anno_list:
                anno_id = id(anno)
                if anno_id in self._applied_annotations:
                    continue

                self._applied_annotations.add(anno_id)
                qs = anno.apply(qs)

        return qs

    def apply_filters(self, query, request=None, view=None):
        """ Main entrypoint for request filtering.

        :param str query: RQL query string
        :param request: Request from API view
        :param view: API view
        :return: Lark AST, Filtered QuerySet
        """
        self._request = request
        self._view = view

        rql_ast, qs, select_filters = None, self.queryset, []
        qs.select_data = None

        if query:
            rql_ast = RQLParser.parse_query(query)
            rql_transformer = RQLToDjangoORMTransformer(self)
            try:
                qs = rql_transformer.transform(rql_ast)
            except LarkError as e:
                # Lark reraises it's errors, but the original ones are needed
                original_error = e.orig_exc
                if not isinstance(original_error, (AssertionError, LarkError)):
                    raise original_error

                raise RQLFilterParsingError()

            qs = self._apply_ordering(qs, rql_transformer.ordering_filters)
            select_filters = rql_transformer.select_filters

            if self._is_distinct:
                qs = qs.distinct()

            qs.select_data = None

        if self.SELECT:
            select_data = self._build_select_data(select_filters)
            qs = self._apply_optimizations(qs, select_data)
            qs.select_data = {
                'depth': 0,
                'select': select_data,
            }

        self.queryset = qs
        self._request = None
        self._view = None

        return rql_ast, qs

    def build_q_for_filter(self, data):
        """ Django Q() builder for extracted from query RQL expression.
        In general, this method should not be overridden.

        :param FilterArgs data: Prepared filter data for custom filtering.
        :rtype: django.db.models.Q
        """
        filter_name, operator, str_value = data.filter_name, data.operator, data.str_value
        list_operator = data.list_operator
        filter_basename, namespace = data.filter_basename, data.namespace

        if namespace and filter_basename == RQL_SEARCH_PARAM:
            raise RQLFilterLookupError(details={
                'error': f'Filter "{filter_basename}" can be applied only on top level.',
            })

        if filter_name == RQL_SEARCH_PARAM:
            return self._build_q_for_search(operator, str_value)

        base_item = self.get_filter_base_item(filter_name)
        if not base_item:
            return Q()

        if base_item.get('distinct'):
            self._is_distinct = True

        filter_item = self.filters[filter_name]
        available_lookups = base_item.get('lookups', set())
        if list_operator:
            if list_operator == ListOperators.IN:
                list_filter_lookup = FilterLookups.IN
            else:
                list_filter_lookup = FilterLookups.OUT

            if list_filter_lookup not in available_lookups:
                raise RQLFilterLookupError(**self._get_error_details(
                    filter_name, list_filter_lookup, str_value,
                ))

        null_values = base_item.get('null_values', set())
        filter_lookup = self._get_filter_lookup(
            filter_name, operator, str_value, available_lookups, null_values,
        )
        django_field = base_item.get('field')
        if django_field and isinstance(django_field, SelectField):
            raise RQLFilterLookupError(**self._get_error_details(
                filter_name, filter_lookup, str_value,
            ))

        django_lookup = self._get_django_lookup(filter_lookup, str_value, null_values)

        use_repr = base_item.get('use_repr', False)

        typed_value = None
        if django_field is not None:
            typed_value = self._get_typed_value(
                filter_name, filter_lookup, str_value, django_field,
                use_repr, null_values, django_lookup,
            )

        if base_item.get('custom'):
            return self.build_q_for_custom_filter(FilterArgs(
                filter_name,
                operator,
                str_value,
                list_operator=list_operator,
                filter_lookup=filter_lookup,
                django_lookup=django_lookup,
            ))

        if not isinstance(filter_item, iterable_types):
            return self._build_django_q(filter_item, django_lookup, filter_lookup, typed_value)

        # filter has different DB field 'sources'
        q = Q()
        for item in filter_item:
            item_q = self._build_django_q(item, django_lookup, filter_lookup, typed_value)
            if filter_lookup == FilterLookups.NE:
                q &= item_q
            else:
                q |= item_q
        return q

    def get_filter_base_item(self, filter_name):
        filter_item = self.filters.get(filter_name)
        if filter_item:
            return filter_item[0] if isinstance(filter_item, iterable_types) else filter_item

    def _build_select_data(self, select):
        select_data = {}

        include_select, exclude_select = self._prepare_selects(select)
        inclusions, exclusions = set(), set()

        select_data.update(
            self._build_select_data_for_inclusions(include_select, inclusions, exclusions),
        )
        select_data.update(
            self._build_select_data_for_exclusions(exclude_select, inclusions, exclusions),
        )

        return select_data

    def _build_select_data_for_inclusions(self, include_select, inclusions, exclusions):
        select_data = {}

        for filter_name in include_select:
            select_data.update(
                self._build_select_data_for_inclusion(filter_name, inclusions, exclusions),
            )

        return select_data

    def _build_select_data_for_inclusion(self, filter_name, inclusions, exclusions):
        select_data = {}

        select_tree = self.select_tree
        parent_parts = ''
        filter_name_parts = filter_name.split('.')
        last_filter_name_part_index = len(filter_name_parts) - 1

        for index, part in enumerate(filter_name_parts):
            if part not in select_tree:
                raise RQLFilterParsingError(details={
                    'error': 'Bad select filter: {0}.'.format(filter_name),
                })

            current_part = '{0}.{1}'.format(parent_parts, part) if parent_parts else part

            inclusions.add(current_part)
            select_data[current_part] = True

            if index != last_filter_name_part_index:
                parent_parts = current_part
                select_tree = select_tree[part]['fields']

            elif parent_parts in self.default_exclusions:
                for neighbour_part in select_tree.keys():
                    if neighbour_part != part:
                        exclusions.add(
                            '{0}.{1}'.format(parent_parts, neighbour_part),
                        )

        return select_data

    def _build_select_data_for_exclusions(self, exclude_select, inclusions, exclusions):
        select_data = {}
        real_exclude_select = exclude_select.union(self.default_exclusions - inclusions)
        real_exclude_select = real_exclude_select.union(exclusions - inclusions)

        for filter_name in real_exclude_select:
            if filter_name in inclusions:
                raise RQLFilterParsingError(details={
                    'error': 'Bad select filter: incompatible properties.',
                })

            select_tree = self.select_tree
            filter_name_parts = filter_name.split('.')
            last_filter_name_part_index = len(filter_name_parts) - 1

            for index, part in enumerate(filter_name_parts):
                if part not in select_tree:
                    raise RQLFilterParsingError(details={
                        'error': 'Bad select filter: -{0}.'.format(filter_name),
                    })

                if index != last_filter_name_part_index:
                    select_tree = select_tree[part]['fields']

            select_data[filter_name] = False

        return select_data

    @staticmethod
    def _prepare_selects(select):
        include_select, exclude_select = [], set()
        for s_prop in select:
            is_included = (s_prop[0] != RQL_MINUS)
            filter_name = s_prop[1:] if s_prop[0] in (RQL_MINUS, RQL_PLUS) else s_prop

            if is_included:
                include_select.append(filter_name)
            else:
                exclude_select.add(filter_name)

        return include_select, exclude_select

    def _build_q_for_search(self, operator, str_value):
        if operator != ComparisonOperators.EQ:
            raise RQLFilterParsingError(details={
                'error': 'Bad search filter: {0}.'.format(operator),
            })

        unquoted_value = self.remove_quotes(str_value)
        if not unquoted_value:
            return Q()

        if not unquoted_value.startswith(RQL_ANY_SYMBOL):
            unquoted_value = '*' + unquoted_value

        if not unquoted_value.endswith(RQL_ANY_SYMBOL):
            unquoted_value += '*'

        q = self._build_q_for_extended_search(unquoted_value)
        for filter_name in self.search_filters:
            q |= self.build_q_for_filter(FilterArgs(
                filter_name, SearchOperators.I_LIKE, unquoted_value,
            ))

        return q

    def _build_q_for_extended_search(self, str_value):
        q = Q()
        extended_search_filter_lookup = FilterLookups.I_LIKE

        for django_orm_route in self.EXTENDED_SEARCH_ORM_ROUTES:
            django_lookup = self._get_searching_django_lookup(
                extended_search_filter_lookup, str_value,
            )
            typed_value = self._get_searching_typed_value(django_lookup, str_value)
            q |= self._build_django_q(
                {'orm_route': django_orm_route},
                django_lookup,
                extended_search_filter_lookup,
                typed_value,
            )

        return q

    def _apply_optimizations(self, queryset, select_data):
        return self.__apply_optimizations(
            OptimizationArgs(queryset, select_data, self.select_tree),
        )

    def __apply_optimizations(self, data):
        """
        :param OptimizationArgs data:
        :return:
        """
        qs, select_data, filter_tree = data.queryset, data.select_data, data.filter_tree

        if filter_tree:
            for node in filter_tree.values():
                filter_path = node['path']

                if select_data.get(filter_path, True):
                    qs = self.__apply_field_optimizations(qs, data, node)

        return qs

    def __apply_field_optimizations(self, qs, data, node):
        select_data, filter_tree = data.select_data, data.filter_tree
        filter_path = node['path']

        optimized_qs = self.optimize_field(
            OptimizationArgs(qs, select_data, filter_tree, node, filter_path),
        )

        optimization = node['qs']
        if optimized_qs is not None:
            qs = optimized_qs
        elif optimization:
            if isinstance(optimization, Annotation):
                qs = self.apply_annotations({filter_path}, qs)
            else:
                qs = optimization.apply(qs)

        return self.__apply_optimizations(
            OptimizationArgs(qs, select_data, node['fields']),
        )

    def _apply_ordering(self, qs, properties):
        if len(properties) == 0:
            return qs
        elif len(properties) > 1:
            raise RQLFilterParsingError(details={
                'error': 'Bad ordering filter: query can contain only one ordering operation.',
            })

        ordering_fields = []
        for prop in properties[0]:
            filter_name, sign = self._get_filter_name_with_sign_for_ordering(prop)
            if filter_name not in self.ordering_filters:
                raise RQLFilterParsingError(details={
                    'error': 'Bad ordering filter: {0}.'.format(filter_name),
                })

            filters = self.filters[filter_name]
            if not isinstance(filters, list):
                filters = [filters]
            for filter_item in filters:
                if filter_item.get('distinct'):
                    self._is_distinct = True

                ordering_name = self._get_filter_ordering_name(filter_item, filter_name)
                ordering_fields.append('{0}{1}'.format(sign, ordering_name))

        return qs.order_by(*ordering_fields)

    @staticmethod
    def _get_filter_name_with_sign_for_ordering(prop):
        if RQL_MINUS == prop[0]:
            filter_name = prop[1:]
            sign = RQL_MINUS
        else:
            filter_name = prop
            sign = ''

        return filter_name, sign

    def _get_filter_ordering_name(self, filter_item, filter_name):
        if filter_item.get('custom'):
            return self.build_name_for_custom_ordering(filter_name)

        return filter_item['orm_route']

    def _build_filters(self, filters, **kwargs):
        """ Converter of provided nested filter configuration to linear inner representation. """
        filter_route = kwargs.get('filter_route', '')
        orm_route = kwargs.get('orm_route', '')
        orm_model = kwargs.get('orm_model')
        select_tree = kwargs.get('select_tree')
        parent_qs = kwargs.get('parent_qs')
        distinct = kwargs.get('distinct', False)

        _model = orm_model or self.MODEL

        if not orm_route:
            self.filters = {}
            select_tree = self.select_tree

        for item in filters:
            if isinstance(item, str):
                field_filter_route = '{0}{1}'.format(filter_route, item)
                field_orm_route = '{0}{1}'.format(orm_route, item)
                field = self._get_field(_model, item)
                self._add_filter_item(
                    field_filter_route, self._build_mapped_item(field, field_orm_route),
                )
                self._fill_select_tree(item, field_filter_route, select_tree, parent_qs=parent_qs)
                continue

            if 'namespace' in item:
                for option in ('filter', 'dynamic', 'custom'):
                    e = "{0}: '{1}' is not supported by namespaces.".format(
                        item['namespace'], option,
                    )
                    assert option not in item, e

                namespace = item['namespace']
                related_filter_route = '{0}{1}'.format(filter_route, namespace)
                orm_field_name = item.get('source', namespace)
                related_orm_route = '{0}{1}__'.format(orm_route, orm_field_name)

                related_model = self._get_field(
                    _model, orm_field_name, get_related=True,
                ).related_model

                qs = item.get('qs')
                tree, p_qs = self._fill_select_tree(
                    namespace,
                    related_filter_route,
                    select_tree,
                    namespace=True,
                    hidden=item.get('hidden', False),
                    qs=qs,
                    parent_qs=parent_qs,
                )

                self._build_filters(
                    item.get('filters', []),
                    filter_route=related_filter_route + '.',
                    orm_route=related_orm_route,
                    orm_model=related_model,
                    select_tree=tree,
                    parent_qs=p_qs,
                    distinct=item.get('distinct', distinct),
                )
                continue

            assert 'filter' in item, "All extended filters must have set 'filter' set."
            filter_name = item['filter']
            field_filter_route = '{0}{1}'.format(filter_route, filter_name)

            self._fill_select_tree(
                filter_name, field_filter_route, select_tree,
                hidden=item.get('hidden', False),
                qs=item.get('qs'),
                parent_qs=parent_qs,
            )

            if item.get('custom', False):
                assert 'lookups' in item, "Custom filters must specify possible lookups."

                self._add_filter_item(field_filter_route, item)
                self._register_ordering_and_search(item, field_filter_route)
                continue

            self._check_use_repr(item, field_filter_route)
            self._check_dynamic(item, field_filter_route, filter_route)
            self._build_filters_for_common_item(
                item, field_filter_route, orm_route, _model, distinct,
            )

    def _build_filters_for_common_item(
        self, item, field_filter_route, orm_route, orm_model, distinct,
    ):
        filter_name = item['filter']
        field = item.get('field')
        kwargs = {
            prop: item.get(prop)
            for prop in ('lookups', 'use_repr', 'null_values', 'openapi', 'hidden')
        }
        kwargs['distinct'] = item.get('distinct', distinct)

        if 'sources' in item:
            items = []
            for source in item['sources']:
                full_orm_route = '{0}{1}'.format(orm_route, source)
                field = field or self._get_field(orm_model, source)
                items.append(self._build_mapped_item(field, full_orm_route, **kwargs))
                self._check_search(item, field_filter_route, field)

        else:
            orm_field_name = item.get('source', filter_name)
            full_orm_route = '{0}{1}'.format(orm_route, orm_field_name)
            field = field or self._get_field(orm_model, orm_field_name)
            items = self._build_mapped_item(field, full_orm_route, **kwargs)
            self._check_search(item, field_filter_route, field)

        self._add_filter_item(field_filter_route, items)
        self._register_ordering_and_search(item, field_filter_route)

    def _fill_select_tree(self, f_name, full_f_name, select_tree,
                          namespace=False, hidden=False, qs=None, parent_qs=None):

        if not self.SELECT:
            return select_tree, None

        if hidden:
            self.default_exclusions.add(full_f_name)

        current_select_tree = select_tree
        filter_name_parts = f_name.split('.')
        last_filter_name_part_index = len(filter_name_parts) - 1

        changed_qs = qs
        if qs:
            # Chains with Annotations are not considered
            if isinstance(qs, Annotation):
                self.annotations[full_f_name] = [qs]
            elif parent_qs and (not isinstance(parent_qs, Annotation)):
                changed_qs = qs.rebuild(parent_qs)

        is_logical_namespace = len(filter_name_parts) > 1
        path = ''
        for index, filter_name_part in enumerate(filter_name_parts):
            path += filter_name_part
            current_select_tree.setdefault(filter_name_part, {
                'hidden': hidden,
                'fields': {},
                'namespace': namespace or (index != last_filter_name_part_index),
                'qs': changed_qs,
                'path': path if is_logical_namespace else full_f_name,
            })
            current_select_tree = current_select_tree[filter_name_part]['fields']
            path += '.'

        return current_select_tree, parent_qs if not qs else changed_qs

    def _add_filter_item(self, filter_name, item):
        e = "'{0}' is a reserved filter name.".format(filter_name)
        assert filter_name not in RESERVED_FILTER_NAMES, e

        self.filters[filter_name] = item

    def _register_ordering_and_search(self, item, field_filter_route):
        if item.get('ordering'):
            self.ordering_filters.add(field_filter_route)

        if item.get('search'):
            self.search_filters.add(field_filter_route)

    def _extend_annotations(self):
        filter_names = tuple(self.filters.keys())
        extended_annotations = defaultdict(list)

        for annotated_filter_name, annotation_list in self.annotations.items():
            for filter_name in filter_names:
                if filter_name.startswith(annotated_filter_name + '.'):
                    extended_annotations[filter_name].append(annotation_list[0])

                    own_annotation = self.annotations.get(filter_name)
                    if own_annotation:
                        extended_annotations[filter_name].append(own_annotation[0])

        self.annotations.update(dict(extended_annotations))

    @classmethod
    def _get_field(cls, base_model, field_name, get_related=False):
        """ Django ORM field getter.

        Notes:
            field_name can have dots or double underscores in them. They are interpreted as
            links to the related models.
        """
        field_name_parts = cls._get_field_name_parts(field_name)
        field_name_parts_length = len(field_name_parts)
        current_model = base_model
        for index, part in enumerate(field_name_parts, start=1):
            current_field = cls._get_model_field(current_model, part)
            if index == field_name_parts_length:
                e = 'Unsupported field type: {0}.'.format(field_name)
                assert get_related or isinstance(current_field, SUPPORTED_FIELD_TYPES), e

                return current_field
            current_model = current_field.related_model

    @staticmethod
    def _get_field_name_parts(field_name):
        if not field_name:
            return []

        return field_name.split('.' if '.' in field_name else '__')

    @classmethod
    def _build_mapped_item(cls, field, field_orm_route, **kwargs):
        lookups = kwargs.get('lookups')
        use_repr = kwargs.get('use_repr')
        null_values = kwargs.get('null_values')
        distinct = kwargs.get('distinct')
        openapi = kwargs.get('openapi')
        hidden = kwargs.get('hidden')

        possible_lookups = lookups or FilterTypes.default_field_filter_lookups(field)
        if not (field.null or cls._is_pk_field(field)):
            possible_lookups.discard(FilterLookups.NULL)

        result = {
            'field': field,
            'orm_route': field_orm_route,
            'lookups': possible_lookups,
            'null_values': null_values or {RQL_NULL},
            'distinct': distinct or False,
            'hidden': hidden or False,
        }

        if use_repr is not None:
            result['use_repr'] = use_repr

        if openapi is not None:
            result['openapi'] = openapi

        return result

    @staticmethod
    def _is_pk_field(field):
        return field == field.model._meta.pk if hasattr(field, 'model') else False

    @staticmethod
    def _get_model_field(model, field_name):
        return model._meta.get_field(field_name)

    @classmethod
    def _get_filter_lookup(cls, filter_name, operator, str_value, available_lookups, null_values):
        filter_lookup = cls._get_filter_lookup_by_operator(operator)

        if str_value in null_values:
            null_lookups = {FilterLookups.EQ, FilterLookups.NE}
            if (FilterLookups.NULL not in available_lookups) or (filter_lookup not in null_lookups):
                raise RQLFilterLookupError(**cls._get_error_details(
                    filter_name, filter_lookup, str_value,
                ))

        if str_value == RQL_EMPTY:
            available_lookups = {FilterLookups.EQ, FilterLookups.NE}

        if filter_lookup not in available_lookups:
            raise RQLFilterLookupError(**cls._get_error_details(
                filter_name, filter_lookup, str_value,
            ))

        return filter_lookup

    @classmethod
    def _get_django_lookup(cls, filter_lookup, str_value, null_values):
        if str_value in null_values:
            return DjangoLookups.NULL

        if cls._is_searching_lookup(filter_lookup):
            return cls._get_searching_django_lookup(filter_lookup, str_value)

        mapper = {
            FilterLookups.EQ: DjangoLookups.EXACT,
            FilterLookups.NE: DjangoLookups.EXACT,
            FilterLookups.LT: DjangoLookups.LT,
            FilterLookups.LE: DjangoLookups.LTE,
            FilterLookups.GT: DjangoLookups.GT,
            FilterLookups.GE: DjangoLookups.GTE,
        }
        return mapper[filter_lookup]

    @classmethod
    def _get_searching_django_lookup(cls, filter_lookup, str_value):
        val, _ = cls._reflect_like_value(str_value)

        prefix = 'I_' if filter_lookup == FilterLookups.I_LIKE else ''

        pattern = 'REGEX'
        if RQL_ANY_SYMBOL not in val:
            pattern = 'EXACT'
        elif val == RQL_ANY_SYMBOL:
            pattern = 'REGEX'
        else:
            sep_count = val.count(RQL_ANY_SYMBOL)
            if sep_count == 1:
                if val[0] == RQL_ANY_SYMBOL:
                    pattern = 'ENDSWITH'
                elif val[-1] == RQL_ANY_SYMBOL:
                    pattern = 'STARTSWITH'
            elif sep_count == 2 and val[0] == RQL_ANY_SYMBOL == val[-1]:
                pattern = 'CONTAINS'

        return getattr(DjangoLookups, '{0}{1}'.format(prefix, pattern))

    @classmethod
    def _get_typed_value(cls, filter_name, filter_lookup, str_value, django_field,
                         use_repr, null_values, django_lookup):
        if str_value in null_values:
            return True

        try:
            if cls._is_searching_lookup(filter_lookup):
                return cls._get_searching_typed_value(django_lookup, str_value)

            typed_value = cls._convert_value(django_field, str_value, use_repr=use_repr)
            return typed_value
        except (ValueError, TypeError, decimal.InvalidOperation):
            raise RQLFilterValueError(**cls._get_error_details(
                filter_name, filter_lookup, str_value,
            ))

    @classmethod
    def _reflect_like_value(cls, str_value):
        star_replacer = uuid4().hex
        return '\\'.join(
            v.replace(r'\{0}'.format(RQL_ANY_SYMBOL), star_replacer)
            for v in cls.remove_quotes(str_value).split(r'\\')
        ), star_replacer

    @classmethod
    def _get_searching_typed_value(cls, django_lookup, str_value):
        val, star_replacer = cls._reflect_like_value(str_value)

        if '{0}{1}'.format(RQL_ANY_SYMBOL, RQL_ANY_SYMBOL) in val:
            raise ValueError

        if django_lookup not in (DjangoLookups.REGEX, DjangoLookups.I_REGEX):
            return val.replace(RQL_ANY_SYMBOL, '').replace(star_replacer, RQL_ANY_SYMBOL)

        any_symbol_regex = '(.*)'
        if val == RQL_ANY_SYMBOL:
            return any_symbol_regex

        new_val = cls._escape_regex_special_symbols(val)
        new_val = new_val[1:] if val[0] == RQL_ANY_SYMBOL else '^{0}'.format(new_val)
        new_val = new_val[:-1] if val[-1] == RQL_ANY_SYMBOL else '{0}$'.format(new_val)
        return new_val.replace(RQL_ANY_SYMBOL, any_symbol_regex).replace(
            star_replacer, RQL_ANY_SYMBOL,
        )

    @staticmethod
    def _escape_regex_special_symbols(str_value):
        """Returns escaped string

        Current like/ilike protocol (* in any place) implementation requires to execute regex.
        Input string could be a not valid (braces not balanced db error)
        or misinterpreted (symbols range). Regex is not supported by RQL so we can safely
        escape redundant special symbols.
        """
        return (
            re.escape(str_value)
            .replace(r'\{0}'.format(RQL_ANY_SYMBOL), RQL_ANY_SYMBOL)
        )

    @classmethod
    def _convert_value(cls, django_field, str_value, use_repr=False):
        val = cls.remove_quotes(str_value)
        filter_type = FilterTypes.field_filter_type(django_field)

        if filter_type == FilterTypes.FLOAT:
            return float(val)

        elif filter_type == FilterTypes.DECIMAL:
            if '.' in val:
                integer_part, fractional_part = val.split('.', 1)
                val = integer_part + '.' + fractional_part[:django_field.decimal_places]
            return decimal.Decimal(val)

        elif filter_type == FilterTypes.DATE:
            return cls._convert_date_value(val)

        elif filter_type == FilterTypes.DATETIME:
            return cls._convert_datetime_value(val)

        elif filter_type == FilterTypes.BOOLEAN:
            return cls._convert_boolean_value(val)

        if val == RQL_EMPTY:
            if (filter_type == FilterTypes.INT) or (not django_field.blank):
                raise ValueError
            return ''

        choices = getattr(django_field, 'choices', None)
        if not choices:
            if filter_type == FilterTypes.INT:
                return int(val)
            return val

        return cls._get_choices_field_db_value(val, choices, filter_type, use_repr)

    @staticmethod
    def _convert_date_value(value):
        dt = parse_date(value)
        if dt is None:
            raise ValueError
        return dt

    @staticmethod
    def _convert_datetime_value(value):
        dt = parse_datetime(value)
        if dt is None:  # pragma: no cover
            dt = parse_date(value)
            if dt is None:
                raise ValueError

            return datetime(year=dt.year, month=dt.month, day=dt.day)
        return dt

    @staticmethod
    def _convert_boolean_value(value):
        if value not in (RQL_FALSE, RQL_TRUE):
            raise ValueError
        return value == RQL_TRUE

    @classmethod
    def _get_choices_field_db_value(cls, value, choices, filter_type, use_repr):
        if type(choices).__name__ == 'Choices':
            return cls._get_choice_class_db_value(value, choices, filter_type, use_repr)

        # `use_repr=True` makes it possible to map choice representations to real db values
        # F.e.: `choices=((0, 'v0'), (1, 'v1'))` can be filtered by 'v1' if `use_repr=True` or
        # by '1' if `use_repr=False`
        if isinstance(choices[0], tuple):
            iterator = iter(
                choice[0] for choice in choices if str(choice[int(use_repr)]) == value
            )
        else:
            iterator = iter(choice for choice in choices if choice == value)
        try:
            db_value = next(iterator)
            return db_value
        except StopIteration:
            raise ValueError

    @staticmethod
    def _get_choice_class_db_value(value, choices, filter_type, use_repr):
        if use_repr:
            try:
                db_value = next(
                    db_value for db_value, value_repr in choices if value_repr == value
                )
                return db_value
            except StopIteration:
                raise ValueError

        if filter_type == FilterTypes.INT:
            db_value = int(value)
        else:
            db_value = value

        if db_value not in choices:
            raise ValueError

        return db_value

    def _build_django_q(self, filter_item, django_lookup, filter_lookup, typed_value):
        kwargs = {'{0}__{1}'.format(filter_item['orm_route'], django_lookup): typed_value}
        return ~Q(**kwargs) if filter_lookup == FilterLookups.NE else Q(**kwargs)

    @staticmethod
    def _get_filter_lookup_by_operator(grammar_operator):
        mapper = {
            ComparisonOperators.EQ: FilterLookups.EQ,
            ComparisonOperators.NE: FilterLookups.NE,
            ComparisonOperators.LT: FilterLookups.LT,
            ComparisonOperators.LE: FilterLookups.LE,
            ComparisonOperators.GT: FilterLookups.GT,
            ComparisonOperators.GE: FilterLookups.GE,
            SearchOperators.LIKE: FilterLookups.LIKE,
            SearchOperators.I_LIKE: FilterLookups.I_LIKE,
        }
        return mapper[grammar_operator]

    @staticmethod
    def _get_error_details(filter_name, filter_lookup, str_value):
        return {
            'details': {
                'filter': filter_name,
                'lookup': filter_lookup,
                'value': str_value,
            },
        }

    @staticmethod
    def remove_quotes(str_value):
        # Values can start with single or double quotes, if they have special chars inside them
        return str_value[1:-1] if str_value and str_value[0] in ('"', "'") else str_value

    @staticmethod
    def _is_searching_lookup(filter_lookup):
        return filter_lookup in (FilterLookups.LIKE, FilterLookups.I_LIKE)

    @staticmethod
    def _check_use_repr(filter_item, filter_name):
        e = "{0}: 'use_repr' and 'ordering' can't be used together.".format(filter_name)
        assert not (filter_item.get('use_repr') and filter_item.get('ordering')), e

        e = "{0}: 'use_repr' and 'search' can't be used together.".format(filter_name)
        assert not (filter_item.get('use_repr') and filter_item.get('search')), e

    @staticmethod
    def _check_dynamic(filter_item, filter_name, filter_route):
        field = filter_item.get('field')
        if filter_item.get('dynamic', False):
            e = "{0}: dynamic filters are not supported in namespaces.".format(filter_name)
            assert filter_route == '', e

            e = "{0}: dynamic filters must have 'field' set.".format(filter_name)
            assert field is not None, e

        else:
            e = "{0}: common filters can't have 'field' set.".format(filter_name)
            assert not filter_item.get('custom', False) and field is None, e

    @staticmethod
    def _check_search(filter_item, filter_name, field):
        is_non_string_field_type = FilterTypes.field_filter_type(field) != FilterTypes.STRING

        e = "{0}: 'search' can be applied only to text filters.".format(filter_name)
        assert not (filter_item.get('search') and is_non_string_field_type), e


class AutoRQLFilterClass(RQLFilterClass):
    """Filter class that automatically collects filters for simple model fields."""

    EXCLUDE_FILTERS = ()
    """This class will collect all simple model fields except the ones in this field."""

    def _get_init_filters(self):
        described_filters = self._described_filters
        filters = tuple(
            {
                'filter': f.name,
                'ordering': True,
                'search': FilterTypes.field_filter_type(f) == FilterTypes.STRING,
            }
            for f in self.MODEL._meta.get_fields()
            if isinstance(f, SUPPORTED_FIELD_TYPES) and (
                f.name not in self.EXCLUDE_FILTERS
            ) and (
                f.name not in described_filters
            )
        )

        return described_filters + filters

    @cached_property
    def _described_filters(self):
        return tuple(self.FILTERS) if self.FILTERS else ()


class NestedAutoRQLFilterClass(AutoRQLFilterClass):
    """
    Filter class that automatically collects filters for all model fields with
    specified depth for related models.
    """
    SELECT = True

    DEPTH = 1
    """
    Specifies how deep model relations will be traversed.
    If `DEPTH = 0` this class behaves as `AutoRQLFilterClass`.
    """

    def _get_init_filters(self):
        if self.DEPTH == 0:
            return super()._get_init_filters()

        depth = 0
        global_namespace = []
        iterator = [(self.MODEL, global_namespace, None, None)]

        while depth <= self.DEPTH and iterator:
            iterator = self._iter_models_to_get_filters(depth, iterator)
            depth += 1

        return self._described_filters + tuple(global_namespace)

    def _iter_models_to_get_filters(self, depth, iterator):
        related_models = []

        for model_data in iterator:
            related_models.extend(self._iter_model_to_get_filters(depth, model_data))

        return related_models

    def _iter_model_to_get_filters(self, depth, model_data):
        model, namespace, circular_related_name, prefix = model_data
        through_models = set()
        model_related_models = []

        for field in model._meta.get_fields():
            rel_f_name = self._get_relative_field_name(field, circular_related_name, prefix)
            if not rel_f_name:
                continue

            if field.is_relation:
                if self._is_through_field(field):
                    through_models.add(field.through)

                relation_data = self._add_relation_to_iterated_models(depth, field, namespace)
                model_related_models.append(relation_data + (rel_f_name,))
                continue

            namespace.append({
                'filter': field.name,
                'ordering': True,
                'search': FilterTypes.field_filter_type(field) == FilterTypes.STRING,
            })

        return [i for i in model_related_models if i[0] not in through_models]

    def _add_relation_to_iterated_models(self, depth, field, namespace):
        if isinstance(field, (ForeignKey, ManyToManyField)):
            circular_related_name = field.remote_field.name
        else:
            circular_related_name = field.field.name

        namespace_filters = []
        if depth < self.DEPTH:
            namespace.append({
                'namespace': field.name,
                'filters': namespace_filters,
                'qs': self._get_field_optimization(field),
            })

        return field.related_model, namespace_filters, circular_related_name

    def _get_relative_field_name(self, field, circular_related_name, prefix):
        field_name = field.name
        if circular_related_name and field_name == circular_related_name:
            # This is needed to avoid circular dependencies
            return

        rel_f_name = '.'.join((prefix, field_name)) if prefix else field_name
        if rel_f_name in self.EXCLUDE_FILTERS or rel_f_name in self._described_filters:
            return

        return rel_f_name

    def _get_field_optimization(self, field):
        if not self.SELECT:
            return

        if isinstance(field, (ForeignKey, OneToOneField, OneToOneRel)):
            return NSR(field.name)

        if not self._is_through_field(field):
            return NPR(field.name)

    @staticmethod
    def _is_through_field(field):
        return getattr(field, 'through', None)
