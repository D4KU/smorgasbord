import bpy

from smorgasbord.common.decorate import register


@register
class QuickFixObjects(bpy.types.Operator):
    bl_idname = "object.quick_fix_objects"
    bl_label = "Quick Fix Objects"
    bl_description = (
        "For every selected object, set auto smooth and add Weighted "
        "Normal modifier."
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object]

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        for o in context.selected_objects:
            if o.type != 'MESH':
                continue

            context.view_layer.objects.active = o
            bpy.ops.mesh.customdata_custom_splitnormals_clear()

            data = o.data
            data.use_auto_smooth = True
            data.auto_smooth_angle = 1.1519173

            bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')
            mod = o.modifiers[-1]
            mod.keep_sharp = True
        return {'FINISHED'}
