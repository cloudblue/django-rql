from django.db.models import IntegerField, Value

from dj_rql.filter_cls import RQLFilterClass
from dj_rql.qs import AN, CH, PR, NPR, NSR, SR

from tests.dj_rf.models import Book
from tests.test_filter_cls.utils import book_qs


class SelectFilterCls(RQLFilterClass):
    MODEL = Book
    SELECT = True
    FILTERS = ('id',)

    @property
    def heirarchy(self):
        return self._select_tree

    @property
    def exclusions(self):
        return self._default_exclusions


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
                        'filters': ('id',)
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


def test_apply_rql_select_not_applied_non_select_cls():
    pass


def test_apply_rql_select_not_applied_no_request():
    pass


def test_apply_rql_select_applied_no_query():
    pass


def test_all_variations_of_select_combinations():
    # Need to check every potential branch
    pass
