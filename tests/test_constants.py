from dj_rql.constants import FilterTypes


def test_field_filter_type():
    custom_field = {}

    assert FilterTypes.field_filter_type(custom_field) == FilterTypes.STRING
