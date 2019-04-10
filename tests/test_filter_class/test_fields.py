from __future__ import unicode_literals

import pytest
from django.core.exceptions import FieldDoesNotExist

from dj_rql.constants import LookupTypes
from dj_rql.rest_framework.filter_cls import RQLFilterClass
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book, Author
from tests.test_filter_class.utils import books_qs, filter_rql


def test_collecting_mapper():
    mapper = BooksFilterClass().mapper

    expected_sub_dct = {
        'id': {'orm_route': 'id', 'lookups': LookupTypes.numeric()},
        'title': {'orm_route': 'title', 'lookups': LookupTypes.string()},
        'current_price': {'orm_route': 'current_price', 'lookups': LookupTypes.numeric()},
        'written': {'orm_route': 'written', 'lookups': LookupTypes.numeric()},
        'status': {'orm_route': 'status', 'lookups': LookupTypes.string()},
        'author__email': {'orm_route': 'author__email', 'lookups': LookupTypes.string()},
        'name': {'orm_route': 'author__name', 'lookups': LookupTypes.string()},
        'author.is_male': {'orm_route': 'author__is_male', 'lookups': LookupTypes.boolean()},
        'author.email': {'orm_route': 'author__email', 'lookups': LookupTypes.string()},
        'author.publisher.id': {
            'orm_route': 'author__publisher__id',
            'lookups': LookupTypes.numeric(),
        },
        'page.number': {'orm_route': 'pages__number', 'lookups': {LookupTypes.EQ, LookupTypes.NE}},
        'page.id': {'orm_route': 'pages__uuid', 'lookups': LookupTypes.string()},
        'published.at': {'orm_route': 'published_at', 'lookups': LookupTypes.numeric()},
        'rating.blog': {
            'orm_route': 'blog_rating', 'lookups': LookupTypes.numeric(), 'use_repr': True,
        },
        'amazon_rating': {
            'orm_route': 'amazon_rating', 'lookups': {LookupTypes.GE, LookupTypes.LT},
        },
        'url': {'orm_route': 'publishing_url', 'lookups': LookupTypes.string()},
    }
    assert set(mapper.keys()) == set(expected_sub_dct.keys())
    for filter_name, filter_dct in expected_sub_dct.items():
        for key, value in filter_dct.items():
            assert key in mapper[filter_name]
            assert mapper[filter_name][key] == value


def test_model_is_not_set():
    with pytest.raises(AssertionError) as e:
        RQLFilterClass()
    assert str(e.value) == 'Model must be set for Filter Class.'


def test_fields_are_not_set():
    class Cls(RQLFilterClass):
        MODEL = Author

    with pytest.raises(AssertionError) as e:
        Cls()
    assert str(e.value) == 'List of filters must be set for Filter Class.'


def test_orm_path_misconfiguration():
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = ['base']

    with pytest.raises(FieldDoesNotExist):
        Cls()


def test_orm_field_type_is_unsupported():
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = ['publisher']

    with pytest.raises(AssertionError) as e:
        Cls()
    assert str(e.value) == 'Unsupported field type: publisher.'


@pytest.mark.django_db
def test_id_filter():
    Book.objects.bulk_create([Book() for _ in range(2)])
    books = list(books_qs())
    assert filter_rql(books_qs(), 'id={}'.format(books[0].pk)) == books[0]
