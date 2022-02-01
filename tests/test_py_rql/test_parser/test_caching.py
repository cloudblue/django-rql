#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from py_rql.exceptions import RQLFilterParsingError
from py_rql.parser import RQLParser

import pytest


def test_cache():
    cache = RQLParser._cache
    cache.clear()

    ast = RQLParser.parse_query('a=b')
    assert RQLParser.parse_query('b=c&x=g')
    assert RQLParser.parse_query('a=b') == ast

    with pytest.raises(RQLFilterParsingError):
        RQLParser.parse_query('&')

    assert cache.maxsize == 1000
    assert cache.currsize == 2
    assert cache.get(hash('a=b')) == ast
    assert cache.get(hash('b=c&x=g'))
