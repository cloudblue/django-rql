from __future__ import unicode_literals

import six
from django.db.models import Q
from django.utils.dateparse import parse_date, parse_datetime
from lark.exceptions import LarkError

from dj_rql.constants import (
    ComparisonOperators, DjangoLookups, FilterLookups, FilterTypes, SearchOperators,
    LIKE_SEPARATOR, RQL_EMPTY, RQL_NULL, SUPPORTED_FIELD_TYPES,
)
from dj_rql.exceptions import RQLFilterLookupError, RQLFilterParsingError, RQLFilterValueError
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

        self.mapper = {}
        self._build_mapper(self.FILTERS)

        self.queryset = queryset

    def apply_filters(self, query):
        """ Entry point function for model queryset filtering. """
        if not query:
            return self.queryset

        try:
            rql_ast = RQLParser.parse(query)
        except LarkError as e:
            raise RQLFilterParsingError(details={
                'error': str(e),
            })

        self.queryset = RQLToDjangoORMTransformer(self).transform(rql_ast)
        return self.queryset

    def build_q_for_filter(self, filter_name, operator, str_value):
        """ Django Q() builder for the given expression. """
        if filter_name not in self.mapper:
            return Q()

        filter_item = self.mapper[filter_name]

        base_item = filter_item[0] if isinstance(filter_item, iterable_types) else filter_item
        django_field = base_item['field']
        available_lookups = base_item['lookups']
        use_repr = base_item.get('use_repr', False)
        null_values = base_item.get('null_values', set())

        # TODO: Think over refactoring for inner ifs (null, filter)
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

    def _build_mapper(self, filters, filter_route='', orm_route='', orm_model=None):
        """ Converter of provided nested filter configuration to linear inner representation. """
        model = orm_model or self.MODEL

        if not orm_route:
            self.mapper = {}

        for item in filters:
            if isinstance(item, six.string_types):
                field_filter_route = '{}{}'.format(filter_route, item)
                field_orm_route = '{}{}'.format(orm_route, item)
                field = self._get_field(model, item)
                self.mapper[field_filter_route] = self._build_mapped_item(field, field_orm_route)

            elif 'namespace' in item:
                related_filter_route = '{}{}.'.format(filter_route, item['namespace'])
                orm_field_name = item.get('source', item['namespace'])
                related_orm_route = '{}{}__'.format(orm_route, orm_field_name)

                related_model = self._get_model_field(model, orm_field_name).related_model
                self._build_mapper(
                    item.get('filters', []), related_filter_route,
                    related_orm_route, related_model,
                )

            else:
                field_filter_route = '{}{}'.format(filter_route, item['filter'])

                if 'sources' in item:
                    mapping = []
                    for source in item['sources']:
                        full_orm_route = '{}{}'.format(orm_route, source)
                        field = self._get_field(model, source)

                        mapping.append(self._build_mapped_item(
                            field, full_orm_route,
                            lookups=item.get('lookups'), use_repr=item.get('use_repr'),
                            null_values=item.get('null_values'),
                        ))
                else:
                    orm_field_name = item.get('source', item['filter'])
                    full_orm_route = '{}{}'.format(orm_route, orm_field_name)

                    field = self._get_field(model, orm_field_name)
                    mapping = self._build_mapped_item(
                        field, full_orm_route,
                        lookups=item.get('lookups'), use_repr=item.get('use_repr'),
                        null_values=item.get('null_values'),
                    )
                self.mapper[field_filter_route] = mapping

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

        # TODO: Move to a separate method
        if filter_lookup in (FilterLookups.LIKE, FilterLookups.I_LIKE):
            if '{}{}'.format(LIKE_SEPARATOR, LIKE_SEPARATOR) in str_value:
                raise ValueError

            # TODO: Move to a separate method
            val = str_value
            if str_value[0] in ('"', "'"):
                val = str_value[1:-1]

            prefix = 'I_' if filter_lookup == FilterLookups.I_LIKE else ''

            if LIKE_SEPARATOR not in val:
                # TODO: Move to a separate method
                return getattr(DjangoLookups, '{}{}'.format(prefix, DjangoLookups.EXACT))

            sep_count = val.count(LIKE_SEPARATOR)
            if sep_count == 1:
                if val[0] == LIKE_SEPARATOR:
                    return getattr(DjangoLookups, '{}{}'.format(prefix, DjangoLookups.STARTSWITH))
                elif val[-1] == LIKE_SEPARATOR:
                    return getattr(DjangoLookups, '{}{}'.format(prefix, DjangoLookups.ENDSWITH))
            elif sep_count == 2 and val[0] == LIKE_SEPARATOR == val[-1]:
                return getattr(DjangoLookups, '{}{}'.format(prefix, DjangoLookups.CONTAINS))

            return getattr(DjangoLookups, '{}{}'.format(prefix, DjangoLookups.REGEX))

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
    def _get_typed_value(cls, filter_lookup, str_value, django_field,
                         use_repr, null_values, django_lookup):
        if str_value in null_values:
            return True

        try:
            # TODO: Move to a separate method
            if filter_lookup in (FilterLookups.LIKE, FilterLookups.I_LIKE):
                if FilterTypes.field_filter_type(django_field) != FilterTypes.STRING:
                    raise ValueError

                if django_lookup != DjangoLookups.REGEX:
                    return str_value.replace(LIKE_SEPARATOR, '')
                # TODO: Fix regex behaviour
                return str_value

            typed_value = cls._convert_value(django_field, str_value, use_repr=use_repr)
            return typed_value
        except (ValueError, TypeError):
            raise RQLFilterValueError(**cls._get_error_details(filter_lookup, str_value))

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
    def _convert_value(django_field, str_value, use_repr=False):
        # Values can start with single or double quotes, if they have special chars inside them
        if str_value[0] in ('"', "'"):
            str_value = str_value[1:-1]
        filter_type = FilterTypes.field_filter_type(django_field)

        if filter_type == FilterTypes.FLOAT:
            return float(str_value)

        elif filter_type == FilterTypes.DECIMAL:
            value = float(str_value)
            if django_field.decimal_places is not None:
                value = round(value, django_field.decimal_places)
            return value

        elif filter_type == FilterTypes.DATE:
            dt = parse_date(str_value)
            if dt is None:
                raise ValueError
        elif filter_type == FilterTypes.DATETIME:
            dt = parse_datetime(str_value)
            if dt is None:
                raise ValueError

        elif filter_type == FilterTypes.BOOLEAN:
            if str_value not in ('false', 'true'):
                raise ValueError
            return str_value == 'true'

        if str_value == RQL_EMPTY:
            if (filter_type == FilterTypes.INT) or (not django_field.blank):
                raise ValueError
            return ''

        choices = getattr(django_field, 'choices', None)
        if not choices:
            if filter_type == FilterTypes.INT:
                return int(str_value)
            return str_value

        # `use_repr=True` makes it possible to map choice representations to real db values
        # F.e.: `choices=((0, 'v0'), (1, 'v1'))` can be filtered by 'v1' if `use_repr=True` or
        # by '1' if `use_repr=False`
        if isinstance(choices[0], tuple):
            iterator = iter(
                choice[0] for choice in choices if str(choice[int(use_repr)]) == str_value
            )
        else:
            iterator = iter(choice for choice in choices if choice == str_value)
        try:
            db_value = next(iterator)
            return db_value
        except StopIteration:
            raise ValueError

    @staticmethod
    def _get_error_details(filter_lookup, str_value):
        return {
            'details': {
                'lookup': filter_lookup,
                'value': str_value,
            },
        }
