from __future__ import unicode_literals

from lark import Transformer, Tree


class ComparisonOperators(object):
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    GE = 'ge'
    LT = 'lt'
    LE = 'le'


class LogicalOperators:
    AND = 'and'
    OR = 'or'

    @staticmethod
    def get_grammar_key(key):
        return '{}_op'.format(key)


class ComparisonTransformer(Transformer):
    @classmethod
    def _cmp_value(cls, obj):
        while isinstance(obj, Tree):
            obj = obj.children[0]
        return obj.value

    def comp(self, args):
        prop_index = 1
        value_index = 2

        if len(args) == 2:
            operation = ComparisonOperators.EQ
            prop_index = 0
            value_index = 1
        elif args[0].data == 'comp_op':
            operation = self._cmp_value(args[0])
        else:
            operation = self._cmp_value(args[1])
            prop_index = 0

        return operation, self._cmp_value(args[prop_index]), self._cmp_value(args[value_index])

    def term(self, args):
        return args[0]

    def expr_term(self, args):
        return args[0]

    def start(self, args):
        return args[0]


class LogicalTransformer(ComparisonTransformer):
    def logical(self, args):
        return {args[0].data: args[0].children}
