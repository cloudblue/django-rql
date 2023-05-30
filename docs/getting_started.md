Getting started
===============

# Requirements

`django-rql` works with Python 3.8 or newer and has the
following dependencies:

-   Django >= 3.2.* and <= 4.1
-   lark-parser 0.8.2

And the following optional dependency:

-   djangorestframework >= 3.12

# Install

`django-rql` can be installed from pypi.org with pip:

``` shell
$ pip install django-rql
```

If you want to use `django-rql` with Django Rest Framework
you have to install the optional dependency:

``` shell
$ pip install django-rql[drf]
```

# Write your first RQL Filter Class

For writing your first RQL Filter Class you need some models to be
ready. Let's imagine you have simple Domain Model in your project, that
can be represented as several models like below:

``` py3
from django.db import models


class Product(models.Model):
    name = models.CharField()
```

Let's create an RQL Filter Class for `Product` model. All you need is
to inherit from `dj_rql.filter_cls.RQLFilterClass`, define `MODEL`
property and add supported `FILTERS` for class:

``` py3
from dj_rql.filter_cls import RQLFilterClass


class ProductFilters(RQLFilterClass):
    MODEL = Product
    FILTERS = (
        'id',
        'name',
    )
```

Using simple strings in `FILTERS` property you can define what fields
are available for filtering. In example above you allow filtering only
by `id` and `name` filter.

If you have a pretty simple model and want everything out of the box
(all filters with search and ordering), there is even a simpler
automated way! All you have to do is inherit from
`dj_rql.filter_cls.AutoRQLFilterClass`:

``` py3
from dj_rql.filter_cls import AutoRQLFilterClass


class ProductFilters(AutoRQLFilterClass):
    MODEL = Product
```

# Use your RQL filter class in your views

``` py3
from urllib.parse import unquote

from products.filters import ProductFilters
from products.models import Product


def search_products_by_name(request):
    query = unquote(request.meta['QUERY_STRING'])

    base_queryset = Product.objects.all()

    my_filter = ProductFilters(base_queryset)

    _, filtered_qs = my_filter.apply_filters(query)

    return render(request, 'products/search.html', {'products': filtered_qs})
```

``` shell
$ curl http://127.0.0.1:8080/api/v1/products?like(name,Unicorn*)|eq(name,LLC)
```

# Use django-rql with Django Rest Framework

## Configuring Django settings

Setup default `filter_backends` in your Django settings file:

``` py3
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['dj_rql.drf.RQLFilterBackend']
}
```

Now your APIs are supporting RQL syntax for query strings.

## Add RQL Filter Class to DRF View

In your latest step you need to add `ProductFilters` class as a
`rql_filter_class` property inside your View:

``` py3
class ProductsViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    rql_filter_class = ProductFilters
```

And that's it! Now you are able to start your local server and try to
filter using RQL syntax

``` shell
$ curl http://127.0.0.1:8080/api/v1/products?like(name,Unicorn*)|eq(name,LLC)
```
