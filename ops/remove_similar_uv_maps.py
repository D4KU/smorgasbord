import bpy
import numpy as np

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_vecs


@register
class RemoveSimilarUvMaps(bpy.types.Operator):
    bl_idname = "object.remove_similar_uv_maps"
    bl_label = "Remove Similar UV Maps"
    bl_description = \
        "Remove UV maps that are too similar to the active one"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_uv_map]

    threshold: bpy.props.FloatProperty(
        name="Difference Threshold",
        description=(
            "UV maps with a smaller similarity to the active one than "
            "this value are removed. Similarity is computed by "
            "summing the absolute distances between each pair of UV "
            "coordinates in both compared maps"
        ),
        default=0.001,
        precision=4,
        step=0.01,
        min=0,
        max=1000,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for o in context.selected_objects:
            if o.type != 'MESH':
                continue

            ls = o.data.uv_layers
            if not ls.active:
                # 'o' has no UV Map
                continue

            uvs_a = get_vecs(ls.active.data, attr='uv', vecsize=2)
            to_del = []
            for i, l in enumerate(ls):
                if i == ls.active_index:
                    continue

                uvs = get_vecs(l.data, attr='uv', vecsize=2)
                diff = np.abs(uvs_a - uvs).sum()
                if diff < self.threshold:
                    to_del.append(ls[i])

            for l in to_del:
                ls.remove(l)

            self.report(
                {'INFO'},
                "Removed " + str(len(to_del)) + " uv maps of " + o.name,
                )
        return {'FINISHED'}
