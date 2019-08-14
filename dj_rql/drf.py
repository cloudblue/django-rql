from __future__ import unicode_literals

from django.utils.http import urlunquote
from lark.exceptions import LarkError
from rest_framework.filters import BaseFilterBackend
from rest_framework.pagination import LimitOffsetPagination, _positive_int
from rest_framework.response import Response

from dj_rql.constants import (
    RQL_ANY_SYMBOL, RQL_NULL, ComparisonOperators as CO, SearchOperators as SO,
)
from dj_rql.exceptions import RQLFilterParsingError
from dj_rql.parser import RQLParser
from dj_rql.transformer import RQLLimitOffsetTransformer


class FilterCache(object):
    CACHE = {}

    @classmethod
    def clear(cls):
        cls.CACHE = {}


class RQLFilterBackend(BaseFilterBackend):
    """ RQL filter backend for DRF GenericAPIViews.

    Examples:
        class ViewSet(mixins.ListModelMixin, GenericViewSet):
            filter_backends = (RQLFilterBackend,)
            rql_filter_class = ModelFilterClass
    """
    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view)
        if not filter_class:
            return queryset

        filter_instance = self._get_filter_instance(filter_class, queryset, view)
        rql_ast, queryset = filter_instance.apply_filters(self.get_query(filter_instance, request))
        setattr(request, 'rql_ast', rql_ast)
        return queryset

    @staticmethod
    def get_filter_class(view):
        return getattr(view, 'rql_filter_class', None)

    @staticmethod
    def _get_filter_instance(filter_class, queryset, view):
        qual_name = '{}.{}'.format(view.basename, filter_class.__name__)
        filter_instance = FilterCache.CACHE.get(qual_name)
        if filter_instance:
            filter_instance.queryset = queryset
        else:
            filter_instance = filter_class(queryset)
            FilterCache.CACHE[qual_name] = filter_instance
        return filter_instance

    @classmethod
    def get_query(cls, filter_instance, request):
        return _get_query(request)


class CompatibilityRQLFilterBackend(RQLFilterBackend):
    """
    If there is necessity to apply RQL filters to a production API, which was working on other
    filter backend (without raising API version number or losing compatibility), this base
    compatibility DRF backend must be inherited from.
    """
    @classmethod
    def get_query(cls, filter_instance, request):
        query_string = cls.modify_initial_query(filter_instance, request, _get_query(request))

        if not cls.is_old_syntax(filter_instance, request, query_string):
            return query_string

        return cls.get_rql_query(filter_instance, request, query_string)

    @classmethod
    def modify_initial_query(cls, filter_instance, request, query_string):
        return query_string

    @classmethod
    def is_old_syntax(cls, filter_instance, request, query_string):
        raise NotImplementedError

    @classmethod
    def get_rql_query(cls, filter_instance, request, query_string):
        raise NotImplementedError


