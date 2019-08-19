from __future__ import unicode_literals

from rest_framework import mixins
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet

from dj_rql.drf import (
    RQLContentRangeLimitOffsetPagination,
    RQLFilterBackend,
)
from dj_rql.compat import DjangoFiltersRQLFilterBackend
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id',)


class BaseViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Book.objects.select_related('author').prefetch_related('pages').all()
    serializer_class = BookSerializer
    rql_filter_class = BooksFilterClass
    pagination_class = RQLContentRangeLimitOffsetPagination


class DRFViewSet(BaseViewSet):
    filter_backends = (RQLFilterBackend,)


class DjangoFiltersViewSet(BaseViewSet):
    filter_backends = (DjangoFiltersRQLFilterBackend,)
