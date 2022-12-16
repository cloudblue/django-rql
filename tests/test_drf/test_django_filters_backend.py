#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

import pytest
from django.http import QueryDict
from django.utils.timezone import now
from py_rql.exceptions import RQLFilterParsingError, RQLFilterValueError
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK

from dj_rql.constants import DjangoLookups
from dj_rql.drf.compat import CompatibilityRQLFilterBackend, DjangoFiltersRQLFilterBackend
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book


def test_compatibility_is_old_syntax():
    with pytest.raises(NotImplementedError):
        CompatibilityRQLFilterBackend.is_old_syntax(None, None, None)


def test_compatibility_get_rql_query():
    with pytest.raises(NotImplementedError):
        CompatibilityRQLFilterBackend.get_rql_query(None, None, None)


@pytest.mark.parametrize('backend', (CompatibilityRQLFilterBackend, DjangoFiltersRQLFilterBackend))
def test_compatibility_modify_initial_query(backend):
    assert backend.modify_initial_query(None, None, 'q') == 'q'


@pytest.mark.parametrize('query,expected', (
    ('', False),
    ('&', True),
    ('k=v&&', True),
    ('k=True', True),
    ('author.is_male=True', True),
    ('&k&', True),
    ('k=v', False),
    ('order_by=v', True),
    ('k=v%20v', True),
    ('k__in=v', True),
    ('l1__l2__in=v', True),
    ('k__random=v', False),
    ('k__in=v,v', True),
    ('k__in=ne', True),
    ('k__in=ne=v', False),
    ('k__in=ne=v""', False),
    ('t__in=v', False),
    ('order_by=k&k__in=v', True),
    ('limit=10,offset=2', False),
    ('limit=10,eq(offset,2)', False),
    ('limit=10,eq(offset__in,2)', False),
    ('limit=10,eq(t__in,b)', False),
    ('limit=10;eq(t__in,b)', False),
    ('select(books)&k__in=v,v', True),
    ('k__in=v,v&select(books)', True),
    ('select(books)', False),
    ('title__in=v,v', True),
    ('limit=10;k__in=2', True),
    ('(k=v;k=z)', False),
    ('limit=10;k__in=2;k=y)', True),
    ('t(email=1)', False),
    ('author=t(email=email)', False),
    ('k__in=v&t(auhtor=1)', False),
))
def test_old_syntax(mocker, query, expected):
    request = mocker.MagicMock(query_params=QueryDict(query))
    filter_instance = BooksFilterClass(Book.objects.none())
    assert DjangoFiltersRQLFilterBackend.is_old_syntax(filter_instance, request, query) == expected


def test_old_syntax_filters(mocker):
    query = 'k__in=v'
    request = mocker.MagicMock(query_params=QueryDict(query))
    filter_instance = BooksFilterClass(Book.objects.none())

    for _ in range(2):
        assert DjangoFiltersRQLFilterBackend.is_old_syntax(filter_instance, request, query) is True
        assert filter_instance.old_syntax_filters == {'t__in'}


def test_bad_syntax_query(mocker):
    query = (
        'limit=10&offset=0&in=(prop,(val1,val2))&in(prop.prop,(val))'
        '&ge=(created,2020-06-01T04:00:00Z)&le=(created,2020-06-24T03:59:59Z)'
    )
    request = mocker.MagicMock(
        query_params=QueryDict(query),
        _request=mocker.MagicMock(META={'QUERY_STRING': query}),
    )
    filter_instance = BooksFilterClass(Book.objects.none())
    mocker.patch('dj_rql.drf.compat.DjangoFiltersRQLFilterBackend.is_old_syntax', return_value=True)

    with pytest.raises(RQLFilterParsingError):
        assert DjangoFiltersRQLFilterBackend.get_query(filter_instance, request, None)


@pytest.mark.parametrize('query', (
    'select(books)&k__in=v,v', 'k__in=v,v&select(books)',
))
def test_old_syntax_select_remains(query, mocker):
    expected = ('select(books)&in(k,("v","v"))', 'in(k,("v","v"))&select(books)')
    request = mocker.MagicMock(query_params=QueryDict(query))
    filter_instance = BooksFilterClass(Book.objects.none())
    assert DjangoFiltersRQLFilterBackend.get_rql_query(filter_instance, request, query) in expected


def filter_api(api_client, query):
    return api_client.get('{0}?{1}'.format(reverse('old_book-list'), query))


def assert_ok_response(response, count):
    assert response.status_code == HTTP_200_OK
    assert len(response.data) == count


def create_book(title=None):
    return Book.objects.create(title=title)


def create_books(titles):
    return [create_book(title=title) for title in titles]


@pytest.mark.django_db
def test_common_comparison(api_client, clear_cache):
    books = create_books(['G', 'H'])

    response = filter_api(api_client, 'order_by=published.at&title=G')
    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[0].id


