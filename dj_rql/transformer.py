#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from lark import Tree
from py_rql.constants import (
    RQL_LIMIT_PARAM,
    RQL_OFFSET_PARAM,
    ComparisonOperators,
    ListOperators,
    LogicalOperators,
)
from py_rql.transformer import BaseRQLTransformer

from dj_rql._dataclasses import FilterArgs


class RQLToDjangoORMTransformer(BaseRQLTransformer):
    """ Parsed RQL AST tree transformer to Django ORM Query.

    Notes:
        Grammar-Function name mapping is made automatically by Lark.

        Transform collects ordering filters, but doesn't apply them.
        They are applied later in FilterCls. This is done on purpose, because transformer knows
        nothing about the mappings between filter names and orm fields.
    """
    NAMESPACE_PROVIDERS = ('comp', 'listing')
    NAMESPACE_FILLERS = ('prop',)
    NAMESPACE_ACTIVATORS = ('tuple',)

    def __init__(self, filter_cls_instance):
        self._filter_cls_instance = filter_cls_instance

        self._ordering = []
        self._select = []
        self._filtered_props = set()

        self._namespace = []
        self._active_namespace = 0

        self.__visit_tokens__ = False

    @property
    def _q(self):
        return self._filter_cls_instance.Q_CLS

    def _push_namespace(self, tree):
        if tree.data in self.NAMESPACE_PROVIDERS:
            self._namespace.append(None)
        elif tree.data in self.NAMESPACE_ACTIVATORS:
            self._active_namespace = len(self._namespace)
        elif (tree.data in self.NAMESPACE_FILLERS
                and self._namespace
                and self._namespace[-1] is None):
            self._namespace[-1] = self._get_value(tree)

    def _pop_namespace(self, tree):
        if tree.data in self.NAMESPACE_PROVIDERS:
            self._namespace.pop()
        elif tree.data in self.NAMESPACE_ACTIVATORS:
            self._active_namespace -= 1

    def _get_current_namespace(self):
        return self._namespace[:self._active_namespace]

    def _transform_tree(self, tree):
        self._push_namespace(tree)
        ret_value = super()._transform_tree(tree)
        self._pop_namespace(tree)
        return ret_value

    def _get_value(self, obj):
        while isinstance(obj, Tree):
            obj = obj.children[0]

        if isinstance(obj, self._q):
            return obj

        return obj.value

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

        if isinstance(value, self._q):
            if operation == ComparisonOperators.EQ:
                return value
            else:
                return ~value

        filter_args = FilterArgs(prop, operation, value, namespace=self._get_current_namespace())
        self._filtered_props.add(filter_args.filter_name)
        return self._filter_cls_instance.build_q_for_filter(filter_args)

    def tuple(self, args):
        return self._q(*args)

    def logical(self, args):
        operation = args[0].data
        children = args[0].children
        if operation == LogicalOperators.get_grammar_key(LogicalOperators.NOT):
            return ~children[0]

        q = self._q()
        if operation == LogicalOperators.get_grammar_key(LogicalOperators.AND):
            for child in children:
                q &= child

            return q

        for child in children:
            q |= child

        return q

    def listing(self, args):
        # Django __in lookup is not used, because of null() values
        operation, prop = self._get_value(args[0]), self._get_value(args[1])
        f_op = ComparisonOperators.EQ if operation == ListOperators.IN else ComparisonOperators.NE

        q = self._q()
        for value_tree in args[2:]:
            value = self._get_value(value_tree)
            if isinstance(value, self._q):
                if f_op == ComparisonOperators.EQ:
                    field_q = value
                else:
                    field_q = ~value
            else:
                field_q = self._filter_cls_instance.build_q_for_filter(FilterArgs(
                    prop, f_op, value,
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
        filter_args = FilterArgs(prop, operation, val, namespace=self._get_current_namespace())
        self._filtered_props.add(filter_args.filter_name)
        return self._filter_cls_instance.build_q_for_filter(filter_args)

    def ordering(self, args):
        props = args[1:]
        self._ordering.append(tuple(props))

        if props:
            for prop in props:
                self._filtered_props.add(prop.replace('-', '').replace('+', ''))

        return self._q()

    def select(self, args):
        assert not self._select

        props = args[1:]
        self._select = props

        if props:
            for prop in props:
                if not prop.startswith('-'):
                    self._filtered_props.add(prop.replace('+', ''))

        return self._q()


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
