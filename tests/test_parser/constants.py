# coding=utf-8

from __future__ import unicode_literals

import sys

from dj_rql.constants import (
    ComparisonOperators, ListOperators, LogicalOperators, SearchOperators,
    RQL_EMPTY, RQL_NULL,
)


OK_PROPS = (
    'p', 'p1', 'prop.p2', 'u_p', 'p1__p2__p3',
    ComparisonOperators.LT, LogicalOperators.AND, LogicalOperators.NOT, ListOperators.OUT,
    SearchOperators.LIKE,
)
OK_VALUES = [
    'value', 'PRD-000-000' "0", '""', "''", '-3.23', '+2', '"text , t lt"', 'val*',
    '2014-01-21T19:31:58+03:00', '2015-02-12', '"eq(1,2)"', 'email@example.com',
    r'\*',
    ComparisonOperators.NE, LogicalOperators.OR, LogicalOperators.NOT, ListOperators.IN,
    SearchOperators.I_LIKE,
    RQL_NULL, RQL_EMPTY,
]
FAIL_PROPS = ['', '=', 't t', '"p"', '23', '1p', 'v*', '+v']

LIST_FAIL_VALUES = ('', '"sdsd')
FAIL_VALUES = LIST_FAIL_VALUES + ('v1,v2',)


if sys.version_info[0] == 3:
    unicode_text = 'текст'
    OK_VALUES.append(unicode_text)
    FAIL_PROPS.append(unicode_text)
