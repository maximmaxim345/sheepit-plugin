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
import threading
from . import sheepit
import time


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
        # test if logged in
        preferences = context.preferences.addons[__package__].preferences
        if not preferences.logged_in:
            return False
        # test if renderer is supported
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
        # test if allready uploading
        if 'sheepit' in bpy.context.window_manager and \
                'upload_active' in bpy.context.window_manager['sheepit']:
            return not bpy.context.window_manager['sheepit']['upload_active']
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            # do nothing if thread is still runing
            if self.thread.is_alive():
                bpy.context.window_manager['sheepit']['progress'] = self.progress
                bpy.context.window_manager['sheepit']['upload_status'] = self.status
                context.area.tag_redraw()
                return {'PASS_THROUGH'}

            # test if error occurred
            if self.error or self.error_at:
                # login error:
                if self.error_at == "login" and self.error == "Please Log in":
                    preferences = context.preferences.addons[__package__].preferences
                    preferences.logged_in = False
                    preferences.cookies = ""
                    preferences.username = ""
                self.report({'ERROR'}, f"{self.error_at}: {self.error}")
                bpy.context.window_manager['sheepit']['upload_status'] = "Upload failed!"
                self.cancel(context)
                return {'CANCELLED'}

            bpy.context.window_manager['sheepit']['upload_status'] = "Project uploaded!"
            self.cancel(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        # prepare cookies
        preferences = context.preferences.addons[__package__].preferences
        self.cookies = json.loads(preferences.cookies)

        # prepare variables
        self.animation = context.scene.sheepit_properties.type == 'animation'
        self.amd = False
        self.nvidia = False
        self.cpu = False
        if bpy.context.scene.render.engine == 'CYCLES':
            self.cpu = context.scene.sheepit_properties.cpu
            self.amd = context.scene.sheepit_properties.opencl
            self.nvidia = context.scene.sheepit_properties.cuda
        else:
            self.amd = context.scene.sheepit_properties.amd
            self.nvidia = context.scene.sheepit_properties.nvidia
        self.public = context.scene.sheepit_properties.public
        self.mp4 = context.scene.sheepit_properties.mp4
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.frame_step = context.scene.frame_step
        self.frame_current = context.scene.frame_current
        self.anim_split = context.scene.sheepit_properties.anim_split

        if 'sheepit' not in bpy.context.window_manager:
            bpy.context.window_manager['sheepit'] = dict()
        bpy.context.window_manager['sheepit']['upload_active'] = True
        bpy.context.window_manager['sheepit']['upload_status'] = ""
        self.status = ""
        bpy.context.window_manager['sheepit']['progress'] = 0
        self.progress = 0

        self.thread = threading.Thread(target=self.send_project)
        self.thread.start()

        self.upload_thread = threading.Thread(target=self.update_progress)
        self.uploading = True

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def send_project(self):
        # create error variables
        self.error = ""
        self.error_at = ""

        session = sheepit.Sheepit()

        # import cookies
        session.import_session(self.cookies)

        self.status = "Testing connection"

        # test if logged in
        try:
            if not session.is_logged_in():
                self.error = "Please Log in"
                self.error_at = "login"
                return
        except sheepit.NetworkException as e:
            self.error = str(e)
            self.error_at = "login"
            return
        self.progress = 5

        self.status = "Getting Token"

        # request a upload token from the SheepIt server
        token = ""
        try:
            token = session.request_upload_token()
        except sheepit.NetworkException as e:
            self.error = str(e)
            self.error_at = "token"
            return
        except sheepit.UploadException as e:
            self.error = str(e)
            self.error_at = "token"
            return
        self.progress = 10

        self.status = "Uploading File"

        self.token = token
        self.upload_thread.start()

        # upload the file
        try:
            session.upload_file(token, bpy.data.filepath)
        except sheepit.NetworkException as e:
            self.error = str(e)
            self.error_at = "upload"
            self.uploading = False
            return
        self.uploading = False
        if self.upload_thread.isAlive():
            self.upload_thread.join()
        self.progress = 95

        self.status = "Adding Project"
        try:
            session.add_job(token,
                            animation=self.animation,
                            cpu=self.cpu,
                            cuda=self.nvidia,
                            opencl=self.amd,
                            public=self.public,
                            mp4=self.mp4,
                            anim_start_frame=self.frame_start,
                            anim_end_frame=self.frame_end,
                            anim_step_frame=self.frame_step,
                            still_frame=self.frame_current,
                            max_ram="",
                            split=self.anim_split)
        except sheepit.NetworkException as e:
            self.error = str(e)
            self.error_at = "add project"
        self.progress = 100
        return

    def update_progress(self):
        session = sheepit.Sheepit()

        # import cookies
        session.import_session(self.cookies)
        while self.uploading:
            time.sleep(1)
            p = session.get_upload_progress(self.token)
            if p:
                self.progress = int(10+(p*85))

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        bpy.context.window_manager['sheepit']['upload_active'] = False
        del bpy.context.window_manager['sheepit']['progress']
        self.uploading = False
        if self.upload_thread.isAlive():
            self.upload_thread.join()
        if self.thread.isAlive():
            self.thread.join()
        context.area.tag_redraw()


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

        context.area.tag_redraw()
        return {'FINISHED'}


class SHEEPIT_OT_refresh_profile(bpy.types.Operator):
    bl_idname = "sheepit.refresh_profile"
    bl_label = "Refresh"

    @classmethod
    def poll(cls, context):
        # test if logged in
        preferences = context.preferences.addons[__package__].preferences
        if not preferences.logged_in:
            return False
        # test if allready refreshing
        if 'sheepit' in bpy.context.window_manager and \
                'refresh_active' in bpy.context.window_manager['sheepit']:
            return not bpy.context.window_manager['sheepit']['refresh_active']
        return True

    def modal(self, context, event):
        if event.type == 'TIMER':
            # do nothing if thread is still runing
            if self.thread.is_alive():
                return {'PASS_THROUGH'}

            # test if error occurred
            if type(self.profile) is sheepit.NetworkException:
                self.report({'ERROR'}, str(self.profile))
                self.cancel(context)
                return {'CANCELLED'}

            # test if logged in
            if not self.profile['Points']:
                self.report({'ERROR'}, "Please Log in")
                preferences.logged_in = False
                preferences.cookies = ""
                preferences.username = ""
                self.cancel(context)
                return {'CANCELLED'}

            # save the profile information to the window manager
            bpy.context.window_manager['sheepit']['profile'] = self.profile
            self.cancel(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        preferences = context.preferences.addons[__package__].preferences
        self.cookies = json.loads(preferences.cookies)

        self.thread = threading.Thread(target=self.request_profile)
        self.thread.start()

        if 'sheepit' not in bpy.context.window_manager:
            bpy.context.window_manager['sheepit'] = dict()
        if 'profile' not in bpy.context.window_manager['sheepit']:
            bpy.context.window_manager['sheepit']['profile'] = dict()
        bpy.context.window_manager['sheepit']['refresh_active'] = True

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        bpy.context.window_manager['sheepit']['refresh_active'] = False
        context.area.tag_redraw()

    def request_profile(self):
        session = sheepit.Sheepit()

        # import cookies
        session.import_session(self.cookies)

        try:
            self.profile = session.get_profile_information()
        except sheepit.NetworkException as e:
            self.profile = e


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

        context.area.tag_redraw()
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
