import pytest
from django.db.models import IntegerField, Value, Prefetch

from dj_rql.qs import *
from tests.dj_rf.models import Book, Page


default_qs = Book.objects.all()


def test_args():
    with pytest.raises(AssertionError) as e:
        DBOptimization()

    assert str(e.value) == 'At least one optimization must be specified.'


def test_parent():
    assert DBOptimization('a', parent=1).parent == 1
    assert DBOptimization('a').parent is None


@pytest.mark.parametrize('cls', (SR, PR))
def test_no_parent(cls):
    assert cls('a', parent=1).parent is None


@pytest.mark.parametrize('relation', (['z'], ['z', 'x']))
def test_main_relation(relation):
    assert DBOptimization(*relation).main_relation


def test_extensions_no_extension():
    assert DBOptimization('z').extensions == {}


def test_extensions_parent_only():
    assert DBOptimization('z', parent='x').extensions == {}


def test_extensions_annotations():
    assert DBOptimization('z', parent='x', anno_1=1, anno_2=2).extensions == {
        'anno_1': 1, 'anno_2': 2,
    }


def test_base_apply():
    with pytest.raises(NotImplementedError):
        DBOptimization('z').apply(None)


@pytest.mark.django_db
def test_annotation_apply():
    Book.objects.create()
    assert Annotation(abc=Value(1, IntegerField())).apply(default_qs).first().abc == 1


def test_sr_apply():
    qs = SelectRelated('author', 'author__publisher').apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_pr_apply():
    p_obj = Prefetch('pages')
    qs = PrefetchRelated('pages', p_obj).apply(default_qs)
    assert qs._prefetch_related_lookups == ('pages', p_obj)


def test_nested_deep_nesting():
    qs = NPR('authors', parent=NSR('publisher', parent=NSR('author'))).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher__authors',)


def test_nested_chain_parent():
    qs = NSR('publisher', parent=Chain(Chain(NSR('author'), NPR('pages')))).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_nested_apply_annotation_parent():
    an = Annotation(**{'a': 1})
    qs = NestedPrefetchRelated('pages', parent=an).apply(default_qs)
    assert qs._prefetch_related_lookups == ('pages',)


def test_nested_prefetch_object_in_parent():
    with pytest.raises(AssertionError) as e:
        NestedPrefetchRelated('pages', parent=PrefetchRelated(Prefetch('pages')))

    assert str(e.value) == 'Only simple parent relations are supported.'


def test_npr_apply_no_parent():
    qs = NestedPrefetchRelated('pages').apply(default_qs)
    assert qs._prefetch_related_lookups == ('pages',)


@pytest.mark.parametrize('parent', (PrefetchRelated('author'), SelectRelated('author')))
def test_npr_apply_parent(parent):
    qs = NestedPrefetchRelated('publisher', parent=parent).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)


def test_npr_apply_multi():
    parent = SelectRelated('author')
    pr_obj = Prefetch('publisher')
    qs = NestedPrefetchRelated(pr_obj, 'publisher', parent=parent).apply(default_qs)
    assert qs._prefetch_related_lookups == (pr_obj, 'author__publisher',)
    assert pr_obj.prefetch_through == pr_obj.prefetch_to == 'author__publisher'


def test_nsr_apply_no_parent():
    qs = NestedSelectRelated('author', 'author__publisher').apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_nsr_apply_sr_parent():
    qs = NestedSelectRelated('publisher', parent=SelectRelated('author')).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_nsr_apply_pr_parent():
    qs = NestedSelectRelated('publisher', parent=PrefetchRelated('author')).apply(default_qs)
    assert qs._prefetch_related_lookups == ('author__publisher',)


def test_chain_without_parent():
    qs = Chain(SelectRelated('author__publisher'), SelectRelated('author')).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}


def test_chain_parent():
    qs = Chain(NSR('publisher'), parent=Chain(SelectRelated('author'))).apply(default_qs)
    assert qs.query.select_related == {'author': {'publisher': {}}}
