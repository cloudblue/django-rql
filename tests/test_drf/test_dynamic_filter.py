#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

import pytest
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK

from tests.dj_rf.models import Author, Book, Publisher


@pytest.mark.django_db
def test_detail_default(api_client, clear_cache):
    publisher = Publisher.objects.create(name='publisher')
    author = Author.objects.create(name='auth', publisher=publisher)
    book = Book.objects.create(author=author, status=Book.PLANNING, amazon_rating=5.0)

    response = api_client.get(reverse('dynamicfiltercls-detail', [book.pk]))

    assert response.status_code == HTTP_200_OK
    assert 'author' in response.data
    assert 'status' in response.data
    assert 'amazon_rating' in response.data


@pytest.mark.django_db
def test_detail_exclude_fields(api_client, clear_cache):
    publisher = Publisher.objects.create(name='publisher')
    author = Author.objects.create(name='auth', publisher=publisher)
    book = Book.objects.create(author=author, status=Book.PLANNING, amazon_rating=5.0)

    response = api_client.get(
        reverse('dynamicfiltercls-detail', [book.pk])
        + '?select(-author,-status,-amazon_rating)',
    )

    assert response.status_code == HTTP_200_OK
    assert 'author' not in response.data
    assert 'status' not in response.data
    assert 'amazon_rating' not in response.data


@pytest.mark.django_db
def test_list_default(api_client, clear_cache):
    publisher = Publisher.objects.create(name='publisher')
    author = Author.objects.create(name='auth', publisher=publisher)
    Book.objects.create(author=author, status=Book.PLANNING, amazon_rating=5.0)

    response = api_client.get(reverse('dynamicfiltercls-list'))

    assert response.status_code == HTTP_200_OK
    assert 'author' not in response.data[0]
    assert 'status' not in response.data[0]
    assert 'amazon_rating' not in response.data[0]


@pytest.mark.django_db
def test_list_include_fields(api_client, clear_cache):
    publisher = Publisher.objects.create(name='publisher')
    author = Author.objects.create(name='auth', publisher=publisher)
    Book.objects.create(author=author, status=Book.PLANNING, amazon_rating=5.0)

    response = api_client.get(
        reverse('dynamicfiltercls-list')
        + '?select(author,status,amazon_rating)',
    )

    assert response.status_code == HTTP_200_OK
    assert 'author' in response.data[0]
    assert 'status' in response.data[0]
    assert 'amazon_rating' in response.data[0]
