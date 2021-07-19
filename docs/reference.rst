=============
API Reference
=============

.. _default-lookups:

Default lookups by field type
-----------------------------

+---------------------------+------------------+
| Model fields              | Lookup operators |
+===========================+==================+
| AutoField                 | ``eq``, ``ne``,  | 
+---------------------------+ ``ge``, ``gt``,  |
| BigAutoField              | ``le``, ``lt``,  |
+---------------------------+ ``in``, ``out``  |
| BigIntegerField           |                  |
+---------------------------+                  |
| DateField                 |                  |
+---------------------------+                  |
| DateTimeField             |                  |
+---------------------------+                  |
| DecimalField              |                  |
+---------------------------+                  |
| FloatField                |                  |
+---------------------------+                  |
| IntegerField              |                  |
+---------------------------+                  |
| PositiveIntegerField      |                  |
+---------------------------+                  |
| PositiveSmallIntegerField |                  |
+---------------------------+                  |
| SmallIntegerField         |                  |
+---------------------------+------------------+
| BooleanField              | ``eq``, ``ne``   |
+---------------------------+                  |
| NullBooleanField          |                  |
+---------------------------+------------------+
| CharField                 | ``eq``, ``ne``,  |
+---------------------------+ ``in``, ``out``, |
| EmailField                | ``like``,        |
+---------------------------+ ``ilike``        |
| SlugField                 |                  |
+---------------------------+                  |
| TextField                 |                  |
+---------------------------+                  |
| URLField                  |                  |
+---------------------------+                  |
| UUIDField                 |                  |
+---------------------------+------------------+


Constants
---------

.. autoclass:: dj_rql.constants.FilterLookups
   :members:


Exceptions
----------

.. automodule:: dj_rql.exceptions
   :members:


Filter classes
------------

.. autoclass:: dj_rql.filter_cls.RQLFilterClass
   :members:


.. autoclass:: dj_rql.filter_cls.AutoRQLFilterClass
   :members:


.. autoclass:: dj_rql.filter_cls.NestedAutoRQLFilterClass
   :members:


DB optimization
---------------

.. autoclass:: dj_rql.qs.SelectRelated
   :members:


.. autoclass:: dj_rql.qs.PrefetchRelated
   :members:

.. automodule:: dj_rql.qs
   :members: SR, PR

Django Rest Framework extensions
--------------------------------


Filter backend
^^^^^^^^^^^^^^

.. autoclass:: dj_rql.drf.backend.RQLFilterBackend
   :members:


Pagination
^^^^^^^^^^

.. automodule:: dj_rql.drf.paginations
   :members:

Serialization
^^^^^^^^^^^^^

.. automodule:: dj_rql.drf.serializers.RQLMixin
   :members:



OpenAPI
^^^^^^^

.. autoclass:: dj_rql.openapi.RQLFilterClassSpecification
   :members:


.. autoclass:: dj_rql.openapi.RQLFilterDescriptionTemplate
   :members: