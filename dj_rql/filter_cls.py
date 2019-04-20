from __future__ import unicode_literals

import six
from django.db.models import Q
from django.utils.dateparse import parse_date, parse_datetime
from lark.exceptions import LarkError

from dj_rql.constants import (
    ComparisonOperators, DjangoLookups, FilterLookups, FilterTypes, SearchOperators,
    RESERVED_FILTER_NAMES, RQL_ANY_SYMBOL, RQL_EMPTY, RQL_NULL, SUPPORTED_FIELD_TYPES,
)
from dj_rql.exceptions import RQLFilterLookupError, RQLFilterValueError
from dj_rql.parser import RQLParser
from dj_rql.transformer import RQLToDjangoORMTransformer


iterable_types = (list, tuple)


class RQLFilterClass(object):
    MODEL = None
    FILTERS = None

    def __init__(self, queryset):
        assert self.MODEL, 'Model must be set for Filter Class.'
        assert isinstance(self.FILTERS, iterable_types) and self.FILTERS, \
            'List of filters must be set for Filter Class.'

        self.ordering_filters = set()
        self.search_filters = set()

        self.filters = {}
        self._build_filters(self.FILTERS)

        self.queryset = queryset

    def apply_filters(self, query):
        """ Entry point function for model queryset filtering. """
        if not query:
            return self.queryset

        rql_ast = RQLParser.parse_query(query)

        rql_transformer = RQLToDjangoORMTransformer(self)
        try:
            qs = rql_transformer.transform(rql_ast)
        except LarkError as e:
            # Lark reraises it's errors, but the original ones are needed
            raise e.orig_exc
        self.queryset = self._apply_ordering(qs, rql_transformer.ordering_filters)
        return self.queryset

    def _apply_ordering(self, qs, properties):
        return qs.order_by(*properties)

    def build_q_for_filter(self, filter_name, operator, str_value):
        """ Django Q() builder for the given expression. """
        if filter_name not in self.filters:
            return Q()

        filter_item = self.filters[filter_name]

        base_item = filter_item[0] if isinstance(filter_item, iterable_types) else filter_item
        django_field = base_item['field']
        available_lookups = base_item['lookups']
        use_repr = base_item.get('use_repr', False)
        null_values = base_item.get('null_values', set())

        filter_lookup = self._get_filter_lookup(operator, str_value, available_lookups, null_values)
        django_lookup = self._get_django_lookup(filter_lookup, str_value, null_values)
        typed_value = self._get_typed_value(
            filter_lookup, str_value, django_field, use_repr, null_values, django_lookup,
        )

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

    def _build_filters(self, filters, filter_route='', orm_route='', orm_model=None):
        """ Converter of provided nested filter configuration to linear inner representation. """
        model = orm_model or self.MODEL

        if not orm_route:
            self.filters = {}

        for item in filters:
            if isinstance(item, six.string_types):
                field_filter_route = '{}{}'.format(filter_route, item)
                field_orm_route = '{}{}'.format(orm_route, item)
                field = self._get_field(model, item)
                self._add_filter_item(
                    field_filter_route, self._build_mapped_item(field, field_orm_route),
                )

            elif 'namespace' in item:
                related_filter_route = '{}{}.'.format(filter_route, item['namespace'])
                orm_field_name = item.get('source', item['namespace'])
                related_orm_route = '{}{}__'.format(orm_route, orm_field_name)

                related_model = self._get_model_field(model, orm_field_name).related_model
                self._build_filters(
                    item.get('filters', []), related_filter_route,
                    related_orm_route, related_model,
                )

            else:
                use_repr = item.get('use_repr')
                ordering = item.get('ordering')
                assert not (use_repr and ordering), \
                    "{}: 'use_repr' and 'ordering' can't be used together.".format(item['filter'])

                field_filter_route = '{}{}'.format(filter_route, item['filter'])
                kwargs = {
                    'lookups': item.get('lookups'),
                    'use_repr': use_repr,
                    'null_values': item.get('null_values'),
                }

                if 'sources' in item:
                    items = []
                    for source in item['sources']:
                        full_orm_route = '{}{}'.format(orm_route, source)
                        field = self._get_field(model, source)
                        items.append(self._build_mapped_item(field, full_orm_route, **kwargs))

                else:
                    orm_field_name = item.get('source', item['filter'])
                    full_orm_route = '{}{}'.format(orm_route, orm_field_name)
                    field = self._get_field(model, orm_field_name)
                    items = self._build_mapped_item(field, full_orm_route, **kwargs)

                self._add_filter_item(field_filter_route, items)

                if ordering:
                    self.ordering_filters.add(field_filter_route)

                if item.get('search'):
                    self.search_filters.add(field_filter_route)

    def _add_filter_item(self, filter_name, item):
        assert filter_name not in RESERVED_FILTER_NAMES, \
            "'{}' is a reserved filter name.".format(filter_name)
        self.filters[filter_name] = item

    @classmethod
    def _get_field(cls, base_model, field_name):
        """ Django ORM field getter.

        Notes:
            field_name can have dots or double underscores in them. They are interpreted as
            links to the related models.
        """
        field_name_parts = field_name.split('.' if '.' in field_name else '__')
        field_name_parts_length = len(field_name_parts)
        current_model = base_model
        for index, part in enumerate(field_name_parts, start=1):
            current_field = cls._get_model_field(current_model, part)
            if index == field_name_parts_length:
                assert isinstance(current_field, SUPPORTED_FIELD_TYPES), \
                    'Unsupported field type: {}.'.format(field_name)
                return current_field
            current_model = current_field.related_model

    @staticmethod
    def _build_mapped_item(field, field_orm_route, lookups=None, use_repr=None, null_values=None):
        possible_lookups = lookups or FilterTypes.default_field_filter_lookups(field)
        if not field.null:
            possible_lookups.discard(FilterLookups.NULL)

        result = {
            'field': field,
            'orm_route': field_orm_route,
            'lookups': possible_lookups,
        }

        if use_repr is not None:
            result['use_repr'] = use_repr
        if FilterLookups.NULL in possible_lookups:
            result['null_values'] = null_values or {RQL_NULL}

        return result

    @staticmethod
    def _get_model_field(model, field_name):
        return model._meta.get_field(field_name)

    @classmethod
    def _get_filter_lookup(cls, operator, str_value, available_lookups, null_values):
        filter_lookup = cls._get_filter_lookup_by_operator(operator)

        if str_value in null_values:
            null_lookups = {FilterLookups.EQ, FilterLookups.NE}
            if (FilterLookups.NULL not in available_lookups) or (filter_lookup not in null_lookups):
                raise RQLFilterLookupError(**cls._get_error_details(filter_lookup, str_value))

        if str_value == RQL_EMPTY:
            available_lookups = {FilterLookups.EQ, FilterLookups.NE}

        if filter_lookup not in available_lookups:
            raise RQLFilterLookupError(**cls._get_error_details(filter_lookup, str_value))

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
        val = cls._remove_quotes(str_value)

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

        return getattr(DjangoLookups, '{}{}'.format(prefix, pattern))

    @classmethod
    def _get_typed_value(cls, filter_lookup, str_value, django_field,
                         use_repr, null_values, django_lookup):
        if str_value in null_values:
            return True

        try:
            if cls._is_searching_lookup(filter_lookup):
                return cls._get_searching_typed_value(django_lookup, str_value)

            typed_value = cls._convert_value(django_field, str_value, use_repr=use_repr)
            return typed_value
        except (ValueError, TypeError):
            raise RQLFilterValueError(**cls._get_error_details(filter_lookup, str_value))

    @classmethod
    def _get_searching_typed_value(cls, django_lookup, str_value):
        if '{}{}'.format(RQL_ANY_SYMBOL, RQL_ANY_SYMBOL) in str_value:
            raise ValueError

        val = cls._remove_quotes(str_value)

        if django_lookup not in (DjangoLookups.REGEX, DjangoLookups.I_REGEX):
            return val.replace(RQL_ANY_SYMBOL, '')

        any_symbol_regex = '(.*?)'
        if val == RQL_ANY_SYMBOL:
            return any_symbol_regex

        new_val = val
        new_val = new_val[1:] if val[0] == RQL_ANY_SYMBOL else '^{}'.format(new_val)
        new_val = new_val[:-1] if val[-1] == RQL_ANY_SYMBOL else '{}$'.format(new_val)
        return new_val.replace(RQL_ANY_SYMBOL, any_symbol_regex)

    @classmethod
    def _convert_value(cls, django_field, str_value, use_repr=False):
        val = cls._remove_quotes(str_value)
        filter_type = FilterTypes.field_filter_type(django_field)

        if filter_type == FilterTypes.FLOAT:
            return float(val)

        elif filter_type == FilterTypes.DECIMAL:
            value = float(val)
            if django_field.decimal_places is not None:
                value = round(value, django_field.decimal_places)
            return value

        elif filter_type == FilterTypes.DATE:
            dt = parse_date(val)
            if dt is None:
                raise ValueError
        elif filter_type == FilterTypes.DATETIME:
            dt = parse_datetime(val)
            if dt is None:
                raise ValueError

        elif filter_type == FilterTypes.BOOLEAN:
            if val not in ('false', 'true'):
                raise ValueError
            return val == 'true'

        if val == RQL_EMPTY:
            if (filter_type == FilterTypes.INT) or (not django_field.blank):
                raise ValueError
            return ''

        choices = getattr(django_field, 'choices', None)
        if not choices:
            if filter_type == FilterTypes.INT:
                return int(val)
            return val

        # `use_repr=True` makes it possible to map choice representations to real db values
        # F.e.: `choices=((0, 'v0'), (1, 'v1'))` can be filtered by 'v1' if `use_repr=True` or
        # by '1' if `use_repr=False`
        if isinstance(choices[0], tuple):
            iterator = iter(
                choice[0] for choice in choices if str(choice[int(use_repr)]) == val
            )
        else:
            iterator = iter(choice for choice in choices if choice == val)
        try:
            db_value = next(iterator)
            return db_value
        except StopIteration:
            raise ValueError

    @staticmethod
    def _build_django_q(filter_item, django_lookup, filter_lookup, typed_value):
        kwargs = {'{}__{}'.format(filter_item['orm_route'], django_lookup): typed_value}
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
    def _get_error_details(filter_lookup, str_value):
        return {
            'details': {
                'lookup': filter_lookup,
                'value': str_value,
            },
        }

    @staticmethod
    def _remove_quotes(str_value):
        # Values can start with single or double quotes, if they have special chars inside them
        return str_value[1:-1] if str_value[0] in ('"', "'") else str_value

    @staticmethod
    def _is_searching_lookup(filter_lookup):
        return filter_lookup in (FilterLookups.LIKE, FilterLookups.I_LIKE)
