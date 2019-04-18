from __future__ import unicode_literals

from django.db import models


RQL_ANY_SYMBOL = '*'
RQL_EMPTY = 'empty()'
RQL_NULL = 'null()'


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

    IN = 'in'
    OUT = 'out'

    NULL = 'null'

    LIKE = 'like'
    I_LIKE = 'ilike'

    @classmethod
    def numeric(cls):
        return {cls.EQ, cls.NE, cls.GE, cls.GT, cls.LT, cls.LE, cls.IN, cls.OUT, cls.NULL}

    @classmethod
    def string(cls):
        return {cls.EQ, cls.NE, cls.IN, cls.OUT, cls.NULL, cls.LIKE, cls.I_LIKE}

    @classmethod
    def boolean(cls):
        return {cls.EQ, cls.NE, cls.NULL}


class FilterTypes(object):
    INT = 'int'
    DECIMAL = 'decimal'
    FLOAT = 'float'
    DATE = 'date'
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
            models.DateField: cls.DATE,
            models.DateTimeField: cls.DATETIME,
            models.DecimalField: cls.DECIMAL,
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
            cls.DECIMAL: FilterLookups.numeric(),
            cls.FLOAT: FilterLookups.numeric(),
            cls.DATE: FilterLookups.numeric(),
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


class ListOperators(object):
    IN = 'in'
    OUT = 'out'


class LogicalOperators(object):
    AND = 'and'
    OR = 'or'
    NOT = 'not'

    @staticmethod
    def get_grammar_key(key):
        return '{}_op'.format(key)


class SearchOperators(object):
    LIKE = 'like'
    I_LIKE = 'ilike'


class DjangoLookups(object):
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
