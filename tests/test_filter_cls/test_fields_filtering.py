from __future__ import unicode_literals

import pytest

from tests.dj_rf.models import Book
from tests.test_filter_cls.utils import books_qs, filter_rql


@pytest.mark.django_db
def test_id_filter():
    Book.objects.bulk_create([Book() for _ in range(2)])
    books = list(books_qs())
    assert filter_rql(books_qs(), 'id={}'.format(books[0].pk)) == books[0]
