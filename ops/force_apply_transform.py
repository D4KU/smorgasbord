import bpy
from mathutils import Matrix

from smorgasbord.common.decorate import register
from smorgasbord.common.hierarchy import get_lvl


@register
class ForceApplyTransform(bpy.types.Operator):
    bl_idname = "object.force_apply_transform"
    bl_label = "Force Apply Transform"
    bl_description = (
        "Apply every selected object's local transform to its mesh. If "
        "the data is shared, the transformation of all instances is "
        "adjusted so that they don't move"
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
        description="Treat cursor as origin",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    # Build matrix to transform mesh data dependent on user choices
    def _get_tmat(self, context, ob):
        if self.apply_to == 'LOC':
            tmat = Matrix.Translation(ob.matrix_local.translation)
        elif self.apply_to == 'ROT':
            tmat = ob.matrix_local.to_quaternion().to_matrix().to_4x4()
        elif self.apply_to == 'SCL':
            tmat = Matrix.Diagonal(ob.matrix_local.to_scale()).to_4x4()
        else:
            tmat = ob.matrix_local.copy()

        if self.to_cursor:
            return context.scene.cursor.matrix.inverted() @ tmat
        return tmat

    def execute(self, context):
        # meshes, armatures, ... transformed by this operator
        datas = dict()

        # Transform data of every selected object and cache the
        # applied transformation
        for o in context.selected_editable_objects:
            if hasattr(o.data, 'transform') and o.data not in datas:
                tmat = self._get_tmat(context, o)
                datas[o.data] = tmat
                o.data.transform(tmat)

        # Traverse scene graph top-down. Even unselected objects must be
        # transformed if sharing data with a selected one.
        for o in sorted(context.scene.objects, key=get_lvl):
            # For every object, find the transformation applied to its
            # data.
            tmat = datas.get(o.data, None)
            if not tmat:
                # Even if o's data hasn't been transformed, get its
                # transform if selected.
                if o.select_get():
                    tmat = self._get_tmat(context, o)
                else:
                    continue

            # Move the object opposite to its data
            o.matrix_local = o.matrix_local @ tmat.inverted()

            # Update children to let them visually stay in place
            for child in o.children:
                child.matrix_local = tmat @ child.matrix_local

            # Without this update, matrix_local is only updated after
            # this script runs, so objects still return their
            # transformation from before the operator, even if it has
            # been set before.
            context.view_layer.update()

        # What does o.matrix_local turn into?
        # * no child, no instance: o.matrix_local
        # * child, no instance: tmat @ o.matrix_local
        # * no child, instance: o.matrix_local @ tmat.inverted()
        # * child, instance: tmat @ o.matrix_local @ tmat.inverted()
        return {'FINISHED'}
