from __future__ import unicode_literals

from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book


def books_qs():
    return Book.objects.all()


def filter_rql(queryset, query):
    return list(BooksFilterClass().filter_queryset(queryset, query).all())
