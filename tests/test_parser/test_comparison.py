# coding=utf-8

from __future__ import unicode_literals

import sys
from functools import partial

import pytest

from lark import Transformer, Tree
from lark.exceptions import LarkError

from dj_rql.parser import RQLParser


class ComparisonOperators(object):
    EQ = 'eq'
    NE = 'ne',
    GT = 'gt'
    GE = 'ge'
    LT = 'lt'
    LE = 'le'


CO = ComparisonOperators


class ComparisonTransformer(Transformer):
    @classmethod
    def _cmp_value(cls, obj):
        while isinstance(obj, Tree):
            obj = obj.children[0]
        return obj.value

    def comp(self, args):
        prop_index = 1
        value_index = 2

        if len(args) == 2:
            operation = ComparisonOperators.EQ
            prop_index = 0
            value_index = 1
        elif args[0].data == 'comp_op':
            operation = self._cmp_value(args[0])
        else:
            operation = self._cmp_value(args[1])
            prop_index = 0

        return operation, self._cmp_value(args[prop_index]), self._cmp_value(args[value_index])

    def term(self, args):
        return args[0]

    def start(self, args):
        return args[0]


def cmp_transform(tpl, operator, prop, value):
    return ComparisonTransformer().transform(RQLParser.parse(tpl.format(
        operator=operator, prop=prop, value=value,
    )))


cmp_base_transform = partial(cmp_transform, '{operator}({prop},{value})')
cmp_alias_transform = partial(cmp_transform, '{prop}={operator}={value}')
cmp_eq_transform = partial(cmp_transform, '{prop}{operator}{value}', '=')

ok_props = ['p', 'p1', 'prop.p2', 'u_p', 'p1__p2__p3', 'lt']
ok_values = [
    'value', 'PRD-000-000', 'ne', "0", '""', "''", '-3.23', '"text , t lt"',
    '2014-01-21T19:31:58+03:00', '2015-02-12', '"eq(1,2)"',
]

fail_props = ['', '23', '=', 't t', '1p', '"p"']
fail_values = ['', '"sdsd']

if sys.version_info[0] >= 3:
    unicode_text = 'текст'
    ok_values.append(unicode_text)
    fail_props.append(unicode_text)


@pytest.mark.parametrize('operator', [CO.EQ, CO.GT, CO.LE])
@pytest.mark.parametrize('prop', ok_props)
@pytest.mark.parametrize('value', ok_values)
def test_comparison_ok(operator, prop, value):
    base_result = cmp_base_transform(operator, prop, value)
    assert base_result == (operator, prop, value)

    alias_result = cmp_alias_transform(operator, prop, value)
    assert alias_result == base_result


@pytest.mark.parametrize('operator', [CO.NE, CO.GE, CO.LT])
@pytest.mark.parametrize('prop', fail_props)
@pytest.mark.parametrize('value', ['value'])
@pytest.mark.parametrize('func', [cmp_base_transform, cmp_alias_transform])
def test_comparison_property_fail(operator, prop, value, func):
    with pytest.raises(LarkError):
        func(operator, prop, value)


@pytest.mark.parametrize('operator', [CO.EQ, CO.GE, CO.LE])
@pytest.mark.parametrize('prop', ['prop'])
@pytest.mark.parametrize('value', fail_values)
@pytest.mark.parametrize('func', [cmp_base_transform, cmp_alias_transform])
def test_comparison_value_fail(operator, prop, value, func):
    with pytest.raises(LarkError):
        func(operator, prop, value)


def test_comparison_order():
    assert cmp_base_transform(CO.EQ, CO.LE, CO.GT) != cmp_alias_transform(CO.LE, CO.EQ, CO.GT)


@pytest.mark.parametrize('prop', ok_props)
@pytest.mark.parametrize('value', ok_values)
def test_comparison_eq_ok(prop, value):
    assert cmp_eq_transform(prop, value) == cmp_base_transform(CO.EQ, prop, value)


@pytest.mark.parametrize('prop', fail_props)
@pytest.mark.parametrize('value', ['value'])
def test_comparison_eq_property_fail(prop, value):
    with pytest.raises(LarkError):
        cmp_eq_transform(prop, value)


@pytest.mark.parametrize('prop', ['prop'])
@pytest.mark.parametrize('value', fail_values)
def test_comparison_eq_value_fail(prop, value):
    with pytest.raises(LarkError):
        cmp_eq_transform(prop, value)
