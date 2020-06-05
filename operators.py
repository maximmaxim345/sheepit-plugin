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
import os
import json
from . import sheepit


def register():
    bpy.utils.register_class(SHEEPIT_OT_send_project)
    bpy.utils.register_class(SHEEPIT_OT_login)
    bpy.utils.register_class(SHEEPIT_OT_logout)
    bpy.utils.register_class(SHEEPIT_OT_create_accout)
    bpy.utils.register_class(SHEEPIT_OT_refresh_profile)


def unregister():
    bpy.utils.unregister_class(SHEEPIT_OT_send_project)
    bpy.utils.unregister_class(SHEEPIT_OT_login)
    bpy.utils.unregister_class(SHEEPIT_OT_logout)
    bpy.utils.unregister_class(SHEEPIT_OT_create_accout)
    bpy.utils.unregister_class(SHEEPIT_OT_refresh_profile)


class SHEEPIT_OT_send_project(bpy.types.Operator):
    """ Send the current project to the Renderfarm """
    bl_idname = "sheepit.send_project"
    bl_label = "Send to SheepIt!"
    @classmethod
    def poll(cls, context):
        supported_renderers = {'CYCLES', 'BLENDER_EEVEE'}
        engine = bpy.context.scene.render.engine
        if engine not in supported_renderers:
            return False
        # Test if at least one device is selected
        if engine == 'CYCLES':
            if not (context.scene.sheepit_properties.cpu or
                    context.scene.sheepit_properties.cuda or
                    context.scene.sheepit_properties.opencl):
                return False
        else:
            if not (context.scene.sheepit_properties.nvidia or
                    context.scene.sheepit_properties.amd):
                return False
        return True

    def execute(self, context):
        session = sheepit.Sheepit()

        # import cookies
        session.import_session(json.loads(
            context.preferences.addons[__package__].preferences.cookies))

        # test if logged in
        try:
            if not session.is_logged_in():
                self.report({'ERROR'}, "Please Log in")
                preferences = context.preferences.addons[__package__].preferences
                preferences.logged_in = False
                preferences.cookies = ""
                preferences.username = ""
                return {'CANCELLED'}
        except sheepit.NetworkException as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        # request a upload token from the SheepIt server
        token = ""
        try:
            token = session.request_upload_token()
        except sheepit.NetworkException as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except sheepit.UploadException as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        # upload the file
        try:
            session.upload_file(token, bpy.data.filepath)
        except sheepit.NetworkException as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        animation = context.scene.sheepit_properties.type == 'animation'
        # and add it with all selected settings
        amd = False
        nvidia = False
        cpu = False
        if bpy.context.scene.render.engine == 'CYCLES':
            cpu = context.scene.sheepit_properties.cpu
            amd = context.scene.sheepit_properties.opencl
            nvidia = context.scene.sheepit_properties.cuda
        else:
            amd = context.scene.sheepit_properties.amd
            nvidia = context.scene.sheepit_properties.nvidia
        try:
            session.add_job(token,
                            animation=animation,
                            cpu=cpu,
                            cuda=nvidia,
                            opencl=amd,
                            public=context.scene.sheepit_properties.public,
                            mp4=context.scene.sheepit_properties.mp4,
                            anim_start_frame=context.scene.frame_start,
                            anim_end_frame=context.scene.frame_end,
                            anim_step_frame=context.scene.frame_step,
                            still_frame=context.scene.frame_current,
                            max_ram="",
                            split=context.scene.sheepit_properties.anim_split)
        except sheepit.NetworkException as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}


class SHEEPIT_OT_logout(bpy.types.Operator):
    bl_idname = "sheepit.logout"
    bl_label = "Logout"

    @classmethod
    def poll(cls, context):
        # test if logged in
        preferences = context.preferences.addons[__package__].preferences
        return preferences.logged_in

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        session = sheepit.Sheepit()

        # import cookies
        session.import_session(json.loads(preferences.cookies))
        try:
            session.logout()
        except sheepit.NetworkException as e:
            self.report({'INFO'}, str(e))

        # delete preferences
        preferences.logged_in = False
        preferences.cookies = ""
        preferences.username = ""
        return {'FINISHED'}


class SHEEPIT_OT_refresh_profile(bpy.types.Operator):
    bl_idname = "sheepit.refresh_profile"
    bl_label = "Refresh"

    @classmethod
    def poll(cls, context):
        # test if logged in
        preferences = context.preferences.addons[__package__].preferences
        return preferences.logged_in

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        session = sheepit.Sheepit()

        # import cookies
        session.import_session(json.loads(preferences.cookies))

        profile = None
        try:
            profile = session.get_profile_information()
        except sheepit.NetworkException as e:
            self.report({'INFO'}, str(e))
            return {'CANCELLED'}

        # test if logged in
        if not profile['Points']:
            self.report({'ERROR'}, "Please Log in")
            preferences.logged_in = False
            preferences.cookies = ""
            preferences.username = ""

        # save the profile information to the window manager
        if 'sheepit' not in bpy.context.window_manager:
            bpy.context.window_manager['sheepit'] = dict()
        if 'profile' not in bpy.context.window_manager['sheepit']:
            bpy.context.window_manager['sheepit']['profile'] = dict()
        bpy.context.window_manager['sheepit']['profile'] = profile
        return {'FINISHED'}


class SHEEPIT_OT_login(bpy.types.Operator):
    """ Login to SheepIt! """
    bl_idname = "sheepit.login"
    bl_label = "Login"

    username: bpy.props.StringProperty(name="Username", maxlen=64)
    password: bpy.props.StringProperty(
        name="Password", subtype='PASSWORD', maxlen=64)

    @classmethod
    def poll(cls, context):
        preferences = context.preferences.addons[__package__].preferences
        return not preferences.logged_in

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        # Login with the provided Username and Password
        session = sheepit.Sheepit()
        error = False
        try:
            session.login(username=self.username, password=self.password)
        except sheepit.NetworkException as e:
            self.report({'ERROR'}, str(e))
            error = True
        except sheepit.LoginException as e:
            self.report({'ERROR'}, str(e))
            error = True
        if error:
            # Delete Password
            self.password = ""
            return {'CANCELLED'}

        # Generate preferences
        cookies = json.dumps(session.export_session())

        # Save
        preferences = context.preferences.addons[__package__].preferences
        preferences.cookies = cookies
        preferences.username = self.username
        preferences.logged_in = True

        # Delete Password and Username
        self.password = ""
        self.username = ""

        return {'FINISHED'}


class SHEEPIT_OT_create_accout(bpy.types.Operator):
    """ Open the Create Account page """
    bl_idname = "sheepit.create_account"
    bl_label = "Create a SheepIt! Account"
    bl_options = {'INTERNAL'}
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.wm.url_open(
            url="https://www.sheepit-renderfarm.com/account.php?mode=register")
        return {'FINISHED'}
