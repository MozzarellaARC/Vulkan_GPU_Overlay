# RetopoView
# Copyright (C) 2021  Loki Bear

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "RetopoView",
    "author": "Loki Bear",
    "description": "Adds colourful overlays for meshes. Useful for marking topology flow when doing retopo/studying topology.",
    "blender": (2, 91, 0),
    "version": (0, 0, 1),
    'location': 'Properties > Data > Topology Groups',
    "warning": "",
    "tracker_url": "https://github.com/LokiTheCuteBear/RetopoView",
    "category": "Object"
}

import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, BoolProperty, StringProperty, CollectionProperty, FloatVectorProperty, FloatProperty

# Import modules
from .main.rv_ui import register as ui_register, unregister as ui_unregister
from .main.rv_ops import *
from .main.rv_group_navigation import *


class RETOPOVIEW_group(PropertyGroup):
    def ensure_unique_name(self, context):
        obj = context.object
        new_name = self.name
        group_names = set()

        for group in obj.rv_groups:
            if group.group_id != self.group_id:
                group_names.add(group.name)

        if new_name not in group_names:
            return

        try:
            extension_number = new_name[new_name.rindex('_') + 1:]
            if not extension_number.isnumeric():
                self.name = self.name + "_1"
            else:
                self.name = new_name[:new_name.rindex('_')] + "_" + str(int(extension_number) + 1)
        except ValueError:
            self.name = self.name + "_1"

    name: StringProperty(default='Group')
    color: FloatVectorProperty(name="Group Color", subtype='COLOR', default=[1.0, 1.0, 1.0], min=0.0, max=1.0)
    group_id: IntProperty(default=1)

    # Workaround to handle unique name enforcement
    def update_name(self, context):
        self.ensure_unique_name(context)

    name_update: StringProperty(default='Group', update=update_name)

def register():
    bpy.utils.register_class(RETOPOVIEW_group)

    classes = (
        RETOPOVIEW_OT_overlay,
        RETOPOVIEW_OT_add_group,
        RETOPOVIEW_OT_handle_face_selection,
        RETOPOVIEW_OT_find_parent_group,
        RETOPOVIEW_OT_move_group,
        RETOPOVIEW_OT_change_selection_group_id,
        RETOPOVIEW_OT_toggle_mode,
        RETOPOVIEW_OT_remove_group,
    )

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Object.rv_enabled = BoolProperty()
    bpy.types.Object.rv_backface_culling = BoolProperty()
    bpy.types.Object.rv_use_x_mirror = BoolProperty()
    bpy.types.Object.rv_show_wire = BoolProperty()
    bpy.types.Object.rv_show_poles = BoolProperty()

    bpy.types.Object.rv_index = IntProperty()
    bpy.types.Object.rv_group_idx_counter = IntProperty(default=1)

    bpy.types.Object.rv_groups = CollectionProperty(type=RETOPOVIEW_group)

    bpy.types.Object.rv_groups_alpha = FloatProperty(default=1.0, max=1.0, min=0.0)
    bpy.types.Object.rv_poles_size = FloatProperty(default=1.0, max=2.0, min=0.0)

    bpy.types.Object.rv_poles_color = FloatVectorProperty(name="Poles Color", subtype='COLOR', default=[1.0, 1.0, 1.0], min=0.0, max=1.0)

    ui_register()  # Register UI components

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('wm.call_menu_pie', 'F', 'PRESS', ctrl=False, shift=True, alt=False)
    kmi.properties.name = "RETOPOVIEW_MT_rv_pie_menu"

    addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    del bpy.types.Object.rv_poles_color
    del bpy.types.Object.rv_poles_size
    del bpy.types.Object.rv_groups_alpha
    del bpy.types.Object.rv_groups
    del bpy.types.Object.rv_group_idx_counter
    del bpy.types.Object.rv_index
    del bpy.types.Object.rv_show_poles
    del bpy.types.Object.rv_show_wire
    del bpy.types.Object.rv_use_x_mirror
    del bpy.types.Object.rv_backface_culling
    del bpy.types.Object.rv_enabled

    classes = (
        RETOPOVIEW_OT_overlay,
        RETOPOVIEW_OT_add_group,
        RETOPOVIEW_OT_handle_face_selection,
        RETOPOVIEW_OT_find_parent_group,
        RETOPOVIEW_OT_move_group,
        RETOPOVIEW_OT_change_selection_group_id,
        RETOPOVIEW_OT_toggle_mode,
        RETOPOVIEW_OT_remove_group,
    )

    for c in classes:
        bpy.utils.unregister_class(c)

    bpy.utils.unregister_class(RETOPOVIEW_group)
    ui_unregister()  # Unregister UI components

if __name__ == "__main__":
    register()