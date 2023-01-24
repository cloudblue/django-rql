#
#  Copyright © 2023 Ingram Micro Inc. All rights reserved.
#
from tests.dj_rf.models import Book
from tests.dj_rf.view import apply_annotations


book_qs = apply_annotations(Book.objects.order_by('id'))
