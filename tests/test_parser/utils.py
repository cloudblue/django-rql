from __future__ import unicode_literals

from lark import Transformer, Tree

from dj_rql.constants import ComparisonOperators


class BaseTransformer(Transformer):
    def term(self, args):
        return args[0]

    def expr_term(self, args):
        return args[0]

    def start(self, args):
        return args[0]

    @staticmethod
    def _get_value(obj):
        while isinstance(obj, Tree):
            obj = obj.children[0]
        return obj.value


class ComparisonTransformer(BaseTransformer):
    def comp(self, args):
        prop_index = 1
        value_index = 2

        if len(args) == 2:
            operation = ComparisonOperators.EQ
            prop_index = 0
            value_index = 1
        elif args[0].data == 'comp_term':
            operation = self._get_value(args[0])
        else:
            operation = self._get_value(args[1])
            prop_index = 0

        return operation, self._get_value(args[prop_index]), self._get_value(args[value_index])


class LogicalTransformer(ComparisonTransformer):
    def logical(self, args):
        return {args[0].data: args[0].children}


class ListTransformer(BaseTransformer):
    def listing(self, args):
        return (self._get_value(args[0]), self._get_value(args[1]),
                tuple(self._get_value(arg) for arg in args[2:]))
