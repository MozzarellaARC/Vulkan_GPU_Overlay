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

def set_up_marker_data_layer(context):
    obj = context.object

    object_mode = obj.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data

    if 'RetopoViewGroupLayer' not in mesh.attributes:
        mesh.attributes.new(name='RetopoViewGroupLayer', type='INT', domain='FACE')

    bpy.ops.object.mode_set(mode=object_mode)