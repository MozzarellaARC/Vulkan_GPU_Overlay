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

import bpy
from bpy.types import UIList, Panel, Menu

class RETOPOVIEW_UL_group_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "color", text="", emboss=True, icon='COLOR')
        layout.prop(item, "name", text="", emboss=False)


class RETOPOVIEW_PT_rv_tool_menu(Panel):
    bl_label = "Topology Groups"
    bl_idname = "RETOPOVIEW_PT_rv_tool_menu"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'RetopoView'
    bl_context = 'data'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is None or obj.type != 'MESH':
            layout.label(text='No valid object')
            return

        if len(obj.rv_groups) > 0:
            toggle_text = 'Show' if not obj.rv_enabled else 'Hide'
            toggle_icon = 'HIDE_OFF' if obj.rv_enabled else 'HIDE_ON'

            enable_box = layout.box()
            enable_container = enable_box.row()
            enable_container.operator('retopoview.toggle_mode', text=toggle_text, icon=toggle_icon)
            enable_container.scale_y = 1.5

        layout.separator(factor=0.1)

        list_row = layout.row()
        list_row.template_list("RETOPOVIEW_UL_group_list", "", obj, "rv_groups", obj, "rv_index")

        list_controls = list_row.column(align=True)
        list_controls.operator("retopoview.add_group", text='', icon='ADD')
        list_controls.operator("retopoview.remove_group", text='', icon='REMOVE')

        list_controls.separator()

        list_controls.operator("retopoview.move_group", text='', icon='TRIA_UP').direction = 'UP'
        list_controls.operator("retopoview.move_group", text='', icon='TRIA_DOWN').direction = 'DOWN'

        layout.separator(factor=0.1)

        if len(obj.rv_groups) <= 0:
            return

        active_box = layout.box()

        active_content_row = active_box.row(align=True)
        active_content_row.alignment = 'LEFT'
        active_content_row.label(text='Active: ')

        group_subrow = active_content_row.row(align=True)

        group_subrow.prop(obj.rv_groups[obj.rv_index], 'color', icon_only=True, icon='COLOR')
        group_subrow.label(text=obj.rv_groups[obj.rv_index].name)

        box = layout.box()
        box.enabled = obj.mode == 'EDIT' and obj.rv_enabled
        edit_column = box.column()

        edit_column.separator(factor=0.5)

        assign_row = edit_column.row(align=True)
        assign_row.operator("retopoview.change_selection_group_id", text='Assign').remove = False
        assign_row.operator("retopoview.change_selection_group_id", text='Remove').remove = True

        edit_column.separator(factor=0.1)

        select_row = edit_column.row(align=True)
        select_row.operator("retopoview.handle_face_selection", text='Select').deselect = False
        select_row.operator("retopoview.handle_face_selection", text='Deselect').deselect = True

        edit_column.separator(factor=0.1)

        parent_finder_row = edit_column.row(align=True)
        parent_finder_row.operator("retopoview.find_parent_group", text='Find Parent Group')

        edit_column.separator(factor=0.5)

        layout.separator(factor=0.1)

        quick_access_column = layout.column()
        quick_access_column.prop(obj, 'rv_groups_alpha', text='Overlay Opacity', slider=True)
        quick_access_column.separator(factor=0.2)
        quick_access_column.prop(obj, 'rv_backface_culling', text='Backface Culling')
        quick_access_column.prop(obj, "rv_show_wire", text="Show Wireframe")
        quick_access_column.prop(obj, 'show_in_front', text='Object In Front')
        quick_access_column.prop(obj, 'rv_use_x_mirror', text='X Mirror')
        quick_access_column.prop(obj, 'rv_show_poles', text='Show Poles')

        poles_settings_column = layout.column()

        if obj.rv_show_poles:
            color_row = poles_settings_column.row()
            color_row.prop(obj, 'rv_poles_color', text='Poles Color', icon='COLOR', emboss=True)
            poles_settings_column.separator(factor=0.1)
            poles_settings_column.prop(obj, 'rv_poles_size', text='Poles Size', slider=True)


def register():
    bpy.utils.register_class(RETOPOVIEW_UL_group_list)
    bpy.utils.register_class(RETOPOVIEW_PT_rv_tool_menu)


def unregister():
    bpy.utils.unregister_class(RETOPOVIEW_UL_group_list)
    bpy.utils.unregister_class(RETOPOVIEW_PT_rv_tool_menu)

classes = (
    RETOPOVIEW_UL_group_list,
    RETOPOVIEW_PT_rv_tool_menu
)
