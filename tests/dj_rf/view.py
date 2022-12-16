#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from django.db.models import CharField, IntegerField, Value
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from dj_rql.drf.backend import RQLFilterBackend
from dj_rql.drf.compat import DjangoFiltersRQLFilterBackend
from dj_rql.drf.paginations import RQLContentRangeLimitOffsetPagination
from dj_rql.filter_cls import AutoRQLFilterClass
from tests.dj_rf.filters import (
    BooksFilterClass,
    SelectBooksFilterClass,
    SelectDetailedBooksFilterClass,
)
from tests.dj_rf.models import Book
from tests.dj_rf.serializers import BookSerializer, SelectBookSerializer


def apply_annotations(qs):
    return qs.annotate(
        anno_int=Value(1000, IntegerField()),
        anno_str=Value('text', CharField(max_length=10)),
    )


class BaseViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = apply_annotations(
        Book.objects.select_related('author').prefetch_related('pages').all(),
    )
    serializer_class = BookSerializer
    rql_filter_class = BooksFilterClass
    pagination_class = RQLContentRangeLimitOffsetPagination


class DRFViewSet(BaseViewSet):
    filter_backends = (RQLFilterBackend,)

    @action(detail=True)
    def act(self, *args):
        return Response()


class OpenAPIRetrieveSpecBackend(DjangoFiltersRQLFilterBackend):
    OPENAPI_RETRIEVE_SPECIFICATION = True


class DjangoFiltersViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, BaseViewSet):
    filter_backends = (OpenAPIRetrieveSpecBackend,)


class SelectViewSet(mixins.RetrieveModelMixin, DRFViewSet):
    serializer_class = SelectBookSerializer
    rql_filter_class = SelectBooksFilterClass


class DynamicFilterClsViewSet(mixins.RetrieveModelMixin, DRFViewSet):
    serializer_class = SelectBookSerializer

    def get_rql_filter_class(self):
        if self.action == 'retrieve':
            return SelectDetailedBooksFilterClass
        return SelectBooksFilterClass


class NoFilterClsViewSet(DRFViewSet):
    rql_filter_class = None


class AutoViewSet(DRFViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @property
    def rql_filter_class(self):
        class Cls(AutoRQLFilterClass):
            MODEL = Book
            QUERIES_CACHE_BACKEND = None

        return Cls
