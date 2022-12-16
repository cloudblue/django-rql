Django RQL
==========
[![pyversions](https://img.shields.io/pypi/pyversions/django-rql.svg)](https://pypi.org/project/django-rql/)
[![PyPi Status](https://img.shields.io/pypi/v/django-rql.svg)](https://pypi.org/project/django-rql/)
[![PyPI status](https://img.shields.io/pypi/status/django-rql.svg)](https://pypi.org/project/django-rql/)
[![Docs](https://readthedocs.org/projects/django-rql/badge/?version=latest)](https://readthedocs.org/projects/django-rql) 
[![Build Status](https://github.com/cloudblue/django-rql/workflows/Build%20Django-RQL%20library/badge.svg)](https://github.com/cloudblue/django-rql/actions)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=django-rql&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=django-rql)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=django-rql&metric=coverage)](https://sonarcloud.io/summary/new_code?id=django-rql)
[![PyPI Downloads](https://img.shields.io/pypi/dm/django-rql)](https://pypi.org/project/django-rql/)

`django-rql` is the Django app, that adds RQL filtering to your application.
This library is based on core [lib-rql](https://github.com/cloudblue/lib-rql) library.


RQL
---

RQL (Resource query language) is designed for modern application development. It is built for the web, ready for NoSQL, and highly extensible with simple syntax.
This is a query language fast and convenient database interaction. RQL was designed for use in URLs to request object-style data structures.

[RQL Reference](https://connect.cloudblue.com/community/api/rql/)


Currently supported operators
=============================
1. Comparison (eq, ne, gt, ge, lt, le, like, ilike, search)
2. List (in, out)
3. Logical (and, or, not)
4. Constants (null(), empty())
5. Ordering (ordering)
6. Select (select)
7. Tuple (t)


Documentation
=============

Full documentation is available at [https://django-rql.readthedocs.org](https://django-rql.readthedocs.org).


Example
=======

```python
from dj_rql.filter_cls import RQLFilterClass, RQL_NULL

from py_rql.constants import FilterLookups


class ModelFilterClass(RQLFilterClass):
    """
    MODEL - Django ORM model
    FILTERS - List of filters
    EXTENDED_SEARCH_ORM_ROUTES - List of additional Django ORM fields for search
    DISTINCT - Boolean flag, that specifies if queryset must always be DISTINCT
    SELECT - Boolean flag, that specifies if Filter Class supports select operations and queryset optimizations
    OPENAPI_SPECIFICATION - Python class that renders OpenAPI specification

    Filters can be set in two ways:
        1) string (default settings are calculated from ORM)
        2) dict (overriding settings for specific cases)

    Filter Dict Structure
    {
        'filter': str
        # or
        'namespace': str

        'source': str
        # or
        'sources': iterable
        # or
        'custom': bool
        # or
        'dynamic': bool
        'field': obj

        'lookups': set

        'qs': obj

        'use_repr': bool  # can't be used in namespaces
        'ordering': bool  # can't be true if 'use_repr=True'
        'search': bool    # can't be true if 'use_repr=True'
        'hidden': bool
    }

    """
    MODEL = Model
    FILTERS = ['id', {
        # `null_values` can be set to override ORM is_null behaviour
        # RQL_NULL is the default value if NULL lookup is supported by field
        'filter': 'title',
        'null_values': {RQL_NULL, 'NULL_ID'},
        'ordering': False,
    }, {
        # `ordering` can be set to True, if filter must support ordering (sorting)
        # `ordering` can't be applied to non-db fields
        'filter': 'status',
        'ordering': True,
    }, {
        # `search` must be set to True for filter to be used in searching
        # `search` must be applied only to text db-fields, which have ilike lookup
        'filter': 'author__email',
        'search': True,
    }, {
        # `source` must be set when filter name doesn't match ORM path
        'filter': 'name',
        'source': 'author__name',
    }, {
        # `namespace` is useful for API consistency, when dealing with related models
        'namespace': 'author',
        'filters': ['id', 'name'],  # will be converted to `author.id` and `author.name`
    },{
        # `distinct` needs to be setup for filters that require QS to work in DISTINCT mode
        # `openapi` configuration is automatically collected by OpenAPI autogenerator
        'filter': 'published.at',
        'source': 'published_at',
        'distinct': True,
        'openapi': {
            'required': True,
            'deprecated': True,
            'description': 'Good description',
            'hidden': False,  # can be set to avoid collecting by autogenerator
            # type and format are collected automatically and shouldn't be setup, in general
            'type': 'string',
            'format': 'date',
        },
    }, {
        # `use_repr` flag is used to filter by choice representations
        'filter': 'rating.blog',
        'source': 'blog_rating',
        'use_repr': True,
    }, {
        # `hidden` flag is used to set default select behaviour for associated field
        'filter': 'rating.blog_int',
        'source': 'blog_rating',
        'use_repr': False,
        'ordering': True,
        'hidden': True,
    }, {
        # We can change default lookups for a certain filter
        'filter': 'amazon_rating',
        'lookups': {FilterLookups.GE, FilterLookups.LT},
    }, {
        # Sometimes it's needed to filter by several sources at once (distinct is always True).
        # F.e. this could be helpful for searching.
        'filter': 'd_id',
        'sources': {'id', 'author__id'},
        'ordering': True,
    }, {
        # Some fields may have no DB representation or non-typical ORM filtering
        # `custom` option must be set to True for such fields
        'filter': 'custom_filter',
        'custom': True,
        'lookups': {FilterLookups.EQ, FilterLookups.IN, FilterLookups.I_LIKE},
        'ordering': True,
        'search': True,
         # Optional ORM field for query parameter value validation
        'field': IntegerField(), 

        'custom_data': [1],
    }]


from dj_rql.drf.backend import RQLFilterBackend
from dj_rql.drf.paginations import RQLContentRangeLimitOffsetPagination


class DRFViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = MODEL.objects.all()
    serializer_class = ModelSerializer
    rql_filter_class = ModelFilterClass
    pagination_class = RQLContentRangeLimitOffsetPagination
    filter_backends = (RQLFilterBackend,)
```

Notes
=====
0. Values with whitespaces or special characters, like ',' need to have "" or ''
1. Supported date format is ISO8601: 2019-02-12
2. Supported datetime format is ISO8601: 2019-02-12T10:02:00 / 2019-02-12T10:02Z / 2019-02-12T10:02:00+03:00
3. Support for Choices() fields from [Django Model Utilities](https://django-model-utils.readthedocs.io/en/latest/utilities.html#choices) is added
4. Library supports [caching with different strategies](https://cachetools.readthedocs.io/en/stable/#cache-implementations) for queryset building, which can be very useful for collections, which use `select()`.
> Queryset execution result (filtered data) is NOT cached (!), only queryset building is cached.

```python
from dj_rql.filter_cls import RQLFilterClass

from cachetools import LRUCache

class MyFilterClass(RQLFilterClass):
    SELECT = True
    QUERIES_CACHE_BACKEND = LRUCache
    QUERIES_CACHE_SIZE = 100
```

Helpers
================================
There is a Django command `generate_rql_class` to decrease development and integration efforts for filtering.
This command automatically generates a filter class for a given model with all relations and all optimizations (!) to the specified depth.

Example
-------
```commandline
django-admin generate_rql_class --settings=tests.dj_rf.settings tests.dj_rf.models.Publisher --depth=1 --exclude=authors,fk2
```
This command for the model `Publisher` from tests package will produce the following output to stdout:
```python
from tests.dj_rf.models import Publisher

from dj_rql.filter_cls import RQLFilterClass
from dj_rql.qs import NSR


class PublisherFilters(RQLFilterClass):
    MODEL = Publisher
    SELECT = True
    EXCLUDE_FILTERS = ['authors', 'fk2']
    FILTERS = [
    {
        "filter": "id",
        "ordering": True,
        "search": False
    },
    {
        "filter": "name",
        "ordering": True,
        "search": True
    },
    {
        "namespace": "fk1",
        "filters": [
            {
                "filter": "id",
                "ordering": True,
                "search": False
            }
        ],
        "qs": NSR('fk1')
    }
]

```


Django Rest Framework Extensions
================================
1. Pagination (limit, offset)
0. Support for custom fields, inherited at any depth from basic model fields, like CharField().
0. Backend `DjangoFiltersRQLFilterBackend` with automatic conversion of [Django-Filters](https://django-filter.readthedocs.io/en/master/) query to RQL query.
0. OpenAPI docs are autogenerated for filter classes.

Best Practices
==============
1. Use `dj_rql.utils.assert_filter_cls` to test your API view filters. If the mappings are correct and there is no custom filtering logic, then it's practically guaranteed, that filtering will work correctly.
2. Prefer using `custom=True` with `RQLFilterClass.build_q_for_custom_filter` overriding over overriding `RQLFilterClass.build_q_for_filter`.
3. Custom filters may support ordering (`ordering=True`) with `build_name_for_custom_ordering`.
4. Django JSON fields can't be used as namespaces currently, but can be supported via `dynamic=True`, for example:
```python
{
    'filter': 'json_data.key',
    'source': 'json_data__key',
    'dynamic': True,
    'field': CharField(null=True),
},
```

Development
===========

1. Python 3.6+
2. Install dependencies `requirements/dev.txt` and `requirements/extra.txt`
3. We use `isort` library to order and format our imports, and we check it using `flake8-isort` library (automatically on `flake8` run).  
For convenience you may run `isort .` to order imports.

Testing
=======

1. Python 3.6+
0. Install dependencies `requirements/test.txt`
0. `export PYTHONPATH=/your/path/to/django-rql/`

Check code style: `flake8`
Run tests: `pytest`

Tests reports are generated in `tests/reports`.
* `out.xml` - JUnit test results
* `coverage.xml` - Coverage xml results

To generate HTML coverage reports use:
`--cov-report html:tests/reports/cov_html`

