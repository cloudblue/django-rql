from __future__ import unicode_literals


from __future__ import unicode_literals

from django.db.models import Q
from lark import Transformer, Tree

from dj_rql.constants import ComparisonOperators, LogicalOperators


class RQLtoDjangoORMTransformer(Transformer):
    def __init__(self, filter_cls_instance):
        self._filter_cls_instance = filter_cls_instance

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
        elif args[0].data == 'comp_term':
            operation = self._cmp_value(args[0])
        else:
            operation = self._cmp_value(args[1])
            prop_index = 0

        return self._filter_cls_instance.get_django_q_for_filter_expression(
            self._cmp_value(args[prop_index]), operation, self._cmp_value(args[value_index])
        )

    def term(self, args):
        return args[0]

    def expr_term(self, args):
        return args[0]

    def start(self, args):
        return self._filter_cls_instance.queryset.filter(args[0]).distinct()

    def logical(self, args):
        operation = args[0].data
        if operation == LogicalOperators.get_grammar_key(LogicalOperators.NOT):
            return ~Q(args[0].children[0])
        if operation == LogicalOperators.get_grammar_key(LogicalOperators.AND):
            return Q(*args[0].children)

        q = Q()
        for child in args[0].children:
            q |= child
        return q
