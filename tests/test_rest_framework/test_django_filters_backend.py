from __future__ import unicode_literals

import pytest
from django.http import QueryDict
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK

from dj_rql.compat import CompatibilityRQLFilterBackend, DjangoFiltersRQLFilterBackend
from dj_rql.exceptions import RQLFilterParsingError, RQLFilterValueError
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book


def test_compatibility_is_old_syntax():
    with pytest.raises(NotImplementedError):
        CompatibilityRQLFilterBackend.is_old_syntax(None, None, None)


def test_compatibility_get_rql_query():
    with pytest.raises(NotImplementedError):
        CompatibilityRQLFilterBackend.is_old_syntax(None, None, None)


@pytest.mark.parametrize('backend', (CompatibilityRQLFilterBackend, DjangoFiltersRQLFilterBackend))
def test_compatibility_modify_initial_query(backend):
    assert backend.modify_initial_query(None, None, 'q') == 'q'


@pytest.mark.parametrize('query,expected', (
    ('', False),
    ('&', False),
    ('k=v&&', False),
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
    # TODO: Check ('title__in=v,v', True),
    ('order_by=k&k__in=v', True),
    ('limit=10,offset=2', False),
    ('limit=10,eq(offset,2)', False),
    ('limit=10,eq(offset__in,2)', False),
    ('limit=10,eq(t__in,b)', False),
    ('limit=10;k__in=2', True),
    ('limit=10;eq(t__in,b)', False),
))
def test_old_syntax(mocker, query, expected):
    request = mocker.MagicMock(query_params=QueryDict(query))
    filter_instance = BooksFilterClass(Book.objects.none())
    assert DjangoFiltersRQLFilterBackend.is_old_syntax(filter_instance, request, query) == expected


def filter_api(api_client, query):
    return api_client.get('{}?{}'.format(reverse('old_book-list'), query))


def assert_ok_response(response, count):
    assert response.status_code == HTTP_200_OK
    assert len(response.data) == count


@pytest.mark.django_db
def test_common_comparison(api_client, clear_cache):
    books = [Book.objects.create(title='G'), Book.objects.create(title='H')]
    response = filter_api(api_client, 'order_by=title&title=G')

    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[0].id


@pytest.mark.django_db
def test__in_with_one_value(api_client, clear_cache):
    books = [Book.objects.create(title='G'), Book.objects.create(title='')]

    for title, index in (('G', 0), ('', 1)):
        response = filter_api(api_client, 'title__in={}'.format(title))
        assert_ok_response(response, 1)
        assert response.data[0]['id'] == books[index].id


@pytest.mark.django_db
def test__in_with_several_values(api_client, clear_cache):
    books = [
        Book.objects.create(title='G'),
        Book.objects.create(title='H'),
        Book.objects.create(title=''),
    ]

    response = filter_api(api_client, 'title__in=G,H')
    assert_ok_response(response, 2)
    assert [response.data[0]['id'], response.data[1]['id']] == [books[0].id, books[1].id]


@pytest.mark.django_db
def test__in_with_several_values_one_empty_one_invalid(api_client, clear_cache):
    Book.objects.create(title='')

    for f in ('other,', ',other'):
        response = filter_api(api_client, 'title__in={}'.format(f))
        assert_ok_response(response, 1)


@pytest.mark.django_db
def test_double__in_property(api_client, clear_cache):
    books = [
        Book.objects.create(title='G'),
        Book.objects.create(title='H'),
        Book.objects.create(title=''),
    ]

    response = filter_api(api_client, 'title__in=G,H&title__in=,G')
    assert_ok_response(response, 1)
    assert response.data[0]['id'] == books[0].id


@pytest.mark.django_db
def test_boolean_value_ok(api_client, clear_cache):
    authors = [
        Author.objects.create(name='n', is_male=True),
        Author.objects.create(name='n', is_male=False),
    ]
    books = [Book.objects.create(author=author) for author in authors]

    for value, index in (('True', 0), ('true', 0), ('False', 1), ('false', 1)):
        response = filter_api(api_client, 'author.is_male={}'.format(value))
        assert_ok_response(response, 1)
        assert response.data[0]['id'] == books[index].id


@pytest.mark.django_db
def test_boolean_value_fail(api_client, clear_cache):
    for value in ('0', '1', 'TRUE', 'other'):
        with pytest.raises(RQLFilterValueError):
            filter_api(api_client, 'author.is_male={}'.format(value))


@pytest.mark.django_db
def test__isnull_ok(api_client, clear_cache):
    books = [Book.objects.create(), Book.objects.create(title='G')]

    for value, index in (('True', 0), ('true', 0), ('1', 0), ('False', 1), ('false', 1), ('0', 1)):
        response = filter_api(api_client, 'title__isnull={}'.format(value))
        assert_ok_response(response, 1)
        assert response.data[0]['id'] == books[index].id


@pytest.mark.django_db
def test__isnull_fail(api_client, clear_cache):
    for value in ('2', 'TRUE', 'other'):
        with pytest.raises(RQLFilterParsingError):
            filter_api(api_client, 'title__isnull={}'.format(value))


@pytest.mark.django_db
def test__exact(api_client, clear_cache):
    Book.objects.create(title='G')

    for value, count in (('"G"', 1), ('g', 0), ('G', 1)):
        response = filter_api(api_client, 'title__exact={}'.format(value))
        assert_ok_response(response, count)


@pytest.mark.django_db
def test_multiple_choice(api_client, clear_cache):
    Book.objects.create(title='G')

    for (v1, v2), count in ((('G', 'G'), 1), (('G', 'H'), 0)):
        response = filter_api(api_client, 'title__exact={}&title__exact={}'.format(v1, v2))
        assert_ok_response(response, count)


def test__contains():
    pass


def test__startswith():
    pass


def test__endswith():
    pass


def test__regex():
    # Not supported
    pass


def test__day_week_etc():
    # Not affecting
    pass


def test__gt_ge_lt_le():
    pass


def test_order_by():
    pass


def test_ordering():
    pass


def test_search():
    pass


def test_is_field_part():
    # For all
    pass


def test_quoted_value_with_special_symbols():
    pass


def test_unquoted_value_with_special_symbols():
    # Whitespaces, commas, |, ;, braces
    pass


def test_empty_property():
    pass


def test_empty_value():
    pass


def test_no_query():
    pass


def test_parsing_error_after_conversion():
    pass


def test_lookup_error_after_conversion():
    pass


def test_value_error_after_conversion():
    pass


def test_no_conversion():
    pass


def test_placing_after_conversion():
    pass


def test_pagination():
    pass


def test_pagination_without_conversion():
    pass
