#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

import pytest

from dj_rql.utils import assert_filter_cls
from tests.data import get_book_filter_cls_ordering_data, get_book_filter_cls_search_data
from tests.dj_rf.filters import BooksFilterClass


def test_ordering_assertion():
    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, {}, set(), get_book_filter_cls_search_data())

    assert str(e.value) == "Ordering filter data doesn't match."


def test_search_assertion():
    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, {}, get_book_filter_cls_ordering_data(), set())

    assert str(e.value) == "Searching filter data doesn't match."


def test_no_key():
    mismatch = {'key': {'orm_route': 'value'}}

    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, mismatch, set(), set())

    assert "Filter `key` is not set" in str(e.value)


def test_mismatch_for_list_data():
    mismatch = {
        'd_id': [
            {'orm_route': 'id'},
            {'orm_route': 'author__id'},
            {'orm_route': 'invalid'},
        ],
    }

    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, mismatch, set(), set())

    assert "Filter `d_id` data doesn't match" in str(e.value)


def test_mismatch_for_value():
    mismatch = {'id': {'orm_route': 'invalid'}}

    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, mismatch, set(), set())

    assert str(e.value) == 'Wrong filter `id` configuration: id != invalid'


def test_mismatch_for_fields():
    mismatch = {'id': {'orm_route': 'id'}}

    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, mismatch, set(), set())

    assert str(e.value) == "Wrong filter `id` configuration: assertion data " \
                           "must contain `orm_route` and `lookups`."
