import bpy
import os
from mathutils import Vector

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_bounds_and_center


@register
class SmartParentToEmpty(bpy.types.Operator):
    bl_idname = "object.smart_parent_to_empty"
    bl_label = "Smart Parent to Empty"
    bl_description = (
        "Parent every selected object to a newly created Empty and "
        "name it after the longest common substring in the names of "
        "all selected objects"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_mesh_add]

    loc: bpy.props.EnumProperty(
        name='Empty location',
        items=[
            ('CURSOR', "Cursor", "At the 3D cursor"),
            ('ACTIVE', "Active", "At the active object"),
            ('CENTER', "Center", (
                "In contrast to the eponymous function of the 'Extra "
                "Objects' plugin, the center is calculated as the "
                "median position of all selected objects, not the "
                "mean. This better handles outliers"
                )
            ),
        ],
        description="Where to place the created parent object",
       )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        sel = context.selected_objects

        # Determine spawn position of new parent object
        if self.loc == 'CENTER':
            obs = [o.location for o in sel]
            loc = Vector(get_bounds_and_center(obs)[1])
        elif self.loc == 'ACTIVE' and context.object:
            loc = context.object.location
        else:
            loc = context.scene.cursor.location

        # Create new Empty parent object
        # Set its name to the longest common substring of all selected
        # objects
        name = os.path.commonprefix([o.name for o in sel])
        name = "Empty" if not name else name
        ob = bpy.data.objects.new(name, None)
        ob.location = loc
        context.collection.objects.link(ob)

        # Set the parent of all selected objects
        for o in sel:
            o.parent = ob
            # Make sure reparenting doesn't make objects jump
            o.location -= loc

        return {'FINISHED'}
