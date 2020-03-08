import bpy
import mathutils as mu

class SetParentAdvanced(bpy.types.Operator):
    bl_idname = "object.set_parent_advanced"
    bl_label = "Set Parent Advanced"
    bl_description = "More options to parent one object to another"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_object_parent
    ]

    op_type: bpy.props.EnumProperty(
        name = "Type",
        items = [
            ("NO_INVERSE_KEEP_TRANSFORM",
             "No Inverse, Keep Transform",
             "Parent selected objects to the active one without setting the inverse parent correction, while keeping the child's world transform"),
            ("NO_INVERSE_KEEP_BASIS",
             "No Inverse, Keep Basis",
             "Parent selected objects to the active one without setting the inverse parent correction, while keeping the child's values set in the properties panel"),
            ("WORLD_TO_LOCAL_ORIGIN",
             "World to Local Origin",
             "Parent selected objects to the active one while keeping the child's world transform. It's world transform is now also its new local origin")
        ]
    )

    def execute(self, context):
        parent = context.object
        par_mat_local_inv = parent.matrix_local.inverted()

        if self.op_type == 'NO_INVERSE_KEEP_TRANSFORM':
            for child in context.selected_objects:
                if child == parent:
                    continue
                child.parent = parent
                child.matrix_basis = par_mat_local_inv @ child.matrix_basis
        elif self.op_type == 'NO_INVERSE_KEEP_BASIS':
            for child in context.selected_objects:
                if child == parent:
                    continue
                child.parent = parent
        else:
            for child in context.selected_objects:
                if child == parent:
                    continue
                child.parent = parent
                child.matrix_parent_inverse = par_mat_local_inv @ child.matrix_basis
                child.matrix_basis = mu.Matrix()

        bpy.context.view_layer.update()
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(SetParentAdvanced.bl_idname)

def register():
    bpy.utils.register_class(SetParentAdvanced)
    for m in SetParentAdvanced.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(SetParentAdvanced)
    for m in SetParentAdvanced.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
