#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from collections import Counter

from dj_rql.constants import (
    ComparisonOperators as CO,
    DjangoLookups as DJL,
    FilterTypes, RQL_NULL,
    SearchOperators as SO,
    RQL_ANY_SYMBOL,
    RQL_FALSE,
    RQL_LIMIT_PARAM,
    RQL_OFFSET_PARAM,
    RQL_ORDERING_OPERATOR,
    RQL_TRUE,
)
from dj_rql.drf.backend import RQLFilterBackend
from dj_rql.drf._utils import get_query
from dj_rql.exceptions import RQLFilterParsingError


class CompatibilityRQLFilterBackend(RQLFilterBackend):
    """
    If there is necessity to apply RQL filters to a production API, which was working on other
    filter backend (without raising API version number or losing compatibility), this base
    compatibility DRF backend must be inherited from.
    """
    @classmethod
    def get_query(cls, filter_instance, request, view):
        try:
            query_string = cls.modify_initial_query(filter_instance, request, get_query(request))

            if not cls.is_old_syntax(filter_instance, request, query_string):
                return query_string

            else:
                return cls.get_rql_query(filter_instance, request, query_string)
        except Exception:
            raise RQLFilterParsingError(details={
                'error': 'Bad filter query.',
            })

    @classmethod
    def modify_initial_query(cls, filter_instance, request, query_string):
        return query_string

    @classmethod
    def is_old_syntax(cls, filter_instance, request, query_string):
        raise NotImplementedError

    @classmethod
    def get_rql_query(cls, filter_instance, request, query_string):
        raise NotImplementedError


