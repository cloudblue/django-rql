from __future__ import unicode_literals

from dj_rql.filter_cls import RQLFilterClass
from dj_rql.constants import FilterLookups, RQL_NULL
from tests.dj_rf.models import Book


AUTHOR_FILTERS = ['is_male', {
    'filter': 'email',
    'ordering': True,
    'search': True,
}, {
    'namespace': 'publisher',
    'filters': ['id']
}]


PAGE_FILTERS = [{
    'filter': 'number',
    'lookups': {FilterLookups.EQ, FilterLookups.NE},
}, {
    'filter': 'id',
    'source': 'uuid',
}]


class BooksFilterClass(RQLFilterClass):
    MODEL = Book
    FILTERS = ['id', {
        'filter': 'title',
        'null_values': {RQL_NULL, 'NULL_ID'},
        'search': True,
    }, 'current_price', 'written', {
        'filter': 'status',
    }, {
        'filter': 'author__email',
        'search': True,
    }, {
        'filter': 'name',
        'source': 'author__name',
    }, {
        'namespace': 'author',
        'filters': AUTHOR_FILTERS,
    }, {
        'namespace': 'page',
        'source': 'pages',
        'filters': PAGE_FILTERS,
    }, {
        'filter': 'published.at',
        'source': 'published_at',
        'ordering': True,
    }, {
        'filter': 'rating.blog',
        'source': 'blog_rating',
        'use_repr': True,
    }, {
        'filter': 'rating.blog_int',
        'source': 'blog_rating',
        'use_repr': False,
    }, {
        'filter': 'amazon_rating',
        'lookups': {FilterLookups.GE, FilterLookups.LT},
    }, {
        'filter': 'url',
        'source': 'publishing_url',
    }, {
        'filter': 'd_id',
        'sources': ['id', 'author__id'],
        'ordering': True,
    }]
