import pytest
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK

from tests.dj_rf.models import Book


@pytest.mark.django_db
def test_quoting(api_client, clear_cache):
    Book.objects.create()
    response = api_client.get(reverse('select-list') + '?select(-id)')
    assert response.status_code == HTTP_200_OK
    assert 'id' not in response.data[0]
