import bpy
from mathutils import Vector
import numpy as np
from smorgasbord.common.decorate import register
from smorgasbord.common.io import (
    get_vecs,
    set_vals,
)


@register
class SelectFlippedFaces(bpy.types.Operator):
    bl_idname = "mesh.select_flipped_faces"
    bl_label = "Select Flipped Faces"
    bl_description = "Select polygons facing away from the viewport"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obs_in_editmode = context.objects_in_mode_unique_data
        bpy.ops.object.mode_set(mode='OBJECT')
        try:
            for o in obs_in_editmode:
                viewdir = Vector((0, 0, -1))

                for area in context.screen.areas:
                    if area.type != 'VIEW_3D':
                        continue

                    r3d = area.spaces[0].region_3d
                    if r3d is None:
                        continue

                    viewdir.rotate(r3d.view_rotation)
                    break

                # For every face normal, calculate the dot product
                # with the view direction
                nrmls = get_vecs(o.data.polygons, attr='normal')
                dotprdcs = np.dot(nrmls, np.array(viewdir))

                # Select each face with dot product entry > 0
                selflags = np.greater(dotprdcs, 0)
                o.data.polygons.foreach_set('select', selflags)
        finally:
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


if __name__ == "__main__":
    register()
