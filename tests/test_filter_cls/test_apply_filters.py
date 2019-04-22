from __future__ import unicode_literals

from functools import partial

import pytest
from django.utils.timezone import now

from dj_rql.constants import ListOperators, RQL_NULL
from dj_rql.exceptions import RQLFilterLookupError, RQLFilterParsingError
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book, Publisher
from tests.test_filter_cls.utils import book_qs, create_books


def apply_filters(query):
    filter_cls = BooksFilterClass(book_qs)
    q = filter_cls.apply_filters(query)
    return list(q)


def test_parsing_error():
    bad_query = 'q='
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters(bad_query)
    assert e.value.details['error'].startswith('Unexpected token')


def test_lookup_error():
    bad_lookup = 'like(id,1)'
    with pytest.raises(RQLFilterLookupError):
        apply_filters(bad_lookup)


@pytest.mark.django_db
@pytest.mark.parametrize('comparison_tpl', ['eq(title,{})', 'title=eq={}', 'title={}'])
def test_comparison(comparison_tpl):
    title = 'book'
    books = [
        Book.objects.create(title=title),
        Book.objects.create(title='another'),
    ]
    assert apply_filters(comparison_tpl.format(title)) == [books[0]]


@pytest.mark.django_db
@pytest.mark.parametrize('searching_tpl', ['like(title,*{}*)', 'ilike(title,*{})'])
def test_searching(searching_tpl):
    title = 'book'
    books = [
        Book.objects.create(title=title),
        Book.objects.create(title='another'),
    ]
    assert apply_filters(searching_tpl.format(title)) == [books[0]]


@pytest.mark.django_db
@pytest.mark.parametrize('operator', ['&', ','])
def test_and(operator):
    email, title = 'george@martin.com', 'book'
    comp1 = 'title={}'.format(title)
    comp2 = 'eq(author.email,{})'.format(email)
    query = '{comp1}{op}{comp2}'.format(comp1=comp1, op=operator, comp2=comp2)

    authors = [
        Author.objects.create(email='email@example.com'),
        Author.objects.create(email=email),
    ]
    books = [Book.objects.create(author=authors[index], title=title) for index in range(2)]

    expected = [books[1]]
    assert apply_filters(query) == expected
    assert apply_filters('{q}{op}{q}'.format(q=query, op=operator)) == expected
    assert apply_filters('and({comp1},{comp2})'.format(comp1=comp1, comp2=comp2)) == expected


@pytest.mark.django_db
@pytest.mark.parametrize('operator', ['|', ';'])
def test_or(operator):
    email, title = 'george@martin.com', 'book'
    comp1 = 'title={}'.format(title)
    comp2 = 'eq(author.email,{})'.format(email)
    query = '({comp1}{op}{comp2})'.format(comp1=comp1, op=operator, comp2=comp2)

    authors = [
        Author.objects.create(email='email@example.com'),
        Author.objects.create(email=email),
    ]
    books = [Book.objects.create(author=authors[index], title=title) for index in range(2)]

    expected = books
    assert apply_filters(query) == expected
    assert apply_filters('or({comp1},{comp2})'.format(comp1=comp1, comp2=comp2)) == expected


@pytest.mark.django_db
def test_not():
    title = 'book'
    books = [
        Book.objects.create(title=title),
        Book.objects.create(title='another'),
    ]
    assert apply_filters('not(title={})'.format(title)) == [books[1]]


@pytest.mark.django_db
def test_nested_logic():
    publisher = [Publisher.objects.create() for _ in range(2)]

    author = Author.objects.create(name='Foo', publisher=publisher[0], is_male=False)
    book = Book.objects.create(amazon_rating=4.0, author=author)

    other_author = Author.objects.create(name='Bar', publisher=publisher[0], is_male=False)
    other_book = Book.objects.create(amazon_rating=4.5, author=other_author)

    assert apply_filters('') == [book, other_book]
    assert apply_filters(
        '(author.publisher.id=2|ne(name,"Bar")),'
        '(eq(author.is_male,true);amazon_rating=ge=4.000)',
    ) == [book]
    assert apply_filters(
        '(and(author.is_male=ne=true,author.is_male=true);gt(id,1))',
    ) == [other_book]


