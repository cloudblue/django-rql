#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from rest_framework.filters import BaseFilterBackend

from dj_rql.drf._utils import get_query


class FilterCache:
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
    OPENAPI_RETRIEVE_SPECIFICATION = False

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view)
        if not filter_class:
            return queryset

        filter_instance = self._get_filter_instance(filter_class, queryset, view)
        rql_ast, queryset = filter_instance.apply_filters(
            self.get_query(filter_instance, request, view), request, view,
        )
        return queryset

    def get_schema_operation_parameters(self, view):
        spec = []
        if view.action not in ('list', 'retrieve'):
            return spec

        if view.action == 'retrieve' and (not self.OPENAPI_RETRIEVE_SPECIFICATION):
            return spec

        filter_class = self.get_filter_class(view)
        if not filter_class:
            return spec

        filter_instance = self._get_filter_instance(filter_class, queryset=None, view=view)
        return filter_instance.openapi_specification

    @staticmethod
    def get_filter_class(view):
        return getattr(view, 'rql_filter_class', None)

    @classmethod
    def get_query(cls, filter_instance, request, view):
        return get_query(request)

    @staticmethod
    def _get_filter_instance(filter_class, queryset, view):
        qual_name = '{}.{}'.format(view.basename, filter_class.__name__)

        filter_instance = FilterCache.CACHE.get(qual_name)
        if filter_instance:
            return filter_class(queryset=queryset, instance=filter_instance)

        filter_instance = filter_class(queryset)
        FilterCache.CACHE[qual_name] = filter_instance
        return filter_instance
