import bmesh as bm
import bpy
import mathutils as mu

from smorgasbord.common.decorate import register


@register
class JoinAsVertexGroup(bpy.types.Operator):
    bl_idname = "object.join_as_vertex_group"
    bl_label = "Join as Vertex Group"
    bl_description = (
        "Join selected into active object and create a vertex "
        "group for each joined-in object"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object]
    add_self: bpy.props.BoolProperty(
            name="Add Self",
            description=(
                "Create a vertex group for vertices already in the "
                "active object prior to joining"
            ),
            default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object

    def execute(self, context):
        for o in context.selected_editable_objects:
            if o.type != 'MESH' or (o is context.object and not self.add_self):
                continue

            vg = o.vertex_groups.new(name=o.name)

            # Add all vertices to group
            vs = list(range(0, len(o.data.vertices)))
            vg.add(vs, 1, 'REPLACE')

        bpy.ops.object.join()
        return {'FINISHED'}
