#
#  Copyright © 2026 CloudBlue. All rights reserved.
#

import pytest
from py_rql.exceptions import RQLFilterParsingError
from py_rql.parser import RQLParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from dj_rql.drf import get_select_props
from tests.dj_rf.filters import BooksFilterClass, SelectBooksFilterClass
from tests.dj_rf.models import Book
from tests.dj_rf.view import select_props_seen

factory = APIRequestFactory()


def make_request(query=''):
    return Request(factory.get('/?{0}'.format(query)))


@pytest.mark.parametrize(
    'query,expected',
    (
        ('select(books)', ('books',)),
        ('select(books,author.email)', ('books', 'author.email')),
        # A real world query shape, where select is one expression among others.
        (
            'eq(title,book)&select(books,author)&ordering(author.email,-id)&limit=5&offset=0',
            ('books', 'author'),
        ),
        # Exclusions keep their sign, while the useless plus is dropped by the grammar.
        ('select(-books)', ('-books',)),
        ('select(+books)', ('books',)),
        # Props are returned as written, neither deduplicated nor reordered.
        ('select(books,books)', ('books', 'books')),
        ('select(id,author,id)', ('id', 'author', 'id')),
        # No select expression at all, and no query at all.
        ('eq(title,book)', ()),
        ('', ()),
        # Only apply_filters rejects a query with more than one select operation, so the
        # props of both are collected here.
        ('select(books)&select(author)', ('books', 'author')),
        # A query that cannot be parsed yields no props instead of raising.
        ('select(', ()),
        ('&&&', ()),
    ),
)
def test_get_select_props(query, expected):
    assert get_select_props(make_request(query)) == expected


def test_props_are_not_validated_against_any_filter_class():
    assert get_select_props(make_request('select(-i_am_not_a_filter)')) == ('-i_am_not_a_filter',)


def test_parsed_ast_is_reused_when_the_request_already_carries_one():
    request = make_request('select(books)')
    request.rql_ast = RQLParser.parse_query('select(author)')

    assert get_select_props(request) == ('author',)


def test_query_is_parsed_when_the_request_carries_no_ast():
    request = make_request('select(books)')

    assert not hasattr(request, 'rql_ast')
    assert get_select_props(request) == ('books',)


def test_empty_ast_on_the_request_falls_back_to_the_query():
    # The filter backend sets rql_ast to None when the query is empty.
    request = make_request('select(books)')
    request.rql_ast = None

    assert get_select_props(request) == ('books',)


@pytest.mark.django_db
def test_same_props_before_and_after_filtering():
    """A view reads the props while building the queryset, a serializer once filtered.

    Both go through the accessor, each one through a different path: the first has no
    parsed AST on the request yet, the second reuses the one filtering left there. They
    have to agree, or a queryset and its serialization would disagree on what was asked
    for.
    """
    query = 'eq(title,book)&select(author,-pages)'
    request = Request(factory.get('/?{0}'.format(query)))

    before_filtering = get_select_props(request)

    rql_ast, _ = BooksFilterClass(Book.objects.none()).apply_filters(query, request)
    request.rql_ast = rql_ast

    assert before_filtering == get_select_props(request) == ('author', '-pages')


@pytest.mark.django_db
def test_props_are_not_the_processed_select_data():
    """What the query asked for is not what `request.rql_select` ends up holding."""
    query = 'select(author)'
    request = Request(factory.get('/?{0}'.format(query)))

    _, queryset = SelectBooksFilterClass(Book.objects.none()).apply_filters(query, request)
    select_data = queryset.select_data['select']

    assert get_select_props(request) == ('author',)
    # The filter class resolves the prop into every field the select implies, which is
    # the shape the filter backend puts on `request.rql_select`.
    assert 'author' in select_data
    assert len(select_data) > 1


@pytest.mark.django_db
def test_props_are_available_while_building_the_queryset(api_client, clear_cache):
    select_props_seen.clear()

    response = api_client.get('/select_props/?select(author,-pages)&eq(title,book)')

    assert response.status_code == 200
    assert select_props_seen == [('author', '-pages')]


@pytest.mark.django_db
def test_undeclared_props_are_neither_rejected_nor_dropped(api_client, clear_cache):
    """The filter class has no SELECT, so nothing validates the props of the query."""
    select_props_seen.clear()

    response = api_client.get('/select_props/?select(i_am_not_a_filter)')

    assert response.status_code == 200
    assert select_props_seen == [('i_am_not_a_filter',)]


@pytest.mark.django_db
def test_malformed_query_still_fails_the_request_after_the_props_are_read(
    api_client,
    clear_cache,
):
    """The accessor stays out of the way and lets the filtering reject the query."""
    select_props_seen.clear()

    with pytest.raises(RQLFilterParsingError):
        api_client.get('/select_props/?select(')

    assert select_props_seen == [()]
