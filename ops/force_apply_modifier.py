import bpy

from smorgasbord.common.decorate import register


@register
class ForceApplyModifier(bpy.types.Operator):
    bl_idname = "object.force_apply_modifier"
    bl_label = "Force Apply Modifier"
    bl_description = (
        "Circumvents the restriction that modifiers can't be applied "
        "to linked data by copying the data block first, applying the "
        "given modifier, and then overwriting the original data block "
        "with the copy")
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object_apply]

    name: bpy.props.StringProperty(
        name="Modifier",
        description="Name of the modifier to delete",
    )

    @classmethod
    def poll(cls, context):
        return context.object and context.mode == 'OBJECT'

    def execute(self, context):
        ob = context.object
        if self.name not in ob.modifiers.keys():
            # Don't return 'CANCELLED' so that the popup opens to insert
            # the modifier's name
            return {'FINISHED'}

        old_data = ob.data
        ob.data = ob.data.copy()
        # Apply modifier to (now single-user) copy of data block
        bpy.ops.object.modifier_apply(modifier=self.name)

        obs = context.selected_objects
        # If no additional objects are selected in addition to the
        # active one, consider all objects in the scene
        if not obs or obs == [ob]:
            obs = context.scene.objects

        # Set copy on all objects that have been sharing the original
        for o in obs:
            if o.data is old_data:
                o.data = ob.data
        return {'FINISHED'}
