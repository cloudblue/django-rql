from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from rest_framework.routers import SimpleRouter

from tests.dj_rf.view import DjangoFiltersViewSet, DRFViewSet


router = SimpleRouter()
router.register(r'books', DRFViewSet, basename='book')
router.register(r'old_books', DjangoFiltersViewSet, basename='old_book')

urlpatterns = [
    url(r'^', include(router.urls)),
]
