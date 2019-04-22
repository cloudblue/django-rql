from __future__ import unicode_literals


def assert_filter_cls(filter_cls, filters, ordering_filters, search_filters):
    """ Helper function for testing of custom view rql filter classes.

    Args:
        filter_cls (cls): Custom RQL Filter.
        filters (dict): filter_cls.filters
        ordering_filters (set): filter_cls.ordering_filters
        search_filters (set): filter_cls.search_filters
    """
    instance = filter_cls(filter_cls.MODEL._default_manager.none())
    _is_filter_subset(instance.filters, filters)
    assert instance.ordering_filters == ordering_filters
    assert instance.search_filters == search_filters


def _is_filter_subset(main_dct, subset_dct):
    keys = set(subset_dct.keys())
    for key, value in subset_dct.items():
        assert key in main_dct
        main_dct_value = main_dct[key]

        if isinstance(value, dict):
            _is_filter_subset(main_dct_value, value)
        elif isinstance(value, list):
            assert len(value) == len(main_dct_value)
            for m_dict, s_dict in zip(main_dct_value, value):
                _is_filter_subset(m_dict, s_dict)
        else:
            assert main_dct[key] == value
            assert {'orm_route', 'lookups'}.issubset(keys)
