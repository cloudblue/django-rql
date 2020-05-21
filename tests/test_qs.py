#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

import pytest
from django.db.models import IntegerField, Value, Prefetch

from dj_rql.qs import (
    Annotation,
    Chain,
    DBOptimization,
    PrefetchRelated,
    NestedPrefetchRelated,
    NestedSelectRelated,
    SelectRelated,
    NPR,
    NSR,
    _NestedOptimizationMixin,
)
from tests.dj_rf.models import Book


default_qs = Book.objects.all()


def test_args():
    with pytest.raises(AssertionError) as e:
        DBOptimization()

    assert str(e.value) == 'At least one optimization must be specified.'


@pytest.mark.parametrize('relation', (['z'], ['z', 'x']))
def test_main_relation(relation):
    assert DBOptimization(*relation).main_relation


def test_extensions_no_extension():
    assert DBOptimization('z').extensions == {}


def test_extensions_annotations():
    assert DBOptimization('z', anno_1=1, anno_2=2).extensions == {
        'anno_1': 1, 'anno_2': 2,
    }


def test_base_apply():
    with pytest.raises(NotImplementedError):
        DBOptimization('z').apply(None)


@pytest.mark.django_db
def test_annotation_apply():
    Book.objects.create()

    anno = Annotation(abc=Value(1, IntegerField()))
    assert anno.apply(default_qs).first().abc == 1

    assert anno.rebuild() == anno


def test_sr_apply():
    qs = SelectRelated('author', 'author__publisher').apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_pr_apply():
    p_obj = Prefetch('pages')
    qs = PrefetchRelated('pages', p_obj).apply(default_qs)
    assert qs._prefetch_related_lookups == ('pages', p_obj)


def test_nested_deep_nesting():
    qs = NPR('authors').rebuild(NSR('publisher').rebuild(NSR('author'))).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher__authors',)


def test_nested_chain_parent():
    qs = NSR('publisher').rebuild(Chain(Chain(NSR('author'), NPR('pages')))).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_nested_apply_annotation_parent():
    qs = NestedPrefetchRelated('pages').rebuild(Annotation(**{'a': 1})).apply(default_qs)
    assert qs._prefetch_related_lookups == ('pages',)


def test_nested_prefetch_object_in_parent():
    with pytest.raises(AssertionError) as e:
        NestedPrefetchRelated('pages').rebuild(PrefetchRelated(Prefetch('pages')))

    assert str(e.value) == 'Only simple parent relations are supported.'


def test_npr_apply_no_parent():
    qs = NestedPrefetchRelated('pages').apply(default_qs)
    assert qs._prefetch_related_lookups == ('pages',)


@pytest.mark.parametrize('parent', (PrefetchRelated('author'), SelectRelated('author')))
def test_npr_apply_parent(parent):
    qs = NestedPrefetchRelated('publisher').rebuild(parent).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)


def test_npr_apply_multi():
    qs = NPR(Prefetch('publisher'), 'publisher').rebuild(SelectRelated('author')).apply(default_qs)

    assert len(qs._prefetch_related_lookups) == 2
    assert qs._prefetch_related_lookups[1] == 'author__publisher'

    pr_obj = qs._prefetch_related_lookups[0]
    assert isinstance(pr_obj, Prefetch)
    assert pr_obj.prefetch_through == pr_obj.prefetch_to == 'author__publisher'


def test_nsr_apply_no_parent():
    qs = NestedSelectRelated('author', 'author__publisher').apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_nsr_apply_sr_parent():
    qs = NestedSelectRelated('publisher').rebuild(SelectRelated('author')).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_nsr_apply_pr_parent():
    qs = NestedSelectRelated('publisher').rebuild(PrefetchRelated('author')).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)


def test_chain_without_parent():
    qs = Chain(SelectRelated('author__publisher'), SelectRelated('author')).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_chain_parent_sr():
    qs = Chain(NSR('publisher')).rebuild(Chain(SelectRelated('author'))).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_chain_parent_pr():
    qs = Chain(NSR('publisher')).rebuild(Chain(PrefetchRelated('author'))).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)


def test_chain_bad_relations():
    with pytest.raises(AssertionError) as e:
        Chain('abc')

    assert str(e.value) == 'Wrong Chain() optimization configuration.'


def test_nested_optimization_mixin_rebuild_nested():
    with pytest.raises(NotImplementedError):
        _NestedOptimizationMixin()._rebuild_nested(None)
