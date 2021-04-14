#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from dj_rql.constants import ListOperators
from dj_rql.parser import RQLParser

from lark.exceptions import LarkError

import pytest

from tests.test_parser.constants import FAIL_PROPS, LIST_FAIL_VALUES, OK_PROPS, OK_VALUES
from tests.test_parser.utils import ListTransformer


REVERSED_OK_VALUES = reversed(OK_VALUES)
list_operators = [ListOperators.IN, ListOperators.OUT]


def list_transform(operator, prop, values):
    query = '{operator}({prop},({values}))'.format(
        operator=operator, prop=prop, values=','.join(values),
    )
    return ListTransformer().transform(RQLParser.parse(query))


@pytest.mark.parametrize('operator', list_operators)
@pytest.mark.parametrize('prop', OK_PROPS)
@pytest.mark.parametrize('v1,v2', zip(OK_VALUES, REVERSED_OK_VALUES))
def test_list_ok(operator, prop, v1, v2):
    for v in (v1, v2):
        assert list_transform(operator, prop, (v,)) == (operator, prop, (v,))
    assert list_transform(operator, prop, (v1, v2)) == (operator, prop, (v1, v2))


@pytest.mark.parametrize('operator', list_operators)
@pytest.mark.parametrize('prop', FAIL_PROPS)
def test_list_property_fail(operator, prop):
    with pytest.raises(LarkError):
        list_transform(operator, prop, ('value',))


@pytest.mark.parametrize('operator', list_operators)
@pytest.mark.parametrize('v1,v2', zip(OK_VALUES, LIST_FAIL_VALUES))
def test_list_value_fail(operator, v1, v2):
    with pytest.raises(LarkError):
        list_transform(operator, 'prop', (v1, v2))
