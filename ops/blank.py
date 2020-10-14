import bmesh as bm
import bpy
import mathutils as mu

from smorgasbord.common.decorate import register


@register
class Blank(bpy.types.Operator):
    bl_idname = ""
    bl_label = ""
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    menus = []

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for o in context.selected_objects:
            pass
        return {'FINISHED'}


if __name__ == "__main__":
    register()
