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
    to_cursor: bpy.props.BoolProperty(
        name="To Cursor",
        description="Regard cursor as origin",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        a = context.mode == 'OBJECT'
        b = context.object is not None
        c = context.object.type == 'MESH'
        return a and b and c

    def execute(self, context):
        ob = context.object
        loc, rot, scl = ob.matrix_local.decompose()

        # If no additional objects are selected in addition to the
        # active one, consider all objects in the scene
        selobs = context.selected_objects
        if not selobs or selobs == [ob]:
            selobs = context.scene.objects

        if self.apply_to == 'LOC':
            tmat = Matrix.Translation(loc)
        elif self.apply_to == 'ROT':
            tmat = rot.to_matrix().to_4x4()
        elif self.apply_to == 'SCL':
            tmat = Matrix.Diagonal(scl).to_4x4()
        else:
            tmat = ob.matrix_local

        if self.to_cursor:
            tmat = context.scene.cursor.matrix.inverted() @ tmat

        ob.data.transform(tmat)
        tmat_inv = tmat.inverted()

        # Update ob's children to let them visually stay in place
        for c in ob.children:
            c.matrix_local = tmat @ c.matrix_local

        # Update objects sharing the same mesh as 'ob'
        for o in selobs:
            if o.data is not ob.data:
                continue

            # Check if an object is a child AND an instance of 'ob'.
            # matrix_local seems to be updated only once per frame after
            # execution of this script, so objects that are children and
            # an instance, whose matrix has already been set in the first
            # loop, still return their transformation from before the loop
            # here
            if ob is o.parent:
                o.matrix_local = tmat @ o.matrix_local @ tmat_inv
            else:
                o.matrix_local = o.matrix_local @ tmat_inv

        # What does o.matrix_local turn into?
        # * no child, no instance: o.matrix_local
        # * child, no instance: tmat @ o.matrix_local
        # * no child, instance: o.matrix_local @ tmat_inv
        # * child, instance: tmat @ o.matrix_local @ tmat_inv
        return {'FINISHED'}
