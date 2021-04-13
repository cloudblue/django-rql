#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#


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
    assert instance.ordering_filters == ordering_filters, "Ordering filter data doesn't match."
    assert instance.search_filters == search_filters, "Searching filter data doesn't match."


def _is_filter_subset(main_dct, subset_dct):
    main_keys = set(main_dct.keys())
    subset_keys = set(subset_dct.keys())

    for key, value in subset_dct.items():
        assert key in main_dct, 'Filter `{0}` is not set ({1}).'.format(key, value)
        main_dct_value = main_dct[key]

        if isinstance(value, dict):
            if 'custom' not in value:
                try:
                    _is_filter_subset(main_dct_value, value)
                except AssertionError as e:
                    raise AssertionError(
                        "Wrong filter `{0}` configuration: {1}".format(key, str(e)),
                    )

        elif isinstance(value, list):
            e = "Filter `{0}` data doesn't match ({1}).".format(key, value)
            assert len(value) == len(main_dct_value), e

            for m_dict, s_dict in zip(main_dct_value, value):
                _is_filter_subset(m_dict, s_dict)

        else:
            assert main_dct[key] == value, "{0} != {1}".format(main_dct[key], value)

            e = "assertion data must contain `orm_route` and `lookups`."
            assert {'orm_route', 'lookups'}.issubset(subset_keys), e

            assert 'field' in main_keys
