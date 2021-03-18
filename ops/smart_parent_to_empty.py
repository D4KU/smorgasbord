import bpy
import os
from mathutils import Vector

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_bounds_and_center
from smorgasbord.common.hierarchy import set_parent


@register
class SmartParentToEmpty(bpy.types.Operator):
    bl_idname = "object.smart_parent_to_empty"
    bl_label = "Smart Parent to Empty"
    bl_description = (
        "Parent every selected object to a newly created Empty and "
        "name it after the longest common substring in the names of "
        "all selected objects. The Empty is parented to the former "
        "parent of the active object. If no active object exists, "
        "the first selected object is chosen instead."
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_mesh_add]

    loc: bpy.props.EnumProperty(
        name='Empty location',
        items=[
            ('CURSOR', "Cursor", "At the 3D cursor"),
            ('ACTIVE', "Active", "At the active object"),
            ('CENTER', "Center", "Average position of selected objects"),
        ],
        description="Where to place the created parent object",
        default='CURSOR',
       )

    set_inv: bpy.props.BoolProperty(
        name="Set Inverse",
        description=(
            "If true, the origin of the re-parented objects is the "
            "world origin. If false, it is the new Empty's location"
        ),
        default=True,
    )

    to_strip: bpy.props.StringProperty(
        name="Chars to Strip",
        description=(
            "Characters to be stripped from the end of the calculated "
            "name of the new Empty."
        ),
        default=" _.",
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.selected_objects

    def execute(self, context):
        sel = context.selected_objects
        ob = context.object

        # Determine spawn position of new parent object
        if self.loc == 'CENTER':
            obs = [o.location for o in sel]
            paloc = Vector(get_bounds_and_center(obs)[1])
        elif self.loc == 'ACTIVE' and ob:
            paloc = ob.location
        else:
            paloc = context.scene.cursor.location

        # Parent name is the longest common substring of all selected
        # objects
        paname = os.path.commonprefix([o.name for o in sel])
        paname = paname.rstrip(self.to_strip) if paname else "Empty"

        # Create new Empty parent object
        pa = bpy.data.objects.new(paname, None)
        pa.location = paloc

        # Idol is the object determining the new Empty's parent and
        # collection
        idol = ob if ob else sel[0]
        pa.parent = idol.parent
        if idol.parent:
            pa.matrix_parent_inverse = idol.parent.matrix_world.inverted()
        idol.users_collection[0].objects.link(pa)

        context.view_layer.update()
        # Set the parent of all selected objects to 'pa'
        for o in sel:
            set_parent(o, pa, self.set_inv)

        return {'FINISHED'}
