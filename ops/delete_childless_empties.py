import bpy


class DeleteChildlessEmpties(bpy.types.Operator):
    bl_idname = "collection.delete_childless_empties"
    bl_label = "Delete Childless Empties"
    bl_description = "Delete all empty objects without a child in current collection"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_object_collection
    ]

    def execute(self, context):
        for o in context.collection.all_objects:
            if o.type == 'EMPTY' and len(o.children) == 0:
                bpy.data.objects.remove(o)
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(DeleteChildlessEmpties.bl_idname)

def register():
    bpy.utils.register_class(DeleteChildlessEmpties)
    for m in DeleteChildlessEmpties.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(DeleteChildlessEmpties)
    for m in DeleteChildlessEmpties.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
