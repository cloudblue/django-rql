from __future__ import unicode_literals

from dj_rql.filter_cls import FilterClass


class RQLFilterClass(FilterClass):
    @classmethod
    def filter_queryset(cls, queryset, query):
        # TODO: Filtering
        return queryset
