#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from django.db.models import Q
from lark import Transformer, Tree

from dj_rql._dataclasses import FilterArgs
from dj_rql.constants import (
    ComparisonOperators,
    ListOperators,
    LogicalOperators,
    RQL_PLUS,
    RQL_LIMIT_PARAM,
    RQL_OFFSET_PARAM,
)


class BaseRQLTransformer(Transformer):
    @classmethod
    def _extract_comparison(cls, args):
        if len(args) == 2:
            # id=1
            operation = ComparisonOperators.EQ
            prop_index = 0
            value_index = 1
        elif args[0].data == 'comp_term':
            # eq(id,1)
            operation = cls._get_value(args[0])
            prop_index = 1
            value_index = 2
        else:
            # id=eq=1
            operation = cls._get_value(args[1])
            prop_index = 0
            value_index = 2

        return cls._get_value(args[prop_index]), operation, cls._get_value(args[value_index])

    @staticmethod
    def _get_value(obj):
        while isinstance(obj, Tree):
            obj = obj.children[0]
        return obj.value

    def sign_prop(self, args):
        if len(args) == 2:
            # has sign
            return '{}{}'.format(self._get_value(args[0]), self._get_value(args[1])) \
                .lstrip(RQL_PLUS)  # Plus is not needed in ordering
        return self._get_value(args[0])

    def term(self, args):
        return args[0]

    def expr_term(self, args):
        return args[0]

    def start(self, args):
        return args[0]


class RQLToDjangoORMTransformer(BaseRQLTransformer):
    """ Parsed RQL AST tree transformer to Django ORM Query.

    Notes:
        Grammar-Function name mapping is made automatically by Lark.

        Transform collects ordering filters, but doesn't apply them.
        They are applied later in FilterCls. This is done on purpose, because transformer knows
        nothing about the mappings between filter names and orm fields.
    """
    def __init__(self, filter_cls_instance):
        self._filter_cls_instance = filter_cls_instance

        self._ordering = []
        self._select = []
        self._filtered_props = set()

    @property
    def ordering_filters(self):
        return self._ordering

    @property
    def select_filters(self):
        return self._select

    def start(self, args):
        qs = self._filter_cls_instance.apply_annotations(self._filtered_props)

        return qs.filter(args[0])

    def comp(self, args):
        prop, operation, value = self._extract_comparison(args)
        self._filtered_props.add(prop)

        return self._filter_cls_instance.build_q_for_filter(FilterArgs(prop, operation, value))

    def logical(self, args):
        operation = args[0].data
        children = args[0].children
        if operation == LogicalOperators.get_grammar_key(LogicalOperators.NOT):
            return ~Q(children[0])
        if operation == LogicalOperators.get_grammar_key(LogicalOperators.AND):
            return Q(*children)

        q = Q()
        for child in children:
            q |= child

        return q

    def listing(self, args):
        # Django __in lookup is not used, because of null() values
        operation, prop = self._get_value(args[0]), self._get_value(args[1])
        f_op = ComparisonOperators.EQ if operation == ListOperators.IN else ComparisonOperators.NE

        q = Q()
        for value_tree in args[2:]:
            field_q = self._filter_cls_instance.build_q_for_filter(FilterArgs(
                prop, f_op, self._get_value(value_tree),
                list_operator=operation,
            ))
            if operation == ListOperators.IN:
                q |= field_q
            else:
                q &= field_q

        self._filtered_props.add(prop)

        return q

    def searching(self, args):
        # like, ilike
        operation, prop, val = tuple(self._get_value(args[index]) for index in range(3))
        self._filtered_props.add(prop)

        return self._filter_cls_instance.build_q_for_filter(FilterArgs(prop, operation, val))

    def ordering(self, args):
        props = args[1:]
        self._ordering.append(tuple(props))

        if props:
            for prop in props:
                self._filtered_props.add(prop.replace('-', '').replace('+', ''))

        return Q()

    def select(self, args):
        assert not self._select

        props = args[1:]
        self._select = props

        if props:
            for prop in props:
                if not prop.startswith('-'):
                    self._filtered_props.add(prop.replace('+', ''))

        return Q()


class RQLLimitOffsetTransformer(BaseRQLTransformer):
    """ Parsed RQL AST tree transformer to (limit, offset) tuple for limit offset pagination. """
    def __init__(self):
        self.limit = None
        self.offset = None

    def start(self, args):
        return self.limit, self.offset

    def comp(self, args):
        prop, operation, val = self._extract_comparison(args)
        if prop in (RQL_LIMIT_PARAM, RQL_OFFSET_PARAM):
            # Only equation operator can be used for limit and offset
            assert operation == ComparisonOperators.EQ

            # There can be only one limit (offset) parameter in the whole query
            if prop == RQL_LIMIT_PARAM:
                assert self.limit is None
                self.limit = val
            else:
                assert self.offset is None
                self.offset = val
