from __future__ import unicode_literals

import pytest
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from dj_rql.drf import RQLFilterBackend, FilterCache
from tests.dj_rf.models import Book


@pytest.fixture
def api_client():
    client = APIClient()
    client.default_format = 'json'
    return client


@pytest.fixture
def clear_cache():
    FilterCache.clear()


@pytest.mark.django_db
def test_quoting(api_client, clear_cache):
    books = [Book.objects.create(title='Title with ws'), Book.objects.create()]
    response = api_client.get(reverse('book-list') + '?title="Title%20with%20ws"')
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
    query = 'id={}'.format(books[0].pk)
    response = api_client.get('{}?{}'.format(reverse('book-list'), query))
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[0].pk}]


@pytest.mark.django_db
def test_list_pagination(api_client, clear_cache):
    books = [Book.objects.create() for _ in range(5)]
    query = 'limit=2,eq(offset,1)'
    response = api_client.get('{}?{}'.format(reverse('book-list'), query))
    assert response.status_code == HTTP_200_OK
    assert response.data == [{'id': books[1].pk}, {'id': books[2].pk}]
    assert response._headers['content-range'][1] == 'items 1-2/5'


def test_rql_filter_cls_is_not_set():
    class View(object):
        pass

    assert RQLFilterBackend().filter_queryset(None, 'str', View()) == 'str'


@pytest.mark.django_db
def test_cache(api_client, clear_cache):
    books = [
        Book.objects.create(title='F'),
        Book.objects.create(title='G'),
    ]

    assert FilterCache.CACHE == {}
    response = api_client.get('{}?{}'.format(reverse('book-list'), 'title=F'))
    assert response.data == [{'id': books[0].pk}]

    expected_cache_key = 'book.BooksFilterClass'
    assert expected_cache_key in FilterCache.CACHE
    cache_item_id = id(FilterCache.CACHE[expected_cache_key])

    response = api_client.get('{}?{}'.format(reverse('book-list'), 'title=G'))
    assert response.data == [{'id': books[1].pk}]

    assert expected_cache_key in FilterCache.CACHE
    assert id(FilterCache.CACHE[expected_cache_key]) == cache_item_id

    FilterCache.clear()
    assert FilterCache.CACHE == {}
