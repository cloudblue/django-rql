#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from dj_rql.constants import SearchOperators
from dj_rql.parser import RQLParser

from lark.exceptions import LarkError

import pytest

from tests.test_parser.constants import FAIL_PROPS, FAIL_VALUES, OK_PROPS, OK_VALUES
from tests.test_parser.utils import SearchTransformer


search_operators = [SearchOperators.LIKE, SearchOperators.I_LIKE]

SEARCH_OKAY_VALUES = OK_VALUES[:]
SEARCH_OKAY_VALUES.extend(['*v', 'v*', '*v*', '*v*v', '*v*v*', '"*v v*"', 'v v'])


def search_transform(operator, prop, value):
    query = '{operator}({prop},{value})'.format(operator=operator, prop=prop, value=value)
    return SearchTransformer().transform(RQLParser.parse(query))


@pytest.mark.parametrize('operator', search_operators)
@pytest.mark.parametrize('prop', OK_PROPS)
@pytest.mark.parametrize('value', SEARCH_OKAY_VALUES)
def test_searching_ok(operator, prop, value):
    assert search_transform(operator, prop, value) == (operator, prop, value)


@pytest.mark.parametrize('operator', search_operators)
@pytest.mark.parametrize('prop', FAIL_PROPS)
def test_searching_property_fail(operator, prop):
    with pytest.raises(LarkError):
        search_transform(operator, prop, 'value')


@pytest.mark.parametrize('operator', search_operators)
@pytest.mark.parametrize('value', FAIL_VALUES)
def test_searching_value_fail(operator, value):
    with pytest.raises(LarkError):
        search_transform(operator, 'prop', value)
