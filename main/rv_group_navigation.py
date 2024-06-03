import bpy
import bmesh
import random
from bpy.props import StringProperty, FloatVectorProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from mathutils import Color

# Import utility functions from rv_utils.py
from .rv_utils import set_up_marker_data_layer

class RETOPOVIEW_OT_add_group(Operator):
    bl_idname = "retopoview.add_group"
    bl_label = "Add New Group"
    bl_description = "Add new group"

    group_name: StringProperty(name="Group Name", default="New Group")
    group_color: FloatVectorProperty(name="Group Color", subtype='COLOR', default=(1, 1, 1), min=0.0, max=1.0)

    def get_random_color(self):
        color = Color()
        color.hsv = (random.random(), 1, 1)
        return color

    def execute(self, context):
        obj = context.object

        group = obj.rv_groups.add()

        group.color = self.group_color
        group.group_id = obj.rv_group_idx_counter
        group.name = self.group_name

        obj.rv_group_idx_counter += 1

        obj.rv_index = len(obj.rv_groups) - 1

        if len(obj.rv_groups) == 1:
            obj.rv_enabled = True
            set_up_marker_data_layer(context)  # Pass only context here
            obj.data.update()
            bpy.ops.retopoview.overlay('INVOKE_DEFAULT')

        return {'FINISHED'}

    def invoke(self, context, event):
        self.group_color = self.get_random_color()
        return context.window_manager.invoke_props_dialog(self)

class RETOPOVIEW_OT_handle_face_selection(Operator):
    bl_idname = "retopoview.handle_face_selection"
    bl_label = "Select/Deselect Faces"
    bl_description = "Select/Deselect Faces assigned to a group"

    deselect: BoolProperty()

    def execute(self, context):
        obj = context.object

        if obj.mode != 'EDIT' or len(obj.rv_groups) <= 0:
            return {'FINISHED'}

        group_id = obj.rv_groups[obj.rv_index].group_id

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        retopoViewGroupLayer = bm.faces.layers.int["RetopoViewGroupLayer"]

        for face in bm.faces:
            if face[retopoViewGroupLayer] == group_id:
                face.select = not self.deselect

        bmesh.update_edit_mesh(mesh)
        mesh.update()

        return {'FINISHED'}

class RETOPOVIEW_OT_find_parent_group(Operator):
    bl_idname = "retopoview.find_parent_group"
    bl_label = "Find Parent Group"
    bl_description = "Find parent group of selected faces, returns the first found group"

    def execute(self, context):
        obj = context.object

        if obj.mode != 'EDIT' or len(obj.rv_groups) <= 0:
            return {'FINISHED'}

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        retopoViewGroupLayer = bm.faces.layers.int["RetopoViewGroupLayer"]

        for face in bm.faces:
            if face.select and face[retopoViewGroupLayer] != 0:
                for idx, group in enumerate(obj.rv_groups):
                    if group.group_id == face[retopoViewGroupLayer]:
                        obj.rv_index = idx
                        return {'FINISHED'}

        return {'FINISHED'}

class RETOPOVIEW_OT_move_group(Operator):
    bl_idname = "retopoview.move_group"
    bl_label = "Move Group"
    bl_description = "Change group position in the list"

    direction: EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", "")
        )
    )

    def move_group(self, offset, context, active_index, obj):
        obj.rv_groups.move(active_index, active_index + offset)
        obj.rv_index += offset

    def execute(self, context):
        obj = context.object

        active_index = obj.rv_index
        max_allowed_index = len(obj.rv_groups) - 1

        if max_allowed_index <= 0:
            return {'FINISHED'}

        if self.direction == 'UP' and active_index > 0:
            self.move_group(-1, context, active_index, obj)

        if self.direction == 'DOWN' and active_index < max_allowed_index:
            self.move_group(1, context, active_index, obj)

        return {'FINISHED'}

class RETOPOVIEW_OT_change_selection_group_id(Operator):
    bl_idname = "retopoview.change_selection_group_id"
    bl_label = "Assign Selection to Group"
    bl_description = "Assign selected faces to group"

    remove: BoolProperty()

    def execute(self, context):
        obj = context.object

        if len(obj.rv_groups) <= 0:
            return {'FINISHED'}

        group_id = obj.rv_groups[obj.rv_index].group_id

        if self.remove:
            group_id = 0

        object_mode = obj.mode

        if object_mode != "EDIT":
            bpy.ops.object.mode_set(mode='EDIT')

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        retopoViewGroupLayer = bm.faces.layers.int["RetopoViewGroupLayer"]

        if obj.rv_use_x_mirror:
            current_selection = set()
            for face in bm.faces:
                if face.select:
                    current_selection.add(face)

            bpy.ops.mesh.select_mirror(axis={'X'}, extend=True)

        for face in bm.faces:
            if face.select:
                face[retopoViewGroupLayer] = group_id

                if obj.rv_use_x_mirror and face not in current_selection:
                    face.select = False

        bmesh.update_edit_mesh(mesh)
        mesh.update()

        if object_mode != "EDIT":
            bpy.ops.object.mode_set(mode=object_mode)

        return {'FINISHED'}

class RETOPOVIEW_OT_toggle_mode(Operator):
    bl_idname = "retopoview.toggle_mode"
    bl_label = "Toggle overlay mode"
    bl_description = "Toggle overlay mode"

    def invoke(self, context, event):
        obj = context.object
        obj.rv_enabled = not obj.rv_enabled

        if obj.rv_enabled:
            set_up_marker_data_layer(context)  # Pass only context here
            obj.data.update()
            bpy.ops.retopoview.overlay('INVOKE_DEFAULT')

        return {'FINISHED'}

class RETOPOVIEW_OT_remove_group(Operator):
    bl_idname = "retopoview.remove_group"
    bl_label = "Remove Group"
    bl_description = "Remove group"

    def execute(self, context):
        obj = context.object

        remove_id = obj.rv_index
        group_id = obj.rv_groups[remove_id].group_id

        object_mode = obj.mode
        bpy.ops.object.mode_set(mode='EDIT')

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        retopoViewGroupLayer = bm.faces.layers.int["RetopoViewGroupLayer"]

        for face in bm.faces:
            if face[retopoViewGroupLayer] == group_id:
                face[retopoViewGroupLayer] = 0

        bmesh.update_edit_mesh(mesh)
        mesh.update()

        bpy.ops.object.mode_set(mode=object_mode)

        obj.rv_groups.remove(remove_id)
        obj.rv_index = obj.rv_index - 1 if obj.rv_index >= 1 else 0

        if len(obj.rv_groups) == 0:
            obj.rv_enabled = False

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event) if len(context.object.rv_groups) != 0 else {'FINISHED'}

classes = (
    RETOPOVIEW_OT_add_group, 
    RETOPOVIEW_OT_handle_face_selection,
    RETOPOVIEW_OT_find_parent_group,
    RETOPOVIEW_OT_move_group,
    RETOPOVIEW_OT_change_selection_group_id,
    RETOPOVIEW_OT_remove_group,
    RETOPOVIEW_OT_toggle_mode
)