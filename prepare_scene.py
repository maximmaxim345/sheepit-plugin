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


def main():
    had_error = False
    error_text = ""
    try:
        # Go to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Select all
        bpy.ops.object.select_all(action="SELECT")
        # Make all linked models local
        bpy.ops.object.make_local(type='ALL')
        # Purge all (reload file because orphans_purge is not working)
        bpy.ops.wm.save_as_mainfile(compress=False)
        for i in range(3):
            bpy.ops.wm.revert_mainfile()
        # Pack all Textures
        bpy.ops.file.pack_all()
        # And save
        bpy.ops.wm.save_as_mainfile(compress=True)

    except Exception as e:
        error_text = e
        had_error = True
    # Generate Log file
    blend_file = bpy.data.filepath
    with open(f"{blend_file}.log", "w") as f:
        f.write("ERR" if had_error else "OK")
        if had_error:
            # write Error
            f.write(f"<->{error_text}")


if __name__ == "__main__":
    main()
