#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

import pytest
from django.core.exceptions import FieldError
from django.db.models import CharField, IntegerField, Value
from py_rql.exceptions import RQLFilterParsingError

from dj_rql.fields import SelectField
from dj_rql.filter_cls import RQLFilterClass
from dj_rql.qs import (
    AN,
    CH,
    NPR,
    NSR,
    PR,
    SR,
)
from tests.dj_rf.models import Author, Book
from tests.test_filter_cls.utils import book_qs


class SelectFilterCls(RQLFilterClass):
    MODEL = Book
    SELECT = True
    FILTERS = ('id',)

    @property
    def heirarchy(self):
        return self.select_tree

    @property
    def exclusions(self):
        return self.default_exclusions


def test_init_no_select():
    class Cls(SelectFilterCls):
        SELECT = False
        FILTERS = (
            {
                'filter': 'hidden',
                'source': 'id',
                'hidden': True,
            },
        )

    instance = Cls(book_qs)
    assert not instance.heirarchy
    assert not instance.exclusions


def test_init_default_select():
    instance = SelectFilterCls(book_qs)
    assert set(instance.heirarchy.keys()) == {'id'}
    assert instance.heirarchy['id']['path'] == 'id'
    assert not instance.heirarchy['id']['qs']
    assert not instance.exclusions


def test_init_select():
    class Cls(SelectFilterCls):
        FILTERS = (
            'id',
            {
                'filter': 'ft',
                'source': 'id',
            },
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': (
                    'id',
                    {
                        'filter': 'ft',
                        'source': 'id',
                    },
                    {
                        'namespace': 'ns',
                        'source': 'publisher',
                        'filters': ('id',),
                    },
                ),
            },
        )

    instance = Cls(book_qs)

    assert set(instance.heirarchy.keys()) == {'id', 'ft', 'ns'}
    assert not instance.heirarchy['id']['fields']
    assert not instance.heirarchy['id']['namespace']
    assert instance.heirarchy['id']['path'] == 'id'

    assert not instance.heirarchy['ft']['fields']
    assert not instance.heirarchy['ft']['namespace']
    assert instance.heirarchy['ft']['path'] == 'ft'

    top_ns = instance.heirarchy['ns']
    assert top_ns['namespace']
    assert top_ns['path'] == 'ns'
    assert set(top_ns['fields'].keys()) == {'id', 'ft', 'ns'}

    assert not top_ns['fields']['id']['fields']
    assert not top_ns['fields']['id']['namespace']
    assert top_ns['fields']['id']['path'] == 'ns.id'

    assert not top_ns['fields']['ft']['fields']
    assert not top_ns['fields']['ft']['namespace']
    assert top_ns['fields']['ft']['path'] == 'ns.ft'

    inner_ns = instance.heirarchy['ns']['fields']['ns']
    assert inner_ns['namespace']
    assert inner_ns['path'] == 'ns.ns'
    assert set(inner_ns['fields'].keys()) == {'id'}

    assert not inner_ns['fields']['id']['fields']
    assert not inner_ns['fields']['id']['namespace']
    assert inner_ns['fields']['id']['path'] == 'ns.ns.id'


