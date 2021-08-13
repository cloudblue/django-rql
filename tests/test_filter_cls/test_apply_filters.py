#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from functools import partial

from dj_rql.constants import FilterLookups, ListOperators, RQL_NULL
from dj_rql.exceptions import RQLFilterLookupError, RQLFilterParsingError, RQLFilterValueError
from dj_rql.filter_cls import RQLFilterClass

from django.core.exceptions import FieldError
from django.db.models import IntegerField, Q
from django.utils.timezone import now

import pytest

from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book, Publisher
from tests.test_filter_cls.utils import book_qs, create_books


def apply_filters(query):
    filter_cls = BooksFilterClass(book_qs)
    _, q = filter_cls.apply_filters(query)
    return list(q)


def test_parsing_error():
    bad_query = 'q='
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters(bad_query)
    assert e.value.details['error'] == 'Bad filter query.'


def test_lookup_error():
    bad_lookup = 'like(id,1)'
    with pytest.raises(RQLFilterLookupError):
        apply_filters(bad_lookup)


@pytest.mark.django_db
@pytest.mark.parametrize('comparison_tpl', ['eq(title,{0})', 'title=eq={0}', 'title={0}'])
def test_comparison(comparison_tpl):
    title = 'book'
    books = [
        Book.objects.create(title=title),
        Book.objects.create(title='another'),
    ]
    assert apply_filters(comparison_tpl.format(title)) == [books[0]]


@pytest.mark.django_db
@pytest.mark.parametrize('searching_tpl', ['like(title,*{0}*)', 'ilike(title,*{0})'])
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
    comp1 = 'title={0}'.format(title)
    comp2 = 'eq(author.email,{0})'.format(email)
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
    comp1 = 'title={0}'.format(title)
    comp2 = 'eq(author.email,{0})'.format(email)
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
    assert apply_filters('not(title={0})'.format(title)) == [books[1]]


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
    assert apply_filters('title={0}'.format(RQL_NULL)) == books
    assert apply_filters('title=ne={0}'.format(RQL_NULL)) == []


@pytest.mark.django_db
def test_null_with_in_or():
    books = create_books()

    title = 'null'
    books[0].title = title
    books[0].save(update_fields=['title'])

    assert apply_filters('in(title,({0},{1}))'.format(title, RQL_NULL)) == books
    assert apply_filters('or(title=eq={0},eq(title,{1}))'.format(title, RQL_NULL)) == books


@pytest.mark.django_db
def test_null_on_foreign_key_pk():
    publisher = Publisher.objects.create()
    authors = [
        Author.objects.create(email='a@m.com', publisher=publisher),
        Author.objects.create(email='z@m.com'),
    ]
    books = [Book.objects.create(author=author) for author in authors]

    assert apply_filters('author.publisher.id={0}'.format(RQL_NULL)) == [books[1]]
    assert apply_filters('ne(author.publisher.id,{0})'.format(RQL_NULL)) == [books[0]]


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

    expected = list(book_qs.order_by('author__email', '-published_at'))
    assert apply_filters('ordering(author.email,-published.at)') == expected


@pytest.mark.django_db
def test_ordering_by_empty_value():
    books = create_books()
    assert apply_filters('ordering()') == books


def test_several_ordering_operations():
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters('ordering(d_id)&ordering(author.email)')

    expected = 'Bad ordering filter: query can contain only one ordering operation.'
    assert e.value.details['error'] == expected


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
    assert apply_filters('(search=Ano*;search=oO)') == books
    assert apply_filters('(search=*aN*r;search=b*k)') == books
    assert apply_filters('(search="*aN*";search="*book")') == books
    assert apply_filters('(search="*aN";search="*b*")') == books
    assert apply_filters('search=bo') == [books[0]]
    assert apply_filters('search=""') == books


def test_search_bad_lookup():
    with pytest.raises(RQLFilterParsingError) as e:
        apply_filters('search=ge=*a*')
    assert e.value.details['error'] == 'Bad search filter: ge.'


