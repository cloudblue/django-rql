from __future__ import unicode_literals

import six
from django.db import models
from django.db.models import Q
from django.utils.dateparse import parse_date, parse_datetime

from dj_rql.constants import (
    ComparisonOperators, DjangoLookups, FilterLookups, FilterTypes, SUPPORTED_FIELD_TYPES,
)


class RQLFilterClass(object):
    MODEL = None
    FILTERS = None

    def __init__(self, queryset):
        assert self.MODEL, 'Model must be set for Filter Class.'
        assert isinstance(self.FILTERS, list) and self.FILTERS, \
            'List of filters must be set for Filter Class.'

        self.mapper = {}
        self._fill_mapper(self.FILTERS)

        self.queryset = queryset

    def apply_filters(self, query):
        # TODO: Implement
        return self.queryset.distinct()

    @classmethod
    def _change_django_lookup_by_value(cls, django_lookup, typed_value):
        # TODO: Add support for specific values, like NULL
        return django_lookup

    def get_django_q_for_filter_expression(self, filter_name, operator, str_value):
        if filter_name not in self.mapper:
            return Q()

        filter_item = self.mapper[filter_name]

        base_item = filter_item[0] if isinstance(filter_item, list) else filter_item
        django_field = base_item['field']
        available_lookups = base_item['lookups']
        use_repr = base_item.get('use_repr', False)

        filter_lookup = self._get_filter_lookup_by_operator(operator)
        if filter_lookup not in available_lookups:
            return Q()

        django_lookup = self._get_django_lookup_by_filter_lookup(filter_lookup)

        # TODO: Check Value Error in tests
        typed_value = self._convert_value(django_field, str_value, use_repr=use_repr)
        django_lookup = self._change_django_lookup_by_value(django_lookup, typed_value)

        if not isinstance(filter_item, list):
            return self._get_django_q_for_filter_expression(
                filter_item, django_lookup, filter_lookup, typed_value,
            )

        q = Q()
        for item in filter_item:
            item_q = self._get_django_q_for_filter_expression(
                item, django_lookup, filter_lookup, typed_value,
            )
            q = q & item_q if filter_lookup == FilterLookups.NE else q | item_q
        return q

    @staticmethod
    def _convert_value(django_field, str_value, use_repr=False):
        if use_repr:
            db_value = next(choice[0] for choice in django_field.choices if choice[1] == str_value)
            return db_value

        filter_type = FilterTypes.field_filter_type(django_field)
        if filter_type == FilterTypes.INT:
            return int(str_value)
        elif filter_type == FilterTypes.FLOAT:
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
        return str_value

    def _fill_mapper(self, filters, filter_route='', orm_route='', orm_model=None):
        model = orm_model or self.MODEL

        if not orm_route:
            self.mapper = {}

        for item in filters:
            if isinstance(item, six.string_types):
                field_filter_route = '{}{}'.format(filter_route, item)
                field_orm_route = '{}{}'.format(orm_route, item)
                field = self._get_field(model, item)
                self.mapper[field_filter_route] = {
                    'field': field,
                    'orm_route': field_orm_route,
                    'lookups': FilterTypes.default_field_filter_lookups(field),
                }

            elif 'namespace' in item:
                related_filter_route = '{}{}.'.format(filter_route, item['namespace'])
                orm_field_name = item.get('source', item['namespace'])
                related_orm_route = '{}{}__'.format(orm_route, orm_field_name)

                related_model = self._get_model_field(model, orm_field_name).related_model
                self._fill_mapper(
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

                        mapping.append({
                            'field': field,
                            'orm_route': full_orm_route,
                            'use_repr': item.get('use_repr', False),
                            'lookups': item.get(
                                'lookups', FilterTypes.default_field_filter_lookups(field),
                            ),
                        })
                else:
                    orm_field_name = item.get('source', item['filter'])
                    full_orm_route = '{}{}'.format(orm_route, orm_field_name)

                    field = self._get_field(model, orm_field_name)
                    mapping = {
                        'field': field,
                        'orm_route': full_orm_route,
                        'use_repr': item.get('use_repr', False),
                        'lookups': item.get(
                            'lookups', FilterTypes.default_field_filter_lookups(field),
                        ),
                    }
                self.mapper[field_filter_route] = mapping

    @classmethod
    def _get_field(cls, base_model, field_name):
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
    def _get_model_field(model, field_name):
        return model._meta.get_field(field_name)

    @staticmethod
    def _get_django_q_for_filter_expression(filter_item, django_lookup, filter_lookup, typed_value):
        kwargs = {'{}__{}'.format(filter_item['orm_route'], django_lookup): typed_value}
        return ~Q(**kwargs) if filter_lookup == FilterLookups.NE else Q(**kwargs)

    @staticmethod
    def _get_filter_lookup_by_operator(operator):
        mapper = {
            ComparisonOperators.EQ: FilterLookups.EQ,
            ComparisonOperators.NE: FilterLookups.NE,
            ComparisonOperators.LT: FilterLookups.LT,
            ComparisonOperators.LE: FilterLookups.LE,
            ComparisonOperators.GT: FilterLookups.GT,
            ComparisonOperators.GE: FilterLookups.GE,
        }
        return mapper[operator]

    @staticmethod
    def _get_django_lookup_by_filter_lookup(filter_lookup):
        mapper = {
            FilterLookups.EQ: DjangoLookups.EXACT,
            FilterLookups.NE: DjangoLookups.EXACT,
            FilterLookups.LT: DjangoLookups.LT,
            FilterLookups.LE: DjangoLookups.LTE,
            FilterLookups.GT: DjangoLookups.GT,
            FilterLookups.GE: DjangoLookups.GTE,
        }
        return mapper[filter_lookup]
