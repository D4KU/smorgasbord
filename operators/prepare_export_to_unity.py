import bpy


class PrepareExportToUnity(bpy.types.Operator):
    bl_idname = "transform.prepare_export_to_unity"
    bl_label = "Prepare Export to Unity"
    bl_description = "Set rotation and scale to match object transform in Unity game engine. Destructive. Fails on linked data."
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_transform_object,
    ]

    prepare_rotation: bpy.props.BoolProperty(
        name = "Prepare Rotation",
        description = "Convert Z-Up to Y-Up",
        default = True,
    )

    prepare_scale: bpy.props.BoolProperty(
        name = "Prepare Scale",
        description = "Convert object scale from cm to m",
        default = True,
    )

    def execute(self, context):
        if self.prepare_rotation:
            bpy.ops.transform.rotate(value=1.5708, orient_axis='X')
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            bpy.ops.transform.rotate(value=-1.5708, orient_axis='X')

        if self.prepare_scale:
            bpy.ops.transform.resize(value=(100, 100, 100))
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))

        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(PrepareExportToUnity.bl_idname)

def register():
    bpy.utils.register_class(PrepareExportToUnity)
    for m in PrepareExportToUnity.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(PrepareExportToUnity)
    for m in PrepareExportToUnity.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
