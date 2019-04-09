from __future__ import unicode_literals

import six
from django.core.exceptions import FieldDoesNotExist

from django.db import models


SUPPORTED_FIELD_TYPES = (
    models.AutoField,
    models.BigAutoField,
    models.BigIntegerField,
    models.BooleanField,
    models.CharField,
    models.DateField,
    models.DateTimeField,
    models.DecimalField,
    models.EmailField,
    models.FloatField,
    models.IntegerField,
    models.NullBooleanField,
    models.PositiveIntegerField,
    models.PositiveSmallIntegerField,
    models.SlugField,
    models.SmallIntegerField,
    models.TextField,
    models.URLField,
    models.UUIDField,
)


class FilterClass(object):
    MODEL = None
    FIELDS = None

    def __init__(self):
        assert self.MODEL, 'Model must be set for Filter Class.'
        assert isinstance(self.FIELDS, list) and self.FIELDS, \
            'List of fields must be set for Filter Class.'

        self._mapper = {}
        self._fill_mapper(self.FIELDS)

    def _fill_mapper(self, fields, orm_route='', orm_model=None):
        model = orm_model or self.MODEL

        if not orm_route:
            self._mapper = {}

        for item in fields:
            if isinstance(item, six.string_types):
                field_name = item
                source = '{}{}'.format(orm_route, field_name)
                try:
                    field = self._check_field(model, item)
                    self._mapper[source] = {
                        'field': field,
                    }
                except (AttributeError, FieldDoesNotExist, TypeError):
                    pass

            elif 'namespace' in item:
                field_name = item.get('source', item['namespace'])
                new_route = '{}{}__'.format(orm_route, field_name)

                try:
                    new_model = self._check_field(model, field_name).related_model
                    self._fill_mapper(item.get('filters', []), new_route, new_model)
                except (AttributeError, FieldDoesNotExist, TypeError):
                    pass

            else:
                field_name = item.get('source', item['filter'])
                source = '{}{}'.format(orm_route, field_name)

                try:
                    field = self._check_field(model, field_name)
                    dct = {
                        'field': field,
                    }
                    dct.update(item)
                    self._mapper[source] = dct

                except (AttributeError, FieldDoesNotExist, TypeError):
                    pass

    @staticmethod
    def _check_field(model, field_name):
        # TODO: Think over lookup check
        field = model._meta.get_field(field_name)
        assert isinstance(field, SUPPORTED_FIELD_TYPES)
        return field


class RQLFilterClass(FilterClass):
    @classmethod
    def filter_queryset(cls, queryset, query):
        # TODO: Filtering
        return queryset
