import bpy
import re

from smorgasbord.common.decorate import register


@register
class RenameVertexGroups(bpy.types.Operator):
    bl_idname = "object.rename_vertex_groups"
    bl_label = "Rename Vertex Groups"
    bl_description = (
        "Find and replace substrings in the vertex group names of all "
        "selected objects. Press F9 after executing it!"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.MESH_MT_vertex_group_context_menu]

    find: bpy.props.StringProperty(
        name="Find",
        description="Regular expression matching substrings to replace",
    )
    repl: bpy.props.StringProperty(
        name="Replace",
        description=(
            "String to insert into every non-overlapping match of the "
            "given regex"
        ),
    )

    def execute(self, context):
        pat = re.compile(self.find)
        for o in context.selected_editable_objects:
            if o.type != 'MESH':
                continue
            for g in o.vertex_groups:
                g.name = pat.sub(self.repl, g.name)
        return {'FINISHED'}
