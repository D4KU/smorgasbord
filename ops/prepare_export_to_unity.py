import bpy
from math import pi
from smorgasbord.common.decorate import register


pihalf = pi * 0.5


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

    prepare_orientation: bpy.props.BoolProperty(
        name="Prepare Orientation",
        description=\
            "Rotate selection 90 degrees around x-axis",
        default=True,
    )
    inv_rot: bpy.props.BoolProperty(
        name="Inverse Rotation",
        description=\
            "Rotate selection -90 degrees instead. Only takes effect "
            "if 'Prepare Orientation' is true",
        default=False,
    )
    correct_bone_roll: bpy.props.BoolProperty(
        name="Correct Bone Roll",
        description=\
            "Iterate over every selected armature and subtract 90 "
            "degrees from every bone's roll angle. Only takes effect "
            "if 'Prepare Orientation' is true",
        default=False,
    )
    swap_left_right: bpy.props.BoolProperty(
        name="Swap Left Right",
        description=\
            "Swap left and right to fully convert the right-handed to "
            "a left-handed coordinate system. Only takes effect if "
            "'Prepare Orientation' is true",
        default=False,
    )
    prepare_scale: bpy.props.BoolProperty(
        name="Prepare Scale",
        description="Convert object scale from cm to m",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        if self.prepare_orientation:
            if self.swap_left_right:
                bpy.ops.transform.resize(
                    value=(-1, -1, 1),
                    center_override=(0, 0, 0),
                )

            angl = -pihalf if self.inv_rot else pihalf
            bpy.ops.transform.rotate(value=angl, orient_axis='X')
            bpy.ops.object.transform_apply(
                location=False,
                rotation=True,
                scale=self.swap_left_right,
                )
            bpy.ops.transform.rotate(value=-angl, orient_axis='X')

            if self.correct_bone_roll:
                for o in context.selected_objects:
                    if o.type != 'ARMATURE':
                        continue

                    bpy.ops.object.mode_set(
                        {'active_object': o}, mode='EDIT')
                    for b in o.data.edit_bones:
                        # TODO test if 2*angl is actually necessary
                        b.roll -= angl
                    bpy.ops.object.mode_set(mode='OBJECT')

        if self.prepare_scale:
            bpy.ops.transform.resize(value=(100, 100, 100))
            bpy.ops.object.transform_apply(
                location=False,
                rotation=False,
                scale=True,
                )
            bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))

        return {'FINISHED'}


if __name__ == "__main__":
    register()
