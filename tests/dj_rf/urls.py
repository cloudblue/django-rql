#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, re_path
from rest_framework.routers import SimpleRouter

from tests.dj_rf.view import DjangoFiltersViewSet, DRFViewSet, SelectViewSet, NoFilterClsViewSet


router = SimpleRouter()
router.register(r'books', DRFViewSet, basename='book')
router.register(r'old_books', DjangoFiltersViewSet, basename='old_book')
router.register(r'select', SelectViewSet, basename='select')
router.register(r'nofiltercls', NoFilterClsViewSet, basename='nofiltercls')

urlpatterns = [
    re_path(r'^', include(router.urls)),
]
