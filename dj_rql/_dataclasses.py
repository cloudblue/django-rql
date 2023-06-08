#
#  Copyright © 2023 Ingram Micro Inc. All rights reserved.
#


class OptimizationArgs:
    def __init__(self, queryset, select_data, filter_tree, filter_node=None, filter_path=None):
        """
        :param django.db.models.QuerySet queryset: QuerySet for optimization
        :param Dict[str, bool] select_data: Storage of selected/deselected fields (filters)
        :param Dict[str, dict] filter_tree: Detailed tree structure of filter items
        :param dict or None filter_node: Field (filter node) on which optimization is applied
        :param str or None filter_path: Full RQL field path (full filter name)
        """
        self.queryset = queryset
        self.select_data = select_data
        self.filter_tree = filter_tree

        self.filter_node = filter_node
        self.filter_path = filter_path


class FilterArgs:
    def __init__(
        self, filter_name, operator, str_value, list_operator=None, namespace=None, **kwargs
    ):
        """
        :param str filter_name: Full filter name (f.e. ns1.ns2.filter1)
        :param str operator: RQL operator (f.e. eq, like, etc.)
        :param str str_value: Raw value from RQL query
        :param str or None list_operator: This is filled only if operation is done within IN or OUT
        :param list or None namespace: List of namespaces
        :param dict kwargs: Other auxiliary data (f.e. to ease custom filtering)
        """
        self.filter_basename = filter_name
        self.filter_name = '.'.join((namespace or []) + [filter_name])
        self.operator = operator
        self.str_value = str_value
        self.list_operator = list_operator
        self.namespace = namespace

        self.filter_lookup = kwargs.get('filter_lookup')
        self.django_lookup = kwargs.get('django_lookup')
        self.distinct = kwargs.get('distinct')
