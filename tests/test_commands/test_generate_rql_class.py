#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

import os

import pytest
from django.core.management import call_command

from tests.dj_rf.models import AutoMain, Publisher


@pytest.mark.django_db
def test_default():
    code = call_command('generate_rql_class', 'tests.dj_rf.models.AutoMain')
    with open(os.path.join(os.path.dirname(__file__), '_generated_filters1.py'), 'w') as f:
        f.write(code)

    from tests.test_commands._generated_filters1 import AutoMainFilters
    assert AutoMainFilters.MODEL == AutoMain
    assert AutoMainFilters.FILTERS
    assert AutoMainFilters.SELECT is True
    assert AutoMainFilters.EXCLUDE_FILTERS == []

    _, qs = AutoMainFilters(AutoMain.objects.all()).apply_filters('')
    assert list(qs.all()) == []


@pytest.mark.django_db
def test_overridden_args():
    code = call_command(
        'generate_rql_class',
        'tests.dj_rf.models.Publisher',
        select=False,
        depth=2,
        exclude='authors,fk1.publisher,fk1.author,fk2,invalid',
    )
    with open(os.path.join(os.path.dirname(__file__), '_generated_filters2.py'), 'w') as f:
        f.write(code)

    from tests.test_commands._generated_filters2 import PublisherFilters
    assert PublisherFilters.MODEL == Publisher
    assert PublisherFilters.FILTERS == [
        {
            "filter": "id",
            "ordering": True,
            "search": False,
        },
        {
            "filter": "name",
            "ordering": True,
            "search": True,
        },
        {
            "namespace": "fk1",
            "filters": [
                {
                    "filter": "id",
                    "ordering": True,
                    "search": False,
                },
            ],
            "qs": None,
        },
    ]
    assert PublisherFilters.SELECT is False
    assert PublisherFilters.EXCLUDE_FILTERS == [
        'authors', 'fk1.publisher', 'fk1.author', 'fk2', 'invalid',
    ]
