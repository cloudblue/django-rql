from __future__ import unicode_literals

from datetime import date, datetime

import pytest

from dj_rql.constants import ComparisonOperators as CO
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book, Page, Publisher

book_qs = Book.objects.order_by('id')
r_book_qs = book_qs.select_related('author', 'author__publisher').prefetch_related('pages')


def filter_field(filter_name, operator, value):
    filter_cls = BooksFilterClass(book_qs)
    q = filter_cls.get_django_q_for_filter_expression(filter_name, operator, value)
    return list(book_qs.filter(q))


@pytest.mark.django_db
def test_id():
    filter_name = 'id'
    Book.objects.bulk_create([Book() for _ in range(2)])
    books = list(book_qs)
    assert filter_field(filter_name, CO.EQ, str(books[0].pk)) == [books[0]]
    assert filter_field(filter_name, CO.EQ, '3') == []
    assert filter_field(filter_name, CO.NE, str(books[1].pk)) == [books[0]]
    assert filter_field(filter_name, CO.LT, str(books[1].pk)) == [books[0]]
    assert filter_field(filter_name, CO.GE, str(books[0].pk)) == books


@pytest.mark.django_db
def test_title():
    filter_name = 'title'
    books = [
        Book.objects.create(title='G'),
        Book.objects.create(title='R'),
    ]
    assert filter_field(filter_name, CO.EQ, books[0].title) == [books[0]]
    assert filter_field(filter_name, CO.EQ, 'N') == []
    assert filter_field(filter_name, CO.NE, books[0].title) == [books[1]]


@pytest.mark.django_db
def test_current_price():
    filter_name = 'current_price'
    books = [
        Book.objects.create(current_price=5.23),
        Book.objects.create(current_price=0.0121),
    ]
    assert filter_field(filter_name, CO.EQ, str(books[0].current_price)) == [books[0]]
    assert filter_field(filter_name, CO.EQ, str(5.2300123)) == [books[0]]
    assert filter_field(filter_name, CO.EQ, 2) == []
    assert filter_field(filter_name, CO.NE, str(books[1].current_price)) == [books[0]]
    assert filter_field(filter_name, CO.LE, str(books[0].current_price)) == books
    assert filter_field(filter_name, CO.GT, str(books[1].current_price)) == [books[0]]


@pytest.mark.django_db
def test_written():
    filter_name = 'written'
    books = [
        Book.objects.create(written=date(2019, 2, 12)),
        Book.objects.create(written=date(2018, 5, 5)),
    ]
    assert filter_field(filter_name, CO.EQ, '2019-02-12') == [books[0]]
    assert filter_field(filter_name, CO.EQ, '2019-05-14') == []
    assert filter_field(filter_name, CO.NE, '2019-02-12') == [books[1]]
    assert filter_field(filter_name, CO.LE, '2020-01-01') == books
    assert filter_field(filter_name, CO.GT, '2000-12-12') == books


@pytest.mark.django_db
def test_status():
    filter_name = 'status'
    books = [
        Book.objects.create(status=Book.WRITING),
        Book.objects.create(status=Book.PUBLISHED),
    ]
    assert filter_field(filter_name, CO.EQ, books[1].status) == [books[1]]
    assert filter_field(filter_name, CO.EQ, Book.PLANNING) == []
    assert filter_field(filter_name, CO.NE, books[1].status) == [books[0]]


@pytest.mark.django_db
def test_name():
    filter_name = 'name'
    authors = [
        Author.objects.create(name='Pushkin'),
        Author.objects.create(name='Lermontov'),
    ]
    books = [Book.objects.create(author=authors[index]) for index in range(2)]
    assert filter_field(filter_name, CO.EQ, authors[1].name) == [books[1]]
    assert filter_field(filter_name, CO.EQ, 'value__v') == []
    assert filter_field(filter_name, CO.NE, authors[1].name) == [books[0]]


@pytest.mark.django_db
@pytest.mark.parametrize('filter_name', ['author__email', 'author.email'])
def test_author__email(filter_name):
    authors = [
        Author.objects.create(email='email@gmail.com'),
        Author.objects.create(email='m.k@ingrammicro.com'),
    ]
    books = [Book.objects.create(author=authors[index]) for index in range(2)]
    assert filter_field(filter_name, CO.EQ, authors[1].email) == [books[1]]
    assert filter_field(filter_name, CO.EQ, 'email@example.com') == []
    assert filter_field(filter_name, CO.NE, authors[1].email) == [books[0]]


@pytest.mark.django_db
def test_author__is_male():
    filter_name = 'author.is_male'
    authors = [Author.objects.create(is_male=True) for _ in range(2)]
    books = [Book.objects.create(author=authors[index]) for index in range(2)]
    assert filter_field(filter_name, CO.EQ, 'true') == books
    assert filter_field(filter_name, CO.EQ, 'false') == []
    assert filter_field(filter_name, CO.NE, 'false') == books


