import bmesh as bm
import numpy as np
import bpy
import mathutils as mu
from smorgasbord.common.io import get_scalars

from smorgasbord.common.decorate import register


@register
class RemoveEmptyVertexGroups(bpy.types.Operator):
    bl_idname = "mesh.remove_empty_vertex_groups"
    bl_label = "Remove Empty Vertex Groups"
    bl_description = "Remove vertex groups not containing any vertex"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.MESH_MT_vertex_group_context_menu]

    threshold: bpy.props.FloatProperty(
        name="Weight Threshold",
        description=(
            "Weights lower than this value are ignored. When no vertex "
            "has a weight higher than this assigned, the group is "
            "removed"
        ),
        default=0.001,
        precision=4,
        step=0.01,
        min=0,
        max=1,
    )

    limit_to_arms: bpy.props.BoolProperty(
        name="Limit to armatures",
        description="Only keep vertex groups linked to an armature",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for o in context.selected_objects:
            if o.type != 'MESH':
                continue

            vgs = o.vertex_groups
            # Bool array storing True at each vertex group's index which
            # is going to be removed
            to_remov = np.ones(len(vgs), np.bool)

            for v in o.data.vertices:
                gindcs  = get_scalars(v.groups, 'group',  np.int8)
                weights = get_scalars(v.groups, 'weight', np.float)
                # Unset every group for which vertex v has a weight
                # bigger than the threshold
                to_remov[gindcs[weights > self.threshold]] = False

            if self.limit_to_arms:
                # Get bones names of all armatures linked to this object
                bonenames = set()
                for m in o.modifiers:
                    if m.type == 'ARMATURE' and m.object:
                        bonenames.update(m.object.data.bones.keys())

                # Mark every vertex group not found under the bone names
                # as 'to remove'
                for i, name in enumerate(vgs.keys()):
                    if name not in bonenames:
                        to_remov[i] = True

            # Remove groups which still have the remove flag set
            for g in np.array(vgs)[to_remov]:
                vgs.remove(g)

        return {'FINISHED'}
