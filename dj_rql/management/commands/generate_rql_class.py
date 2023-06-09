#
#  Copyright © 2023 Ingram Micro Inc. All rights reserved.
#

import json
import re

from django.core.management import BaseCommand
from django.db.models import ForeignKey, OneToOneField, OneToOneRel
from django.utils.module_loading import import_string

from dj_rql.filter_cls import NestedAutoRQLFilterClass


TEMPLATE = """from {model_package} import {model_name}

from dj_rql.filter_cls import RQLFilterClass
{optimizations_import}

class {model_name}Filters(RQLFilterClass):
    MODEL = {model_name}
    SELECT = {select_flag}
    EXCLUDE_FILTERS = {exclusions}
    FILTERS = {filters}
"""


class Command(BaseCommand):
    help = (
        'Automatically generates a filter class for a model '
        'with all relations to the specified depth.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'model',
            nargs=1,
            type=str,
            help='Importable model location string.',
        )
        parser.add_argument(
            '-d',
            '--depth',
            type=int,
            default=1,
            help='Max depth of traversed model relations.',
        )
        parser.add_argument(
            '-s',
            '--select',
            action='store_true',
            default=True,
            help='Flag to include QuerySet optimizations: true by default.',
        )
        parser.add_argument(
            '-e',
            '--exclude',
            type=str,
            help='List of coma separated filter names or namespace to be excluded from generation.',
        )

    def handle(self, *args, **options):
        model_import = options['model'][0]
        model = import_string(model_import)
        is_select = options['select']
        exclusions = options['exclude'].split(',') if options['exclude'] else []

        class Cls(NestedAutoRQLFilterClass):
            MODEL = model
            DEPTH = options['depth']
            SELECT = is_select
            EXCLUDE_FILTERS = exclusions

            def _get_init_filters(self):
                self.init_filters = super()._get_init_filters()

                self.DEPTH = 0
                self.SELECT = False
                return super()._get_init_filters()

            def _get_field_optimization(self, field):
                if not self.SELECT:
                    return

                if isinstance(field, (ForeignKey, OneToOneField, OneToOneRel)):
                    return "NSR('{0}')".format(field.name)

                if not self._is_through_field(field):
                    return "NPR('{0}')".format(field.name)

        filters = Cls(model._default_manager.all()).init_filters
        filters_str = (
            json.dumps(filters, sort_keys=False, indent=4)
            .replace(
                '"ordering": true',
                '"ordering": True',
            )
            .replace(
                '"ordering": false',
                '"ordering": False',
            )
            .replace(
                '"search": true',
                '"search": True',
            )
            .replace(
                '"search": false',
                '"search": False',
            )
            .replace(
                '"qs": null',
                '"qs": None',
            )
        )

        filters_str = re.sub(r"\"((NPR|NSR)\('\w+?'\))\"", r'\1', filters_str)

        model_package, model_name = model_import.rsplit('.', 1)
        code = TEMPLATE.format(
            model_package=model_package,
            model_name=model_name,
            filters=filters_str,
            select_flag='True' if is_select else 'False',
            optimizations_import='from dj_rql.qs import NPR, NSR\n' if is_select else '',
            exclusions=exclusions,
        )

        return code
