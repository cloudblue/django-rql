#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#


def get_book_filter_cls_ordering_data():
    return {
        'author.email',
        'published.at',
        'd_id',
        'int_choice_field',
        'ordering_filter',
        'fsm',
        'anno_int',
        'anno_int_ref',
    }


def get_book_filter_cls_search_data():
    return {
        'title',
        'author.email',
        'author__email',
        'str_choice_field',
        'fsm',
        'anno_str',
        'anno_title_dynamic',
    }
