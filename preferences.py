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


import bpy


def register():
    bpy.utils.register_class(SheepItPreferences)


def unregister():
    bpy.utils.unregister_class(SheepItPreferences)


class SheepItPreferences(bpy.types.AddonPreferences):
    """ Persistant properties for this Addon
        Currently only login information is stored here. """
    bl_idname = __package__

    # cookies are stored as a serialized dict
    cookies: bpy.props.StringProperty(default="")
    username: bpy.props.StringProperty(default="")
    logged_in: bpy.props.BoolProperty(default=False)
