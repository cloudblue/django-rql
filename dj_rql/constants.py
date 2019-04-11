from __future__ import unicode_literals

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


class FilterLookups(object):
    EQ = 'eq'
    NE = 'ne'
    GE = 'ge'
    GT = 'gt'
    LE = 'le'
    LT = 'lt'

    @classmethod
    def numeric(cls):
        return {cls.EQ, cls.NE, cls.GE, cls.GT, cls.LT, cls.LE}

    @classmethod
    def string(cls):
        return {cls.EQ, cls.NE}

    @classmethod
    def boolean(cls):
        return {cls.EQ, cls.NE}


class FilterTypes(object):
    INT = 'int'
    FLOAT = 'float'
    DATETIME = 'datetime'
    STRING = 'string'
    BOOLEAN = 'boolean'

    @classmethod
    def field_filter_type(cls, field):
        mapper = {
            models.AutoField: cls.INT,
            models.BigAutoField: cls.INT,
            models.BigIntegerField: cls.INT,
            models.BooleanField: cls.BOOLEAN,
            models.CharField: cls.STRING,
            models.DateField: cls.DATETIME,
            models.DateTimeField: cls.DATETIME,
            models.DecimalField: cls.FLOAT,
            models.EmailField: cls.STRING,
            models.FloatField: cls.FLOAT,
            models.IntegerField: cls.INT,
            models.NullBooleanField: cls.BOOLEAN,
            models.PositiveIntegerField: cls.INT,
            models.PositiveSmallIntegerField: cls.INT,
            models.SlugField: cls.STRING,
            models.SmallIntegerField: cls.INT,
            models.TextField: cls.STRING,
            models.URLField: cls.STRING,
            models.UUIDField: cls.STRING,
        }
        return mapper[type(field)]

    @classmethod
    def default_field_filter_lookups(cls, field):
        lookups = {
            cls.INT: FilterLookups.numeric(),
            cls.FLOAT: FilterLookups.numeric(),
            cls.DATETIME: FilterLookups.numeric(),
            cls.STRING: FilterLookups.string(),
            cls.BOOLEAN: FilterLookups.boolean(),
        }
        return lookups[cls.field_filter_type(field)]


class ComparisonOperators(object):
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    GE = 'ge'
    LT = 'lt'
    LE = 'le'


class LogicalOperators:
    AND = 'and'
    OR = 'or'
    NOT = 'not'

    @staticmethod
    def get_grammar_key(key):
        return '{}_op'.format(key)


class DjangoLookups:
    EXACT = 'exact'
    GT = 'gt'
    GTE = 'gte'
    LT = 'lt'
    LTE = 'lte'
