#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from datetime import timedelta

from django.utils import timezone

from tests.dj_rf.models import Author, Book, Publisher
from tests.dj_rf.view import apply_annotations


book_qs = apply_annotations(Book.objects.order_by('id'))


def create_books(count=2):
    for i in range(count):
        author = Author.objects.create(
            name=f'author{i}',
            email=f'author{i}@example.com',
            is_male=True,
            publisher=Publisher.objects.create(),
        )
        Book.objects.create(author=author, published_at=timezone.now() - timedelta(days=i))
    books = list(book_qs)
    return books
