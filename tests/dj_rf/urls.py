#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from django.conf.urls import include
from django.urls import re_path
from rest_framework.routers import SimpleRouter

from tests.dj_rf.view import (
    AutoViewSet,
    DjangoFiltersViewSet,
    DRFViewSet,
    DynamicFilterClsViewSet,
    NoFilterClsViewSet,
    SelectViewSet,
)


router = SimpleRouter()
router.register(r'books', DRFViewSet, basename='book')
router.register(r'old_books', DjangoFiltersViewSet, basename='old_book')
router.register(r'select', SelectViewSet, basename='select')
router.register(r'nofiltercls', NoFilterClsViewSet, basename='nofiltercls')
router.register(r'auto', AutoViewSet, basename='auto')
router.register(r'dynamicfiltercls', DynamicFilterClsViewSet, basename='dynamicfiltercls')

urlpatterns = [
    re_path(r'^', include(router.urls)),
]
