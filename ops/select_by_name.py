import bpy
import re
from smorgasbord.common.decorate import register


@register
class SelectByName(bpy.types.Operator):
    bl_idname = "object.select_by_name"
    bl_label = "Select by Name"
    bl_description = "Select all objects in view layer with a given name"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_object]

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
            ('REGEX', "Regex", "Interpret name as regular expression"),
        ]
    )

    def execute(self, context):
        if self.match_metric == 'CONTAINS':
            compare = lambda a, b: b in a
        elif self.match_metric == 'EQUALS':
            compare = lambda a, b: a == b
        elif self.match_metric == 'STARTS_WITH':
            compare = lambda a, b: a.startswith(b)
        elif self.match_metric == 'ENDS_WITH':
            compare = lambda a, b: a.endswith(b)
        else:
            compare = lambda a, b: re.fullmatch(b, a)

        for o in context.view_layer.objects:
            if compare(o.name, self.name):
                o.select_set(True)

        return {'FINISHED'}
