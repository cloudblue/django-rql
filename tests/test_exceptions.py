#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

import pytest

from dj_rql.exceptions import (
    RQLFilterError, RQLFilterLookupError, RQLFilterParsingError, RQLFilterValueError,
)


@pytest.mark.parametrize('exception_cls,message', [
    (RQLFilterError, 'RQL Filtering error.'),
    (RQLFilterLookupError, 'RQL Lookup error.'),
    (RQLFilterParsingError, 'RQL Parsing error.'),
    (RQLFilterValueError, 'RQL Value error.'),
])
def test_exception_message(exception_cls, message):
    with pytest.raises(exception_cls) as e:
        raise exception_cls
    assert str(e.value) == message
