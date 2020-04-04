import bpy
from smorgasbord.common.decorate import register


@register
class ApplyName(bpy.types.Operator):
    bl_idname = "object.apply_name"
    bl_label = "Apply Name"
    bl_description = "Copy the object's name to its data block's name"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
         bpy.types.VIEW3D_MT_object_apply
    ]


    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0


    def execute(self, context):
       for o in context.selected_objects:
            o.data.name = o.name

       return {'FINISHED'}


if __name__ == "__main__":
    register()
