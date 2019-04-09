from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from rest_framework.routers import SimpleRouter

from tests.dj_rf.view import DRFViewSet


router = SimpleRouter()
router.register(r'books', DRFViewSet, basename='books')

urlpatterns = [
    url(r'^', include(router.urls)),
]
