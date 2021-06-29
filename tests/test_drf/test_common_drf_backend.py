#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from dj_rql.drf import FilterCache, RQLFilterBackend

from django.db import connection
from django.test.utils import CaptureQueriesContext

import pytest

from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK

from tests.dj_rf.models import Book


@pytest.mark.django_db
def test_quoting(api_client, clear_cache):
    books = [Book.objects.create(title='Title with ws'), Book.objects.create()]
    response = api_client.get(reverse('book-list') + '?title="Title%20with%20ws"')
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}]


@pytest.mark.django_db
def test_reflecting_star_in_like(api_client, clear_cache):
    books = [Book.objects.create(title=r'title\*'), Book.objects.create(title='title\\')]
    response = api_client.get(reverse('book-list') + r'?like(title,"title\\\*")')
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}]


@pytest.mark.django_db
def test_reflecting_20_and_minus(api_client, clear_cache):
    books = [Book.objects.create(title='A  B-c0')]
    response = api_client.get(reverse('book-list') + r'?like(title,*A%20 B-c0*)')
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}]


@pytest.mark.django_db
def test_list(api_client, clear_cache):
    books = [Book.objects.create() for _ in range(2)]
    response = api_client.get(reverse('book-list') + '?')
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}, {'id': books[1].pk}]


@pytest.mark.django_db
def test_list_empty(api_client, clear_cache):
    response = api_client.get(reverse('book-list'))
    assert response.status_code == HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
def test_list_filtering(api_client, clear_cache):
    books = [Book.objects.create() for _ in range(2)]
    query = 'id={0}'.format(books[0].pk)
    response = api_client.get('{0}?{1}'.format(reverse('book-list'), query))
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}]


@pytest.mark.django_db
def test_list_pagination(api_client, clear_cache):
    books = [Book.objects.create() for _ in range(5)]
    query = 'limit=2,eq(offset,1)'
    response = api_client.get('{0}?{1}'.format(reverse('book-list'), query))
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[1].pk}, {'id': books[2].pk}]
    assert response.get('Content-Range') == 'items 1-2/5'


@pytest.mark.django_db
def test_list_pagination_zero_limit(api_client, clear_cache):
    [Book.objects.create() for _ in range(5)]
    query = 'limit=0'
    response = api_client.get('{0}?{1}'.format(reverse('book-list'), query))
    assert response.status_code == HTTP_200_OK
    assert response.data == []
    assert response.get('Content-Range') == 'items 0-0/5'


def test_rql_filter_cls_is_not_set():
    class View:
        pass

    assert RQLFilterBackend().filter_queryset(None, 'str', View()) == 'str'


@pytest.mark.django_db
def test_cache(api_client, clear_cache):
    books = [
        Book.objects.create(title='F'),
        Book.objects.create(title='G'),
    ]

    assert FilterCache.CACHE == {}
    response = api_client.get('{0}?{1}'.format(reverse('book-list'), 'title=F'))
    assert response.data == [{'id': books[0].pk}]

    expected_cache_key = 'book.BooksFilterClass'
    assert expected_cache_key in FilterCache.CACHE
    cache_item_id = id(FilterCache.CACHE[expected_cache_key])

    response = api_client.get('{0}?{1}'.format(reverse('book-list'), 'title=G'))
    assert response.data == [{'id': books[1].pk}]

    assert expected_cache_key in FilterCache.CACHE
    assert id(FilterCache.CACHE[expected_cache_key]) == cache_item_id

    FilterCache.clear()
    assert FilterCache.CACHE == {}


@pytest.mark.django_db
def test_distinct_sequence(api_client, clear_cache):
    with CaptureQueriesContext(connection) as context:
        api_client.get('{0}?{1}'.format(reverse('book-list'), 'status=planning'))

        assert 'distinct' in context.captured_queries[0]['sql'].lower()

    with CaptureQueriesContext(connection) as context:
        api_client.get('{0}?{1}'.format(reverse('book-list'), 'title=abc'))

        assert 'distinct' not in context.captured_queries[0]['sql'].lower()


@pytest.mark.django_db
def test_list_filtering_for_auto(api_client, clear_cache):
    books = [Book.objects.create() for _ in range(2)]
    query = 'id={0}'.format(books[0].pk)
    response = api_client.get('{0}?{1}'.format(reverse('auto-list'), query))
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}]
