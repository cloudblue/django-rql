from __future__ import unicode_literals

import pytest
from django.core.exceptions import FieldDoesNotExist

from dj_rql.constants import FilterLookupTypes as FLT
from dj_rql.rest_framework.filter_cls import RQLFilterClass
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author


def test_collecting_mapper():
    mapper = BooksFilterClass().mapper

    expected_sub_dct = {
        'id': {'orm_route': 'id', 'lookups': FLT.numeric()},
        'title': {'orm_route': 'title', 'lookups': FLT.string()},
        'current_price': {'orm_route': 'current_price', 'lookups': FLT.numeric()},
        'written': {'orm_route': 'written', 'lookups': FLT.numeric()},
        'status': {'orm_route': 'status', 'lookups': FLT.string()},
        'author__email': {'orm_route': 'author__email', 'lookups': FLT.string()},
        'name': {'orm_route': 'author__name', 'lookups': FLT.string()},
        'author.is_male': {'orm_route': 'author__is_male', 'lookups': FLT.boolean()},
        'author.email': {'orm_route': 'author__email', 'lookups': FLT.string()},
        'author.publisher.id': {
            'orm_route': 'author__publisher__id',
            'lookups': FLT.numeric(),
        },
        'page.number': {'orm_route': 'pages__number', 'lookups': {FLT.EQ, FLT.NE}},
        'page.id': {'orm_route': 'pages__uuid', 'lookups': FLT.string()},
        'published.at': {'orm_route': 'published_at', 'lookups': FLT.numeric()},
        'rating.blog': {
            'orm_route': 'blog_rating', 'lookups': FLT.numeric(), 'use_repr': True,
        },
        'amazon_rating': {
            'orm_route': 'amazon_rating', 'lookups': {FLT.GE, FLT.LT},
        },
        'url': {'orm_route': 'publishing_url', 'lookups': FLT.string()},
        'd_id': [
            {'orm_route': 'id', 'lookups': FLT.numeric()},
            {'orm_route': 'author__id', 'lookups': FLT.numeric()},
        ]
    }
    assert set(mapper.keys()) == set(expected_sub_dct.keys())
    for filter_name, filter_struct in expected_sub_dct.items():
        if isinstance(filter_struct, dict):
            for key, value in filter_struct.items():
                assert key in mapper[filter_name]
                assert mapper[filter_name][key] == value
        else:
            for index, filter_dct in enumerate(filter_struct):
                for key, value in filter_dct.items():
                    assert key in mapper[filter_name][index]
                    assert mapper[filter_name][index][key] == value


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
