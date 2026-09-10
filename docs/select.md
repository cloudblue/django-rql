# The "Power of Select"


## The `select` operator

The `select` operator is very powerful and is expecially useful for REST
APIs.

Suppose you have the following models:

``` py3
class Category(models.Model):
    name = models.CharField(max_length=100)

class Company(models.Model):
    name = models.CharField(max_length=100)
    vat_number = models.CharField(max_length=15)

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    manufacturer = models.ForeignKey(Company, on_delete=models.CASCADE)
```

and the following filter class:

``` py3
from dj_rql.filter_cls import RQLFilterClass
from dj_rql.qs import SelectRelated

class ProductFilters(RQLFilterClass):

    MODEL = Product
    SELECT = True
    FILTERS = (
        'name',
        {
            'namespace': 'category',
            'filters': ('name',),
            'qs': SelectRelated('category'),
        },
        {
            'namespace': 'manufacturer',
            'filters': ('name', 'vat_number'),
            'hidden': True,
            'qs': SelectRelated('manufacturer'),
        }
    )
```

Issuing the following query:

``` 
GET /products?ilike(name,*rql*)
```

Behind the scenes ** django-rql ** applies a `select_releted`
optimization to the queryset to retrive the category of each product
doing a SQL JOIN.

Since the `manufacturer` has been declared `hidden`
django-rql doesn't retrive the related manufacturer unless you write:

``` 
GET /products?ilike(name,*rql*)&select(manufacturer)
```

If you issue such query, ** django-rql ** apply the `qs`
database optimization so it adds a JOIN with the `Company`
model to optimize database access.

The `select` operator can also be used to exclude fields so if you want
to retrieve products without retrieving the associated category you can
write:

``` 
GET /products?ilike(name,*rql*)&select(-category)
```

So the category will be not fetched.

## Django Rest Framework support

If you are writing a REST API with Django Rest Framework,
** django-rql ** offers an utility mixin
`dj_rql.drf.serializers.RQLMixin` for your model serializers to
automatically adjust the serialization of related models depending on
select.

``` py3
from rest_framework import serializers

from dj_rql.drf.serializers import RQLMixin

from ..models import Category, Company, Product


class CategorySerializer(RQLMixin, serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class CompanySerializer(RQLMixin, serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name')


class ProductSerializer(RQLMixin, serializers.ModelSerializer):
    category = CategorySerializer()
    company = CompanySerializer()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'company')
```

!!! note

    A complete working example of how the `select` operator works can be
    found [here](https://github.com/maxipavlovic/django_rql_select_example).

## Reading what a request selected

Sometimes a view has to know what the caller selected *before* the filtering runs,
because the queryset it builds depends on it. A typical case is deciding which
`Prefetch` objects or annotations are worth adding, which happens in `get_queryset()`,
and Django Rest Framework calls it before the filter backend gets to run.

`dj_rql.drf.get_select_props` reads the props straight from the query string of the
request:

``` py3
from dj_rql.drf import get_select_props


class ProductViewSet(mixins.ListModelMixin, GenericViewSet):
    filter_backends = (RQLFilterBackend,)
    rql_filter_class = ProductFilters

    def get_queryset(self):
        queryset = Product.objects.all()

        if 'reviews' in get_select_props(self.request):
            queryset = queryset.prefetch_related(
                Prefetch('reviews', queryset=Review.objects.published()),
            )

        return queryset
```

The props come back as the query wrote them, so an exclusion keeps its `-` prefix and
it is up to the view to decide what that means to it:

```
GET /products?select(reviews,-category)
```

``` py3
('reviews', '-category')
```

!!! note

    The accessor doesn't check the props against the filters of the filter class, and
    doesn't require `SELECT = True`, which is what makes it usable on a collection that
    accepts prop names it doesn't declare. It also never raises: a query that cannot be
    parsed simply has no props to read, and the request still gets rejected afterwards,
    by the filtering.
