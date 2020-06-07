# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from . import operators, renderpanel_ui, properties, preferences


bl_info = {
    "name": "SheepIt!",
    "author": "Maxim Raznatovski",
    "description": "Upload Your Projects Directly to the SheepIt! Renderfarm",
    "blender": (2, 80, 0),
    "version": (0, 2, 0),
    "location": "Properties > Render > SheepIt! Renderfarm",
    "warning": "",
    "support": "COMMUNITY",
    "category": "Render"
}


def register():
    operators.register()
    renderpanel_ui.register()
    properties.register()
    preferences.register()


def unregister():
    operators.unregister()
    renderpanel_ui.unregister()
    properties.unregister()
    preferences.unregister()
