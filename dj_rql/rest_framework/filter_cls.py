from __future__ import unicode_literals

from dj_rql.filter_cls import FilterClass


class RQLFilterClass(FilterClass):
    def apply_filters(self, query):
        # TODO: Filtering
        return self.queryset