def test_init_hidden():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'vi',
                'source': 'id',
            },
            {
                'namespace': 'vn',
                'source': 'author',
                'filters': (
                    {
                        'filter': 'vi',
                        'source': 'id',
                    }, {
                        'filter': 'nvi',
                        'source': 'id',
                        'hidden': True,
                    },
                ),
            },
            {
                'namespace': 'nvn',
                'source': 'author',
                'hidden': True,
                'filters': (
                    {
                        'filter': 'vi',
                        'source': 'id',
                        'hidden': False,
                    },
                    {
                        'filter': 'nvi',
                        'source': 'id',
                        'hidden': True,
                    },
                    {
                        'namespace': 'vn',
                        'source': 'publisher',
                        'filters': ('id',),
                    },
                ),
            },
        )

    instance = Cls(book_qs)
    assert set(instance.heirarchy.keys()) == {'vi', 'vn', 'nvn'}
    assert not instance.heirarchy['vi']['hidden']
    assert not instance.heirarchy['vn']['hidden']
    assert instance.heirarchy['nvn']['hidden']

    assert set(instance.heirarchy['vn']['fields'].keys()) == {'vi', 'nvi'}
    assert not instance.heirarchy['vn']['fields']['vi']['hidden']
    assert instance.heirarchy['vn']['fields']['nvi']['hidden']

    assert set(instance.heirarchy['nvn']['fields'].keys()) == {'vi', 'nvi', 'vn'}
    assert not instance.heirarchy['nvn']['fields']['vi']['hidden']
    assert not instance.heirarchy['nvn']['fields']['vn']['hidden']
    assert instance.heirarchy['nvn']['fields']['nvi']['hidden']
    assert instance.heirarchy['vn']['fields']['nvi']['hidden']

    assert not instance.heirarchy['nvn']['fields']['vn']['fields']['id']['hidden']

    assert instance.exclusions == {'nvn', 'vn.nvi', 'nvn.nvi'}


def test_init_qs():
    class Cls(SelectFilterCls):
        FILTERS = (
            'id',
            {
                'filter': 'ft1',
                'source': 'id',
                'qs': SR('author'),
            },
            {
                'filter': 'ft2',
                'source': 'id',
                'qs': NSR('author'),
            },
            {
                'namespace': 'ns',
                'source': 'author',
                'qs': NPR('author', 'pages'),
                'filters': (
                    {
                        'filter': 'ft1',
                        'source': 'id',
                        'qs': SR('author__publisher'),
                    },
                    {
                        'filter': 'ft2',
                        'source': 'id',
                        'qs': NSR('publisher'),
                    },
                    {
                        'namespace': 'ns',
                        'source': 'publisher',
                        'qs': NPR('publisher'),
                        'filters': (
                            {
                                'filter': 'id',
                                'qs': AN(abc=Value(1, IntegerField())),
                            },
                        ),
                    },
                ),
            },
            {
                'namespace': 'pages',
                'qs': PR('pages'),
                'filters': (
                    {
                        'namespace': 'book',
                        'filters': (
                            {
                                'filter': 'author',
                                'source': 'author__id',
                                'qs': CH(NSR('author'), NSR('author__publisher')),
                            },
                        ),
                    },
                ),
            },
        )

    base_qs = Book.objects.all()
    instance = Cls(base_qs)

    assert instance.heirarchy['id']['qs'] is None

    qs = instance.heirarchy['ft1']['qs'].apply(base_qs)
    assert qs.query.select_related == {'author': {}}

    qs = instance.heirarchy['ft2']['qs'].apply(base_qs)
    assert qs.query.select_related == {'author': {}}

    top_ns = instance.heirarchy['ns']
    qs = top_ns['qs'].apply(base_qs)
    assert qs._prefetch_related_lookups == ('author', 'pages')

    qs = top_ns['fields']['ft1']['qs'].apply(base_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}

    qs = top_ns['fields']['ft2']['qs'].apply(base_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)

    inner_ns = top_ns['fields']['ns']
    qs = inner_ns['qs'].apply(base_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)

    qs = inner_ns['fields']['id']['qs'].apply(base_qs)
    assert set(qs.query.annotations.keys()) == {'abc'}

    pages = instance.heirarchy['pages']
    qs = pages['qs'].apply(base_qs)
    assert qs._prefetch_related_lookups == ('pages',)

    assert pages['fields']['book']['qs'] is None

    qs = pages['fields']['book']['fields']['author']['qs'].apply(base_qs)
    assert qs._prefetch_related_lookups == ('pages__author', 'pages__author__publisher')


class _Request:
    pass


def test_apply_rql_select_not_applied_non_select_cls():
    class Cls(SelectFilterCls):
        SELECT = False
        FILTERS = (
            {
                'filter': 'hidden',
                'source': 'id',
                'hidden': True,
            },
        )

    request = _Request()
    _, qs = Cls(book_qs).apply_filters('select(+hidden)', request)
    assert not hasattr(request, 'rql_ast')
    assert not hasattr(request, 'rql_select')
    assert not hasattr(qs, 'rql_select')


