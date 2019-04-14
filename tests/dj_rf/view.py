from __future__ import unicode_literals

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from dj_rql.backend import RQLFilterBackend
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book


class DRFViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Book.objects.select_related('author').prefetch_related('pages').all()
    filter_backends = (RQLFilterBackend,)
    rql_filter_class = BooksFilterClass
