import bpy
import numpy as np

from smorgasbord.common.io import get_scalars, get_vecs
from smorgasbord.common.transf import transf_vecs
from smorgasbord.common.decorate import register


@register
class LerpWeight(bpy.types.Operator):
    bl_idname = "object.lerp_weight"
    bl_label = "Lerp Weight"
    bl_description = \
        "Linearly interpolate the weights between two given bones"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_vertex_group,
        bpy.types.VIEW3D_MT_edit_mesh_weights
    ]
    bone1: bpy.props.StringProperty(
        name="Bone A",
        description=(
            "The bone from which the distance is interpolated. At its "
            "position a weight of one is applied."
        ),
    )
    bone2: bpy.props.StringProperty(
        name="Bone B",
        description=(
            "The bone towards which the distance is interpolated. At "
            "its position a weight of zero is applied."
        ),
    )
    bidirect: bpy.props.BoolProperty(
        name="Bidirectional",
        description=(
            "If false the calculated weight is only set in the vertex "
            "group for bone A. If true, the inverted weight is also "
            "set for bone B"
        ),
        default=True,
    )
    axes: bpy.props.BoolVectorProperty(
        name="Axes",
        description=(
            "Axes along which the bone distance is interpolated. If "
            "two axes are active, the distance is projected into the "
            "corresponding plane. If one is active, onto the line"
        ),
        default=(True, False, False),
        subtype='XYZ',
    )

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'EDIT_MESH'
            and len(context.selected_objects) > 1
            )

    def execute(self, context):
        if not self.bone1:
            # This little hack allows the user to insert the bone names
            # in the F9 panel before the operator really executes.
            return {'FINISHED'}

        selobs = context.selected_objects
        arms = [o for o in selobs if o.type == 'ARMATURE']

        if not arms:
            self.report({'ERROR_INVALID_INPUT'},
                        "Exactly one armature must be selected.")
            return {'CANCELLED'}

        arm = arms[0]
        bones = arm.data.bones
        try:
            b1 = np.array(bones[self.bone1].head)
            b2 = np.array(bones[self.bone2].head)
        except KeyError:
            self.report(
                {'ERROR_INVALID_INPUT'},
                (
                    f"Bone '{self.bone1}' or '{self.bone2}' doesn't "
                    "exist in armature '{arm.name}'"
                ),
            )
            return {'CANCELLED'}
        b1b2 = b2 - b1

        wrldmat_inv = np.array(arm.matrix_world.inverted())
        dims = np.array(self.axes)
        ndims = np.sum(dims)

        for o in selobs:
            if o.type != 'MESH':
                continue

            # Get selected vertices
            verts = o.data.vertices
            selflags = get_scalars(verts)
            pts = get_vecs(verts)[selflags]

            # Transform vertices into the armature's local coordinate
            # system
            pts = transf_vecs(
                wrldmat_inv @ np.array(o.matrix_world),
                pts,
                )
            # Calc vector from bone1 to every point and zero coordinates
            # of dimensions that are ignored.
            b1pts_proj = (pts - b1) * dims
            # Calc dot product those vectors and the vector from bone1
            # to bone2
            weights = np.dot(b1b2, b1pts_proj.T)
            # Calc reciprocal where weight is not zero. Multiply with
            # the total number of dimensions we considered.
            np.divide(ndims, weights, out=weights, where=weights != 0)

            # Get indices of selected vertices
            indcs = np.arange(len(selflags))[selflags]
            vgs = o.vertex_groups
            try:
                vg1 = vgs[self.bone1]
            except KeyError:
                self.report(
                    {'ERROR_INVALID_INPUT'},
                    (
                        f"Vertex group '{self.bone1}' does not exist on"
                        "object '{o.name}'"
                    ),
                )
                return {'CANCELLED'}
            if self.bidirect:
                try:
                    vg2 = vgs[self.bone2]
                except KeyError:
                    self.report(
                        {'ERROR_INVALID_INPUT'},
                        (
                            f"Vertex group '{self.bone2}' does not "
                            "exist on object '{o.name}'"
                        ),
                    )
                    return {'CANCELLED'}

            # The mesh doesn't update in edit mode.
            bpy.ops.object.mode_set(mode='OBJECT')
            try:
                for i, w in zip(indcs, weights):
                    # No clue why add expects a one-element list, but
                    # that's how it is.
                    # item() converts the NumPy int to a native int
                    idx = [i.item()]
                    vg1.add(idx, 1 - w, 'REPLACE')
                    if self.bidirect:
                        vg2.add(idx, w, 'REPLACE')
            finally:
                bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


if __name__ == "__main__":
    register()
