#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

import pytest
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK

from tests.dj_rf.models import (
    Author,
    Book,
    Page,
    Publisher,
)


@pytest.mark.django_db
def test_simple(api_client, clear_cache):
    Book.objects.create()
    response = api_client.get(reverse('select-list') + '?select(-id)')
    assert response.status_code == HTTP_200_OK
    assert 'id' not in response.data[0]


@pytest.mark.django_db
def test_complex(api_client, clear_cache):
    publisher = Publisher.objects.create(name='publisher')
    author = Author.objects.create(name='auth', publisher=publisher)
    book = Book.objects.create(author=author)
    Page.objects.create(book=book, number=1, content='text')

    response = api_client.get(reverse('select-list') + '?select(-author)')

    assert response.status_code == HTTP_200_OK
    assert 'author' not in response.data[0]
    assert 'author_ref' in response.data[0]
