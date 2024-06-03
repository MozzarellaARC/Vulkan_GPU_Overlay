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

vertex_shader = '''
    uniform mat4 viewProjectionMatrix;
    uniform mat4 worldMatrix;
    uniform float alpha;

    in vec3 position;
    in vec4 color;
    out vec4 fragColor;

    void main()
    {
        fragColor = vec4(color.r, color.g, color.b, color.a * alpha);
        gl_Position = viewProjectionMatrix * worldMatrix * vec4(position, 1.0f);
    }
'''

fragment_shader = '''
    in vec4 fragColor;
    out vec4 outColor;

    void main()
    {
        if (fragColor.a == 0) discard;
        outColor = fragColor;
    }
'''