def test_apply_rql_select_applied_no_request():
    result = SelectFilterCls(book_qs).apply_filters('select(id)')
    assert result


def test_apply_rql_select_applied_no_query():
    _, qs = SelectFilterCls(book_qs).apply_filters('')

    assert qs.select_data == {'depth': 0, 'select': {}}


def test_default_exclusion_included():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ft1',
                'source': 'id',
                'hidden': True,
            },
            {
                'filter': 'ft2',
                'source': 'id',
            },
        )

    _, qs = Cls(book_qs).apply_filters('select(-ft2)')
    assert qs.select_data['select'] == {'ft1': False, 'ft2': False}


def test_default_exclusion_overridden():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ft1',
                'source': 'id',
                'hidden': True,
            },
            {
                'filter': 'ft2',
                'source': 'id',
            },
        )

    request = _Request()
    _, qs = Cls(book_qs).apply_filters('select(-ft2,ft1)', request)
    assert qs.select_data['select'] == {'ft1': True, 'ft2': False}


def test_signs_select():
    class Cls(SelectFilterCls):
        FILTERS = tuple(
            {
                'filter': 'ft{0}'.format(i),
                'source': 'id',
            }
            for i in range(1, 5)
        )

    _, qs = Cls(book_qs).apply_filters('select(ft1,+ft2,-ft3)')
    assert qs.select_data['select'] == {'ft1': True, 'ft2': True, 'ft3': False}


def test_bad_select_prop_top_level_include_select():
    with pytest.raises(RQLFilterParsingError) as e:
        SelectFilterCls(book_qs).apply_filters('select(abc)')

    assert e.value.details['error'] == 'Bad select filter: abc.'


def test_bad_select_prop_nested_include_select():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': ('id',),
            },
        )

    with pytest.raises(RQLFilterParsingError) as e:
        Cls(book_qs).apply_filters('select(+ns.abc)')

    assert e.value.details['error'] == 'Bad select filter: ns.abc.'


def test_bad_select_prop_top_level_exclude_select():
    with pytest.raises(RQLFilterParsingError) as e:
        SelectFilterCls(book_qs).apply_filters('select(-abc)')

    assert e.value.details['error'] == 'Bad select filter: -abc.'


def test_bad_select_prop_nested_exclude_select():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': ('id',),
            },
        )

    with pytest.raises(RQLFilterParsingError) as e:
        Cls(book_qs).apply_filters('select(-ns.abc)')

    assert e.value.details['error'] == 'Bad select filter: -ns.abc.'


def test_bad_select_prop_namespace_with_dot():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': ('id',),
            },
        )

    with pytest.raises(RQLFilterParsingError) as e:
        Cls(book_qs).apply_filters('select(+ns.)')

    assert e.value.details['error'] == 'Bad select filter: ns..'


def test_bad_select_prop_double_underscore_not_supported():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': ('id',),
            },
        )

    with pytest.raises(RQLFilterParsingError) as e:
        Cls(book_qs).apply_filters('select(+ns__id)')

    assert e.value.details['error'] == 'Bad select filter: ns__id.'


def test_bad_select_conf_included_then_excluded():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': ('id',),
            },
        )

    with pytest.raises(RQLFilterParsingError) as e:
        Cls(book_qs).apply_filters('select(ns.id,-ns)')

    assert e.value.details['error'] == 'Bad select filter: incompatible properties.'


def test_bad_select_conf_excluded_then_included():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'filters': ('id',),
            },
        )

    with pytest.raises(RQLFilterParsingError) as e:
        Cls(book_qs).apply_filters('select(-ns,+ns.id)')

    assert e.value.details['error'] == 'Bad select filter: incompatible properties.'


def test_exclude_ok():
    _, qs = SelectFilterCls(book_qs).apply_filters('select(-id)')
    assert qs.select_data == {'depth': 0, 'select': {'id': False}}


