#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

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


class FilterTypes:
    INT = 'int'
    DECIMAL = 'decimal'
    FLOAT = 'float'
    DATE = 'date'
    DATETIME = 'datetime'
    STRING = 'string'
    BOOLEAN = 'boolean'


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
