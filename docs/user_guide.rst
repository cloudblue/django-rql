User guide
==========


Supported operators
-------------------

The following operators are currently supported by `django-rql`:

1. Comparison (eq, ne, gt, ge, lt, le, like, ilike, search)
#. List (in, out)
#. Logical (and, or, not)
#. Constants (null(), empty())
#. Ordering (ordering)
#. Select (select)


.. note::

    This guide assumes that you have already read the `RQL Reference <https://connect.cloudblue.com/community/api/rql/>`_.


Write your filter classes
-------------------------

A simple filter class looks like:

.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = ('a_field', 'another_field',)



Filter fields must be specified using the ``FILTERS`` attribute of the RQLFilterClass subclass.

For each field listed through the ``FILTERS`` attribute, `django-rql` determines defaults (lookup operators, null values, etc).
For example if your field is a models.CharField by default you can use the operators
``eq``, ``ne``, ``in``, ``out``, ``like``, ``ilike`` as long as the ``null`` constant.

Please refers to :ref:`default-lookups` for a complete list of defaults.

If you want a fine grained control of your filters (allowed lookups, null values, aliases, etc) you can do that
using a dictionary instead of a string with the name of the field.


Overriding default lookups
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want for a certain filter to specify which lookups it supports you can do that using the ``lookups`` property:


.. code-block:: python

    from dj_rql.constants import FilterLookups

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            {
                'filter': 'title',
                'lookups': {FilterLookups.EQ, FilterLookups.LIKE, FilterLookups.I_LIKE}
            },
        )


ordering
^^^^^^^^

You can allow users to sort by a specific filter using the ``ordering`` property:

.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title', 
            {
                'filter': 'published_at',
                'ordering': True,
            },
        )

On such filter you can sort in ascending order giving:

.. code-block::

    GET /books?ordering(published_at)


To sort in descending order you can use the ``-`` symbol:

.. code-block::

    GET /books?ordering(-published_at)


.. note:: 

    Ordering can only be specified for database fields.



distinct
^^^^^^^^

If you want to apply a SELECT DISTINCT to the resulting queryset you can use the ``distinct`` property:


.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title', 
            {
                'filter': 'published_at',
                'distinct': True,
            },
        )

This way, if the `published_at` fielter is present in the query, a SELECT DISTINCT will be applied.

.. note::

    If you want to perform a `SELECT DISTINCT` regardless of which filter is involved in the query,
    you can do that by adding the ``DISTINCT`` attribute to your filter class set to True.
    See :class:`dj_rql.filter_cls.RQLFilterClass`.


search
^^^^^^

Search allows filtering by all properties supporting such lookups that match a given pattern.

If you want to use the ``search`` operator you must set the ``search`` property to True:

.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title', 
            {
                'filter': 'synopsis',
                'search': True,
            },
        )


This way you can issue the following query:

.. code-block::

    GET /books?search(synopsis,murder)


this is equivalent to:

.. code-block::

    GET /books?ilike(synopsis,*murder*)


.. note::

    The ``search`` property can be applied only to text database fields, which have the ``ilike`` lookup.



use_repr
^^^^^^^^

For fields with choices, you may want to allow users to filter for the choice label instead of its database value,
so in this case you can set the ``use_repr`` property to True:


.. code-block:: python

    STATUSES = (
        ('1', 'Available'),
        ('2', 'Reprint'),
        ...
    )

    class Book(models.Model):
        ...

        status = models.CharField(max_length=2, choices=STATUSES)


    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title', 
            {
                'filter': 'status',
                'use_repr': True,
            },
        )


So you can filter for status like:

.. code-block::

    GET /books?eq(status,Available)


.. note::

    ``use_repr`` can be used neither with ``ordering`` nor ``search``.


source and sources
^^^^^^^^^^^^^^^^^^

Sometimes it is better to use a name other than the field name for the filter. 
In this case you can use the ``source`` property to specify the name of the field:

.. code-block:: python

    class MyFilterClass(RQLFilterClass):

        MODEL = MyModel
        FILTERS = (
            'a_field',
            {
                'filter': 'filter_name',
                'source': 'field_name',
            },
        )

