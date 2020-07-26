Quickstart
==========

We're going to create a simple API and configure filters to support RQL syntax.


Installation
------------
Install `django-rql` library in your existing or new Django and Django REST Framework project using command

```
pip install django-rql
```

Configuring Django settings
---------------------------

Setup default `filter_backends` in your Django settings file

```
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['dj_rql.drf.RQLFilterBackend']
}
```

Now your APIs are supporting RQL syntax for query strings. Let's write some filters

Write your first RQL Filter Class
---------------------------------

For writing your first RQL Filter Class you need some models to be ready. Let's imagine you have simple Domain Model in your project, that can be represented as several models like below

```
from django.db import models


class Product(models.Model):
    name = models.CharField()
```

Let's create an RQL Filter Class for `Product` model. All you need is to inherit from `dj_rql.filter_cls.RQLFilterClass`, define `MODEL` property and add supported `FILTERS` for class

```
from dj_rql.filter_cls import RQLFilterClass


class ProductFilters(RQLFilterClass):
    MODEL = Product
    FILTERS = (
        'id',
        'name',
    )

```

Using simple strings in `FILTERS` property you can define what fields are available for filtering. In example above you allow filtering only by `id` and `name` filter

Add RQL Filter Class to DRF View
--------------------------------

In your latest step you need to add `ProductFilters` class as a `rql_filter_class` property inside your View

```
class ProductsViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    rql_filter_class = ProductFilters
```

And that's it! Now you are able to start your local server and try to filter using RQL syntax

```
curl http://127.0.0.1:8080/api/v1/products?like(name,Unicorn*)|eq(name,LLC)
```

For learning RQL Syntax use following links:

[RQL Reference][rql_reference]

[RQL for Web][rql_for_web]

For learning how to define more complex filters use [Filters Guide][filters_guide]

[rql_reference]: https://connect.cloudblue.com/community/api/rql/
[rql_for_web]: https://www.sitepen.com/blog/resource-query-language-a-query-language-for-the-web-nosql/
[filters_guide]: ./filters_guide.md
