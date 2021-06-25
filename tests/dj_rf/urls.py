#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from django.conf.urls import include, re_path

from rest_framework.routers import SimpleRouter

from tests.dj_rf.view import (
    AutoViewSet, DRFViewSet, DjangoFiltersViewSet, NoFilterClsViewSet, SelectViewSet,
)


router = SimpleRouter()
router.register(r'books', DRFViewSet, basename='book')
router.register(r'old_books', DjangoFiltersViewSet, basename='old_book')
router.register(r'select', SelectViewSet, basename='select')
router.register(r'nofiltercls', NoFilterClsViewSet, basename='nofiltercls')
router.register(r'auto', AutoViewSet, basename='auto')

urlpatterns = [
    re_path(r'^', include(router.urls)),
]
