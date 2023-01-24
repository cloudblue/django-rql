#
#  Copyright © 2023 Ingram Micro Inc. All rights reserved.
#

from urllib.parse import unquote


def get_query(drf_request):
    return unquote(drf_request._request.META['QUERY_STRING'])
