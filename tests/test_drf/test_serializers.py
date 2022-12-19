#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from collections import OrderedDict

import pytest

from tests.dj_rf.models import (
    Author,
    Book,
    Page,
    Publisher,
)
from tests.dj_rf.serializers import SelectBookSerializer


@pytest.mark.django_db
def test_select_complex():
    publisher = Publisher.objects.create(name='publisher')
    author = Author.objects.create(name='auth', publisher=publisher)
    book = Book.objects.create(author=author, status='planning', amazon_rating=5.0)
    page = Page.objects.create(book=book, number=1, content='text')

    select = OrderedDict()
    select['blog_rating'] = True
    select['github_stars'] = False
    select['author'] = True
    select['author.publisher'] = True
    select['author.publisher.name'] = False
    select['author_ref.name'] = False
    select['pages'] = True
    select['pages.content'] = False

    class Request:
        rql_select = {
            'depth': 0,
            'select': select,
        }

    data = SelectBookSerializer(book, context={'request': Request}).data
    assert {
        'id': book.id,
        'blog_rating': None,
        'star': {},
        'author_ref': {
            'id': author.id,
        },
        'author': {
            'id': author.id,
            'name': 'auth',
            'publisher': {
                'id': publisher.id,
            },
        },
        'pages': [{
            'id': str(page.uuid),
        }],
        'status': book.status,
        'amazon_rating': book.amazon_rating,
    } == data


@pytest.mark.django_db
def test_select_request_without_rql_select():
    book = Book.objects.create()

    class Request:
        pass

    data = SelectBookSerializer(book, context={'request': Request}).data
    assert data


@pytest.mark.django_db
def test_select_no_request():
    book = Book.objects.create()

    data = SelectBookSerializer(book).data
    assert data


@pytest.mark.django_db
def test_select_misconfiguration():
    book = Book.objects.create()

    select = OrderedDict()
    select['invalid'] = True
    select['invalid.invalid'] = False

    class Request:
        rql_select = {
            'depth': 0,
            'select': select,
        }

    data = SelectBookSerializer(book, context={'request': Request}).data
    assert data
