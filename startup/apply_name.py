import bpy


class ApplyName(bpy.types.Operator):
    bl_idname = "object.apply_name"
    bl_label = "Apply Name"
    bl_description = "Copy the object's name to its data block's name"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
         bpy.types.VIEW3D_MT_object_apply
    ]

    def execute(self, context):
        for o in context.selected_objects:
            o.data.name = o.name
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(ApplyName.bl_idname)

def register():
    bpy.utils.register_class(ApplyName)
    for m in ApplyName.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(ApplyName)
    for m in ApplyName.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
