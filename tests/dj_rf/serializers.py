#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from rest_framework import serializers

from dj_rql.drf.serializers import RQLMixin
from tests.dj_rf.models import (
    Author,
    Book,
    Page,
    Publisher,
)


class PublisherReferenceSerializer(RQLMixin, serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ('id', 'name')


class AuthorReferenceSerializer(RQLMixin, serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name')


class AuthorSerializer(RQLMixin, serializers.ModelSerializer):
    publisher = PublisherReferenceSerializer()

    class Meta:
        model = Author
        fields = (
            'id',
            'name',
            'publisher',
        )


class PageReferenceSerializer(RQLMixin, serializers.ModelSerializer):
    id = serializers.CharField(source='uuid')

    class Meta:
        model = Page
        fields = (
            'id',
            'content',
        )


class StarAuthorSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {}


class SelectBookSerializer(RQLMixin, serializers.ModelSerializer):
    write_only = serializers.CharField(source='title', write_only=True)

    author_ref = AuthorReferenceSerializer(source='author')
    author = serializers.SerializerMethodField()
    pages = PageReferenceSerializer(many=True)
    star = StarAuthorSerializer(source='*')

    class Meta:
        model = Book
        fields = (
            'id',  # must always be shown in both detail and list
            'blog_rating',  # by default not shown in list, but shown in detail
            'github_stars',  # by default not shown anywhere
            'star',
            'write_only',
            'author_ref',  # One level reference field (FK)
            'author',  # Deep nested fields (FK)
            'pages',  # List of backrefs
            'status',
            'amazon_rating',
        )

    def get_author(self, obj):
        if obj.author:
            return AuthorSerializer(obj.author, context=self.rql_context('author')).data


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ('id',)
