#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from lark.exceptions import LarkError
from py_rql.exceptions import RQLFilterParsingError
from py_rql.parser import RQLParser
from rest_framework.pagination import LimitOffsetPagination, _positive_int
from rest_framework.response import Response

from dj_rql.drf._utils import get_query
from dj_rql.transformer import RQLLimitOffsetTransformer


class RQLLimitOffsetPagination(LimitOffsetPagination):
    """ RQL limit offset pagination. """
    def __init__(self, *args, **kwargs):
        super(RQLLimitOffsetPagination, self).__init__(*args, **kwargs)

        self._rql_limit = None
        self._rql_offset = None

    def get_paginated_response_schema(self, schema):
        return schema

    def paginate_queryset(self, queryset, request, view=None):
        rql_ast = None
        try:
            rql_ast = request.rql_ast
        except AttributeError:
            query = get_query(request)
            if query:
                rql_ast = RQLParser.parse_query(query)

        if rql_ast is not None:
            try:
                self._rql_limit, self._rql_offset = RQLLimitOffsetTransformer().transform(rql_ast)
            except LarkError:
                raise RQLFilterParsingError(details={
                    'error': 'Limit and offset are set incorrectly.',
                })

        self.limit = self.get_limit(request)
        if self.limit == 0:
            self.count = self.get_count(queryset)
            self.offset = 0
            return []

        elif self.limit is None:
            return None

        self.count = self.get_count(queryset)
        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []

        if self.limit + self.offset > self.count:
            self.limit = self.count - self.offset

        return list(queryset[self.offset:self.offset + self.limit])

    def get_limit(self, *args):
        if self._rql_limit is not None:
            try:
                return _positive_int(self._rql_limit, strict=False, cutoff=self.max_limit)
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
        content_range = 'items {0}-{1}/{2}'.format(
            self.offset, self.offset + length, self.count,
        )
        return Response(data, headers={'Content-Range': content_range})
