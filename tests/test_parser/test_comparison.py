#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from functools import partial

from dj_rql.constants import ComparisonOperators as CompOp
from dj_rql.parser import RQLParser

from lark.exceptions import LarkError

import pytest

from tests.test_parser.constants import FAIL_PROPS, FAIL_VALUES, OK_PROPS, OK_VALUES
from tests.test_parser.utils import ComparisonTransformer


def cmp_transform(tpl, operator, prop, value):
    return ComparisonTransformer().transform(RQLParser.parse(tpl.format(
        operator=operator, prop=prop, value=value,
    )))


base_cmp_transform = partial(cmp_transform, '{operator}({prop},{value})')
alias_cmp_transform = partial(cmp_transform, '{prop}={operator}={value}')
eq_cmp_transform = partial(cmp_transform, '{prop}{operator}{value}', '=')


@pytest.mark.parametrize('operator', [CompOp.EQ, CompOp.GT, CompOp.LE])
@pytest.mark.parametrize('prop', OK_PROPS)
@pytest.mark.parametrize('value', OK_VALUES)
def test_comparison_ok(operator, prop, value):
    base_result = base_cmp_transform(operator, prop, value)
    assert base_result == (operator, prop, value)

    alias_result = alias_cmp_transform(operator, prop, value)
    assert alias_result == base_result


@pytest.mark.parametrize('operator', [CompOp.NE, CompOp.GE, CompOp.LT])
@pytest.mark.parametrize('prop', FAIL_PROPS)
@pytest.mark.parametrize('value', ['value'])
@pytest.mark.parametrize('func', [base_cmp_transform, alias_cmp_transform])
def test_comparison_property_fail(operator, prop, value, func):
    with pytest.raises(LarkError):
        func(operator, prop, value)


@pytest.mark.parametrize('operator', [CompOp.EQ, CompOp.GE, CompOp.LE])
@pytest.mark.parametrize('prop', ['prop'])
@pytest.mark.parametrize('value', FAIL_VALUES)
@pytest.mark.parametrize('func', [base_cmp_transform, alias_cmp_transform])
def test_comparison_value_fail(operator, prop, value, func):
    with pytest.raises(LarkError):
        func(operator, prop, value)


def test_comparison_order():
    r1 = base_cmp_transform(CompOp.EQ, CompOp.LE, CompOp.GT)
    r2 = alias_cmp_transform(CompOp.LE, CompOp.EQ, CompOp.GT)

    assert r1 != r2


@pytest.mark.parametrize('prop', OK_PROPS)
@pytest.mark.parametrize('value', OK_VALUES)
def test_comparison_eq_ok(prop, value):
    assert eq_cmp_transform(prop, value) == base_cmp_transform(CompOp.EQ, prop, value)


@pytest.mark.parametrize('prop', FAIL_PROPS)
@pytest.mark.parametrize('value', ['value'])
def test_comparison_eq_property_fail(prop, value):
    with pytest.raises(LarkError):
        eq_cmp_transform(prop, value)


@pytest.mark.parametrize('prop', ['prop'])
@pytest.mark.parametrize('value', FAIL_VALUES)
def test_comparison_eq_value_fail(prop, value):
    with pytest.raises(LarkError):
        eq_cmp_transform(prop, value)