class DjangoFiltersRQLFilterBackend(CompatibilityRQLFilterBackend):
    """
    DRF Backend, that automatically converts Django Filter specific queries to correct RQL queries.

    IMPORTANT NOTES:
        * `;` separation is context-based;
        * MultipleChoiceFilter works by OR logic in RQL.

    Currently NOT SUPPORTED:
        * range fields and filters;
        * regex and iregex conversion;
        * OrderingFilter;

        * ?&& syntax in queries;
        * etc.
    """
    RESERVED_ORDERING_WORDS = {'order_by', 'ordering'}

    _POSSIBLE_DF_LOOKUPS = DJL.all()
    _RQL_COMPARISON_OPERATORS = {CO.EQ, CO.NE, CO.LE, CO.GE, CO.LT, CO.GT}
    _IMPOSSIBLE_PROP_SYMBOLS = {'(', ',', ')', ' ', "'", '"'}

    @classmethod
    def is_old_syntax(cls, filter_instance, request, query_string):
        if not query_string.strip():
            return False

        if query_string[-1] == '&':
            return True

        qp_all_filters = set()
        qp_old_filters = set()
        for filter_name in request.query_params.keys():
            select_not_in_filter = not cls._is_select_in_filter(filter_name)
            if select_not_in_filter and \
                    (not set(Counter(filter_name)).isdisjoint(cls._IMPOSSIBLE_PROP_SYMBOLS)):
                return False

            for v in request.query_params.getlist(filter_name):
                if select_not_in_filter and not v:
                    return True

                if v in ('True', 'False'):
                    return True

                vc = Counter(v)
                no_quotes = not (vc.get('"', 0) > 1 or vc.get("'", 0) > 1)
                if vc.get(' ') and no_quotes:
                    return True

                if vc.get('=') and no_quotes:
                    return False

                if len(v) > 2 and v[2] == '=' and v[:2] in cls._RQL_COMPARISON_OPERATORS:
                    return False

            qp_all_filters.add(filter_name)
            if cls._is_old_style_filter(filter_name):
                lookup = cls._get_filter_and_lookup(filter_name)[-1]
                if lookup in (DJL.REGEX, DJL.I_REGEX):
                    cls._conversion_error()

                qp_old_filters.add(filter_name)

        if not qp_all_filters.isdisjoint(cls.RESERVED_ORDERING_WORDS):
            return True

        if not qp_old_filters:
            return False

        if not qp_old_filters - cls._get_filters_similar_to_old_syntax(filter_instance):
            return False

        return True

    @classmethod
    def get_rql_query(cls, filter_instance, request, query_string):
        filter_value_pairs = []

        for filter_name in request.query_params.keys():
            if cls._is_select_in_filter(filter_name):
                filter_value_pairs.append(filter_name)
                continue

            one_filter_value_pairs = []
            for value in request.query_params.getlist(filter_name):
                if not value:
                    continue

                if filter_name in (RQL_LIMIT_PARAM, RQL_OFFSET_PARAM):
                    one_filter_value_pairs.append('{}={}'.format(filter_name, value))
                    continue

                if filter_name in cls.RESERVED_ORDERING_WORDS:
                    one_filter_value_pairs.append('{}({})'.format(RQL_ORDERING_OPERATOR, value))
                    continue

                f_item = filter_instance.get_filter_base_item(filter_name)
                if f_item and (not f_item.get('custom', False)):
                    if FilterTypes.field_filter_type(f_item['field']) == FilterTypes.BOOLEAN:
                        value = cls._convert_bool_value(value)

                if not cls._is_old_style_filter(filter_name):
                    one_filter_value_pairs.append(
                        '{}={}'.format(filter_name, cls._add_quotes_to_value(value)),
                    )

                else:
                    one_filter_value_pairs.append(
                        cls._convert_filter_to_rql(filter_name, value),
                    )

            if one_filter_value_pairs:
                filter_value_pairs.append('&'.join(one_filter_value_pairs))

        return '&'.join(filter_value_pairs) if filter_value_pairs else ''

    @staticmethod
    def _is_select_in_filter(filter_name):
        return 'select(' in filter_name

    @classmethod
    def _convert_filter_to_rql(cls, filter_name, value):
        filter_base, lookup = cls._get_filter_and_lookup(filter_name)

        if lookup == DJL.IN:
            return 'in({},({}))'.format(
                filter_base, ','.join(cls._add_quotes_to_value(v) for v in value.split(',') if v),
            )

        if lookup == DJL.NULL:
            operator = CO.EQ if cls._convert_bool_value(value) == 'true' else CO.NE
            return '{}={}={}'.format(filter_base, operator, RQL_NULL)

        if lookup in (DJL.GT, DJL.GTE, DJL.LT, DJL.LTE):
            if lookup == DJL.GTE:
                operator = CO.GE
            elif lookup == DJL.LTE:
                operator = CO.LE
            else:
                operator = lookup
            return '{}={}={}'.format(filter_base, operator, value)

        operator = SO.I_LIKE if lookup[0] == 'i' else SO.LIKE
        if lookup in (DJL.CONTAINS, DJL.I_CONTAINS, DJL.ENDSWITH, DJL.I_ENDSWITH) and \
                value[0] != RQL_ANY_SYMBOL:
            value = RQL_ANY_SYMBOL + value

        if lookup in (DJL.CONTAINS, DJL.I_CONTAINS, DJL.STARTSWITH, DJL.I_STARTSWITH) and \
                value[-1] != RQL_ANY_SYMBOL:
            value += RQL_ANY_SYMBOL

        return '{}({},{})'.format(operator, filter_base, cls._add_quotes_to_value(value))

    @classmethod
    def _convert_bool_value(cls, value):
        if value in ('True', 'true', '1'):
            return RQL_TRUE
        elif value in ('False', 'false', '0'):
            return RQL_FALSE

        cls._conversion_error()

    @classmethod
    def _add_quotes_to_value(cls, value):
        for quote in ('"', "'"):
            if quote not in value:
                return '{q}{}{q}'.format(value, q=quote)

        cls._conversion_error()

    @staticmethod
    def _conversion_error():
        raise RQLFilterParsingError(details={'error': 'Bad filter query.'})

    @classmethod
    def _get_filters_similar_to_old_syntax(cls, filter_instance):
        old_syntax_filters = getattr(filter_instance, 'old_syntax_filters', None)
        if old_syntax_filters:
            return old_syntax_filters

        similar_to_old_syntax_filters = set()
        for filter_name in filter_instance.filters.keys():
            if cls._is_old_style_filter(filter_name):
                similar_to_old_syntax_filters.add(filter_name)

        setattr(filter_instance, 'old_syntax_filters', similar_to_old_syntax_filters)
        return similar_to_old_syntax_filters

    @classmethod
    def _is_old_style_filter(cls, filter_name):
        return cls._get_filter_and_lookup(filter_name)[-1] in cls._POSSIBLE_DF_LOOKUPS

    @classmethod
    def _get_filter_and_lookup(cls, filter_name):
        return filter_name.rsplit('__', 1)
