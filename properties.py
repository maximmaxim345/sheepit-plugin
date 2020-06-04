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
    bpy.utils.register_class(SheepItSceneProperties)
    bpy.types.Scene.sheepit_properties = bpy.props.PointerProperty(
        type=SheepItSceneProperties)


def unregister():
    bpy.utils.unregister_class(SheepItSceneProperties)


class SheepItSceneProperties(bpy.types.PropertyGroup):
    """ Scene specific properties of sheepit """
    public: bpy.props.BoolProperty(
        name="Renderable by all members",
        default=True,
        description="By default every member can render your project. "
        "If you want to restrict the access to your project do not check "
        "this box. On the project administration page you will be "
        "able to modify this setting and add specific members to renderers.")
    mp4: bpy.props.BoolProperty(
        name="Generate MP4 video",
        default=False,
        description="Generate an MP4 video of the projects, it is really "
        "ressources intensive for the server so only check it if "
        "you really need it.")

    # Cycles specific
    cpu: bpy.props.BoolProperty(
        "CPU", description="Render on CPU", default=True)
    cuda: bpy.props.BoolProperty(
        "CUDA", description="Render on Nvidia GPUs", default=False)
    opencl: bpy.props.BoolProperty(
        "OPEN-CL", description="Render on AMD GPUs", default=False)

    # Eevee specific
    nvidia: bpy.props.BoolProperty(
        "NVIDIA", description="Render on Nvidia GPUs", default=True)
    amd: bpy.props.BoolProperty(
        "AMD", description="Render on AMD GPUs", default=True)

    type: bpy.props.EnumProperty(
        items=[
            ("frame", "Single Frame", "Render only one Image"),
            ("animation", "Animation", "Render a series of frames")
        ],
        name="Render Type",
    )
    anim_split: bpy.props.EnumProperty(
        name="Split each frame in",
        description="To increase the render time allowed by frame you "
        "can split each frame in tiles. These tiles will create a "
        "chessboard to compose your final fame. "
        "You are allowed a maximum of 30 min per tile.",
        items=[
            ("1", "Full frame", "Don't split the Image"),
            ("2", "2x2", "Split the Image into 4 parts"),
            ("4", "4x4", "Split the Image into 16 parts"),
            ("5", "5x5", "Split the Image into 25 parts"),
            ("6", "6x6", "Split the Image into 36 parts"),
        ]
    )
