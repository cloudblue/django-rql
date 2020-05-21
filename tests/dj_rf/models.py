#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from uuid import uuid4

from django.db import models
from django_fsm import FSMField
from model_utils import Choices


class RandomFk(models.Model):
    pass


class Publisher(models.Model):
    name = models.CharField(max_length=20, null=True)

    fk1 = models.ForeignKey(RandomFk, on_delete=models.SET_NULL, null=True)
    fk2 = models.ForeignKey(RandomFk, on_delete=models.SET_NULL, null=True)


class Author(models.Model):
    name = models.CharField(max_length=20, null=True, blank=False)
    email = models.EmailField(null=True)

    is_male = models.NullBooleanField()

    publisher = models.ForeignKey(
        Publisher, related_name='authors', on_delete=models.SET_NULL, null=True,
    )

    fk1 = models.ForeignKey(RandomFk, on_delete=models.SET_NULL, null=True)


class Book(models.Model):
    LOW_RATING, HIGH_RATING = 0, 1
    BLOG_RATING_CHOICES = ((LOW_RATING, 'low'), (HIGH_RATING, 'high'))
    PLANNING, WRITING, PUBLISHED = 'planning', 'writing', 'publishing'
    STATUS_CHOICES = (PLANNING, WRITING, PUBLISHED)

    title = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PLANNING)
    publishing_url = models.URLField(null=True)

    blog_rating = models.BigIntegerField(null=True, choices=BLOG_RATING_CHOICES)
    github_stars = models.PositiveIntegerField(null=True)
    amazon_rating = models.FloatField(null=True)
    current_price = models.DecimalField(null=True, decimal_places=4)

    written = models.DateField(null=True)
    published_at = models.DateTimeField(null=True)

    author = models.ForeignKey(Author, related_name='books', on_delete=models.CASCADE, null=True)

    INT_CHOICES = Choices(
        (1, 'one', 'I'),
        (2, 'two', 'II'),
    )
    int_choice_field = models.IntegerField(choices=INT_CHOICES, default=INT_CHOICES.one)

    STR_CHOICES = Choices(
        ('one', 'I'),
        ('two', 'II'),
    )
    str_choice_field = models.CharField(max_length=5, choices=STR_CHOICES, default=STR_CHOICES.one)

    fsm_field = FSMField(default=STR_CHOICES.one, choices=STR_CHOICES, null=True)


class Page(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    content = models.TextField(null=True)

    number = models.IntegerField(null=True)
    book = models.ForeignKey(Book, related_name='pages', on_delete=models.CASCADE)
