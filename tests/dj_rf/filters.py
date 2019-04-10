from __future__ import unicode_literals


from dj_rql.rest_framework.filter_cls import RQLFilterClass
from dj_rql.constants import LookupTypes
from tests.dj_rf.models import Book


AUTHOR_FILTERS = ['is_male', {
    'filter': 'email',
}, {
    'namespace': 'publisher',
    'filters': ['id']
}]


PAGE_FILTERS = [{
    'filter': 'number',
    'lookups': {LookupTypes.EQ, LookupTypes.NE},
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
        'lookups': {LookupTypes.GE, LookupTypes.LT},
    }, {
        'filter': 'url',
        'source': 'publishing_url',
    }]
