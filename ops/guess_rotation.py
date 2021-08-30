import bpy
import numpy as np
from mathutils import Matrix

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_vecs, set_vals
from smorgasbord.common.mat_manip import append_row_and_col


@register
class GuessRotation(bpy.types.Operator):
    bl_idname = "object.guess_rotation"
    bl_label = "Guess Rotation"
    bl_description = (
        "Try to reconstruct the rotation of every selected object"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object_apply]

    @classmethod
    def poll(cls, context):
        return bool(context.selected_editable_objects)

    def execute(self, context):
        for o in context.selected_editable_objects:
            if o.type != 'MESH':
                continue

            coords = get_vecs(o.data.vertices)

            # Reconstruct basis vectors via Singular Value Decomposition
            _, _, v = np.linalg.svd(coords)

            # Ensure basis vectors are as close to world axes as
            # possible: if a basis vector points in the opposite
            # direction, invert it
            i3 = np.identity(3)
            for i in range(3):
                if np.dot(v[i], i3[i]) < 0:
                    v[i] = -v[i]

            # Apply new basis to mesh
            set_vals(o.data.vertices, coords @ v.T)

            # Modify object rotation so object stays in the same place,
            # even with its mesh changed
            o.matrix_basis @= Matrix(append_row_and_col(v.T))
        return {'FINISHED'}
