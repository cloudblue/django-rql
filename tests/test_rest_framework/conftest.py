from __future__ import unicode_literals

import pytest
from rest_framework.test import APIClient

from dj_rql.drf import FilterCache


@pytest.fixture
def api_client():
    client = APIClient()
    client.default_format = 'json'
    return client


@pytest.fixture
def clear_cache():
    FilterCache.clear()
