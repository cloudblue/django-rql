The "Power of Select"
=====================

The ``select`` operator
-----------------------

The ``select`` operator is very powerful and is expecially useful for REST APIs.


Suppose you have the following models:

.. code-block:: python

    class Category(models.Model):
        name = models.CharField(max_length=100)

    class Company(models.Model):
        name = models.CharField(max_length=100)
        vat_number = models.CharField(max_length=15)

    class Product(models.Model):
        name = models.CharField(max_length=100)
        category = models.ForeignKey(Category, on_delete=models.CASCADE)
        manufacturer = models.ForeignKey(Company, on_delete=models.CASCADE)

    

and the following filter class:

.. code-block:: python

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


Issuing the following query:

.. code-block::

    GET /products?ilike(name,*rql*)

Behind the scenes `django-rql` applies a ``select_releted`` optimization
to the queryset to retrive the category of each product doing a SQL JOIN.

Since the `manufacturer` has been declared ``hidden`` django-rql doesn't 
retrive the related manufacturer unless you write:

.. code-block::

    GET /products?ilike(name,*rql*)&select(manufacturer)

if you issue such query, `django-rql` apply the ``qs`` database optimization
so it adds a JOIN with the `Company` model to optimize database access.

The ``select`` operator can also be used to exclude fields so if you want to
retrieve products without retrieving the associated category you can write:

.. code-block::

    GET /products?ilike(name,*rql*)&select(-category)


So the category will be not fetched.

Django Rest Framework support
-----------------------------

If you are writing a REST API with Django Rest Framework, `django-rql` offers
an utility mixin (dj_rql.drf.serializers.RQLMixin) for your model serializers to automatically adjust the serialization
of related models depending on select.

.. code-block:: python

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


.. note::

    A complete working example of how the ``select`` operator works can be found at:

    `https://github.com/maxipavlovic/django_rql_select_example <https://github.com/maxipavlovic/django_rql_select_example>`_.

