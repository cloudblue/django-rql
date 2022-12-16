#
#  Copyright © 2022 Ingram Micro Inc. All rights reserved.
#

from copy import copy
from numbers import Number

from py_rql.constants import (
    RQL_NULL,
    RQL_ORDERING_OPERATOR,
    RQL_SEARCH_PARAM,
    FilterLookups,
)

from dj_rql.constants import FilterTypes


class RQLFilterDescriptionTemplate:
    BASE_TEMPLATE = '{description}\n\n**lookups:** {lookups}'
    DEFAULT_DESCRIPTION = 'Filter for: {description}'
    IN_PLACE_RENDERERS = (
        '_render_search_inplace',
        '_render_ordering_inplace',
        '_render_null_inplace',
        '_render_default_inplace',
    )

    @classmethod
    def render(cls, filter_item, filter_instance):
        """
        :param dict filter_item: Extended Filter item
        :param dj_rql.filter_cls.RQLFilterClass filter_instance: Instance of Filter Class
        :return: Rendered description for filter item
        :rtype: str
        """
        result = cls._render_base(filter_item, filter_instance)

        for render_func in cls.IN_PLACE_RENDERERS:
            result = getattr(cls, render_func)(result, filter_item, filter_instance)

        return result

    @classmethod
    def _render_base(cls, filter_item, filter_instance):
        sorted_lookups = (
            FilterLookups.EQ,
            FilterLookups.NE,
            FilterLookups.GE,
            FilterLookups.GT,
            FilterLookups.LE,
            FilterLookups.LT,
            FilterLookups.LIKE,
            FilterLookups.I_LIKE,
            FilterLookups.NULL,
            FilterLookups.IN,
            FilterLookups.OUT,
        )
        filter_lookups = filter_item.get('lookups', {})

        description = filter_item['oa']['description']
        if not description:
            description = cls.DEFAULT_DESCRIPTION.format(description=filter_item['oa']['name'])

        return cls.BASE_TEMPLATE.format(
            description=description,
            lookups=', '.join(fl for fl in sorted_lookups if fl in filter_lookups),
        )

    @classmethod
    def _render_search_inplace(cls, base, filter_item, filter_instance):
        if filter_item['oa']['name'] not in filter_instance.search_filters:
            return base

        return cls._render_common_key_inplace(base, RQL_SEARCH_PARAM, 'true')

    @classmethod
    def _render_ordering_inplace(cls, base, filter_item, filter_instance):
        if filter_item['oa']['name'] not in filter_instance.ordering_filters:
            return base

        return cls._render_common_key_inplace(base, RQL_ORDERING_OPERATOR, 'true')

    @classmethod
    def _render_null_inplace(cls, base, filter_item, filter_instance):
        null_values = filter_item.get('null_values', {RQL_NULL})

        if FilterLookups.NULL in filter_item.get('lookups', {}) and null_values != {RQL_NULL}:
            return cls._render_common_key_inplace(
                base, 'null', ', '.join(sorted(null_values)),
            )

        return base

    @classmethod
    def _render_default_inplace(cls, base, filter_item, filter_instance):
        if filter_item.get('hidden', False):
            return cls._render_common_key_inplace(base, 'default', '*hidden*')

        return base

    @classmethod
    def _render_common_key_inplace(cls, base, key, value):
        return '{base}\n\n**{key}:** {value}'.format(base=base, key=key, value=value)


class RQLFilterClassSpecification:
    FIELD_DESCRIPTION_TEMPLATE = RQLFilterDescriptionTemplate

    @classmethod
    def get(cls, filter_instance):
        """
        Returns OpenAPI specification for filters.
        Filter sorting is alphabetic with deprecated filters in the end.

        :param dj_rql.filter_cls.RQLFilterClass filter_instance: Instance of Filter Class
        :return: OpenAPI compatible specification of Filter Class Filters
        :rtype: list of dict
        """
        extended_filter_items = {}
        common_filter_names, deprecated_filter_names = [], []

        for filter_name, filter_item in filter_instance.filters.items():
            f_item = filter_item[0] if isinstance(filter_item, list) else filter_item
            openapi_data = cls._get_filter_item_openapi_data(filter_name, f_item)

            if not openapi_data['hidden']:
                extended_filter_items[filter_name] = copy(f_item)
                extended_filter_items[filter_name]['oa'] = openapi_data

                if not openapi_data['deprecated']:
                    common_filter_names.append(filter_name)
                else:
                    deprecated_filter_names.append(filter_name)

        result = []
        for filter_name in sorted(common_filter_names) + sorted(deprecated_filter_names):
            filter_item = extended_filter_items[filter_name]

            filter_spec = cls.get_for_field(filter_item, filter_instance)
            if not filter_spec:
                filter_spec = cls._get_default_for_field(filter_item, filter_instance)

            result.append(filter_spec)

        return result

    @classmethod
    def get_for_field(cls, filter_item, filter_instance):
        """ This method can be overridden to support custom specs for certain filters.

        :param dict filter_item: Extended Filter Item
        :param dj_rql.filter_cls.RQLFilterClass filter_instance: Instance of Filter Class
        :rtype: dict or None
        """
        pass

    @classmethod
    def _get_default_for_field(cls, filter_item, filter_instance):
        return {
            'name': filter_item['oa']['name'],
            'description': cls.FIELD_DESCRIPTION_TEMPLATE.render(filter_item, filter_instance),
            'in': 'query',
            'required': filter_item['oa']['required'],
            'deprecated': filter_item['oa']['deprecated'],
            'schema': cls._get_schema_for_field(filter_item, filter_instance),
        }

    @classmethod
    def _get_schema_for_field(cls, filter_item, filter_instance):
        result = {}

        if filter_item['oa']['type']:
            result = {'type': filter_item['oa']['type']}

            if filter_item['oa']['format']:
                result['format'] = filter_item['oa']['format']

        if not result and ('field' not in filter_item):
            return {'type': 'string'}

        field = filter_item['field']
        if not result:
            field_type_oa_type_mapper = {
                FilterTypes.STRING: {'type': 'string'},
                FilterTypes.INT: {'type': 'integer'},
                FilterTypes.DECIMAL: {'type': 'number', 'format': 'double'},
                FilterTypes.FLOAT: {'type': 'number', 'format': 'float'},
                FilterTypes.DATETIME: {'type': 'string', 'format': 'date-time'},
                FilterTypes.DATE: {'type': 'string', 'format': 'date'},
                FilterTypes.BOOLEAN: {'type': 'boolean'},
            }
            result = field_type_oa_type_mapper[FilterTypes.field_filter_type(field)]

        choices = getattr(field, 'choices', None)
        if choices:
            if type(choices).__name__ == 'Choices' or isinstance(choices[0], tuple):
                use_repr = filter_item.get('use_repr', False)
                enum = [choice[int(use_repr)] for choice in choices]
            else:
                enum = list(choices)
            result['enum'] = enum

            if isinstance(enum[0], Number):
                result['type'] = 'integer'
            else:
                result['type'] = 'string'

        return result

    @classmethod
    def _get_filter_item_openapi_data(cls, filter_name, filter_item):
        openapi_data = copy(filter_item.get('openapi', {}))

        openapi_data['description'] = openapi_data.get('description')
        openapi_data['hidden'] = openapi_data.get('hidden', False)
        openapi_data['required'] = openapi_data.get('required', False)
        openapi_data['deprecated'] = openapi_data.get('deprecated', False)
        openapi_data['name'] = filter_name
        openapi_data['type'] = openapi_data.get('type')
        openapi_data['format'] = openapi_data.get('format')

        return openapi_data
