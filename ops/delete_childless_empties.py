import bpy
from smorgasbord.common.decorate import register


@register
class DeleteChildlessEmpties(bpy.types.Operator):
    bl_idname = "collection.delete_childless_empties"
    bl_label = "Delete Childless Empties"
    bl_description = "Delete all empty objects without a child in current collection"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_object_collection
    ]


    def execute(self, context):
        for o in context.collection.objects:
            if o.type == 'EMPTY' and len(o.children) == 0:
                bpy.data.objects.remove(o)

        return {'FINISHED'}


if __name__ == "__main__":
    register()
