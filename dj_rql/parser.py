# coding=utf-8
from __future__ import unicode_literals

from lark import Lark
from lark.exceptions import LarkError

from dj_rql.exceptions import RQLFilterParsingError
from dj_rql.grammar import RQL_GRAMMAR


class RQLLarkParser(Lark):
    def parse_query(self, query):
        try:
            rql_ast = RQLParser.parse(query)
            return rql_ast
        except LarkError as e:
            raise RQLFilterParsingError(details={
                'error': 'Bad filter query.',
                'original_error': str(e),
            })


RQLParser = RQLLarkParser(RQL_GRAMMAR, parser='lalr', start='start')
