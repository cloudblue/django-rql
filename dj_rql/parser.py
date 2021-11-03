#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from dj_rql.exceptions import RQLFilterParsingError
from dj_rql.grammar import RQL_GRAMMAR

from lark import Lark
from lark.exceptions import LarkError


class RQLLarkParser(Lark):
    def parse_query(self, query):
        try:
            rql_ast = RQLParser.parse(query)
            return rql_ast
        except LarkError:
            raise RQLFilterParsingError()


RQLParser = RQLLarkParser(RQL_GRAMMAR, parser='lalr', start='start')