@pytest.mark.django_db
@pytest.mark.parametrize('operator', (ListOperators.IN, ListOperators.OUT))
def test_custom_filter_list_lookup_ok(operator):
    class CustomCls(BooksFilterClass):
        def build_q_for_custom_filter(self, *args, **kwargs):
            return Q(id__gte=2)

    books = [Book.objects.create() for _ in range(2)]
    assert list(
        CustomCls(book_qs).apply_filters('{0}(has_list_lookup,(1,2))'.format(operator))[1],
    ) == [books[1]]


@pytest.mark.parametrize('operator', (ListOperators.IN, ListOperators.OUT))
def test_custom_filter_list_lookup_fail(operator):
    class CustomCls(BooksFilterClass):
        def build_q_for_custom_filter(self, *args, **kwargs):
            return Q(id__gte=2)

    with pytest.raises(RQLFilterLookupError) as e:
        CustomCls(book_qs).apply_filters('{0}(no_list_lookup,(1,2))'.format(operator))
    assert e.value.details['lookup'] == operator


@pytest.mark.django_db
def test_custom_filter_ordering():
    class CustomCls(BooksFilterClass):
        def build_name_for_custom_ordering(self, filter_name):
            return 'id'

        def assert_ordering(self, filter_name, expected):
            assert list(self.apply_filters('ordering({0})'.format(filter_name))[1]) == expected

    books = create_books()

    CustomCls(book_qs).assert_ordering('ordering_filter', [books[0], books[1]])
    CustomCls(book_qs).assert_ordering('-ordering_filter', [books[1], books[0]])


@pytest.mark.django_db
def test_custom_filter_search_ok(mocker):
    class CustomCls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'search_filter',
            'custom': True,
            'search': True,
            'lookups': {FilterLookups.I_LIKE},
        }]

        def assert_search(self, value, expected):
            assert list(self.apply_filters('search={0}'.format(value))[1]) == expected

        @classmethod
        def side_effect(cls, data):
            django_lookup = data.django_lookup
            return Q(**{
                'title__{0}'.format(django_lookup): cls._get_searching_typed_value(
                    django_lookup, data.str_value,
                ),
            })

    build_q_for_custom_filter_patch = mocker.patch.object(
        CustomCls, 'build_q_for_custom_filter', side_effect=CustomCls.side_effect,
    )

    books = [
        Book.objects.create(title='book'),
        Book.objects.create(title='another'),
    ]

    CustomCls(book_qs).assert_search('ok', [books[0]])
    CustomCls(book_qs).assert_search('AN', [books[1]])
    CustomCls(book_qs).assert_search('o', books)

    assert build_q_for_custom_filter_patch.call_count == 3


@pytest.mark.django_db
def test_test_custom_filter_with_type_ok():
    class CustomWithFieldCLS(RQLFilterClass):
        MODEL = Book
        FILTERS = [
            {
                'filter': 'int_field',
                'custom': True,
                'field': IntegerField(),
                'lookups': {FilterLookups.EQ},
            },
        ]

        def build_q_for_custom_filter(self, data):
            if data.filter_name == 'int_field':
                from django.db.models import Q
                return Q(**{f'int_choice_field__{data.django_lookup}': data.str_value})
            return super().build_q_for_custom_filter(data)

    book_1, _ = (
        Book.objects.create(title='book', int_choice_field=1),
        Book.objects.create(title='another', int_choice_field=2),
    )

    _, qs = CustomWithFieldCLS(book_qs).apply_filters('int_field=1')

    assert qs.get() == book_1


