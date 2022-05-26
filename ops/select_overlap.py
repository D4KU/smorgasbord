import bpy
from mathutils.kdtree import KDTree

from smorgasbord.common.decorate import register


@register
class SelectOverlap(bpy.types.Operator):
    bl_idname = "mesh.select_overlap"
    bl_label = "Select Overlap"
    bl_description = (
        "Select vertices in the active object close to vertices in "
        "selected objects"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    dist: bpy.props.FloatProperty(
        name="Distance",
        description=(
            "Radius in which each vertex of a selected object selects "
            "vertices in the active object"
        )
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and context.object

    def execute(self, context):
        # Mesh can't be updated in edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        try:
            self._execute(context)
        finally:
            bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

    def _execute(self, context):
        ob = context.object
        verts = ob.data.vertices
        kd = KDTree(len(verts))

        for i, v in enumerate(verts):
            kd.insert(ob.matrix_world @ v.co, i)
        kd.balance()

        for o in context.selected_objects:
            if ob is o or o.type != 'MESH':
                continue
            for v in o.data.vertices:
                nearest = kd.find_range(o.matrix_world @ v.co, self.dist)
                for _, idx, _ in nearest:
                    verts[idx].select = True