@pytest.mark.django_db
@pytest.mark.parametrize('title,count', (
    ('G', 1),
    ('', 2),
))
def test__in_with_one_value(api_client, clear_cache, title, count):
    create_books(['G', ''])

    response = filter_api(api_client, 'title__in={0}'.format(title))
    assert_ok_response(response, count)


@pytest.mark.django_db
def test__in_with_several_values(api_client, clear_cache):
    books = create_books(['G', 'H', ''])

    response = filter_api(api_client, 'title__in=G,H')
    assert_ok_response(response, 2)
    assert [response.data[0]['id'], response.data[1]['id']] == [books[0].id, books[1].id]


@pytest.mark.django_db
@pytest.mark.parametrize('query', (
    'G,',
    ',G',
))
def test__in_with_several_values_one_empty_one_invalid(api_client, clear_cache, query):
    create_books(['G', ''])

    response = filter_api(api_client, 'title__in={0}'.format(query))
    assert_ok_response(response, 1)


@pytest.mark.django_db
def test_double__in_property(api_client, clear_cache):
    books = create_books(['G', 'H', ''])

    response = filter_api(api_client, 'title__in=G,H&title__in=,G')
    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[0].id


@pytest.mark.django_db
@pytest.mark.parametrize('value,index', (
    ('True', 0),
    ('true', 0),
    ('False', 1),
    ('false', 1),
))
def test_boolean_value_ok(api_client, clear_cache, value, index):
    authors = [
        Author.objects.create(name='n', is_male=True),
        Author.objects.create(name='n', is_male=False),
    ]
    books = [Book.objects.create(author=author) for author in authors]

    response = filter_api(api_client, 'author.is_male={0}'.format(value))
    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[index].id


@pytest.mark.django_db
@pytest.mark.parametrize('value', (
    '0',
    '1',
    'TRUE',
    'other',
))
def test_boolean_value_fail(api_client, clear_cache, value):
    with pytest.raises(RQLFilterValueError):
        filter_api(api_client, 'author.is_male={0}'.format(value))


@pytest.mark.django_db
@pytest.mark.parametrize('value,index', (
    ('True', 0),
    ('true', 0),
    ('1', 0),
    ('False', 1),
    ('false', 1),
    ('0', 1),
))
def test__isnull_ok(api_client, clear_cache, value, index):
    books = create_books([None, 'G'])

    response = filter_api(api_client, 'title__isnull={0}'.format(value))
    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[index].id


@pytest.mark.django_db
@pytest.mark.parametrize('value', (
    '2',
    'TRUE',
    'other',
))
def test__isnull_fail(api_client, clear_cache, value):
    with pytest.raises(RQLFilterParsingError):
        filter_api(api_client, 'title__isnull={0}'.format(value))


@pytest.mark.django_db
@pytest.mark.parametrize('value,count', (
    ('"G"', 0),
    ('g', 0),
    ('G', 1),
))
def test__exact(api_client, clear_cache, value, count):
    create_book('G')

    response = filter_api(api_client, 'title__exact={0}'.format(value))
    assert_ok_response(response, count)


@pytest.mark.django_db
@pytest.mark.parametrize('values,count', (
    (('G', 'G'), 1),
    (('G', 'H'), 0),
))
def test_multiple_choice(api_client, clear_cache, values, count):
    create_book('G')

    response = filter_api(
        api_client, 'title__exact={0}&title__exact={1}'.format(values[0], values[1]),
    )
    assert_ok_response(response, count)


@pytest.mark.django_db
@pytest.mark.parametrize('operator', (
    DjangoLookups.CONTAINS,
    DjangoLookups.I_CONTAINS,
))
@pytest.mark.parametrize('value,count', (
    ('Title', 1),
    ('Ti', 1),
    ('it', 1),
    ('le', 1),
    ('"Title"', 0),
    ('other', 0),
    ('iT', 1),
    ('titlE', 1),
))
def test__contains(api_client, clear_cache, value, count, operator):
    create_book('Title')

    response = filter_api(api_client, 'title__{0}={1}'.format(operator, value))
    assert_ok_response(response, count)


@pytest.mark.django_db
@pytest.mark.parametrize('operator', (
    DjangoLookups.STARTSWITH,
    DjangoLookups.I_STARTSWITH,
))
@pytest.mark.parametrize('value,count', (
    ('Title', 1),
    ('Ti', 1),
    ('it', 0),
    ('le', 0),
    ('"Title"', 0),
    ('other', 0),
    ('iT', 0),
    ('titlE', 1),
))
def test__startswith(api_client, clear_cache, value, count, operator):
    create_book('Title')

    response = filter_api(api_client, 'title__{0}={1}'.format(operator, value))
    assert_ok_response(response, count)


