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

from .main.rv_ops import RenderVertex
from .main.rv_shaders import vertex_shader_source, fragment_shader_source
from .main.rv_ui import RenderUI

__all__ = [
    "RenderVertex",
    "vertex_shader_source",
    "fragment_shader_source",
    "RenderUI"
]

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
        if hasattr(bpy.types, c.bl_idname):
            bpy.utils.unregister_class(c)
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

def unregister():
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
        if hasattr(bpy.types, c.bl_idname):
            bpy.utils.unregister_class(c)

    bpy.utils.unregister_class(RETOPOVIEW_group)
    ui_unregister()  # Unregister UI components

if __name__ == "__main__":
    register()
