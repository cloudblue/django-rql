# TODO: Great Readme
from django.db.models import Prefetch


class DBOptimization:
    def __init__(self, *relations, parent=None, **kwargs):
        assert relations, 'At least one optimization must be specified.'

        self._relations = relations
        self._parent = parent
        self._extensions = kwargs

    @property
    def parent(self):
        return self._parent

    @property
    def main_relation(self):
        return self._relations[0]

    @property
    def extensions(self):
        return self._extensions

    @property
    def relations(self):
        return self._relations

    def apply(self, queryset):
        raise NotImplementedError


class SimpleOptimization(DBOptimization):
    @property
    def parent(self):
        return None


class Annotation(SimpleOptimization):
    def __init__(self, parent=None, **kwargs):
        super(Annotation, self).__init__('None', parent=parent, **kwargs)

    def apply(self, queryset):
        return queryset.annotate(**self._extensions)


class SelectRelated(SimpleOptimization):
    def apply(self, queryset):
        return queryset.select_related(*self._relations)


class PrefetchRelated(SimpleOptimization):
    def apply(self, queryset):
        return queryset.prefetch_related(*self._relations)


class _NestedOptimization(DBOptimization):
    SR = 0
    PR = 1

    def __init__(self, *relations, parent=None, **kwargs):
        if parent and isinstance(parent, Annotation):
            parent = None

        self._parents_relation_data = self._get_parents_relation_data(parent)
        super(_NestedOptimization, self).__init__(*relations, parent=parent, **kwargs)

    @property
    def parents_relation_data(self):
        return self._parents_relation_data

    @classmethod
    def _get_parents_relation_data(cls, parent):
        parents_relation, relation_type = '', cls.SR
        prev = parent
        while prev:
            if isinstance(prev, Chain):
                prev = prev.main_relation
                continue

            if isinstance(prev, PrefetchRelated):
                relation_type = cls.PR

            prev_relation = prev.main_relation
            assert isinstance(prev_relation, str), 'Only simple parent relations are supported.'

            parents_relation = '{}__{}'.format(prev_relation, parents_relation)
            prev = prev.parent

        return {
            'relation': parents_relation,
            'type': relation_type,
        }


class NestedPrefetchRelated(_NestedOptimization):
    def apply(self, queryset):
        if self.parent is None:
            return PrefetchRelated(*self._relations, **self._extensions).apply(queryset)

        parents_relation = self.parents_relation_data['relation']
        for relation in self._relations:
            if isinstance(relation, Prefetch):
                relation.prefetch_through = parents_relation + relation.prefetch_through
                relation.prefetch_to = parents_relation + relation.prefetch_to
                pr = relation
            else:
                pr = parents_relation + relation

            queryset = queryset.prefetch_related(pr)
        return queryset


class NestedSelectRelated(_NestedOptimization):
    def apply(self, queryset):
        if self.parent is None:
            return SelectRelated(*self._relations, **self._extensions).apply(queryset)

        parents_relation_data = self.parents_relation_data
        parents_relation = parents_relation_data['relation']
        optimization_cls = SelectRelated \
            if parents_relation_data['type'] == self.SR \
            else PrefetchRelated

        for relation in self._relations:
            queryset = optimization_cls('{}{}'.format(parents_relation, relation)).apply(queryset)

        return queryset


class Chain(DBOptimization):
    def __init__(self, *relations, parent=None, **kwargs):
        assert all(isinstance(rel, DBOptimization) for rel in relations), \
            'Wrong Chain() optimization configuration.'

        super(Chain, self).__init__(*relations, parent=parent, **kwargs)

    def apply(self, queryset):
        if self.parent:
            for opt in self._relations:
                full_opt = opt.__class__(*opt.relations, parent=self.parent, **opt.extensions)
                queryset = full_opt.apply(queryset)

        else:
            for opt in self._relations:
                queryset = opt.apply(queryset)

        return queryset


AN = Annotation
SR = SelectRelated
NSR = NestedSelectRelated
PR = PrefetchRelated
NPR = NestedPrefetchRelated
CH = Chain
