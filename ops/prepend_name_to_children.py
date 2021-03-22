import bpy
import re

from smorgasbord.common.decorate import register


@register
class PrependNameToChildren(bpy.types.Operator):
    bl_idname = "object.prepend_name_to_children"
    bl_label = "Prepend Name to Children"
    bl_description = (
        "Prepend the name of each selected object to the name of its "
        "children."
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object_relations]

    divider: bpy.props.StringProperty(
        name="Divider",
        default="_",
        description="String inserted between parent and child name",
    )
    pattern: bpy.props.StringProperty(
        name="Child name pattern",
        description=(
            "Regular expression matching the part of a child's name "
            "passed to the final name. Default removes '.001', etc"
        ),
        default=".*(?=\.\d+)",
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        pat = re.compile(self.pattern)

        for o in context.selected_objects:
            for c in o.children:
                name = c.name
                match = pat.match(name)

                try:
                    # Get matched part of child name
                    name = name[match.start():match.end()]
                except AttributeError:
                    # Regex didn't match anything
                    pass

                c.name = o.name + self.divider + name

        return {'FINISHED'}
