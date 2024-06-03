import bpy

def set_up_marker_data_layer(context):
    obj = context.object

    object_mode = obj.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data

    if 'RetopoViewGroupLayer' not in mesh.attributes:
        mesh.attributes.new(name='RetopoViewGroupLayer', type='INT', domain='FACE')

    bpy.ops.object.mode_set(mode=object_mode)