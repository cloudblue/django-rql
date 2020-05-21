#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from dj_rql.transformer import BaseRQLTransformer


class ComparisonTransformer(BaseRQLTransformer):
    def comp(self, args):
        prop, operation, value = self._extract_comparison(args)
        return operation, prop, value


class LogicalTransformer(ComparisonTransformer):
    def logical(self, args):
        return {args[0].data: args[0].children}


class ListTransformer(BaseRQLTransformer):
    def listing(self, args):
        return (self._get_value(args[0]), self._get_value(args[1]),
                tuple(self._get_value(arg) for arg in args[2:]))


class SearchTransformer(BaseRQLTransformer):
    def searching(self, args):
        return tuple(self._get_value(args[index]) for index in range(3))


class OrderingTransformer(BaseRQLTransformer):
    def ordering(self, args):
        return tuple(args[1:])
