class OptimizationArgs:
    def __init__(self, queryset, select_data, filter_tree, filter_node=None, filter_path=None):
        self.queryset = queryset
        self.select_data = select_data
        self.filter_tree = filter_tree

        self.filter_node = filter_node
        self.filter_path = filter_path
