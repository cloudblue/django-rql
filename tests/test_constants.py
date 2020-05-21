#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

import pytest

from dj_rql.constants import FilterLookups, FilterTypes


def test_field_filter_type():
    custom_field = {}

    assert FilterTypes.field_filter_type(custom_field) == FilterTypes.STRING


@pytest.mark.parametrize('func', ('numeric', 'string', 'boolean'))
def test_filter_lookups_non_null(func):
    result = getattr(FilterLookups, func)()
    result.discard(FilterLookups.NULL)

    assert result == getattr(FilterLookups, func)(with_null=False)
