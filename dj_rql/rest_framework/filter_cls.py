from __future__ import unicode_literals


from dj_rql.constants import ComparisonOperators, DjangoLookups
from dj_rql.filter_cls import FilterClass


class RQLFilterClass(FilterClass):
    def apply_filters(self, query):
        # TODO: Filtering
        return self.queryset

    @classmethod
    def _get_filter_lookup_by_operator(cls, operator):
        mapper = {
            ComparisonOperators.EQ: DjangoLookups.EXACT,
            ComparisonOperators.NE: DjangoLookups.EXACT,
            ComparisonOperators.LT: DjangoLookups.LT,
            ComparisonOperators.LE: DjangoLookups.LTE,
            ComparisonOperators.GT: DjangoLookups.GT,
            ComparisonOperators.GE: DjangoLookups.GTE,
        }
        return mapper[operator]
