from __future__ import unicode_literals

import pytest

from dj_rql.utils import assert_filter_cls
from tests.data import BOOK_FILTER_CLS_ORDERING_DATA, BOOK_FILTER_CLS_SEARCH_DATA
from tests.dj_rf.filters import BooksFilterClass


def test_ordering_assertion():
    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, {}, set(), BOOK_FILTER_CLS_SEARCH_DATA)

    assert str(e.value) == "Ordering filter data doesn't match."


def test_search_assertion():
    with pytest.raises(AssertionError) as e:
        assert_filter_cls(BooksFilterClass, {}, BOOK_FILTER_CLS_ORDERING_DATA, set())

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