def test_select_complex():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ft1',
                'source': 'id',
            },
            {
                'filter': 'ft2',
                'source': 'id',
            },
            {
                'namespace': 'ns1',
                'source': 'author',
                'filters': (
                    {
                        'filter': 'ft1',
                        'source': 'id',
                        'hidden': True,
                    },
                    {
                        'filter': 'ft2',
                        'source': 'id',
                    },
                    {
                        'namespace': 'ns1',
                        'source': 'publisher',
                        'hidden': False,
                        'filters': ('id',),
                    },
                ),
            },
            {
                'namespace': 'ns2',
                'hidden': True,
                'source': 'author',
                'filters': (
                    {
                        'filter': 'ft1',
                        'source': 'id',
                        'hidden': True,
                    },
                    {
                        'filter': 'ft2',
                        'source': 'id',
                    },
                    {
                        'filter': 'ft3',
                        'source': 'id',
                    },
                    {
                        'namespace': 'ns1',
                        'source': 'publisher',
                        'filters': ('id',),
                    },
                    {
                        'namespace': 'ns2',
                        'source': 'publisher',
                        'filters': ('id',),
                    },
                ),
            },
        )

    _, qs = Cls(book_qs).apply_filters('select(ns2.ns2.id,ft1,ns1,ns1.ft1,ns2.ft2)')
    assert qs.select_data['select'] == {
        'ft1': True,
        'ns1': True,
        'ns1.ft1': True,
        'ns2': True,
        'ns2.ft1': False,
        'ns2.ft2': True,
        'ns2.ft3': False,
        'ns2.ns2': True,
        'ns2.ns2.id': True,
        'ns2.ns1': False,
    }


def test_qs_optimization_full_tree():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ft1',
                'source': 'id',
                'qs': SR('author'),
            },
            {
                'filter': 'ft2',
                'source': 'id',
                'qs': PR('pages'),
                'hidden': True,
            },
            {
                'namespace': 'ns',
                'source': 'author',
                'qs': NSR('author'),
                'filters': (
                    {
                        'filter': 'ft1',
                        'source': 'id',
                        'qs': NSR('publisher'),
                    },
                    {
                        'filter': 'ft2',
                        'source': 'id',
                        'qs': NPR('publisher'),
                    },
                ),
            },
        )

    _, qs = Cls(book_qs).apply_filters('select(-ns.ft2,ns)')
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_qs_optimization_custom_optimization():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ft1',
                'source': 'id',
            },
            {
                'filter': 'ft2',
                'source': 'id',
                'hidden': True,
            },
            {
                'namespace': 'ns',
                'source': 'author',
                'qs': NSR('author'),
                'filters': (
                    {
                        'filter': 'ft1',
                        'source': 'id',
                    },
                    {
                        'filter': 'ft2',
                        'source': 'id',
                    },
                ),
            },
        )

        def optimize_field(self, data):
            optimization_mapper = {
                'ft1': '_optimize_ft1',
                'ft2': '_optimize_ft2',
                'ns.ft1': '_optimize_ns_ft1',
                'ns.ft2': '_optimize_ns_ft2',
            }

            optimization_func = optimization_mapper.get(data.filter_path)
            if optimization_func:
                return getattr(self, optimization_func)(data)

        def _optimize_ft1(self, data):
            return data.queryset.select_related('author')

        def _optimize_ft2(self, data):
            return data.queryset.prefetch_related('pages')

        def _optimize_ns_ft1(self, data):
            return data.queryset.select_related('author__publisher')

        def _optimize_ns_ft2(self, data):
            return data.queryset.prefetch_related('author__publisher')

    _, qs = Cls(book_qs).apply_filters('select(-ns.ft2,ns)')
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_qs_optimization_django_error():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ft1',
                'source': 'id',
                'qs': SR('invalid'),
            },
        )

    _, qs = Cls(book_qs).apply_filters('')

    with pytest.raises(FieldError):
        list(qs.all())


