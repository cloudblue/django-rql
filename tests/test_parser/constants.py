# coding=utf-8

from __future__ import unicode_literals

import sys

from dj_rql.constants import (
    ComparisonOperators, ListOperators, LogicalOperators,
    RQL_EMPTY, RQL_NULL,
)


OK_PROPS = [
    'p', 'p1', 'prop.p2', 'u_p', 'p1__p2__p3',
    ComparisonOperators.LT, LogicalOperators.AND, LogicalOperators.NOT, ListOperators.OUT,
]
OK_VALUES = [
    'value', 'PRD-000-000' "0", '""', "''", '-3.23', '"text , t lt"',
    '2014-01-21T19:31:58+03:00', '2015-02-12', '"eq(1,2)"', 'email@example.com',
    ComparisonOperators.NE, LogicalOperators.OR, LogicalOperators.NOT, ListOperators.IN,
    RQL_NULL, RQL_EMPTY,
]
FAIL_PROPS = ['', '=', 't t', '"p"', '23', '1p']
FAIL_VALUES = ['', '"sdsd']


if sys.version_info[0] == 3:
    unicode_text = 'текст'
    OK_VALUES.append(unicode_text)
    FAIL_PROPS.append(unicode_text)
