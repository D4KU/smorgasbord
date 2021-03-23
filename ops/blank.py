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
        a = context.mode == 'OBJECT'
        b = context.object is not None
        c = context.object.type == 'MESH'
        return a and b and c

    def execute(self, context):
        for o in context.selected_editable_objects:
            pass
        return {'FINISHED'}
