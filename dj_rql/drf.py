from __future__ import unicode_literals

from django.utils.http import urlunquote
from lark.exceptions import LarkError
from rest_framework.filters import BaseFilterBackend
from rest_framework.pagination import LimitOffsetPagination, _positive_int
from rest_framework.response import Response

from dj_rql.exceptions import RQLFilterParsingError
from dj_rql.filter_cls import RQLFilterClass
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
        return filter_instance.apply_filters(_get_query(request))

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


class RQLLimitOffsetPagination(LimitOffsetPagination):
    """ RQL limit offset pagination. """
    def __init__(self, *args, **kwargs):
        super(RQLLimitOffsetPagination, self).__init__(*args, **kwargs)

        self._rql_limit = None
        self._rql_offset = None

    def paginate_queryset(self, queryset, request, view=None):
        rql_ast = RQLParser.parse_query(_get_query(request))
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