def apply_listing_filters(operator, *values):
    return apply_filters('{operator}(id,({values}))'.format(
        operator=operator, values=','.join(tuple(values)),
    ))


apply_in_listing_filters = partial(apply_listing_filters, ListOperators.IN)
apply_out_listing_filters = partial(apply_listing_filters, ListOperators.OUT)


@pytest.mark.django_db
def test_in():
    books = create_books()
    assert apply_in_listing_filters(str(books[0].pk)) == [books[0]]
    assert apply_in_listing_filters(str(books[1].pk), '23') == [books[1]]
    assert apply_in_listing_filters(str(books[1].pk), str(books[0].pk)) == books
    assert apply_in_listing_filters('23') == []


@pytest.mark.django_db
def test_out():
    books = create_books()
    assert apply_out_listing_filters(str(books[0].pk)) == [books[1]]
    assert apply_out_listing_filters(str(books[1].pk), '23') == [books[0]]
    assert apply_out_listing_filters(str(books[1].pk), str(books[0].pk)) == []
    assert apply_out_listing_filters('23') == books


@pytest.mark.django_db
def test_null():
    books = create_books()
    assert apply_filters('title={}'.format(RQL_NULL)) == books
    assert apply_filters('title=ne={}'.format(RQL_NULL)) == []


@pytest.mark.django_db
def test_null_with_in_or():
    books = create_books()

    title = 'null'
    books[0].title = title
    books[0].save(update_fields=['title'])

    assert apply_filters('in(title,({},{}))'.format(title, RQL_NULL)) == books
    assert apply_filters('or(title=eq={},eq(title,{}))'.format(title, RQL_NULL)) == books


@pytest.mark.django_db
def test_ordering_source():
    authors = [
        Author.objects.create(email='a@m.com'),
        Author.objects.create(email='z@m.com'),
    ]
    books = [Book.objects.create(author=author) for author in authors]
    assert apply_filters('ordering(-author.email)') == [books[1], books[0]]
    assert apply_filters('ordering(author.email)') == [books[0], books[1]]
    assert apply_filters('ordering(author.email,-author.email)') == [books[0], books[1]]


@pytest.mark.django_db
def test_ordering_sources():
    books = create_books()
    assert apply_filters('ordering(d_id)') == [books[0], books[1]]
    assert apply_filters('ordering(-d_id)') == [books[1], books[0]]


@pytest.mark.django_db
def test_ordering_by_several_filters():
    same_email = 'a@m.com'
    authors = [
        Author.objects.create(email=same_email),
        Author.objects.create(email=same_email),
    ]
    books = [Book.objects.create(author=author, published_at=now()) for author in authors]
    books.append(Book.objects.create(published_at=now()))

    assert apply_filters('ordering(author.email,-published.at)') == \
        list(book_qs.order_by('author__email', '-published_at'))


def test_several_ordering_operations():
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters('ordering(d_id)&ordering(author.email)')
    assert e.value.details['error'] == 'Query can contain only one ordering operation.'


def test_bad_ordering_filter():
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters('ordering(id)')
    assert e.value.details['error'] == 'Bad ordering filter: id.'


@pytest.mark.django_db
def test_search():
    title = 'book'
    books = [
        Book.objects.create(title=title),
        Book.objects.create(title='another'),
    ]

    assert apply_filters('(search=*aN*r;search=b*k)') == books
    assert apply_filters('(search="*aN*";search="*book")') == books
    assert apply_filters('(search="*aN";search="*b*")') == [books[0]]


def test_search_bad_lookup():
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters('search=ge=*a*')
    assert e.value.details['error'] == 'Bad search operation: ge.'
