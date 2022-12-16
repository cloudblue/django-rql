#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from unittest import TestCase

from py_rql.exceptions import RQLFilterParsingError
from rest_framework.pagination import PAGE_BREAK, PageLink
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from dj_rql.drf import RQLContentRangeLimitOffsetPagination


factory = APIRequestFactory()


class TestRQLLimitOffsetPagination(TestCase):
    """ An adopted copy of DRF pagination test case. """
    def setUp(self):
        class ExamplePagination(RQLContentRangeLimitOffsetPagination):
            default_limit = 10
            max_limit = 15

        self.pagination = ExamplePagination()
        self.queryset = range(1, 101)

    def paginate_queryset(self, request):
        return list(self.pagination.paginate_queryset(self.queryset, request))

    def get_paginated_content(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response.data

    def get_content_range_data(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response['Content-Range']

    def get_html_context(self):
        return self.pagination.get_html_context()

    def test_no_offset(self):
        request = Request(factory.get('/', {'limit': 5}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [1, 2, 3, 4, 5]
        assert content == [1, 2, 3, 4, 5]
        assert context == {
            'previous_url': None,
            'next_url': 'http://testserver/?limit=5&offset=5',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, True, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ],
        }
        assert self.pagination.display_page_controls

        content_range_data = self.get_content_range_data(queryset)
        assert content_range_data == 'items 0-4/100'

    def test_pagination_not_applied_if_limit_or_default_limit_not_set(self):
        class MockPagination(RQLContentRangeLimitOffsetPagination):
            default_limit = None

        request = Request(factory.get('/'))
        queryset = MockPagination().paginate_queryset(self.queryset, request)
        assert queryset is None

    def test_single_offset(self):
        """
        When the offset is not a multiple of the limit we get some edge cases:
        * The first page should still be offset zero.
        * We may end up displaying an extra page in the pagination control.
        """
        request = Request(factory.get('/', {'limit': 5, 'offset': 1}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [2, 3, 4, 5, 6]
        assert content == [2, 3, 4, 5, 6]
        assert context == {
            'previous_url': 'http://testserver/?limit=5',
            'next_url': 'http://testserver/?limit=5&offset=6',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=1', 2, True, False),
                PageLink('http://testserver/?limit=5&offset=6', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=96', 21, False, False),
            ],
        }

        content_range_data = self.get_content_range_data(queryset)
        assert content_range_data == 'items 1-5/100'

    def test_first_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 5}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [6, 7, 8, 9, 10]
        assert content == [6, 7, 8, 9, 10]
        assert context == {
            'previous_url': 'http://testserver/?limit=5',
            'next_url': 'http://testserver/?limit=5&offset=10',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, True, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ],
        }

        content_range_data = self.get_content_range_data(queryset)
        assert content_range_data == 'items 5-9/100'

    def test_middle_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 10}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [11, 12, 13, 14, 15]
        assert content == [11, 12, 13, 14, 15]
        assert context == {
            'previous_url': 'http://testserver/?limit=5&offset=5',
            'next_url': 'http://testserver/?limit=5&offset=15',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, True, False),
                PageLink('http://testserver/?limit=5&offset=15', 4, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ],
        }

        content_range_data = self.get_content_range_data(queryset)
        assert content_range_data == 'items 10-14/100'

    def test_ending_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 95}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [96, 97, 98, 99, 100]
        assert content == [96, 97, 98, 99, 100]
        assert context == {
            'previous_url': 'http://testserver/?limit=5&offset=90',
            'next_url': None,
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=85', 18, False, False),
                PageLink('http://testserver/?limit=5&offset=90', 19, False, False),
                PageLink('http://testserver/?limit=5&offset=95', 20, True, False),
            ],
        }

        content_range_data = self.get_content_range_data(queryset)
        assert content_range_data == 'items 95-99/100'

    def test_erronous_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 1000}))
        queryset = self.paginate_queryset(request)
        self.get_paginated_content(queryset)
        self.get_html_context()

    def test_invalid_offset(self):
        """
        An invalid offset query param should be treated as 0.
        """
        request = Request(factory.get('/', {'limit': 5, 'offset': 'invalid'}))
        queryset = self.paginate_queryset(request)
        assert queryset == [1, 2, 3, 4, 5]

    def test_invalid_limit(self):
        """
        An invalid limit query param should be ignored in favor of the default.
        """
        request = Request(factory.get('/', {'limit': 'invalid', 'offset': 0}))
        queryset = self.paginate_queryset(request)
        assert queryset == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def test_zero_limit(self):
        """
        An zero limit query param should be ignored in favor of the default.
        """
        request = Request(factory.get('/', {'limit': 0, 'offset': 0}))
        queryset = self.paginate_queryset(request)
        assert queryset == []

    def test_max_limit(self):
        """
        The limit defaults to the max_limit when there is a max_limit and the
        requested limit is greater than the max_limit
        """
        offset = 50
        request = Request(factory.get('/', {'limit': '11235', 'offset': offset}))
        queryset = self.paginate_queryset(request)
        assert queryset == list(range(51, 66))

    def test_limit_gt_than_count_wout_offset(self):
        self.pagination.max_limit = 500

        request = Request(factory.get('/', {'limit': 125}))
        queryset = self.paginate_queryset(request)
        assert queryset == list(range(1, 101))

    def test_limit_gt_than_count_with_offset(self):
        request = Request(factory.get('/', {'limit': 125, 'offset': 95}))
        queryset = self.paginate_queryset(request)
        assert queryset == list(range(96, 101))

    def test_rql_operators(self):
        limit, offset = 1, 2
        request = Request(
            factory.get('/?search=0&limit=eq={0},eq(offset,{1})'.format(limit, offset)),
        )
        queryset = self.paginate_queryset(request)
        assert queryset == [3]

    def assert_rql_parsing_error(self, query):
        request = Request(factory.get('/?{0}'.format(query)))
        with self.assertRaises(RQLFilterParsingError) as e:
            self.paginate_queryset(request)
        assert e.exception.details['error'] == 'Limit and offset are set incorrectly.'

    def test_bad_rql_comparison_operator(self):
        self.assert_rql_parsing_error('limit=ge=1')

    def test_several_limit_parameters(self):
        self.assert_rql_parsing_error('limit=1,offset=1,eq(limit,2)')

    def test_several_offset_parameters(self):
        self.assert_rql_parsing_error('limit=1,offset=1,offset=eq=2')