@pytest.mark.django_db
def test_author__publisher__id():
    filter_name = 'author.publisher.id'
    publishers = [Publisher.objects.create() for _ in range(2)]
    authors = [Author.objects.create(publisher=publishers[index]) for index in range(2)]
    books = [Book.objects.create(author=authors[index]) for index in range(2)]
    assert filter_field(filter_name, CO.EQ, str(publishers[0].pk)) == [books[0]]
    assert filter_field(filter_name, CO.EQ, '3') == []
    assert filter_field(filter_name, CO.NE, str(publishers[1].pk)) == [books[0]]
    assert filter_field(filter_name, CO.LT, str(publishers[1].pk)) == [books[0]]
    assert filter_field(filter_name, CO.GE, str(publishers[0].pk)) == books


@pytest.mark.django_db
def test_page__number():
    filter_name = 'page.number'
    books = [Book.objects.create() for _ in range(2)]
    pages = [Page.objects.create(book=books[index], number=index) for index in range(2)]
    assert filter_field(filter_name, CO.EQ, str(pages[1].number)) == [books[1]]
    assert filter_field(filter_name, CO.EQ, '22') == []
    assert filter_field(filter_name, CO.NE, str(pages[1].number)) == [books[0]]


@pytest.mark.django_db
def test_page__id():
    filter_name = 'page.id'
    books = [Book.objects.create() for _ in range(2)]
    pages = [Page.objects.create(book=books[index]) for index in range(2)]
    assert filter_field(filter_name, CO.EQ, pages[1].pk) == [books[1]]
    assert filter_field(filter_name, CO.EQ, '5fde36e2-3442-4d2e-b221-a6758663dd72') == []
    assert filter_field(filter_name, CO.NE, pages[1].pk) == [books[0]]


@pytest.mark.django_db
def test_published_at():
    filter_name = 'published.at'
    books = [
        Book.objects.create(published_at=datetime(2019, 2, 12, 10, 2)),
        Book.objects.create(published_at=datetime(2018, 5, 5, 3, 4, 5)),
    ]
    assert filter_field(filter_name, CO.EQ, '2019-02-12T10:02:00') == [books[0]]
    assert filter_field(filter_name, CO.EQ, '2019-02-12T10:02Z') == [books[0]]
    assert filter_field(filter_name, CO.EQ, '2019-02-12T10:02:00+03:00') == []
    assert filter_field(filter_name, CO.NE, '2019-02-12T10:02') == [books[1]]
    assert filter_field(filter_name, CO.LE, '2020-01-01T00:00+08:00') == books
    assert filter_field(filter_name, CO.GT, '2000-12-12T00:21:00') == books


@pytest.mark.django_db
def test_rating_blog():
    filter_name = 'rating.blog'
    books = [
        Book.objects.create(blog_rating=Book.LOW_RATING),
        Book.objects.create(blog_rating=Book.HIGH_RATING),
    ]
    assert filter_field(filter_name, CO.EQ, 'low') == [books[0]]
    assert filter_field(filter_name, CO.EQ, 'high') == [books[1]]
    assert filter_field(filter_name, CO.NE, 'high') == [books[0]]


@pytest.mark.django_db
def test_amazon_rating():
    filter_name = 'amazon_rating'
    books = [
        Book.objects.create(amazon_rating=3.02),
        Book.objects.create(amazon_rating=2),
    ]
    assert filter_field(filter_name, CO.GE, 3.0200000) == [books[0]]
    assert filter_field(filter_name, CO.GE, 2.01) == [books[0]]
    assert filter_field(filter_name, CO.LT, 3.02) == [books[1]]


@pytest.mark.django_db
def test_url():
    filter_name = 'url'
    books = [
        Book.objects.create(publishing_url='http://www.site.com/'),
        Book.objects.create(publishing_url='https://example.com/'),
    ]
    assert filter_field(filter_name, CO.EQ, books[0].publishing_url) == [books[0]]
    assert filter_field(filter_name, CO.EQ, 'https://www.example.com/') == []
    assert filter_field(filter_name, CO.NE, books[1].publishing_url) == [books[0]]


@pytest.mark.django_db
def test_d_id():
    filter_name = 'd_id'
    authors = [Author.objects.create() for _ in range(2)]
    books = [
        Book.objects.create(author=authors[0]),
        Book.objects.create(author=authors[0]),
        Book.objects.create(author=authors[1]),
    ]
    assert filter_field(filter_name, CO.EQ, '2') == [books[1], books[2]]
    assert filter_field(filter_name, CO.NE, '2') == [books[0]]
    assert filter_field(filter_name, CO.EQ, '0') == []
    assert filter_field(filter_name, CO.EQ, '1') == [books[0], books[1]]
    assert filter_field(filter_name, CO.NE, '1') == [books[2]]
