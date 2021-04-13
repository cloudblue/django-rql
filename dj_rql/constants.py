#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from django.db import models


RQL_ANY_SYMBOL = '*'
RQL_PLUS = '+'
RQL_MINUS = '-'
RQL_EMPTY = 'empty()'
RQL_NULL = 'null()'
RQL_TRUE = 'true'
RQL_FALSE = 'false'
RQL_LIMIT_PARAM = 'limit'
RQL_OFFSET_PARAM = 'offset'
RQL_ORDERING_OPERATOR = 'ordering'
RQL_SEARCH_PARAM = 'search'

RESERVED_FILTER_NAMES = {RQL_LIMIT_PARAM, RQL_OFFSET_PARAM, RQL_SEARCH_PARAM}


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


class FilterLookups:
    EQ = 'eq'
    """`Equal` operator"""

    NE = 'ne'
    """`Not equal` operator"""

    GE = 'ge'
    """`Greater or equal` operator"""

    GT = 'gt'
    """`Greater than` operator"""

    LE = 'le'
    """`Less or equal` operator"""

    LT = 'lt'
    """`Less then` operator"""

    IN = 'in'
    """`In` operator"""

    OUT = 'out'
    """`Not in` operator"""

    NULL = 'null'
    """`null` operator"""

    LIKE = 'like'
    """`like` operator"""

    I_LIKE = 'ilike'
    """`Case-insensitive like` operator"""

    @classmethod
    def numeric(cls, with_null=True):
        """
        Returns the default lookups for numeric fields.

        :param with_null: if true, includes the `null` lookup, defaults to True
        :type with_null: bool, optional
        :return: a set with the default lookups.
        :rtype: set
        """
        return cls._add_null(
            {cls.EQ, cls.NE, cls.GE, cls.GT, cls.LT, cls.LE, cls.IN, cls.OUT}, with_null,
        )

    @classmethod
    def string(cls, with_null=True):
        """
        Returns the default lookups for string fields.

        :param with_null: if true, includes the `null` lookup, defaults to True
        :type with_null: bool, optional
        :return: a set with the default lookups.
        :rtype: set
        """
        return cls._add_null({cls.EQ, cls.NE, cls.IN, cls.OUT, cls.LIKE, cls.I_LIKE}, with_null)

    @classmethod
    def boolean(cls, with_null=True):
        """
        Returns the default lookups for boolean fields.

        :param with_null: if true, includes the `null` lookup, defaults to True
        :type with_null: bool, optional
        :return: a set with the default lookups.
        :rtype: set
        """
        return cls._add_null({cls.EQ, cls.NE}, with_null)

    @classmethod
    def _add_null(cls, lookup_set, with_null):
        if with_null:
            lookup_set.add(cls.NULL)

        return lookup_set


class FilterTypes:
    INT = 'int'
    DECIMAL = 'decimal'
    FLOAT = 'float'
    DATE = 'date'
    DATETIME = 'datetime'
    STRING = 'string'
    BOOLEAN = 'boolean'

    @classmethod
    def field_filter_type(cls, field):
        mapper = [
            (models.AutoField, cls.INT),
            (models.BooleanField, cls.BOOLEAN),
            (models.NullBooleanField, cls.BOOLEAN),
            (models.DateTimeField, cls.DATETIME),
            (models.DateField, cls.DATE),
            (models.DecimalField, cls.DECIMAL),
            (models.FloatField, cls.FLOAT),
            (models.IntegerField, cls.INT),
            (models.TextField, cls.STRING),
            (models.UUIDField, cls.STRING),
            (models.CharField, cls.STRING),
        ]
        return next(
            (
                filter_type for base_cls, filter_type in mapper
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


class ComparisonOperators:
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    GE = 'ge'
    LT = 'lt'
    LE = 'le'


class ListOperators:
    IN = 'in'
    OUT = 'out'


class LogicalOperators:
    AND = 'and'
    OR = 'or'
    NOT = 'not'

    @staticmethod
    def get_grammar_key(key):
        return '{0}_op'.format(key)


class SearchOperators:
    LIKE = 'like'
    I_LIKE = 'ilike'


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