def test_test_custom_filter_with_type_fail():
    class CustomWithFieldCLS(RQLFilterClass):
        MODEL = Book
        FILTERS = [
            {
                'filter': 'int_field',
                'custom': True,
                'field': IntegerField(),
                'lookups': {FilterLookups.EQ},
            },
        ]

        def build_q_for_custom_filter(self, data):
            pass

    with pytest.raises(RQLFilterValueError) as e:
        CustomWithFieldCLS(book_qs).apply_filters('int_field=string')

    assert e.value.args[0] == 'RQL Value error.'
    assert e.value.details == {'filter': 'int_field', 'lookup': 'eq', 'value': 'string'}


@pytest.mark.django_db
def test_dynamic_no_annotation():
    class CustomCls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'anno',
            'dynamic': True,
            'field': IntegerField(),
        }]

    # We want to be error unhandled in this case
    with pytest.raises(FieldError):
        CustomCls(book_qs).apply_filters('anno=5')


@pytest.mark.django_db
def test_extended_search_ok():
    class CustomCls(RQLFilterClass):
        MODEL = Book
        FILTERS = ['id']
        EXTENDED_SEARCH_ORM_ROUTES = ['title']

        def assert_search(self, value, expected):
            assert list(self.apply_filters('search={0}'.format(value))[1]) == expected

    books = [
        Book.objects.create(title='book'),
        Book.objects.create(title='another'),
    ]

    CustomCls(book_qs).assert_search('ok', [books[0]])
    CustomCls(book_qs).assert_search('AN', [books[1]])
    CustomCls(book_qs).assert_search('o', books)


@pytest.mark.django_db
def test_extended_search_fail():
    class CustomCls(RQLFilterClass):
        MODEL = Book
        FILTERS = ['id']
        EXTENDED_SEARCH_ORM_ROUTES = ['invalid']

    # We want to be error unhandled in this case
    with pytest.raises(FieldError):
        CustomCls(book_qs).apply_filters('search=text')


@pytest.mark.django_db
@pytest.mark.parametrize('select', ('title,+page,-rating.blog_int', '', 'title'))
def test_select(select):
    assert apply_filters('select({0})'.format(select)) == []


@pytest.mark.django_db
def test_braces_in_braces():
    books = [
        Book.objects.create(title='book'),
        Book.objects.create(title='another'),
    ]
    assert apply_filters('(((title=book)))&(title=book)') == [books[0]]
    assert apply_filters('(title=book|(title=invalid))') == [books[0]]


@pytest.mark.django_db
@pytest.mark.parametrize('distinct', (True, False))
def test_global_distinct(distinct):
    class CustomCls(RQLFilterClass):
        MODEL = Book
        FILTERS = ['id']
        DISTINCT = distinct

    _, qs = CustomCls(book_qs).apply_filters('id=1')
    assert qs.query.distinct is distinct


@pytest.mark.django_db
def test_distinct_on_field_no_field_in_filter():
    _, qs = BooksFilterClass(book_qs).apply_filters('title=abc')
    assert not qs.query.distinct


@pytest.mark.django_db
def test_distinct_on_field_field_in_filter():
    _, qs = BooksFilterClass(book_qs).apply_filters('status=planning')
    assert qs.query.distinct


@pytest.mark.django_db
def test_two_distinct_fields():
    _, qs = BooksFilterClass(book_qs).apply_filters('status=planning,name=author')
    assert qs.query.distinct


@pytest.mark.django_db
def test_distinct_with_custom():
    class CustomCls(BooksFilterClass):
        def build_q_for_custom_filter(self, *args, **kwargs):
            return Q()

    _, qs = CustomCls(book_qs).apply_filters('ilike(custom_filter,text)')
    assert qs.query.distinct


@pytest.mark.django_db
def test_distinct_on_field_field_in_ordering():
    _, qs = BooksFilterClass(book_qs).apply_filters('ordering(published.at)')
    assert qs.query.distinct


@pytest.mark.django_db
def test_distinct_on_field_field_not_in_ordering():
    _, qs = BooksFilterClass(book_qs).apply_filters('ordering(int_choice_field)')
    assert not qs.query.distinct
