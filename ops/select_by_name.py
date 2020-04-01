import bpy


class SelectAllByName(bpy.types.Operator):
    bl_idname = "object.select_all_by_name"
    bl_label = "Select All by Name"
    bl_description = "Select all objects in scene with a given name"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_select_object
    ]

    name: bpy.props.StringProperty(
        name = "Name",
        description = "Name to search for",
    )

    match_metric: bpy.props.EnumProperty(
        name = "Match Metric",
        items = [
            ('CONTAINS', "Contains", "Object name must contain string"),
            ('EQUALS', "Equals", "Object name must equal string"),
            ('STARTS_WITH', "Starts with", "Object name must start with string"),
            ('ENDS_WITH', "Ends with", "Object name must end with string"),
        ]
    )

    def execute(self, context):
        if self.match_metric == 'CONTAINS':
            compare = lambda a, b: b in a
        elif self.match_metric == 'EQUALS':
            compare = lambda a, b: a == b
        elif self.match_metric == 'STARTS_WITH':
            compare = lambda a, b: a.startswith(b)
        else:
            compare = lambda a, b: a.endswith(b)

        for o in context.scene.objects:
            if compare(o.name, self.name):
                o.select_set(True)

        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(SelectAllByName.bl_idname)

def register():
    bpy.utils.register_class(SelectAllByName)
    for m in SelectAllByName.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(SelectAllByName)
    for m in SelectAllByName.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