class DjangoFiltersRQLFilterBackend(CompatibilityRQLFilterBackend):
    """
    DRF Backend, that automatically converts Django Filter specific queries to correct RQL queries.

    Currently NOT SUPPORTED:
        * range fields and filters;
        * regex and iregex conversion;
        * OrderingFilter;
        * MultipleChoiceFilter;
        * ?&& syntax in queries;
        * etc.
    """
    RESERVED_ORDERING_WORDS = {'order_by', 'ordering'}
    POSSIBLE_DF_LOOKUPS = {
        'in', 'isnull', 'exact',
        'contains', 'icontains', 'startswith', 'endswith', 'istartswith', 'iendswith',
        'gt', 'gte', 'lt', 'lte',
        'regex', 'iregex',
    }

    @classmethod
    def is_old_syntax(cls, filter_instance, request, query_string):
        if not query_string.strip():
            return False

        query_params = request.query_params
        for v in query_params.values():
            if not v or (' ' in v and (not (v.count('"') > 1 or v.count("'") > 1))):
                return True

            if len(v) > 2 and v[2] == '=' and v[:2] in {CO.EQ, CO.NE, CO.LE, CO.GE, CO.LT, CO.GT}:
                return False

        return cls._has_old_syntax_keys(filter_instance, query_params)

    @classmethod
    def _has_old_syntax_keys(cls, filter_instance, query_params):
        qp_all_filters = set()
        qp_old_filters = set()
        for filter_name in query_params.keys():
            qp_all_filters.add(filter_name)
            if cls._is_old_style_filter(filter_name):
                qp_old_filters.add(filter_name)

        if not qp_all_filters.isdisjoint(cls.RESERVED_ORDERING_WORDS):
            return True

        if not qp_old_filters:
            return False

        if not qp_old_filters - cls._get_filters_similar_to_old_syntax(filter_instance):
            return False

        return True

    @classmethod
    def get_rql_query(cls, filter_instance, request, query_string):
        filter_value_str_pairs = []

        for filter_name, value in request.query_params.items():
            if not cls._is_old_style_filter(filter_name):
                filter_value_str_pairs.append(
                    '{}={}'.format(filter_name, cls._add_quotes_to_value(value)),
                )

            else:
                filter_value_str_pairs.append(cls._convert_filter_to_rql(filter_name, value))

        return '&'.join(filter_value_str_pairs)

    @classmethod
    def _convert_filter_to_rql(cls, filter_name, value):
        filter_base, lookup = cls._get_filter_and_lookup(filter_name)

        if lookup in ('regex', 'iregex'):
            cls._conversion_error()

        if lookup == 'in':
            return 'in({},({}))'.format(
                filter_base, ','.join(cls._add_quotes_to_value(v) for v in value.split(',')),
            )

        if lookup == 'isnull':
            operator = CO.EQ if cls._convert_bool_value(value) else CO.NE
            return '{}={}={}'.format(filter_base, operator, RQL_NULL)

        if lookup == 'exact':
            return '{}={}'.format(filter_base, cls._add_quotes_to_value(value))

        if lookup in ('gt', 'gte', 'lt', 'lte'):
            if lookup == 'gte':
                operator = CO.GE
            elif lookup == 'lte':
                operator = CO.LE
            else:
                operator = lookup
            return '{}={}={}'.format(filter_base, operator, value)

        if lookup in (
                'contains', 'icontains', 'startswith', 'endswith', 'istartswith', 'iendswith',
        ):
            operator = SO.I_LIKE if lookup[0] == 'i' else SO.LIKE

            if lookup in ('contains', 'icontains', 'endswith', 'iendswith') and \
                    value[0] != RQL_ANY_SYMBOL:
                value = RQL_ANY_SYMBOL + value

            if lookup in ('contains', 'icontains', 'startswith', 'istartswith') and \
                    value[-1] != RQL_ANY_SYMBOL:
                value += RQL_ANY_SYMBOL

            return '{}({},{})'.format(operator, filter_base, cls._add_quotes_to_value(value))

    @classmethod
    def _convert_bool_value(cls, value):
        if value in ('True', 'true', '1'):
            return True
        elif value in ('False', 'false', '0'):
            return False

        cls._conversion_error()

    @classmethod
    def _add_quotes_to_value(cls, value):
        for quote in ('"', "'"):
            if quote not in value:
                return '"{}"'.format(value)

        cls._conversion_error()

    @staticmethod
    def _conversion_error():
        raise RQLFilterParsingError(details={'error': 'Bad filter query.'})

    @classmethod
    def _get_filters_similar_to_old_syntax(cls, filter_instance):
        old_syntax_filters = getattr(filter_instance, 'old_syntax_filters', None)
        if old_syntax_filters:
            return old_syntax_filters

        similar_to_old_syntax_filters = set()
        for filter_name in filter_instance.filters.keys():
            if cls._is_old_style_filter(filter_name):
                similar_to_old_syntax_filters.add(filter_name)

        setattr(filter_instance, 'old_syntax_filters', similar_to_old_syntax_filters)
        return similar_to_old_syntax_filters

    @classmethod
    def _is_old_style_filter(cls, filter_name):
        return cls._get_filter_and_lookup(filter_name)[-1] in cls.POSSIBLE_DF_LOOKUPS

    @classmethod
    def _get_filter_and_lookup(cls, filter_name):
        return filter_name.rsplit('__', 1)


class RQLLimitOffsetPagination(LimitOffsetPagination):
    """ RQL limit offset pagination. """
    def __init__(self, *args, **kwargs):
        super(RQLLimitOffsetPagination, self).__init__(*args, **kwargs)

        self._rql_limit = None
        self._rql_offset = None

    def paginate_queryset(self, queryset, request, view=None):
        try:
            rql_ast = getattr(request, 'rql_ast')
        except AttributeError:
            rql_ast = RQLParser.parse_query(_get_query(request))

        if rql_ast is not None:
            try:
                self._rql_limit, self._rql_offset = RQLLimitOffsetTransformer().transform(rql_ast)
            except LarkError:
                raise RQLFilterParsingError(details={
                    'error': 'Limit and offset are set incorrectly.',
                })
        return super(RQLLimitOffsetPagination, self).paginate_queryset(queryset, request, view)

    def get_limit(self, *args):
        if self._rql_limit is not None:
            try:
                return _positive_int(self._rql_limit, strict=True, cutoff=self.max_limit)
            except ValueError:
                pass
        return self.default_limit

    def get_offset(self, *args):
        if self._rql_offset is not None:
            try:
                return _positive_int(self._rql_offset)
            except ValueError:
                pass
        return 0


class RQLContentRangeLimitOffsetPagination(RQLLimitOffsetPagination):
    """ RQL RFC2616 limit offset pagination.

    Examples:
        Response

        200 OK
        Content-Range: items <FIRST>-<LAST>/<TOTAL>
    """

    def get_paginated_response(self, data):
        length = len(data) - 1 if data else 0
        content_range = "items {}-{}/{}".format(
            self.offset, self.offset + length, self.count,
        )
        return Response(data, headers={"Content-Range": content_range})


def _get_query(drf_request):
    return urlunquote(drf_request._request.META['QUERY_STRING'])
