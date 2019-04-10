from __future__ import unicode_literals

import six

from dj_rql.constants import FilterTypes, SUPPORTED_FIELD_TYPES


class FilterClass(object):
    MODEL = None
    FILTERS = None

    def __init__(self):
        assert self.MODEL, 'Model must be set for Filter Class.'
        assert isinstance(self.FILTERS, list) and self.FILTERS, \
            'List of filters must be set for Filter Class.'

        self.mapper = {}
        self._fill_mapper(self.FILTERS)
        pass

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
                    'lookups': FilterTypes.default_field_lookups(field),
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
                orm_field_name = item.get('source', item['filter'])
                full_orm_route = '{}{}'.format(orm_route, orm_field_name)

                field = self._get_field(model, orm_field_name)
                self.mapper[field_filter_route] = {
                    'field': field,
                    'orm_route': full_orm_route,
                    'use_repr': item.get('use_repr', False),
                    'lookups': item.get('lookups', FilterTypes.default_field_lookups(field)),
                }

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
