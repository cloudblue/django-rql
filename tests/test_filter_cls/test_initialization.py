#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

import pytest
from django.core.exceptions import FieldDoesNotExist
from py_rql.constants import RESERVED_FILTER_NAMES, RQL_NULL, FilterLookups as FL

from dj_rql.filter_cls import AutoRQLFilterClass, NestedAutoRQLFilterClass, RQLFilterClass
from dj_rql.utils import assert_filter_cls
from tests.data import get_book_filter_cls_ordering_data, get_book_filter_cls_search_data
from tests.dj_rf.filters import AUTHOR_FILTERS, BooksFilterClass
from tests.dj_rf.models import Author, AutoMain, Book


empty_qs = Author.objects.none()


def test_building_filters():
    non_null_string_lookups = FL.string()
    non_null_string_lookups.discard(FL.NULL)

    non_null_numeric_lookups = FL.numeric()
    non_null_numeric_lookups.discard(FL.NULL)

    expected_sub_dct = {
        'id': {'orm_route': 'id', 'lookups': FL.numeric()},
        'title': {
            'orm_route': 'title', 'lookups': FL.string(), 'null_values': {RQL_NULL, 'NULL_ID'},
        },
        'current_price': {
            'orm_route': 'current_price', 'lookups': FL.numeric(), 'null_values': {RQL_NULL},
        },
        'written': {'orm_route': 'written', 'lookups': FL.numeric()},
        'status': {'orm_route': 'status', 'lookups': non_null_string_lookups},
        'author__email': {'orm_route': 'author__email', 'lookups': FL.string()},
        'name': {'orm_route': 'author__name', 'lookups': FL.string()},
        'author.is_male': {'orm_route': 'author__is_male', 'lookups': FL.boolean()},
        'author.email': {'orm_route': 'author__email', 'lookups': FL.string()},
        'author.publisher.id': {
            'orm_route': 'author__publisher__id',
            'lookups': FL.numeric(),
        },
        'page.number': {'orm_route': 'pages__number', 'lookups': {FL.EQ, FL.NE}},
        'page.id': {'orm_route': 'pages__uuid', 'lookups': FL.string()},
        'published.at': {'orm_route': 'published_at', 'lookups': FL.numeric()},
        'rating.blog': {
            'orm_route': 'blog_rating', 'lookups': FL.numeric(), 'use_repr': True,
        },
        'rating.blog_int': {
            'orm_route': 'blog_rating', 'lookups': FL.numeric(), 'use_repr': False,
        },
        'amazon_rating': {
            'orm_route': 'amazon_rating', 'lookups': {FL.GE, FL.LT},
        },
        'url': {'orm_route': 'publishing_url', 'lookups': FL.string()},
        'd_id': [
            {'orm_route': 'id', 'lookups': FL.numeric()},
            {'orm_route': 'author__id', 'lookups': FL.numeric()},
        ],
        'custom_filter': {'custom': True, 'custom_data': [1], 'lookups': {FL.I_LIKE}},
        'int_choice_field': {
            'orm_route': 'int_choice_field', 'lookups': non_null_numeric_lookups,
        },
        'int_choice_field_repr': {
            'orm_route': 'int_choice_field', 'lookups': {FL.EQ, FL.NE}, 'use_repr': True,
        },
        'str_choice_field': {
            'orm_route': 'str_choice_field', 'lookups': non_null_string_lookups,
        },
        'str_choice_field_repr': {
            'orm_route': 'str_choice_field', 'lookups': {FL.EQ, FL.NE}, 'use_repr': True,
        },
        'has_list_lookup': {'custom': True, 'lookups': {FL.EQ, FL.IN, FL.OUT}},
        'no_list_lookup': {'custom': True, 'lookups': {FL.EQ}},
        't__in': {'orm_route': 'title', 'lookups': FL.string()},
        'github_stars': {'orm_route': 'github_stars', 'lookups': FL.numeric()},
        'ordering_filter': {'custom': True, 'ordering': True, 'lookups': {FL.EQ}},
        'fsm': {'orm_route': 'fsm_field', 'lookups': FL.string()},
        'anno_int': {'orm_route': 'anno_int', 'lookups': {FL.EQ}},
        'anno_int_ref': {'orm_route': 'anno_int', 'lookups': non_null_numeric_lookups},
        'anno_str': {'orm_route': 'anno_str', 'lookups': non_null_string_lookups},
        'anno_auto': {'orm_route': 'anno_auto', 'lookups': FL.numeric()},
        'anno_title_non_dynamic': {'orm_route': 'title', 'lookups': FL.string()},
        'anno_title_dynamic': {'orm_route': 'title', 'lookups': non_null_string_lookups},
        'author_publisher.id': {
            'orm_route': 'author__publisher__id',
            'lookups': FL.numeric(),
        },
    }

    assert_filter_cls(
        BooksFilterClass,
        expected_sub_dct,
        get_book_filter_cls_ordering_data(),
        get_book_filter_cls_search_data(),
    )


