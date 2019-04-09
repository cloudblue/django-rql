from __future__ import unicode_literals


from dj_rql.rest_framework.filter_class import RQLFilterClass
from tests.dj_rf.models import Book


class BooksFilterClass(RQLFilterClass):
    MODEL = Book
    FIELDS = ['id', 'title', 'current_price', 'written', 'status', {
        'filter': 'author.name',
    }, {
        'filter': 'name',
        'source': 'author__name',
    }, {
        'filter': 'author__email',
    }, {
        'namespace': 'author',
        'filters': ['is_male', 'publisher.id'],
    }, {
        'namespace': 'page',
        'source': 'pages',
        'filters': [{
            'filter': 'number',
            'lookups': ['eq', 'ne'],
        }, {
            'filter': 'id',
            'source': 'uuid',
        }]
    }, {
        'filter': 'published.at',
        'source': 'published_at',
    }, {
        'filter': 'rating.blog',
        'source': 'blog_rating',
        'use_repr': True,
    }, {
        'filter': 'amazon_rating',
        'lookups': ['ge', 'lt'],
    }, {
        'filter': 'url',
        'source': 'publishing_url',
    }]
