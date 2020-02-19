# TODO: Describe limitations, work on potential errors, related to Prefetch objects,
#  wrong order in qs


class DBOptimization:
    def __init__(self, *relations, parent=None):
        self._relations = relations
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def main_relation(self):
        return self._relations[0]

    @property
    def relations(self):
        return self._relations

    def apply(self, queryset):
        raise NotImplementedError


class SelectRelatedOptimization(DBOptimization):
    def apply(self, queryset):
        return queryset.select_related(*self._relations)


class PrefetchRelatedOptimization(DBOptimization):
    def apply(self, queryset):
        return queryset.prefetch_related(*self._relations)


class _NestedOptimizationMixin:
    SR = 0
    PR = 1

    @property
    def parents_relation_data(self):
        parents_relation, relation_type = '', self.SR
        prev = self.parent
        while prev:
            if isinstance(prev, PrefetchRelatedOptimization):
                relation_type = self.PR

            # TODO: We don't support Prefetch objects in Parents Path
            prev_relation = prev.main_relation
            parents_relation = '{}__{}'.format(prev_relation, parents_relation)
            prev = prev.parent

        return {
            'relation': parents_relation,
            'type': relation_type,
        }


class NestedPrefetchRelatedOptimization(_NestedOptimizationMixin, PrefetchRelatedOptimization):
    def apply(self, queryset):
        if self.parent is None:
            return super(NestedPrefetchRelatedOptimization, self).apply(queryset)

        parents_relation = self.parents_relation_data['relation']
        for relation in self._relations:
            # TODO: Check if relation is a Prefetch object
            queryset = queryset.prefetch_related('{}{}'.format(parents_relation, relation))
        return queryset


class NestedSelectRelatedOptimization(_NestedOptimizationMixin, SelectRelatedOptimization):
    def apply(self, queryset):
        if self.parent is None:
            return super(NestedSelectRelatedOptimization, self).apply(queryset)

        parents_relation_data = self.parents_relation_data
        parents_relation = parents_relation_data['relation']
        optimization_cls = SelectRelatedOptimization \
            if parents_relation_data['type'] == self.SR \
            else PrefetchRelatedOptimization

        for relation in self._relations:
            queryset = optimization_cls('{}{}'.format(parents_relation, relation)).apply(queryset)

        return queryset


class ChainOptimization(DBOptimization):
    def apply(self, queryset):
        for opt in self._relations:
            queryset = opt.apply(queryset, parent=self.parent)
        return queryset


SR = SelectRelatedOptimization
PR = PrefetchRelatedOptimization
CH = ChainOptimization
