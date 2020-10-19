import bpy
from mathutils import Matrix
from math import pi
from smorgasbord.common.decorate import register


# Swap Y with Z and invert X to transform a right-handed Z-up
# coordinate system (Blender) to a left-handed Y-up coordinate system
# (Unity) and vise versa.
# Rotates the object so that after 't_post' sets its location, it ends
# up with a (90, 0, 0) rotation.
t_pre = Matrix(((-1, 0, 0, 0),
                ( 0, 0, 1, 0),
                ( 0, 1, 0, 0),
                ( 0, 0, 0, 1)))

# Places the object so that in Unity it ends up in the same place as in
# Blender. It's a rotation of 180 degrees around z.
t_post = Matrix(((-1,  0, 0, 0),
                 ( 0, -1, 0, 0),
                 ( 0,  0, 1, 0),
                 ( 0,  0, 0, 1)))


@register
class PrepareExportToUnity(bpy.types.Operator):
    bl_idname = "transform.prepare_export_to_unity"
    bl_label = "Prepare Export to Unity"
    bl_description = (
        "Transforms selected objects so that they export to Unity"
        "without unwanted transformations applied. Blender's coordinate"
        "system is right-handed Z-up, Unity's left-handed Y-up"
        )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_transform_object]

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        # Set to make sure that when data is shared across objects,
        # it is not transformed several times. 'None' keeps Empty
        # objects away.
        datas = {None}
        for o in context.selected_editable_objects:
            data = o.data
            if data not in datas:
                # Transforms the object's data so that the object does
                # not end up mirrored in Unity.
                data.transform(t_pre)
                datas.add(data)
                if o.type == 'ARMATURE':
                    # After transforming an armature's data with
                    # 't_pre', every bone gets an additional roll of 180
                    # degrees. To remove that, the armature has to be
                    # set to edit mode.
                    bpy.ops.object.mode_set(
                        {'active_object': o}, mode='EDIT')
                    for b in o.data.edit_bones:
                        b.roll -= pi
                    bpy.ops.object.mode_set(mode='OBJECT')
            # Set every root object's location and add a rotation of 90
            # degrees around the x axis. This rotation is subtracted on
            # import into Unity. God knows why.
            # Since this is only done for objects without parents, it
            # might lead to unexpected behaviour when those root objects
            # are not prepared and exported.
            if not o.parent:
                o.matrix_world = t_post @ o.matrix_world @ t_pre

        return {'FINISHED'}


if __name__ == "__main__":
    register()
