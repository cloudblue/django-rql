#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

import pytest
from rest_framework.test import APIClient

from dj_rql.drf.backend import FilterCache


@pytest.fixture
def api_client():
    client = APIClient()
    client.default_format = 'json'
    return client


@pytest.fixture
def clear_cache():
    FilterCache.clear()
