import bpy
from mathutils import Matrix
import numpy as np
from math import pi
from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_vecs, set_vals
from smorgasbord.common.transf import transf_vecs


pihalf = pi * 0.5

# Transforms the object's data so that the object does not end up
# mirrored in Unity.
mat = Matrix(((0, -1, 0, 0),
              (0,  0, 1, 0),
              (1,  0, 0, 0),
              (0,  0, 0, 1)))

# Rotates the object so that after 'posmat' sets its location, it ends
# up with a (90, 0, 0) rotation vector.
met = Matrix(((-1, 0,  0, 0),
              (0,  0,  1, 0),
              (0,  1,  0, 0),
              (0,  0,  0, 1)))

# posmat @ met
# posmet = Matrix(((1, 0,  0, 0),
#               (0, 0, -1, 0),
#               (0, 1,  0, 0),
#               (0, 0,  0, 1)))

# Places the object so that in Unity it ends up in the same place as in
# Blender. It a rotation of 180 degrees around z.
posmat = Matrix(((-1,  0, 0, 0),
                 ( 0, -1, 0, 0),
                 ( 0,  0, 1, 0),
                 ( 0,  0, 0, 1)))


@register
class PrepareExportToUnity(bpy.types.Operator):
    bl_idname = "transform.prepare_export_to_unity"
    bl_label = "Prepare Export to Unity"
    bl_description = (
        "Set rotation and scale to match object transform in "
        "the Unity game engine. Destructive. Fails on linked data."
        )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_transform_object]

    invert: bpy.props.BoolProperty(
        name="Invert",
        description=\
            "",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        if self.invert:
            mad = mat.inverted()
            med = met.inverted()
            posmad = posmat.inverted()
        else:
            mad = mat
            med = met
            posmad = posmat
        datas = {None}
        arms = []
        obs = sorted(context.selected_editable_objects, key=get_lvl)
        for o in obs:
            data = o.data
            if data not in datas:
                data.transform(mad)
                datas.add(data)
                if o.type == 'MESH':
                    data.flip_normals()
                if o.type == 'ARMATURE':
                    arms.append(o)
            o.matrix_world = posmad @ o.matrix_world @ med

        for o in arms:
            bpy.ops.object.mode_set(
                {'active_object': o}, mode='EDIT')
            for b in o.data.edit_bones:
                b.roll -= pihalf
            bpy.ops.object.mode_set(mode='OBJECT')

        # context.view_layer.update()
        return {'FINISHED'}


def get_lvl(ob):
    lvl = -1
    while ob:
        ob = ob.parent
        lvl += 1
    return lvl


if __name__ == "__main__":
    register()
