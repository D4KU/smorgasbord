import bpy
import numpy as np

from smorgasbord.common.io import get_scalars, get_vecs
from smorgasbord.common.transf import transf_vecs, transf_point
from smorgasbord.common.decorate import register


@register
class LerpWeight(bpy.types.Operator):
    bl_idname = "object.lerp_weight"
    bl_label = "Lerp Weight"
    bl_description = \
        "Linearly interpolate the weights between two given bones"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_paint_weight]
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
        return context.mode == 'PAINT_WEIGHT' \
               and len(context.selected_objects) > 1

    def execute(self, context):
        mode = context.mode
        selobs = context.selected_objects
        arms = [o for o in selobs if o.type == 'ARMATURE']

        if not arms:
            self.report({'ERROR_INVALID_INPUT'},
                        "Select exactly one armature.")
            return {'CANCELLED'}

        arm = arms[0]
        bone1, bone2 = None, None

        for b in arm.data.bones:
            if b.select:
                if bone1 is None:
                    bone1 = b
                else:
                    bone2 = b
                    break
        if bone2 is None:
            self.report({'ERROR_INVALID_INPUT'},
                        "Select exactly two bones.")
            return {'CANCELLED'}

        # Transform bones into world system
        arm2wrld = np.array(arm.matrix_world)
        b1 = transf_point(arm2wrld, bone1.head_local)
        b2 = transf_point(arm2wrld, bone2.head_local)

        dims = np.array(self.axes)

        # Vector from bone1 to bone2, if wished projected onto the
        # axis/plane isolated through the 'axes' parameter by zeroing
        # coordinates in ignored dimensions
        b1b2 = (b2 - b1) * dims

        # Squared distance between the bones
        sqrbdist = np.linalg.norm(b1b2) ** 2

        if sqrbdist == 0:
            # If both bones are in the same position after projection,
            # we can't interpolate between them.
            # This way, bone1 is assigned a weight of one.
            sqrbdist = 1e-15

        for o in selobs:
            if o.type != 'MESH':
                continue

            # Get selected vertices
            o.update_from_editmode()
            verts = o.data.vertices
            selflags = get_scalars(verts)
            pts = get_vecs(verts)[selflags]

            # Also transform vertices into the world system
            pts = transf_vecs(o.matrix_world, pts)
            # Calc vector from bone1 to every point and zero coordinates
            # of dimensions that are ignored.
            b1pts = (pts - b1) * dims
            # Calc dot product of this vector and the vector from bone1
            # to bone2
            # Get final weight by dividing through the squared bone
            # distance
            weights = np.dot(b1b2, b1pts.T) / sqrbdist
            # breakpoint()

            # Get indices of selected vertices
            indcs = np.arange(len(selflags))[selflags]
            vgs = o.vertex_groups
            try:
                vg1 = vgs[bone1.name]
            except KeyError:
                self.report(
                    {'ERROR_INVALID_INPUT'},
                    (
                        f"Vertex group '{bone1.name}' does not exist "
                        f"on object '{o.name}'"
                    ),
                )
                continue
            if self.bidirect:
                try:
                    vg2 = vgs[bone2.name]
                except KeyError:
                    self.report(
                        {'ERROR_INVALID_INPUT'},
                        (
                            f"Vertex group '{bone2.name}' does not "
                            f"exist on object '{o.name}'"
                        ),
                    )
                    continue

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
                # This is so stupid Blender! Why not make those
                # strings match!?
                if mode == 'PAINT_WEIGHT':
                    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
                else:
                    bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
