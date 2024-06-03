import bpy
import bmesh
import numpy as np
import gpu
from bpy.props import StringProperty, FloatVectorProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Color
from gpu_extras.batch import batch_for_shader

# Import shaders from rv_shaders.py
from .rv_shaders import vertex_shader, fragment_shader

class RETOPOVIEW_OT_overlay(Operator):
    bl_idname = "retopoview.overlay"
    bl_label = "Retopoview face overlay operator"
    bl_description = "Draw RetopoView face overlay"

    def get_smallest_vector_dimension(self, vector):
        smallest_dimension = vector[0]

        for dimension in vector:
            if dimension < smallest_dimension:
                smallest_dimension = dimension

        return smallest_dimension

    def prep_wireframe_batch(self, shader, mesh, obj, vert_idx_cache, edge_indices):
        coords = np.empty((len(mesh.vertices), 3), 'f')
        mesh.vertices.foreach_get("co", np.reshape(coords, len(mesh.vertices) * 3))

        for c_idx, coord in enumerate(coords):
            coords[c_idx] = coord + mesh.vertices[c_idx].normal * 0.0035

        wireframe_colors = np.empty((len(mesh.vertices), 4), 'f')
        for v_idx, _ in enumerate(mesh.vertices):
            wireframe_colors[v_idx] = (0, 0, 0, obj.rv_groups_alpha) if v_idx in vert_idx_cache else (0, 0, 0, 0)

        return batch_for_shader(shader, 'LINES', {"position": coords, "color": wireframe_colors}, indices=edge_indices)

    def prep_pole_batch(self, shader, mesh, obj):
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        pole_verts = [vert for vert in bm.verts if len(vert.link_edges) > 4]
        pole_coords = []
        pole_indices = []

        pole_idx = 0
        for vert in pole_verts:
            pole_coords.append(vert.co)

            smallest_dimension = self.get_smallest_vector_dimension(obj.dimensions)
            pole_coords.append(vert.co + vert.normal * smallest_dimension * 0.5 * obj.rv_poles_size)
            pole_indices.append([pole_idx, pole_idx + 1])

            pole_idx += 2

        pole_color = (obj.rv_poles_color.r, obj.rv_poles_color.g, obj.rv_poles_color.b, 1)
        pole_colors = [pole_color for _ in pole_coords]

        return batch_for_shader(shader, 'LINES', {"position": pole_coords, "color": pole_colors}, indices=pole_indices)

    def draw_overlay(self, context, depsgraph, obj):
        try:
            if not obj or not obj.rv_enabled or len(obj.rv_groups) <= 0:
                return {'FINISHED'}
        except ReferenceError:
            return {'FINISHED'}

        obj = obj.evaluated_get(depsgraph)
        mesh = obj.to_mesh()

        mesh.calc_loop_triangles()
        shader = gpu.types.GPUShader(vertex_shader, fragment_shader)

        verts = []
        triangle_indices = []
        colors = []
        edge_indices = []
        vert_idx_cache = set()

        retopoViewGroupLayer = mesh.attributes["RetopoViewGroupLayer"]

        idx = 0
        for _, triangle in enumerate(mesh.loop_triangles):
            if mesh.polygons[triangle.polygon_index].hide and obj.mode == 'EDIT':
                continue

            group_color = (1, 1, 1, 0)
            triangle_parent_poly_group_id = retopoViewGroupLayer.data[triangle.polygon_index].value

            for group in obj.rv_groups:
                if group.group_id == triangle_parent_poly_group_id:
                    group_color = (group.color.r, group.color.g, group.color.b, 0.5)

                    if obj.rv_show_wire:
                        parent_poly = mesh.polygons[triangle.polygon_index]
                        for edge_key in parent_poly.edge_keys:
                            edge_indices.append(edge_key)

                        for i in range(3):
                            vert_idx_cache.add(triangle.vertices[i])

            for i in range(3):
                verts.append(mesh.vertices[triangle.vertices[i]].co)
                colors.append(group_color)

            triangle_indices.append([idx, idx + 1, idx + 2])
            idx = idx + 3

        batch = batch_for_shader(
            shader, 'TRIS',
            {"position": verts, "color": colors},
            indices=triangle_indices,
        )

        if obj.rv_show_wire:
            wireframe_batch = self.prep_wireframe_batch(shader, mesh, obj, vert_idx_cache, edge_indices)

        if obj.rv_show_poles:
            pole_batch = self.prep_pole_batch(shader, mesh, obj)

        if obj.rv_backface_culling:
            gpu.state.face_culling_set('BACK')

        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('ALPHA')

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D' and space.shading.type == 'WIREFRAME':
                        gpu.state.depth_test_set('ALWAYS')

        if obj.show_in_front:
            gpu.state.depth_test_set('ALWAYS')
            gpu.state.face_culling_set('BACK')

        shader.bind()
        shader.uniform_float("viewProjectionMatrix", context.region_data.perspective_matrix)
        shader.uniform_float("worldMatrix", obj.matrix_world)
        shader.uniform_float("alpha", obj.rv_groups_alpha)
        batch.draw(shader)

        gpu.state.depth_test_set('LESS_EQUAL')
        shader.uniform_float("alpha", 1)

        if obj.rv_show_wire:
            wireframe_batch.draw(shader)

        if obj.rv_show_poles and pole_batch:
            gpu.state.line_width_set(2)
            pole_batch.draw(shader)

        gpu.state.line_width_set(1)
        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')

        if obj.rv_backface_culling:
            gpu.state.face_culling_set('NONE')

    def modal(self, context, event):
        context.area.tag_redraw()

        try:
            if not self.invoked_obj.rv_enabled:
                bpy.types.SpaceView3D.draw_handler_remove(self.overlay_handler, 'WINDOW')
                return {'FINISHED'}
        except ReferenceError:
            bpy.types.SpaceView3D.draw_handler_remove(self.overlay_handler, 'WINDOW')
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        args = (context, depsgraph, context.object)

        self.invoked_obj = context.object
        self.overlay_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_overlay, args, 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
