from __future__ import unicode_literals

import pytest
from django.core.exceptions import FieldDoesNotExist

from dj_rql.constants import FilterLookups as FL, RESERVED_FILTER_NAMES, RQL_NULL
from dj_rql.filter_cls import RQLFilterClass
from dj_rql.utils import assert_filter_cls
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book

empty_qs = Author.objects.none()


def test_building_filters():
    non_null_numeric_lookups = FL.numeric()
    non_null_numeric_lookups.discard(FL.NULL)
    non_null_string_lookups = FL.string()
    non_null_string_lookups.discard(FL.NULL)

    expected_sub_dct = {
        'id': {'orm_route': 'id', 'lookups': non_null_numeric_lookups},
        'title': {
            'orm_route': 'title', 'lookups': FL.string(), 'null_values': {RQL_NULL, 'NULL_ID'},
        },
        'current_price': {
            'orm_route': 'current_price', 'lookups': FL.numeric(), 'null_values': {RQL_NULL},
        },
        'written': {'orm_route': 'written', 'lookups': FL.numeric()},
        'status': {'orm_route': 'status', 'lookups': non_null_string_lookups},
        'author__email': {'orm_route': 'author__email', 'lookups': FL.string()},
        'name': {'orm_route': 'author__name', 'lookups': FL.string()},
        'author.is_male': {'orm_route': 'author__is_male', 'lookups': FL.boolean()},
        'author.email': {'orm_route': 'author__email', 'lookups': FL.string()},
        'author.publisher.id': {
            'orm_route': 'author__publisher__id',
            'lookups': non_null_numeric_lookups,
        },
        'page.number': {'orm_route': 'pages__number', 'lookups': {FL.EQ, FL.NE}},
        'page.id': {'orm_route': 'pages__uuid', 'lookups': non_null_string_lookups},
        'published.at': {'orm_route': 'published_at', 'lookups': FL.numeric()},
        'rating.blog': {
            'orm_route': 'blog_rating', 'lookups': FL.numeric(), 'use_repr': True,
        },
        'rating.blog_int': {
            'orm_route': 'blog_rating', 'lookups': FL.numeric(), 'use_repr': False,
        },
        'amazon_rating': {
            'orm_route': 'amazon_rating', 'lookups': {FL.GE, FL.LT},
        },
        'url': {'orm_route': 'publishing_url', 'lookups': FL.string()},
        'd_id': [
            {'orm_route': 'id', 'lookups': non_null_numeric_lookups},
            {'orm_route': 'author__id', 'lookups': non_null_numeric_lookups},
        ],
    }

    assert_filter_cls(
        BooksFilterClass, expected_sub_dct,
        {'author.email', 'published.at', 'd_id'},
        {'title', 'author.email', 'author__email'},
    )


def test_bad_filter_configuration():
    with pytest.raises(AssertionError):
        assert_filter_cls(BooksFilterClass, {'prop': {}}, set(), set())


def test_model_is_not_set():
    with pytest.raises(AssertionError) as e:
        RQLFilterClass(empty_qs)
    assert str(e.value) == 'Model must be set for Filter Class.'


@pytest.mark.parametrize('filters', [None, {}, set()])
def test_fields_are_not_set(filters):
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = filters

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'List of filters must be set for Filter Class.'


def test_orm_path_misconfiguration():
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = ['base']

    with pytest.raises(FieldDoesNotExist):
        Cls(empty_qs)


def test_orm_field_type_is_unsupported():
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = ['publisher']

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'Unsupported field type: publisher.'


@pytest.mark.parametrize('filter_name', RESERVED_FILTER_NAMES)
def test_reserved_filter_name_is_used(filter_name):
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = [{
            'filter': filter_name,
            'source': 'id',
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "'{}' is a reserved filter name.".format(filter_name)


def test_bad_ordering():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'rating.blog',
            'source': 'blog_rating',
            'use_repr': True,
            'ordering': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "rating.blog: 'use_repr' and 'ordering' can't be used together."


def test_bad_search():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'id',
            'search': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "id: 'search' can be applied only to text filters."
