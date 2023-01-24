## Default lookups by field type

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


## Constants

More details about the specifications for the constants `py_rql.constants` could be found in the library [lib-rql](https://lib-rql.readthedocs.io/en/latest/).

### py_rql.constants.<strong>FilterLookups</strong>

::: py_rql.constants.FilterLookups
    options:
        heading_level: 3

## Exceptions

More details about the specifications for the exceptions `py_rql.exceptions` could be found in the library [lib-rql](https://lib-rql.readthedocs.io/en/latest/).

### <strong>RQLFilterError</strong>

::: py_rql.exceptions.RQLFilterError
    options:
        heading_level: 3

### <strong>RQLFilterParsingError</strong>

::: py_rql.exceptions.RQLFilterParsingError
    options:
        heading_level: 3

### <strong>RQLFilterLookupError</strong>

::: py_rql.exceptions.RQLFilterLookupError
    options:
        heading_level: 3

### <strong>RQLFilterValueError</strong>

::: py_rql.exceptions.RQLFilterValueError
    options:
        heading_level: 3


## Filter classes

### dj_rql.filter_cls.<strong>RQLFilterClass</strong>

::: dj_rql.filter_cls.RQLFilterClass
    options:
        members:
            - build_q_for_custom_filter
            - build_name_for_custom_ordering
            - optimize_field apply_annotations
            - apply_filters
            - build_q_for_filter
            - get_filter_base_item
        heading_level: 3

### dj_rql.filter_cls.<strong>AutoRQLFilterClass</strong>

::: dj_rql.filter_cls.AutoRQLFilterClass
    options:
        heading_level: 3

### dj_rql.filter_cls.<strong>NestedAutoRQLFilterClass</strong>

::: dj_rql.filter_cls.NestedAutoRQLFilterClass
    options:
        heading_level: 3

## DB optimization

The following DB optimizations could be done found on `dj_rql.filter_cls`.

### <strong>Annotation</strong>

::: dj_rql.qs.Annotation
    options:
        members:
            - apply
        heading_level: 3

### <strong>SelectRelated</strong>

::: dj_rql.qs.SelectRelated
    options:
        members:
            - apply
        heading_level: 3

### <strong>PrefetchRelated</strong>

::: dj_rql.qs.PrefetchRelated
    options:
        members:
            - apply
        heading_level: 3

### <strong>NestedPrefetchRelated</strong>

::: dj_rql.qs.NestedPrefetchRelated
    options:
        members:
            - apply
        heading_level: 3

### <strong>NestedSelectRelated</strong>

::: dj_rql.qs.NestedSelectRelated
    options:
        members:
            - apply
        heading_level: 3

### <strong>Chain</strong>

::: dj_rql.qs.Chain
    options:
        members:
            - apply
        heading_level: 3

## Django Rest Framework extensions

### Filter backend dj_rql.drf.backend.<strong>RQLFilterBackend</strong>

::: dj_rql.drf.backend.RQLFilterBackend
    options:
        members:
            - filter_queryset
        heading_level: 3

## Pagination

The following pagination classes found on `dj_rql.drf.paginations`:

### <strong>RQLLimitOffsetPagination</strong>

::: dj_rql.drf.paginations.RQLLimitOffsetPagination
    options:
        heading_level: 3

### <strong>RQLContentRangeLimitOffsetPagination</strong>

::: dj_rql.drf.paginations.RQLContentRangeLimitOffsetPagination
    options:
        heading_level: 3

## Serialization

### dj_rql.drf.serializers.<strong>RQLMixin</strong>

::: dj_rql.drf.serializers.RQLMixin
    options:
        heading_level: 3

## OpenAPI

The following OpenAPI classes found on `dj_rql.openapi`:

### <strong>RQLFilterClassSpecification</strong>

::: dj_rql.openapi.RQLFilterClassSpecification
    options:
        members:
            - get
            - get_for_field
        heading_level: 3

### <strong>RQLFilterClassSpecification</strong>

::: dj_rql.openapi.RQLFilterDescriptionTemplate
    options:
        members:
            - render
        heading_level: 3 

## Testing

### dj_rql.utils.<strong>assert_filter_cls</strong>

::: dj_rql.utils.assert_filter_cls
    options:
        heading_level: 3