def test_bad_filter_configuration():
    with pytest.raises(AssertionError):
        assert_filter_cls(BooksFilterClass, {'prop': {}}, set(), set())


def test_model_is_not_set():
    with pytest.raises(AssertionError) as e:
        RQLFilterClass(empty_qs)
    assert str(e.value) == 'Django model must be set for Filter Class.'


def test_is_not_django_model():
    class Cls(RQLFilterClass):
        MODEL = BooksFilterClass

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'Django model must be set for Filter Class.'


def test_wrong_extended_search_setup():
    class Cls(BooksFilterClass):
        EXTENDED_SEARCH_ORM_ROUTES = 'invalid'

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'Extended search ORM routes must be iterable.'


@pytest.mark.parametrize('filters', [{}, set()])
def test_wrong_filters_type(filters):
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = filters

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'Wrong filter settings type for Filter Class.'


@pytest.mark.parametrize('filters', [(), []])
def test_filters_are_not_set(filters):
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = filters

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'At least one filter must be set for Filter Class.'


def test_orm_path_misconfiguration():
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = ['base']

    with pytest.raises(FieldDoesNotExist):
        Cls(empty_qs)


def test_orm_field_type_is_unsupported():
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = ['publisher']

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == 'Unsupported field type: publisher.'


@pytest.mark.parametrize('filter_name', sorted(RESERVED_FILTER_NAMES))
def test_reserved_filter_name_is_used(filter_name):
    class Cls(RQLFilterClass):
        MODEL = Author
        FILTERS = [{
            'filter': filter_name,
            'source': 'id',
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "'{0}' is a reserved filter name.".format(filter_name)


def test_bad_use_repr_and_ordering():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'rating.blog',
            'source': 'blog_rating',
            'use_repr': True,
            'ordering': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "rating.blog: 'use_repr' and 'ordering' can't be used together."


def test_bad_use_repr_and_search():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'str_choice_field',
            'use_repr': True,
            'search': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "str_choice_field: 'use_repr' and 'search' can't be used together."


@pytest.mark.parametrize('option', ('filter', 'dynamic', 'custom'))
def test_bad_option_in_namespace(option):
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'namespace': 'title',
            option: True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "title: '{0}' is not supported by namespaces.".format(option)


def test_bad_item_structure():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'source': 'title',
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "All extended filters must have set 'filter' set."


def test_bad_dynamic_in_namespace():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'namespace': 'author',
            'filters': [{
                'filter': 'a',
                'dynamic': True,
            }],
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "author.a: dynamic filters are not supported in namespaces."


def test_dynamic_field_not_set():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'title',
            'dynamic': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "title: dynamic filters must have 'field' set."


def test_bad_dynamic_set():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'custom',
            'custom': True,
            'field': True,
            'lookups': {FL.EQ},
        }, {
            'filter': 'common',
            'field': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "common: common filters can't have 'field' set."


def test_bad_search():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = [{
            'filter': 'id',
            'search': True,
        }]

    with pytest.raises(AssertionError) as e:
        Cls(empty_qs)
    assert str(e.value) == "id: 'search' can be applied only to text filters."


def test_get_field():
    class Cls(RQLFilterClass):
        MODEL = Book
        FILTERS = ['id']

        @classmethod
        def get_field(cls, *args):
            return cls._get_field(*args)

    assert Cls.get_field(Book, '') is None


def _default_expected_book_auto_filters():
    return {
        'id': {'orm_route': 'id', 'lookups': FL.numeric()},
        'title': {'orm_route': 'title', 'lookups': FL.string(), 'null_values': {RQL_NULL}},
        'current_price': {
            'orm_route': 'current_price', 'lookups': FL.numeric(), 'null_values': {RQL_NULL},
        },
        'written': {'orm_route': 'written', 'lookups': FL.numeric()},
        'status': {'orm_route': 'status', 'lookups': FL.string(with_null=False)},
        'published_at': {'orm_route': 'published_at', 'lookups': FL.numeric()},
        'blog_rating': {'orm_route': 'blog_rating', 'lookups': FL.numeric()},
        'amazon_rating': {'orm_route': 'amazon_rating', 'lookups': FL.numeric()},
        'publishing_url': {'orm_route': 'publishing_url', 'lookups': FL.string()},
        'int_choice_field': {
            'orm_route': 'int_choice_field', 'lookups': FL.numeric(with_null=False),
        },
        'str_choice_field': {
            'orm_route': 'str_choice_field', 'lookups': FL.string(with_null=False),
        },
        'github_stars': {'orm_route': 'github_stars', 'lookups': FL.numeric()},
        'fsm_field': {'orm_route': 'fsm_field', 'lookups': FL.string()},
    }


def test_auto_building_filters():
    class Cls(AutoRQLFilterClass):
        MODEL = Book

    expected_sub_dct = _default_expected_book_auto_filters()
    assert len(Cls(empty_qs).filters) == len(expected_sub_dct)

    assert_filter_cls(
        Cls,
        expected_sub_dct,
        set(expected_sub_dct.keys()),
        {
            'title',
            'status',
            'publishing_url',
            'str_choice_field',
            'fsm_field',
        },
    )


def test_auto_filtering_override():
    class Cls(AutoRQLFilterClass):
        MODEL = Book
        EXCLUDE_FILTERS = ('id', 'fsm_field')
        FILTERS = (
            'title',
            {
                'namespace': 'author',
                'filters': AUTHOR_FILTERS,
            },
        )

    expected_sub_dct = _default_expected_book_auto_filters()
    del expected_sub_dct['id']
    del expected_sub_dct['fsm_field']
    expected_sub_dct.update({
        'author.is_male': {'orm_route': 'author__is_male', 'lookups': FL.boolean()},
        'author.email': {'orm_route': 'author__email', 'lookups': FL.string()},
        'author.publisher.id': {
            'orm_route': 'author__publisher__id',
            'lookups': FL.numeric(),
        },
    })

    assert len(Cls(empty_qs).filters) == len(expected_sub_dct)
    assert_filter_cls(
        Cls,
        expected_sub_dct,
        set(expected_sub_dct.keys()) - {'title', 'author.is_male', 'author.publisher.id'},
        {'status', 'publishing_url', 'str_choice_field', 'author.email'},
    )


def test_nested_auto_building_filters_depth_0():
    class Cls(NestedAutoRQLFilterClass):
        MODEL = AutoMain
        DEPTH = 0

    assert set(Cls(AutoMain.objects.all()).filters.keys()) == {'id', 'common_int', 'common_str'}


def test_nested_auto_building_filters_depth_1_check_structure():
    class Cls(NestedAutoRQLFilterClass):
        MODEL = AutoMain
        SELECT = False

    filter_cls = Cls(AutoMain.objects.all())
    assert set(filter_cls.filters.keys()) == {
        'id',
        'common_int',
        'common_str',
        'parent.id',
        'parent.common_int',
        'parent.common_str',
        'self.id',
        'self.common_int',
        'self.common_str',
        'related1.id',
        'related2.id',
        'one_to_one.id',
        'many_to_many.id',
        'reverse_OtM.id',
        'reverse_OtO.id',
        'reverse_MtM.id',
    }

    _, qs = filter_cls.apply_filters('')
    assert not qs.query.select_related
    assert not qs._prefetch_related_lookups


@pytest.mark.django_db
def test_nested_auto_building_filters_depth_2_check_select():
    class Cls(NestedAutoRQLFilterClass):
        MODEL = AutoMain
        DEPTH = 2

    filter_cls = Cls(AutoMain.objects.all())
    assert set(filter_cls.filters.keys()) == {
        'common_int',
        'common_str',
        'id',
        'many_to_many.id',
        'one_to_one.id',
        'parent.common_int',
        'parent.common_str',
        'parent.id',
        'parent.many_to_many.id',
        'parent.one_to_one.id',
        'parent.parent.common_int',
        'parent.parent.common_str',
        'parent.parent.id',
        'parent.related1.id',
        'parent.related2.id',
        'parent.reverse_MtM.id',
        'parent.reverse_OtM.id',
        'parent.reverse_OtO.id',
        'related1.r.id',
        'related1.id',
        'related2.id',
        'related2.related21.id',
        'reverse_MtM.id',
        'reverse_MtM.through.common_int',
        'reverse_MtM.through.id',
        'reverse_OtM.auto2.common_int',
        'reverse_OtM.auto2.common_str',
        'reverse_OtM.auto2.id',
        'reverse_OtM.id',
        'reverse_OtO.id',
        'self.common_int',
        'self.common_str',
        'self.id',
        'self.many_to_many.id',
        'self.one_to_one.id',
        'self.related1.id',
        'self.related2.id',
        'self.reverse_MtM.id',
        'self.reverse_OtM.id',
        'self.reverse_OtO.id',
        'self.self.common_int',
        'self.self.common_str',
        'self.self.id',
    }

    _, qs = filter_cls.apply_filters('')
    assert qs.query.select_related == {
        'reverse_OtO': {},
        'self': {
            'reverse_OtO': {},
            'self': {},
            'related1': {},
            'related2': {},
            'one_to_one': {},
        },
        'related1': {},
        'related2': {
            'related21': {},
        },
        'one_to_one': {},
    }
    assert set(qs._prefetch_related_lookups) == {
        'parent',
        'parent__parent',
        'parent__reverse_OtM',
        'parent__reverse_OtO',
        'parent__through',
        'parent__related1',
        'parent__related2',
        'parent__one_to_one',
        'parent__many_to_many',
        'reverse_OtM',
        'reverse_OtM__auto2',
        'through',
        'self__reverse_OtM',
        'self__through',
        'self__many_to_many',
        'related1__r',
        'many_to_many',
    }
    assert list(qs.all()) == []


def test_nested_auto_building_filters_depth_3_described_and_exclusions():
    class Cls(NestedAutoRQLFilterClass):
        MODEL = AutoMain
        DEPTH = 3
        EXCLUDE_FILTERS = ('common_int', 'parent.parent', 'related1')
        FILTERS = ({
            'filter': 'random',
            'source': 'id',
        },)

    filter_set = set(Cls(AutoMain.objects.all()).filters.keys())

    assert {
        'random',
        'common_str',
        'self.self.self.common_int',
        'self.self.self.common_str',
        'self.self.self.id',
    }.issubset(filter_set)
    assert {'parent.parent.id', 'related1.id', 'common_int'}.isdisjoint(filter_set)
