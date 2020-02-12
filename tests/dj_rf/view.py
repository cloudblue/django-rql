from __future__ import unicode_literals

from django.db.models import CharField, F, IntegerField, Value
from rest_framework import mixins
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet

from dj_rql.drf import (
    RQLContentRangeLimitOffsetPagination,
    RQLFilterBackend,
)
from dj_rql.compat import DjangoFiltersRQLFilterBackend
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Author, Book, Page, Publisher


class PublisherReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ('id', 'name')


class AuthorReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name')


class AuthorSerializer(serializers.ModelSerializer):
    publisher = PublisherReferenceSerializer()

    class Meta:
        model = Author
        fields = (
            'id',
            'name',
            'publisher',
        )


class PageReferenceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='uuid')

    class Meta:
        model = Page
        fields = (
            'id',
            'content',
        )


class SelectBookSerializer(serializers.ModelSerializer):
    write_only = serializers.CharField(source='title', write_only=True)

    author_ref = AuthorReferenceSerializer(source='author')
    author = serializers.SerializerMethodField()
    pages = PageReferenceSerializer(many=True)

    class Meta:
        model = Book
        fields = (
            'id',  # must always be shown in both detail and list
            'blog_rating',  # by default not shown in list, but shown in detail
            'github_stars',  # by default not shown anywhere
            'write_only',
            'author_ref',  # One level reference field (FK)
            'author',  # Deep nested fields (FK)
            'pages',  # List of backrefs
        )

    def get_author(self, obj):
        return AuthorSerializer(obj).data


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id',)


def apply_annotations(qs):
    return qs.annotate(
        anno_int=Value(1000, IntegerField()),
        anno_str=Value('text', CharField(max_length=10)),
        anno_auto=F('id'),
    )


class BaseViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = apply_annotations(
        Book.objects.select_related('author').prefetch_related('pages').all(),
    )
    serializer_class = BookSerializer
    rql_filter_class = BooksFilterClass
    pagination_class = RQLContentRangeLimitOffsetPagination


class DRFViewSet(BaseViewSet):
    filter_backends = (RQLFilterBackend,)


class DjangoFiltersViewSet(BaseViewSet):
    filter_backends = (DjangoFiltersRQLFilterBackend,)


class SelectViewSet(mixins.RetrieveModelMixin, BaseViewSet):
    serializer_class =