#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from dj_rql.constants import RQL_ORDERING_OPERATOR
from dj_rql.parser import RQLParser

from lark.exceptions import LarkError

import pytest

from tests.test_parser.constants import FAIL_PROPS, OK_PROPS
from tests.test_parser.utils import OrderingTransformer


REVERSED_OK_PROPS = reversed(OK_PROPS)


def ordering_transform(props):
    query = '{operator}({props})'.format(
        operator=RQL_ORDERING_OPERATOR, props=','.join(props),
    )
    return OrderingTransformer().transform(RQLParser.parse(query))


@pytest.mark.parametrize('p1,p2', zip(OK_PROPS, REVERSED_OK_PROPS))
def test_ordering_ok(p1, p2):
    assert ordering_transform(('+{0}'.format(p1),)) == (p1,)
    assert ordering_transform(('-{0}'.format(p2),)) == ('-{0}'.format(p2),)
    assert ordering_transform((p2, p1)) == (p2, p1)
    assert ordering_transform((p2, p1, '+{0}'.format(p2))) == (p2, p1, p2)


def test_ordering_empty_ok():
    assert ordering_transform([]) == ()


@pytest.mark.parametrize('prop', FAIL_PROPS[1:])
def test_ordering_property_fail(prop):
    with pytest.raises(LarkError):
        ordering_transform(prop)


# Temporary is here
@pytest.mark.parametrize('prop', ('', 'prop'))
def test_select_ok(prop):
    RQLParser.parse('select({0})'.format(prop))
