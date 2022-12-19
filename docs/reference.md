API Reference
=============


# Default lookups by field type


| Model fields              | Lookup operators                                               |
| ------------------------- | -------------------------------------------------------------- |
| AutoField                 | `eq`, `ne`, `ge`, `gt`, `le`, `lt`, `in`, `out` {: rowspan=11} |
| BigAutoField              | &#8288 {: style="padding:0"}                                   |
| BigIntegerField           | &#8288 {: style="padding:0"}                                   |
| DateField                 | &#8288 {: style="padding:0"}                                   |
| DateTimeField             | &#8288 {: style="padding:0"}                                   |
| DecimalField              | &#8288 {: style="padding:0"}                                   |
| FloatField                | &#8288 {: style="padding:0"}                                   |
| IntegerField              | &#8288 {: style="padding:0"}                                   |
| PositiveIntegerField      | &#8288 {: style="padding:0"}                                   |
| PositiveSmallIntegerField | &#8288 {: style="padding:0"}                                   |
| SmallIntegerField         | &#8288 {: style="padding:0"}                                   |
| BooleanField              | `eq`, `ne` {: rowspan=2}                                       |
| NullBooleanField          | &#8288 {: style="padding:0"}                                   |
| CharField                 | `eq`, `ne`, `in`,`out`, `like`,`ilike` {: rowspan=6}           |
| EmailField                | &#8288 {: style="padding:0"}                                   |
| SlugField                 | &#8288 {: style="padding:0"}                                   |
| TextField                 | &#8288 {: style="padding:0"}                                   |
| URLField                  | &#8288 {: style="padding:0"}                                   |
| UUIDField                 | &#8288 {: style="padding:0"}                                   |


# Constants

::: dj_rql.constants.FilterLookups
    :docstring:

# Exceptions

The specifications for the exceptions could be found in the library [Lib rql](https://lib-rql.readthedocs.io/en/latest/)

# Filter classes

::: dj_rql.filter_cls.RQLFilterClass
    :docstring:
    :members: build_q_for_custom_filter build_name_for_custom_ordering optimize_field apply_annotations apply_filters build_q_for_filter get_filter_base_item

::: dj_rql.filter_cls.AutoRQLFilterClass
    :docstring:

::: dj_rql.filter_cls.NestedAutoRQLFilterClass
    :docstring:

# DB optimization

::: dj_rql.qs.SelectRelated
    :docstring:
    :members: apply

::: dj_rql.qs.PrefetchRelated
    :docstring:
    :members: apply

# Django Rest Framework extensions

## Filter backend

::: dj_rql.drf.backend.RQLFilterBackend
    :docstring:
    :members: filter_queryset get_schema_operation_parameters get_filter_class get_query

## Pagination

::: dj_rql.drf.paginations.RQLLimitOffsetPagination
    :docstring:
    :members: get_paginated_response_schema paginate_queryset get_limit get_offset

::: dj_rql.drf.paginations.RQLContentRangeLimitOffsetPagination
    :docstring:
    :members: get_paginated_response

## Serialization

::: dj_rql.drf.serializers.RQLMixin
    :docstring:
    :members: to_representation apply_rql_select rql_context

## OpenAPI

::: dj_rql.openapi.RQLFilterClassSpecification
    :docstring:
    :members: get get_for_field 

::: dj_rql.openapi.RQLFilterDescriptionTemplate
    :docstring:
    :members: render 
