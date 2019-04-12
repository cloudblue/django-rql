from __future__ import unicode_literals

from datetime import date

import pytest

from dj_rql.constants import ComparisonOperators as CO
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book


book_qs = Book.objects.order_by('-written')
r_book_qs = book_qs.select_related('author', 'author__publisher').prefetch_related('pages')


def filter_field(filter_name, operator, value):
    filter_cls = BooksFilterClass(book_qs)
    q = filter_cls.get_django_q_for_filter_expression(filter_name, operator, value)
    return list(book_qs.filter(q))


@pytest.mark.django_db
def test_id():
    Book.objects.bulk_create([Book() for _ in range(2)])
    books = list(book_qs)
    assert filter_field('id', CO.EQ, str(books[0].pk)) == [books[0]]
    assert filter_field('id', CO.EQ, '3') == []
    assert filter_field('id', CO.NE, str(books[1].pk)) == [books[0]]
    assert filter_field('id', CO.LT, str(books[1].pk)) == [books[0]]
    assert filter_field('id', CO.GE, str(books[0].pk)) == books


@pytest.mark.django_db
def test_title():
    books = [
        Book.objects.create(title='G'),
        Book.objects.create(title='R'),
    ]
    assert filter_field('title', CO.EQ, books[0].title) == [books[0]]
    assert filter_field('title', CO.EQ, 'N') == []
    assert filter_field('title', CO.NE, books[0].title) == [books[1]]


@pytest.mark.django_db
def test_current_price():
    books = [
        Book.objects.create(current_price=5.23),
        Book.objects.create(current_price=0.0121),
    ]
    assert filter_field('current_price', CO.EQ, str(books[0].current_price)) == [books[0]]
    assert filter_field('current_price', CO.EQ, str(5.2300123)) == [books[0]]
    assert filter_field('current_price', CO.EQ, 2) == []
    assert filter_field('current_price', CO.NE, str(books[1].current_price)) == [books[0]]
    assert filter_field('current_price', CO.LE, str(books[0].current_price)) == books
    assert filter_field('current_price', CO.GT, str(books[1].current_price)) == [books[0]]


@pytest.mark.django_db
def test_written():
    books = [
        Book.objects.create(written=date(2019, 2, 12)),
        Book.objects.create(written=date(2018, 5, 5)),
    ]
    assert filter_field('written', CO.EQ, '2019-02-12') == [books[0]]
    assert filter_field('written', CO.EQ, '2019-05-14') == []
    assert filter_field('written', CO.NE, '2019-02-12') == [books[1]]
    assert filter_field('written', CO.LE, '2020-01-01') == books
    assert filter_field('written', CO.GT, '2000-12-12') == books
