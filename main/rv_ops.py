import bpy
import bmesh
import numpy as np
import gpu
from bpy.props import StringProperty, FloatVectorProperty, BoolProperty, EnumProperty, CollectionProperty, IntProperty
from bpy.types import Operator, PropertyGroup
from gpu_extras.batch import batch_for_shader
from .rv_shaders import vertex_shader, fragment_shader

class RETOPOVIEW_OT_overlay(Operator):
    bl_idname = "retopoview.overlay"
    bl_label = "Retopoview face overlay operator"
    bl_description = "Draw RetopoView face overlay"

    def get_smallest_vector_dimension(self, vector):
        return min(vector)

    def prep_wireframe_batch(self, shader, mesh, obj, vert_idx_cache, edge_indices):
        coords = np.empty((len(mesh.vertices), 3), dtype=np.float32)
        mesh.vertices.foreach_get("co", np.reshape(coords, len(mesh.vertices) * 3))

        # Using numpy operations for better performance
        coords += np.array([v.normal * 0.0035 for v in mesh.vertices])

        wireframe_colors = np.zeros((len(mesh.vertices), 4), dtype=np.float32)
        for v_idx in vert_idx_cache:
            wireframe_colors[v_idx] = (0, 0, 0, obj.rv_groups_alpha)

        return batch_for_shader(shader, 'LINES', {"position": coords, "color": wireframe_colors}, indices=edge_indices)

    def prep_pole_batch(self, shader, mesh, obj):
        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.normal_update()

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        retopoViewGroupLayer = bm.faces.layers.int.get("RetopoViewGroupLayer")

        pole_verts = [
            vert for vert in bm.verts
            if sum(1 for edge in vert.link_edges if any(face[retopoViewGroupLayer] == obj.rv_groups[obj.rv_index].group_id for face in edge.link_faces)) >= 2
        ]

        if not pole_verts:
            return None

        pole_coords = []
        pole_indices = []
        smallest_dimension = self.get_smallest_vector_dimension(obj.dimensions)
        pole_size = smallest_dimension * 0.5 * obj.rv_poles_size

        for vert in pole_verts:
            pole_coords.extend([vert.co, vert.co + vert.normal * pole_size])
            pole_indices.append([len(pole_coords) - 2, len(pole_coords) - 1])

        pole_color = (obj.rv_poles_color.r, obj.rv_poles_color.g, obj.rv_poles_color.b, 1)
        pole_colors = [pole_color] * len(pole_coords)

        return batch_for_shader(shader, 'LINES', {"position": pole_coords, "color": pole_colors}, indices=pole_indices)

    def draw_overlay(self, context, depsgraph, obj):
        try:
            if not obj or not obj.rv_enabled or not obj.rv_groups:
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
        group_dict = {group.group_id: group.color for group in obj.rv_groups}

        for triangle in mesh.loop_triangles:
            if mesh.polygons[triangle.polygon_index].hide and obj.mode == 'EDIT':
                continue

            group_color = (1, 1, 1, 0)
            triangle_parent_poly_group_id = retopoViewGroupLayer.data[triangle.polygon_index].value

            if triangle_parent_poly_group_id in group_dict:
                group_color = (*group_dict[triangle_parent_poly_group_id][:3], 0.5)
                if obj.rv_show_wire:
                    parent_poly = mesh.polygons[triangle.polygon_index]
                    edge_indices.extend(parent_poly.edge_keys)
                    vert_idx_cache.update(triangle.vertices)

            verts.extend([mesh.vertices[v_idx].co for v_idx in triangle.vertices])
            colors.extend([group_color] * 3)
            triangle_indices.append([idx, idx + 1, idx + 2])
            idx += 3

        batch = batch_for_shader(shader, 'TRIS', {"position": verts, "color": colors}, indices=triangle_indices)

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

classes = (
    RETOPOVIEW_OT_overlay,
)