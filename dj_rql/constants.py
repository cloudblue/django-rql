#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from django.db import models
from py_rql.constants import FilterLookups, FilterTypes as FT


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


class FilterTypes(FT):
    mapper = [
        (models.AutoField, FT.INT),
        (models.BooleanField, FT.BOOLEAN),
        (models.NullBooleanField, FT.BOOLEAN),
        (models.DateTimeField, FT.DATETIME),
        (models.DateField, FT.DATE),
        (models.DecimalField, FT.DECIMAL),
        (models.FloatField, FT.FLOAT),
        (models.IntegerField, FT.INT),
        (models.TextField, FT.STRING),
        (models.UUIDField, FT.STRING),
        (models.CharField, FT.STRING),
    ]

    @classmethod
    def field_filter_type(cls, field):
        return next(
            (
                filter_type for base_cls, filter_type in cls.mapper
                if issubclass(field.__class__, base_cls)
            ),
            cls.STRING,
        )

    @classmethod
    def default_field_filter_lookups(cls, field):
        lookups = {
            cls.INT: FilterLookups.numeric(),
            cls.DECIMAL: FilterLookups.numeric(),
            cls.FLOAT: FilterLookups.numeric(),
            cls.DATE: FilterLookups.numeric(),
            cls.DATETIME: FilterLookups.numeric(),
            cls.STRING: FilterLookups.string(),
            cls.BOOLEAN: FilterLookups.boolean(),
        }
        return lookups[cls.field_filter_type(field)]


class DjangoLookups:
    EXACT = 'exact'
    GT = 'gt'
    GTE = 'gte'
    LT = 'lt'
    LTE = 'lte'

    NULL = 'isnull'

    I_EXACT = 'iexact'
    CONTAINS = 'contains'
    I_CONTAINS = 'icontains'
    STARTSWITH = 'startswith'
    I_STARTSWITH = 'istartswith'
    ENDSWITH = 'endswith'
    I_ENDSWITH = 'iendswith'
    REGEX = 'regex'
    I_REGEX = 'iregex'

    IN = 'in'

    @classmethod
    def all(cls):
        return {
            cls.IN,
            cls.NULL,
            cls.EXACT,
            cls.I_EXACT,
            cls.CONTAINS,
            cls.I_CONTAINS,
            cls.STARTSWITH,
            cls.I_STARTSWITH,
            cls.ENDSWITH,
            cls.I_ENDSWITH,
            cls.REGEX,
            cls.I_REGEX,
            cls.GT,
            cls.GTE,
            cls.LT,
            cls.LTE,
        }
