# coding=utf-8
from __future__ import unicode_literals

from lark import Lark

from dj_rql.grammar import RQL_GRAMMAR


RQLParser = Lark(RQL_GRAMMAR, parser='lalr', start='start', lexer='standard')
