#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#

from copy import copy

from rest_framework.schemas.openapi import SchemaGenerator

from dj_rql.openapi import RQLFilterClassSpecification, RQLFilterDescriptionTemplate
from tests.dj_rf.filters import BooksFilterClass
from tests.dj_rf.models import Book


def filter_instance():
    return BooksFilterClass(None)


def filter_item(f_name, f_item):
    class Cls(RQLFilterClassSpecification):
        @classmethod
        def enrich_with_openapi_data(cls):
            item = copy(f_item)
            item['oa'] = cls._get_filter_item_openapi_data(f_name, f_item)
            return item

    return Cls.enrich_with_openapi_data()


def filter_data(f_name):
    f_instance = filter_instance()
    f_item = filter_item(f_name, f_instance.filters[f_name])
    return f_item, f_instance


def test_description_common_render():
    result = RQLFilterDescriptionTemplate.render(*filter_data('id'))
    assert result == '**Filter for: id**\n\nlookups: eq, ne, ge, gt, le, lt, null, in, out'


def test_description_search_render():
    result = RQLFilterDescriptionTemplate.render(*filter_data('str_choice_field'))
    assert result == '**Filter for: str_choice_field**\n\nlookups: ' \
                     'eq, ne, like, ilike, in, out\nsearch: true'


def test_description_ordering_render():
    result = RQLFilterDescriptionTemplate.render(*filter_data('int_choice_field'))
    assert result == '**Filter for: int_choice_field**\n\nlookups: ' \
                     'eq, ne, ge, gt, le, lt, in, out\nordering: true'


def test_description_null_overridden_render():
    result = RQLFilterDescriptionTemplate.render(*filter_data('title'))
    assert result == '**Filter for: title**\n\n' \
                     'lookups: eq, ne, like, ilike, null, in, out\nsearch: true\n' \
                     'null: NULL_ID, null()'


def test_description_hidden_render():
    result = RQLFilterDescriptionTemplate.render(*filter_data('select_author'))
    assert result == '**Filter for: select_author**\n\n' \
                     'lookups: eq, ne, like, ilike, in, out\ndefault: **hidden**'


def test_description_custom_render():
    class Cls(RQLFilterDescriptionTemplate):
        IN_PLACE_RENDERERS = ('_render_custom_inplace',)

        @classmethod
        def _render_custom_inplace(cls, *args):
            return 'COMMON'

    result = Cls.render(*filter_data('id'))
    assert result == 'COMMON'


def test_specification_render():
    class Cls(RQLFilterClassSpecification):
        @classmethod
        def get_for_field(cls, filter_item, filter_instance):
            if filter_item['oa']['name'] == 'd_id':
                return {'name': 'd_id', 'custom': True}

    f_instance = filter_instance()
    result = Cls.get(f_instance)

    assert result[0]['name'] == 'amazon_rating'
    assert result[-2]['name'] == 'written'
    assert result[-1]['name'] == 'author__email'

    converted_result = {f['name']: f for f in result}

    assert not converted_result['id']['required']
    assert not converted_result['id']['deprecated']
    assert converted_result['id']['in'] == 'query'
    assert converted_result['id']['schema'] == {'type': 'integer'}

    assert converted_result['status']['required']
    assert converted_result['status']['schema'] == {
        'type': 'string',
        'enum': list(Book.STATUS_CHOICES),
    }

    assert 'Author Email' in converted_result['author__email']['description']
    assert converted_result['author__email']['deprecated']

    assert 'name' not in converted_result
    assert 'author' not in converted_result

    assert converted_result['published.at']['schema'] == {'type': 'string', 'format': 'date-time'}

    assert converted_result['rating.blog']['schema'] == {
        'type': 'string',
        'enum': ['low', 'high'],
    }
    assert converted_result['rating.blog_int']['schema'] == {
        'type': 'integer',
        'enum': [Book.LOW_RATING, Book.HIGH_RATING],
    }

    assert converted_result['d_id'] == {'name': 'd_id', 'custom': True}

    assert converted_result['str_choice_field']['schema'] == {
        'type': 'string',
        'enum': ['one', 'two'],
    }
    assert converted_result['str_choice_field_repr']['schema'] == {
        'type': 'string',
        'enum': ['I', 'II'],
    }

    assert converted_result['anno_int']['schema'] == {'type': 'integer'}
    assert converted_result['author.is_male']['schema'] == {'type': 'boolean'}
    assert converted_result['written']['schema'] == {'type': 'string', 'format': 'date'}
    assert converted_result['current_price']['schema'] == {'type': 'number', 'format': 'double'}
    assert converted_result['amazon_rating']['schema'] == {'type': 'number', 'format': 'float'}

    assert converted_result['url']['schema'] == {'type': 'string'}
    assert converted_result['t__in']['schema'] == {'type': 'custom', 'format': 'custom'}


def test_default_get_for_field():
    assert RQLFilterClassSpecification.get_for_field(None, None) is None


def test_api_auto_genereation():
    openapi_schema = SchemaGenerator().get_schema()

    assert '/books/' in openapi_schema['paths']
    parameters = openapi_schema['paths']['/books/']['get']['parameters']
    assert len(parameters) > 10
    assert parameters[0]['name'] == 'limit'
    assert parameters[0]['schema'] == {'type': 'integer'}
    assert parameters[1]['name'] == 'offset'
    assert parameters[1]['schema'] == {'type': 'integer'}
    assert parameters[2]['name'] == 'amazon_rating'

    assert '/nofiltercls/' in openapi_schema['paths']

    assert '/books/{id}/' not in openapi_schema['paths']

    assert '/books/{id}/act/' in openapi_schema['paths']
    parameters = openapi_schema['paths']['/books/{id}/act/']['get']['parameters']
    assert len(parameters) == 1
    assert parameters[0]['name'] == 'id'

    assert '/select/{id}/' in openapi_schema['paths']
    parameters = openapi_schema['paths']['/select/{id}/']['get']['parameters']
    assert len(parameters) == 1
    assert parameters[0]['name'] == 'id'

    assert '/old_books/{id}/' in openapi_schema['paths']
    get_parameters = openapi_schema['paths']['/old_books/{id}/']['get']['parameters']
    assert len(get_parameters) > 10
    put_parameters = openapi_schema['paths']['/old_books/{id}/']['put']['parameters']
    assert len(put_parameters) == 1
    assert put_parameters[0]['name'] == 'id'