@pytest.mark.django_db
@pytest.mark.parametrize('operator', (
    DjangoLookups.ENDSWITH,
    DjangoLookups.I_ENDSWITH,
))
@pytest.mark.parametrize('value,count', (
    ('Title', 1),
    ('Ti', 0),
    ('it', 0),
    ('le', 1),
    ('"Title"', 0),
    ('other', 0),
    ('iT', 0),
    ('titlE', 1),
))
def test__endswith(api_client, clear_cache, value, count, operator):
    create_book('Title')

    response = filter_api(api_client, 'title__{0}={1}'.format(operator, value))
    assert_ok_response(response, count)


@pytest.mark.django_db
@pytest.mark.parametrize('lookup', (
    DjangoLookups.REGEX,
    DjangoLookups.I_REGEX,
))
def test__regex(api_client, clear_cache, lookup):
    with pytest.raises(RQLFilterParsingError):
        filter_api(api_client, 'title__{0}=true'.format(lookup))


@pytest.mark.django_db
@pytest.mark.parametrize('lookup', (
    'day',
    'week',
    'month',
    'time',
    'hour',
    'minute',
    'second',
    'day__gt',
))
def test__day_week_etc(api_client, clear_cache, lookup):
    response = filter_api(api_client, 'title__{0}=2020'.format(lookup))
    assert_ok_response(response, 0)


@pytest.mark.django_db
@pytest.mark.parametrize('lookup,p_value,n_value', (
    (DjangoLookups.GT, 1, 5),
    (DjangoLookups.GTE, 5, 10),
    (DjangoLookups.LT, 10, 5),
    (DjangoLookups.LTE, 10, 1),
))
def test__gt_ge_lt_le(api_client, clear_cache, lookup, p_value, n_value):
    Book.objects.create(github_stars=5)

    response = filter_api(api_client, 'github_stars__{0}={1}'.format(lookup, p_value))
    assert_ok_response(response, 1)

    response = filter_api(api_client, 'github_stars__{0}={1}'.format(lookup, n_value))
    assert_ok_response(response, 0)


@pytest.mark.django_db
@pytest.mark.parametrize('ordering_term', (
    'order_by',
    'ordering',
))
def test_order_ok(api_client, clear_cache, ordering_term):
    same_email = 'a@m.com'
    authors = [
        Author.objects.create(email=same_email),
        Author.objects.create(email=same_email),
    ]
    books = [Book.objects.create(author=author, published_at=now()) for author in authors]
    books.append(Book.objects.create(published_at=now()))

    response = filter_api(api_client, '{0}=author.email,-published.at'.format(ordering_term))

    expected = [b.id for b in Book.objects.all().order_by('author__email', '-published_at')]
    assert [d['id'] for d in response.data] == expected


@pytest.mark.django_db
@pytest.mark.parametrize('ordering_term', (
    'order_by',
    'ordering',
))
def test_order_fail(api_client, clear_cache, ordering_term):
    with pytest.raises(RQLFilterParsingError):
        filter_api(api_client, '{0}=invalid'.format(ordering_term))


@pytest.mark.django_db
def test_quoted_value_with_special_symbols(api_client, clear_cache):
    title = "'|(), '"
    create_book(title)

    response = filter_api(api_client, 'title={0}'.format(title))
    assert_ok_response(response, 0)


@pytest.mark.django_db
def test_unquoted_value_with_special_symbols(api_client, clear_cache):
    title = '|(),"'
    with pytest.raises(RQLFilterParsingError):
        filter_api(api_client, 'title={0}'.format(title))


@pytest.mark.django_db
def test_value_with_quotes_fail(api_client, clear_cache):
    title = '|\'(),"'
    with pytest.raises(RQLFilterParsingError):
        filter_api(api_client, 'title__exact={0}'.format(title))


@pytest.mark.django_db
def test_empty_property(api_client, clear_cache):
    create_book()

    response = filter_api(api_client, '=')
    assert_ok_response(response, 1)


@pytest.mark.django_db
@pytest.mark.parametrize('prop', (
    'title',
    'title__exact',
))
def test_empty_value(api_client, clear_cache, prop):
    create_book()

    response = filter_api(api_client, '{0}='.format(prop))
    assert_ok_response(response, 1)


@pytest.mark.django_db
def test_no_query(api_client, clear_cache):
    create_book()

    response = filter_api(api_client, '')
    assert_ok_response(response, 1)


@pytest.mark.django_db
def test_pagination(api_client, clear_cache):
    create_books(['G', 'G', 'H'])

    response = filter_api(api_client, 'limit=1&offset=1&title__exact=G')
    assert response['Content-Range'] == 'items 1-1/2'


@pytest.mark.django_db
def test_choice(api_client, clear_cache):
    books = [Book.objects.create(str_choice_field=choice) for choice, _ in Book.STR_CHOICES]

    response = filter_api(api_client, 'str_choice_field__in={0},{1}'.format('one', 'two'))
    assert_ok_response(response, 2)

    response = filter_api(api_client, 'str_choice_field__in=,{0}'.format('one'))
    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[0].id
