#
#  Copyright © 2021 Ingram Micro Inc. All rights reserved.
#

from collections import OrderedDict
from copy import deepcopy


class RQLMixin:
    def to_representation(self, instance):
        self.apply_rql_select()
        return super(RQLMixin, self).to_representation(instance)

    def apply_rql_select(self):
        rql_select = self._get_field_rql_select(self)

        self.rql_select = rql_select
        deeper_rql_select = self._get_deeper_rql_select()

        for field_name, is_included in rql_select['select'].items():
            split_field_name = field_name.split('.')
            is_current_level_field = (len(split_field_name) == 1)
            current_depth_field_name = split_field_name[0]

            if is_current_level_field:
                if not is_included:
                    self.fields.pop(current_depth_field_name, None)

            elif current_depth_field_name in self.fields:
                deeper_depth_field_name = '.'.join(split_field_name[1:])
                deeper_field = self.fields[current_depth_field_name]

                deeper_field_select = {deeper_depth_field_name: is_included}
                self._set_field_rql_select(deeper_field, select=deeper_field_select)

                deeper_rql_select.setdefault(current_depth_field_name, OrderedDict())
                deeper_rql_select[current_depth_field_name].update(deeper_field_select)

    def rql_context(self, field_name):
        deeper_select = self._get_deeper_rql_select()
        depth = deeper_select.get('depth', 0) + 1
        select = deeper_select.get(field_name, OrderedDict())
        return {'rql_select': {'depth': depth, 'select': select}}

    def _get_deeper_rql_select(self):
        self._deeper_rql_select = getattr(self, '_deeper_rql_select', {})
        return self._deeper_rql_select

    def _get_field_rql_select(self, field):
        take_parent = bool(
            field.parent and getattr(field.parent, 'many', False) and isinstance(
                field, field.parent.child.__class__,
            ),
        )
        if take_parent:
            rql_field = field.parent
        else:
            rql_field = field

        rql_select = getattr(rql_field, 'rql_select', None)
        if rql_select is None:
            context = getattr(rql_field, '_context', {})
            default = getattr(
                context.get('request'),
                'rql_select',
                context.get('rql_select', None),
            )
            rql_select = deepcopy(default) if default else {'depth': 0, 'select': OrderedDict()}

        field.rql_select = rql_select
        return field.rql_select

    def _set_field_rql_select(self, field, select):
        rql_select = self._get_field_rql_select(field)

        rql_select['depth'] = self.rql_select['depth'] + 1
        rql_select['select'].update(select)