A typical use case is to define filters for fields on related models:


.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title',
            {
                'filter': 'author',
                'source': 'author__name',
            },
        )


If you want to use a filter to search in two or more fields you can use the property ``sources``:

.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title',
            {
                'filter': 'author',
                'sources': ('author__name', 'author__surname'),
            },
        )



dynamic and field
^^^^^^^^^^^^^^^^^

``django-rql`` allows to filter for dynamic fields (aggregations and annotations).

Suppose you have an initial queryset like:

.. code-block:: python

    queryset = Book.objects.annotate(num_authors=Count('authors'))


And you want to allows to filter by the number of authors that contribute to the book,
you can do that by setting the ``dynamic`` property to True and specify the data type for
the `num_authors` column through the ``field`` property:


.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title',
            {
                'filter': 'num_authors',
                'dynamic': True,
                'field': models.IntegerField(),
            },
        )


So you can write queries like this:

.. code-block::

    GET /books?ge(num_authors,2)

And obtain all the books that have two or more authors.


null_values
^^^^^^^^^^^

In some circumstances you may have some of the values for a field that you would like to consider equivalent to a database NULL.

In this case you can specify which values can considered equivalent to NULL so you can use the ``null()`` contant to filter:


.. code-block:: python

    from dj_rql.filter_cls import RQLFilterClass, RQL_NULL

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title',
            {
                'filter': 'isbn',
                'null_values': {RQL_NULL, '0-0000000-0-0'}
            },
        )


So if you issue the following query:

.. code-block::

    GET /books?eq(isbn,null())


The resulting queries will contains both records where the `isbn` column is NULL and records
that has the `isbn` column equal to `0-0000000-0-0`.


namespace
^^^^^^^^^

You can allow users to filter by fields on related models. Namespaces allow to do that and is usefull
for api consistency.

Consider the following filter class:


.. code-block:: python

    class Author(models.Model):
        name = models.CharField(max_length=50)
        surname = models.CharField(max_length=100)

    class Book(models.Model):
        title = models.CharField(max_length=255)
        autor = models.ForeignKey(Author, on_delete=models.CASCADE)

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            'title',
            {
                'namespace': 'author',
                'filters': ('name', 'surname'),
            },
        )


With this filters definition you can filter also for author's name and surname the following way:

.. code-block::

    GET /books?and(eq(author.name,Ken),eq(author.surname,Follett))


custom
^^^^^^

Sometimes you may want to apply your specific filtering logic for a filter.

To do so, you have to set the ``custom`` property for that filter to True, define available ``lookups``
and override the ``build_q_for_custom_filter`` method of your filter class.

.. code-block:: python

    class BookFilters(RQLFilterClass):

        MODEL = Book
        FILTERS = (
            {
                'filter': 'title',
                'lookups': {FilterLookups.EQ, FilterLookups.IN},
                'custom': True,
            },
        )

        def build_q_for_custom_filter(self, filter_name, operator, str_value, **kwargs):
            pass  #  Put your filtering logic here and return a ``django.db.models.Q`` object.



Django Rest Framework extensions
--------------------------------

Pagination
^^^^^^^^^^

`django-rql` supports pagination for your api view through the :class:`dj_rql.drf.paginations.RQLLimitOffsetPagination`.


OpenAPI specifications
^^^^^^^^^^^^^^^^^^^^^^

If you are using `django-rql` with Django Rest Framework to expose filters for your REST API,
the ``openapi`` property allow you to describe the filter as long as control how specs for
that filter will be generated.

.. code-block:: python

    'openapi': {
        'description': 'Good description',
    }


Additional properties are:

    * ``required``: You can do a filter mandatory by set it to True.
    * ``deprecated``: You can mark a filter as deprecated set it to True.
    * ``hidden``: Set it to True if you don't want this filter to be included in specs.
    * ``type``: Allow overriding the filter data type inferred by the underlying model field.
    * ``format``: Allow overriding the default field format inferred by the underlying model field.


For the ``type`` and ``format`` attributes please refers to the `Data Types <http://spec.openapis.org/oas/v3.0.3#data-types>`_ 
section of the OpenAPI specifications.
