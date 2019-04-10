from __future__ import unicode_literals


from dj_rql.rest_framework.filter_cls import RQLFilterClass
from dj_rql.constants import FilterLookupTypes
from tests.dj_rf.models import Book


AUTHOR_FILTERS = ['is_male', {
    'filter': 'email',
}, {
    'namespace': 'publisher',
    'filters': ['id']
}]


PAGE_FILTERS = [{
    'filter': 'number',
    'lookups': {FilterLookupTypes.EQ, FilterLookupTypes.NE},
}, {
    'filter': 'id',
    'source': 'uuid',
}]


class BooksFilterClass(RQLFilterClass):
    MODEL = Book
    FILTERS = ['id', 'title', 'current_price', 'written', {
        'filter': 'status',
    }, {
        'filter': 'author__email',
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
    }, {
        'filter': 'rating.blog',
        'source': 'blog_rating',
        'use_repr': True,
    }, {
        'filter': 'amazon_rating',
        'lookups': {FilterLookupTypes.GE, FilterLookupTypes.LT},
    }, {
        'filter': 'url',
        'source': 'publishing_url',
    }, {
        # Sometimes it's needed to filter by several sources at once (distinct is always True).
        # F.e. this could be helpful for searching.
        'filter': 'd_id',
        'sources': {'id', 'author__id'},
    }]
