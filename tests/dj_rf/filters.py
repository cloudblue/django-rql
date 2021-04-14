#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from dj_rql.constants import FilterLookups, RQL_NULL
from dj_rql.drf.fields import SelectField
from dj_rql.filter_cls import RQLFilterClass
from dj_rql.qs import AN, NSR, PR, SR

from django.db.models import AutoField, CharField, F, IntegerField

from tests.dj_rf.models import Book


AUTHOR_FILTERS = ['is_male', {
    'filter': 'email',
    'ordering': True,
    'search': True,
}, {
    'namespace': 'publisher',
    'filters': ['id'],
    'qs': NSR('publisher'),
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
        'distinct': True,
        'openapi': {
            'required': True,
        },
    }, {
        'filter': 'author__email',
        'search': True,
        'openapi': {
            'description': 'Author Email',
            'deprecated': True,
        },
    }, {
        'filter': 'name',
        'source': 'author__name',
        'distinct': True,
        'openapi': {
            'hidden': True,
        },
    }, {
        'namespace': 'author',
        'filters': AUTHOR_FILTERS,
        'qs': SR('author', 'author__publisher'),
    }, {
        'namespace': 'page',
        'source': 'pages',
        'filters': PAGE_FILTERS,
        'qs': PR('pages'),
    }, {
        'filter': 'published.at',
        'source': 'published_at',
        'ordering': True,
        'distinct': True,
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
        'null_values': {'random'},
    }, {
        'filter': 'url',
        'source': 'publishing_url',
        'openapi': {
            'type': 'string',
        },
    }, {
        'filter': 'd_id',
        'sources': ['id', 'author__id'],
        'ordering': True,
    }, {
        'filter': 'custom_filter',
        'distinct': True,
        'custom': True,
        'lookups': {FilterLookups.I_LIKE},

        'custom_data': [1],
    }, {
        'filter': 'int_choice_field',
        'ordering': True,
    }, {
        'filter': 'int_choice_field_repr',
        'source': 'int_choice_field',
        'use_repr': True,
        'lookups': {FilterLookups.EQ, FilterLookups.NE},
    }, {
        'filter': 'str_choice_field',
        'search': True,
    }, {
        'filter': 'str_choice_field_repr',
        'source': 'str_choice_field',
        'use_repr': True,
        'lookups': {FilterLookups.EQ, FilterLookups.NE},
    }, {
        'filter': 'has_list_lookup',
        'custom': True,
        'lookups': {FilterLookups.EQ, FilterLookups.NE, FilterLookups.IN, FilterLookups.OUT},
    }, {
        'filter': 'no_list_lookup',
        'custom': True,
        'lookups': {FilterLookups.EQ},
    }, {
        'filter': 't__in',
        'source': 'title',
        'openapi': {
            'type': 'custom',
            'format': 'custom',
        },
    }, 'github_stars', {
        'filter': 'ordering_filter',
        'custom': True,
        'ordering': True,
        'lookups': {FilterLookups.EQ},
    }, {
        'filter': 'fsm',
        'source': 'fsm_field',
        'ordering': True,
        'search': True,
    }, {
        'filter': 'anno_int',
        'dynamic': True,
        'field': IntegerField(),
        'lookups': {FilterLookups.EQ},
        'ordering': True,
    }, {
        'filter': 'anno_str',
        'dynamic': True,
        'field': CharField(),
        'search': True,
    }, {
        'filter': 'anno_int_ref',
        'dynamic': True,
        'field': IntegerField(),
        'source': 'anno_int',
        'ordering': True,
    }, {
        'filter': 'anno_auto',
        'dynamic': True,
        'field': AutoField(null=True),
        'qs': AN(anno_auto=F('id')),
    }, {
        'filter': 'anno_title_non_dynamic',
        'dynamic': False,
        'source': 'title',
    }, {
        'filter': 'anno_title_dynamic',
        'dynamic': True,
        'source': 'title',
        'field': CharField(),
        'search': True,
    }, {
        'namespace': 'author_publisher',
        'source': 'author__publisher',
        'filters': ['id'],
    }, {
        'filter': 'select_author',
        'dynamic': True,
        'field': SelectField(),
        'hidden': True,
        'qs': SR('author'),
    }]


class SelectBooksFilterClass(BooksFilterClass):
    SELECT = True