def test_qs_optimization_deep_various_nesting():
    class AuthorCls(SelectFilterCls):
        MODEL = Author
        FILTERS = (
            {
                'namespace': 'publisher',
                'qs': NSR('publisher'),
                'filters': (
                    {
                        'namespace': 'fk',
                        'source': 'fk1',
                        'qs': NSR('fk1'),
                        'filters': ('id',),
                    },
                    {
                        'namespace': 'fk2',
                        'source': 'fk2',
                        'qs': NSR('fk2'),
                        'filters': ('id',),
                    },
                    {
                        'namespace': 'authors',
                        'qs': NPR('authors'),
                        'filters': ('id',),
                    },
                ),
            },
            {
                'namespace': 'fk1',
                'qs': NSR('fk'),
                'filters': ('id',),
            },
            {
                'filter': 'id',
                'qs': NPR('books'),
            },
        )

    class BookCls(SelectFilterCls):
        MODEL = Book
        FILTERS = (
            {
                'namespace': 'author',
                'qs': NSR('author'),
                'filters': AuthorCls.FILTERS,
            },
        )

    _, qs = BookCls(book_qs).apply_filters('')
    assert qs.query.select_related == {'author': {'publisher': {'fk1': {}, 'fk2': {}}, 'fk': {}}}
    assert qs._prefetch_related_lookups == (
        'author__publisher__authors', 'author__books',
    )


@pytest.mark.django_db
def test_annotations():
    class AnnotationCls(SelectFilterCls):
        FILTERS = (
            {
                'namespace': 'ns',
                'source': 'author',
                'qs': AN(ns=Value('abc', CharField(max_length=128))),
                'filters': (
                    'id',
                    {
                        'filter': 'ft',
                        'source': 'id',
                        'qs': AN(ns_ft=Value('abc', CharField(max_length=128))),
                    },
                ),
            },
            {
                'filter': 'ft1',
                'source': 'id',
                'hidden': True,
                'qs': AN(ft1=Value(1, IntegerField())),
            },
            {
                'filter': 'ft2',
                'dynamic': True,
                'field': IntegerField(),
                'qs': AN(ft2=Value(1, IntegerField())),
            },
            {
                'filter': 'vns.ft',
                'source': 'vns_ft',
                'dynamic': True,
                'field': IntegerField(),
                'qs': AN(vns_ft=Value(1, IntegerField())),
            },
        )

    qs = Book.objects.all()

    instance = AnnotationCls(qs)
    assert set(instance.filters.keys()) == set(instance.annotations.keys()) - {'ns'}
    assert instance.annotations['ns'] == instance.annotations['ns.id']
    assert instance.annotations['ns'] != instance.annotations['ns.ft']

    _, qs = AnnotationCls(qs, instance=instance).apply_filters('')
    assert set(qs.query.annotations.keys()) == {'ns', 'ns_ft', 'ft2', 'vns_ft'}
    assert not list(qs)

    _, qs = AnnotationCls(qs, instance=instance).apply_filters('ft1=3&ft2=5&vns.ft=3')
    assert set(qs.query.annotations.keys()) == {'ns', 'ns_ft', 'ft1', 'ft2', 'vns_ft'}
    assert not list(qs)


def test_annotations_misconfiguration():
    class AnnotationCls(RQLFilterClass):
        MODEL = Book
        FILTERS = (
            {
                'filter': 'ft',
                'dynamic': True,
                'field': IntegerField(),
                'qs': AN(ft=Value(1, IntegerField())),
            },
        )

    with pytest.raises(FieldError):
        AnnotationCls(book_qs).apply_filters('ft=2')


def test_deselect_namespace():
    class Cls(SelectFilterCls):
        FILTERS = (
            {
                'filter': 'ns.author',
                'dynamic': True,
                'qs': NSR('author'),
                'field': SelectField(),
            },
            {
                'namespace': 'ns2',
                'source': 'author',
                'qs': AN(ns=Value('abc', CharField(max_length=128))),
                'filters': ('id',),
            },
        )

    _, qs = Cls(book_qs).apply_filters('')
    assert qs.query.select_related == {'author': {}}

    _, qs = Cls(book_qs).apply_filters('select(-ns,-ns2)')
    assert not qs.query.select_related
