#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from uuid import uuid4

from django.db import models
from django_fsm import FSMField
from model_utils import Choices


class RandomFk(models.Model):
    pass


class Publisher(models.Model):
    name = models.CharField(max_length=20, null=True)

    fk1 = models.ForeignKey(RandomFk, on_delete=models.SET_NULL, null=True, related_name='r')
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
    current_price = models.DecimalField(null=True, decimal_places=4, max_digits=20)

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


class FKRelated1(models.Model):
    pass


class FKRelated2(models.Model):
    related21 = models.ForeignKey(FKRelated1, null=True, on_delete=models.PROTECT, related_name='r')


class OneTOneRelated(models.Model):
    pass


class ManyToManyRelated(models.Model):
    pass


class AutoMain(models.Model):
    common_int = models.IntegerField(default=0)
    common_str = models.CharField(max_length=32, null=True)

    self = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='parent')
    related1 = models.ForeignKey(FKRelated1, null=True, on_delete=models.CASCADE, related_name='+')
    related2 = models.ForeignKey(FKRelated2, on_delete=models.CASCADE, related_name='autos')

    one_to_one = models.OneToOneField(OneTOneRelated, on_delete=models.CASCADE)
    many_to_many = models.ManyToManyField(ManyToManyRelated)


class ReverseFKRelated(models.Model):
    auto1 = models.ForeignKey(AutoMain, on_delete=models.CASCADE, related_name='reverse_OtM')
    auto2 = models.ForeignKey(AutoMain, on_delete=models.CASCADE, related_name='+')


class ReverseOneToOneRelated(models.Model):
    auto = models.OneToOneField(
        AutoMain, null=True, on_delete=models.SET_NULL, related_name='reverse_OtO',
    )


class ReverseManyToManyRelated(models.Model):
    auto = models.ManyToManyField(AutoMain, related_name='+')


class ReverseManyToManyTroughRelated(models.Model):
    auto = models.ManyToManyField(
        AutoMain, through='Through', through_fields=('mtm', 'auto'), related_name='reverse_MtM',
    )


class Through(models.Model):
    auto = models.ForeignKey(AutoMain, on_delete=models.CASCADE)
    mtm = models.ForeignKey(ReverseManyToManyTroughRelated, on_delete=models.CASCADE)
    common_int = models.IntegerField(default=0)
