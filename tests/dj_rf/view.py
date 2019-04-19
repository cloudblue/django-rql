from __future__ import unicode_literals

from rest_framework import mixins
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet

from dj_rql.drf import RQLContentRangeLimitOffsetPagination, RQLFilterBackend
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id',)


class DRFViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Book.objects.select_related('author').prefetch_related('pages').all()
    serializer_class = BookSerializer
    filter_backends = (RQLFilterBackend,)
    rql_filter_class = BooksFilterClass
    pagination_class = RQLContentRangeLimitOffsetPagination
