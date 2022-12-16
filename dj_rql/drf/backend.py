#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#
from threading import Lock

from rest_framework.filters import BaseFilterBackend

from dj_rql.drf._utils import get_query


lock = Lock()


class _FilterClassCache:
    CACHE = {}

    @classmethod
    def clear(cls):
        cls.CACHE = {}


class RQLFilterBackend(BaseFilterBackend):
    """ RQL filter backend for DRF GenericAPIViews.

    Set the backend filter for the ``GenericAPIView`` class-based view, and set the
    ``rql_filter_class`` class attribute to the ``RQLFilterClass`` to use:

    .. code-block:: python

        class ViewSet(mixins.ListModelMixin, GenericViewSet):
            filter_backends = (RQLFilterBackend,)
            rql_filter_class = ModelFilterClass

    Yo can also add a ``get_rql_filter_class()`` method to the view to get the filter class:

    .. code-block:: python

        class ViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
            filter_backends = (RQLFilterBackend,)

            def get_rql_filter_class(self):
                if self.action == 'retrieve':
                    return ModelDetailFilterClass
                return ModelFilterClass
    """
    OPENAPI_RETRIEVE_SPECIFICATION = False

    _CACHES = {}

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view)
        if not filter_class:
            return queryset

        filter_instance = self._get_filter_instance(filter_class, queryset, view)
        query = self.get_query(filter_instance, request, view)

        can_query_be_cached = all((
            filter_class.QUERIES_CACHE_BACKEND,
            filter_class.QUERIES_CACHE_SIZE,
            request.method in ('GET', 'HEAD', 'OPTIONS'),
        ))
        if can_query_be_cached:
            # We must use the combination of queryset and query to make a cache key as
            #  queryset can already contain some filters (e.x. based on authentication)
            cache_key = str(queryset.query) + query

            query_cache = self._get_or_init_cache(filter_class, view)
            try:
                filters_result = query_cache[cache_key]
            except KeyError:
                filters_result = filter_instance.apply_filters(query, request, view)
                with lock:
                    query_cache[cache_key] = filters_result

        else:
            filters_result = filter_instance.apply_filters(query, request, view)

        rql_ast, queryset = filters_result

        request.rql_ast = rql_ast
        if queryset.select_data:
            request.rql_select = queryset.select_data

        return queryset.all()

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
        if hasattr(view, 'get_rql_filter_class') and callable(view.get_rql_filter_class):
            return view.get_rql_filter_class()
        return getattr(view, 'rql_filter_class', None)

    @classmethod
    def get_query(cls, filter_instance, request, view):
        return get_query(request)

    @classmethod
    def _get_or_init_cache(cls, filter_class, view):
        qual_name = cls._get_filter_cls_qual_name(view, filter_class)
        return cls._CACHES.setdefault(
            qual_name, filter_class.QUERIES_CACHE_BACKEND(int(filter_class.QUERIES_CACHE_SIZE)),
        )

    @classmethod
    def _get_filter_instance(cls, filter_class, queryset, view):
        qual_name = cls._get_filter_cls_qual_name(view, filter_class)

        filter_instance = _FilterClassCache.CACHE.get(qual_name)
        if filter_instance:
            return filter_class(queryset=queryset, instance=filter_instance)

        filter_instance = filter_class(queryset)
        _FilterClassCache.CACHE[qual_name] = filter_instance
        return filter_instance

    @staticmethod
    def _get_filter_cls_qual_name(view, filter_class):
        return '{0}.{1}+{2}.{3}'.format(
            view.__class__.__module__, view.__class__.__name__,
            filter_class.__module__, filter_class.__name__,
        )
