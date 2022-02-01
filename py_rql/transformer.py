from django.db.models import Q

from lark import Transformer, Tree

from py_rql.constants import ComparisonOperators, RQL_PLUS


class BaseRQLTransformer(Transformer):
    @classmethod
    def _extract_comparison(cls, args):
        if len(args) == 2:
            # Notation: id=1  # noqa: E800
            operation = ComparisonOperators.EQ
            prop_index = 0
            value_index = 1
        elif args[0].data == 'comp_term':
            # Notation: eq(id,1)  # noqa: E800
            operation = cls._get_value(args[0])
            prop_index = 1
            value_index = 2
        else:
            # Notation: id=eq=1
            operation = cls._get_value(args[1])
            prop_index = 0
            value_index = 2

        return cls._get_value(args[prop_index]), operation, cls._get_value(args[value_index])

    @staticmethod
    def _get_value(obj):
        while isinstance(obj, Tree):
            obj = obj.children[0]

        if isinstance(obj, Q):
            return obj

        return obj.value

    def sign_prop(self, args):
        if len(args) == 2:
            # has sign
            return '{0}{1}'.format(
                self._get_value(args[0]), self._get_value(args[1]),
            ).lstrip(RQL_PLUS)  # Plus is not needed in ordering
        return self._get_value(args[0])

    def term(self, args):
        return args[0]

    def expr_term(self, args):
        return args[0]

    def start(self, args):
        return args[0]
