#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from tests.dj_rf.models import Book
from tests.dj_rf.view import apply_annotations

book_qs = apply_annotations(Book.objects.order_by('id'))


def create_books(count=2):
    Book.objects.bulk_create([Book() for _ in range(count)])
    books = list(book_qs)
    return books
