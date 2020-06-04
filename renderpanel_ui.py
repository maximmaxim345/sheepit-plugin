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
from . import sheepit


def register():
    bpy.utils.register_class(LoginPanel)
    bpy.utils.register_class(AddProjectPanel)
    bpy.utils.register_class(ProfilePanel)


def unregister():
    bpy.utils.unregister_class(LoginPanel)
    bpy.utils.unregister_class(AddProjectPanel)
    bpy.utils.unregister_class(ProfilePanel)


class SheepItRenderPanel():
    """ SheepIt panel in the Render tab """
    bl_label = "SheepIt!"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"


class LoginPanel(SheepItRenderPanel, bpy.types.Panel):
    """ Login Panel, will be hidden if allready logged in """
    bl_idname = "SHEEPIT_PT_login_panel"
    @classmethod
    def poll(cls, context):
        preferences = context.preferences.addons[__package__].preferences
        return not preferences.logged_in

    def draw(self, context):
        self.layout.operator("sheepit.login")
        self.layout.operator("sheepit.create_account")


class AddProjectPanel(SheepItRenderPanel, bpy.types.Panel):
    """ Add Project Menu in the render Panel,
        this will be disabled if not logged in """
    bl_idname = "SHEEPIT_PT_add_project"
    @classmethod
    def poll(cls, context):
        preferences = context.preferences.addons[__package__].preferences
        return preferences.logged_in

    def draw(self, context):
        supported_renderers = {'CYCLES', 'BLENDER_EEVEE'}
        if bpy.context.scene.render.engine in supported_renderers:
            # Renderable by all members
            self.layout.prop(context.scene.sheepit_properties, "public")

            # Select device
            compute_method = self.layout.row(align=True)
            if bpy.context.scene.render.engine == 'CYCLES':
                compute_method.prop(
                    context.scene.sheepit_properties, "cpu", toggle=True)
            compute_method.prop(
                context.scene.sheepit_properties, "cuda", toggle=True)
            compute_method.prop(context.scene.sheepit_properties,
                                "opencl", toggle=True)

            # Select job type (Animation or still)
            self.layout.prop(context.scene.sheepit_properties,
                             "type", expand=True)

            settings = self.layout.column(align=True)
            if context.scene.sheepit_properties.type == 'frame':
                # settings for Single Frame renders
                settings.prop(context.scene, "frame_current")
                self.layout.label(text="The frame will be split in 8x8 tiles.")
            else:
                # settings for Animations
                settings.prop(context.scene, "frame_start")
                settings.prop(context.scene, "frame_end")
                settings.prop(context.scene, "frame_step")
                settings.prop(context.scene.sheepit_properties, "mp4")

                split_frame = self.layout.row(align=True)
                split_frame.prop(context.scene.sheepit_properties,
                                 "anim_split", expand=True)
                if context.scene.sheepit_properties.anim_split != '1':
                    self.layout.label(
                        text="If you split frames, compositor and "
                        "denoising will be disabled.")

            self.layout.operator("sheepit.send_project")
            if not (context.scene.sheepit_properties.cpu or
                    context.scene.sheepit_properties.cuda or
                    context.scene.sheepit_properties.opencl):
                self.layout.label(
                    text="You need to set a compute method "
                    "before adding a project.")
        else:
            self.layout.label(
                text="SheepIt is only compatible with Eevee or Cycles")


class ProfilePanel(SheepItRenderPanel, bpy.types.Panel):
    """ Profile Panel shown under the Submit Panel
        Used for Userinfo, logout and other Profile operations """
    bl_idname = "SHEEPIT_PT_profile_panel"
    bl_parent_id = "SHEEPIT_PT_add_project"
    bl_label = "Profile"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        preferences = context.preferences.addons[__package__].preferences
        return preferences.logged_in

    def draw(self, context):
        preferences = context.preferences.addons[__package__].preferences

        self.layout.label(text=f"logged in as {preferences.username}")
        self.layout.operator("sheepit.logout")
