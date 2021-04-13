#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from collections import namedtuple

from django.db.models import Prefetch


class DBOptimization:
    def __init__(self, *relations, **kwargs):
        assert relations, 'At least one optimization must be specified.'

        self._relations = relations
        self._extensions = kwargs

    def rebuild(self, parent_optimization=None):
        return self.__class__(*self._relations, **self._extensions)

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


class Annotation(DBOptimization):
    def __init__(self, **kwargs):
        super(Annotation, self).__init__('None', **kwargs)

    def rebuild(self, parent_optimization=None):
        return self

    def apply(self, queryset):
        return queryset.annotate(**self._extensions)


class SelectRelated(DBOptimization):
    """Apply a ``select_related`` optimization to the queryset."""
    def apply(self, queryset):
        return queryset.select_related(*self._relations)


class PrefetchRelated(DBOptimization):
    """Apply a ``prefetch_related`` optimization to the queryset."""
    def apply(self, queryset):
        return queryset.prefetch_related(*self._relations)


_ParentData = namedtuple('_ParentData', 'parent relation type')


class _NestedOptimizationMixin:
    _SR = 0
    _PR = 1

    def rebuild(self, parent_optimization=None):
        if not parent_optimization or isinstance(parent_optimization, Annotation):
            return super(_NestedOptimizationMixin, self).rebuild()

        real_parent_optimization = parent_optimization
        while isinstance(real_parent_optimization, Chain):
            real_parent_optimization = real_parent_optimization.main_relation

        parent_relation = real_parent_optimization.main_relation
        assert isinstance(parent_relation, str), 'Only simple parent relations are supported.'

        if isinstance(real_parent_optimization, PrefetchRelated):
            parent_type = self._PR
        else:
            parent_type = self._SR

        return self._rebuild_nested(
            _ParentData(real_parent_optimization, parent_relation, parent_type),
        )

    def _rebuild_nested(self, parent_data):
        """
        :param _ParentData parent_data:
        """
        raise NotImplementedError

    @staticmethod
    def _join_relation(parent_relation, relation):
        return '{0}__{1}'.format(parent_relation, relation)


class NestedPrefetchRelated(_NestedOptimizationMixin, PrefetchRelated):
    def _rebuild_nested(self, parent_data):
        rebuilt_relations = []

        for relation in self._relations:
            if isinstance(relation, Prefetch):
                rebuilt_relations.append(
                    Prefetch(
                        self._join_relation(parent_data.relation, relation.prefetch_to),
                        queryset=relation.queryset,
                        to_attr=relation.to_attr,
                    ),
                )
            else:
                rebuilt_relations.append(self._join_relation(parent_data.relation, relation))

        return self.__class__(*rebuilt_relations, **self._extensions)


class NestedSelectRelated(_NestedOptimizationMixin, SelectRelated):
    def _rebuild_nested(self, parent_data):
        optimization_cls = NSR if parent_data.type == self._SR else NPR
        rebuilt_relations = [self._join_relation(parent_data.relation, r) for r in self._relations]

        return optimization_cls(*rebuilt_relations, **self._extensions)


class Chain(_NestedOptimizationMixin, DBOptimization):
    def __init__(self, *relations, **extensions):
        e = 'Wrong Chain() optimization configuration.'
        assert all(isinstance(rel, DBOptimization) for rel in relations), e

        super(Chain, self).__init__(*relations, **extensions)

    def _rebuild_nested(self, parent_data):
        rebuilt_relations = [r.rebuild(parent_data.parent) for r in self.relations]

        return self.__class__(*rebuilt_relations, **self.extensions)

    def apply(self, queryset):
        for opt in self._relations:
            queryset = opt.apply(queryset)

        return queryset


AN = Annotation
SR = SelectRelated
NSR = NestedSelectRelated
PR = PrefetchRelated
NPR = NestedPrefetchRelated
CH = Chain
