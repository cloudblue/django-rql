# coding=utf-8

from __future__ import unicode_literals

import sys
from functools import partial

import pytest

from lark.exceptions import LarkError

from dj_rql.parser import RQLParser
from tests.test_parser.utils import ComparisonTransformer
from dj_rql.constants import ComparisonOperators as CompOp


def cmp_transform(tpl, operator, prop, value):
    return ComparisonTransformer().transform(RQLParser.parse(tpl.format(
        operator=operator, prop=prop, value=value,
    )))


base_cmp_transform = partial(cmp_transform, '{operator}({prop},{value})')
alias_cmp_transform = partial(cmp_transform, '{prop}={operator}={value}')
eq_cmp_transform = partial(cmp_transform, '{prop}{operator}{value}', '=')

ok_props = ['p', 'p1', 'prop.p2', 'u_p', 'p1__p2__p3', 'lt', 'and', 'not']
ok_values = [
    'value', 'PRD-000-000', 'ne', "0", '""', "''", '-3.23', '"text , t lt"',
    '2014-01-21T19:31:58+03:00', '2015-02-12', '"eq(1,2)"', 'or', 'not', 'email@example.com',
]

fail_props = ['', '=', 't t', '"p"', '23', '1p']
fail_values = ['', '"sdsd']

if sys.version_info[0] == 3:
    unicode_text = 'текст'
    ok_values.append(unicode_text)
    fail_props.append(unicode_text)


@pytest.mark.parametrize('operator', [CompOp.EQ, CompOp.GT, CompOp.LE])
@pytest.mark.parametrize('prop', ok_props)
@pytest.mark.parametrize('value', ok_values)
def test_comparison_ok(operator, prop, value):
    base_result = base_cmp_transform(operator, prop, value)
    assert base_result == (operator, prop, value)

    alias_result = alias_cmp_transform(operator, prop, value)
    assert alias_result == base_result


@pytest.mark.parametrize('operator', [CompOp.NE, CompOp.GE, CompOp.LT])
@pytest.mark.parametrize('prop', fail_props)
@pytest.mark.parametrize('value', ['value'])
@pytest.mark.parametrize('func', [base_cmp_transform, alias_cmp_transform])
def test_comparison_property_fail(operator, prop, value, func):
    with pytest.raises(LarkError):
        func(operator, prop, value)


@pytest.mark.parametrize('operator', [CompOp.EQ, CompOp.GE, CompOp.LE])
@pytest.mark.parametrize('prop', ['prop'])
@pytest.mark.parametrize('value', fail_values)
@pytest.mark.parametrize('func', [base_cmp_transform, alias_cmp_transform])
def test_comparison_value_fail(operator, prop, value, func):
    with pytest.raises(LarkError):
        func(operator, prop, value)


def test_comparison_order():
    assert base_cmp_transform(CompOp.EQ, CompOp.LE, CompOp.GT) != \
        alias_cmp_transform(CompOp.LE, CompOp.EQ, CompOp.GT)


@pytest.mark.parametrize('prop', ok_props)
@pytest.mark.parametrize('value', ok_values)
def test_comparison_eq_ok(prop, value):
    assert eq_cmp_transform(prop, value) == base_cmp_transform(CompOp.EQ, prop, value)


@pytest.mark.parametrize('prop', fail_props)
@pytest.mark.parametrize('value', ['value'])
def test_comparison_eq_property_fail(prop, value):
    with pytest.raises(LarkError):
        eq_cmp_transform(prop, value)


@pytest.mark.parametrize('prop', ['prop'])
@pytest.mark.parametrize('value', fail_values)
def test_comparison_eq_value_fail(prop, value):
    with pytest.raises(LarkError):
        eq_cmp_transform(prop, value)
