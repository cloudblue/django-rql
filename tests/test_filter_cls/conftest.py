#
#  Copyright © 2023 Ingram Micro Inc. All rights reserved.
#

from datetime import timedelta

import pytest
from django.utils import timezone

from tests.dj_rf.models import Author, Book, Publisher
from tests.dj_rf.view import apply_annotations


@pytest.fixture
def generate_books():
    def _generate_books(count=2):
        for i in range(count):
            author = Author.objects.create(
                name=f'author{i}',
                email=f'author{i}@example.com',
                is_male=True,
                publisher=Publisher.objects.create(),
            )
            b = Book.objects.create(author=author, published_at=timezone.now() - timedelta(days=i))
            if b.published_at is None:
                b.published_at = timezone.now()
                b.save()
        book_qs = apply_annotations(Book.objects.order_by('id'))
        books = list(book_qs)
        return books

    return _generate_books
