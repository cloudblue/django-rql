from __future__ import unicode_literals

from django.db.models import CharField, F, IntegerField, Value
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from dj_rql.drf import (
    RQLContentRangeLimitOffsetPagination,
    RQLFilterBackend,
)
from dj_rql.compat import DjangoFiltersRQLFilterBackend
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book
from tests.dj_rf.serializers import SelectBookSerializer, BookSerializer


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


class DjangoFiltersViewSet(BaseViewSet):
    filter_backends = (DjangoFiltersRQLFilterBackend,)


class SelectViewSet(mixins.RetrieveModelMixin, DRFViewSet):
    serializer_class = SelectBookSerializer
