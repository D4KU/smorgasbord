import bpy
from mathutils import Matrix

from smorgasbord.common.decorate import register


@register
class ForceApplyTransform(bpy.types.Operator):
    bl_idname = "object.force_apply_transform"
    bl_label = "Force Apply Transform"
    bl_description = (
        "Apply the active object's transform to its mesh. If the data "
        "is shared, the transformation of all instances is adjusted so "
        "that they don't move. If other instances are selected besides "
        "the active object, the adjustment is only applied to those"
    )

    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object_apply]

    apply_to: bpy.props.EnumProperty(
        name="Apply",
        description="Part of the transform to apply",
        items=(
            ('ALL', "Transform", ""),
            ('LOC', "Location", ""),
            ('ROT', "Rotation", ""),
            ('SCL', "Scale", ""),
        ),
        default='ALL',
    )
    round_to: bpy.props.IntProperty(
        name="Round to digits",
        description="Round transform entries to this number of digits",
        default=6,
    )
    to_cursor: bpy.props.BoolProperty(
        name="To Cursor",
        description="Regard cursor as origin",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        a = context.mode == 'OBJECT'
        b = bool(context.object)
        return a and b and context.object.type == 'MESH'

    def execute(self, context):
        ob = context.object

        # Build matrix to transform mesh data
        if self.apply_to == 'LOC':
            tmat = Matrix.Translation(ob.matrix_local.translation)
        elif self.apply_to == 'ROT':
            tmat = ob.matrix_local.to_quaternion().to_matrix().to_4x4()
        elif self.apply_to == 'SCL':
            tmat = Matrix.Diagonal(ob.matrix_local.to_scale()).to_4x4()
        else:
            tmat = ob.matrix_local

        if self.to_cursor:
            tmat = context.scene.cursor.matrix.inverted() @ tmat

        ob.data.transform(tmat)
        tmat_inv = tmat.inverted()

        # If no additional objects are selected in addition to the
        # active one, consider all objects in the scene
        selobs = context.selected_editable_objects
        if selobs == [ob] or not selobs:
            selobs = context.scene.objects

        # Update instances (objects sharing the same mesh as 'ob'),
        # including 'ob' itself
        for o in selobs:
            if o.data is not ob.data:
                continue

            # Update children of instances to let them visually stay in
            # place
            for child in o.children:
                self._set_mat_local(child, tmat @ child.matrix_local)

            # matrix_local is updated only after execution of this
            # script, so objects still return their transformation from
            # before the operator, even if it has been set before
            if o.parent and o.parent.data is ob.data:
                # 'o' is an instance AND child to an instance
                self._set_mat_local(o, tmat @ o.matrix_local @ tmat_inv)
            else:
                self._set_mat_local(o, o.matrix_local @ tmat_inv)

        # What does o.matrix_local turn into?
        # * no child, no instance: o.matrix_local
        # * child, no instance: tmat @ o.matrix_local
        # * no child, instance: o.matrix_local @ tmat_inv
        # * child, instance: tmat @ o.matrix_local @ tmat_inv
        return {'FINISHED'}

    def _set_mat_local(self, ob, mat):
        round_mat(mat, self.round_to)
        ob.matrix_local = mat


def round_mat(mat, ndigits=6):
    """
    Round every entry in the given matrix to consist of maximally
    n digits
    """
    for row in mat:
        for i in range(len(row)):
            row[i] = round(row[i], ndigits)
