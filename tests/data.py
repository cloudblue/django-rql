from __future__ import unicode_literals

BOOK_FILTER_CLS_ORDERING_DATA = {
    'author.email',
    'published.at',
    'd_id',
    'int_choice_field',
    'ordering_filter',
    'fsm',
    'anno_int',
    'anno_int_ref',
}

BOOK_FILTER_CLS_SEARCH_DATA = {
    'title',
    'author.email',
    'author__email',
    'str_choice_field',
    'fsm',
    'anno_str',
    'anno_title_dynamic',
}
