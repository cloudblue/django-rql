from __future__ import unicode_literals

import pytest

from dj_rql.exceptions import RQLFilterParsingError
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book, Publisher

book_qs = Book.objects.order_by('id')


def apply_filters(query):
    filter_cls = BooksFilterClass(book_qs)
    q = filter_cls.apply_filters(query)
    return list(q)


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


def test_parsing_error():
    bad_query = 'q='
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters(bad_query)
    assert e.value.details['error'].startswith('Unexpected token')
