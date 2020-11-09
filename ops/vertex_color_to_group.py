import bpy
import numpy as np

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_vecs, get_scalars


def get_red(arr):
    return arr[:, 0:1].ravel()


def get_green(arr):
    return arr[:, 1:2].ravel()


def get_blue(arr):
    return arr[:, 2:3].ravel()


def avg_rgb(arr):
    # Strip alpha values in last column
    return np.average(arr[:, :-1], axis=1)


@register
class VertexColorToGroup(bpy.types.Operator):
    bl_idname = "object.vertex_color_to_group"
    bl_label = "Vertex Color to Group"
    bl_description = (
        "For every selected object, converts the active vertex color "
        "layer into a eponymous vertex group, given a conversion method"
        )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.MESH_MT_vertex_group_context_menu]

    method: bpy.props.EnumProperty(
        name="Method",
        description="Method used to calculate scalar weights from rgb colors",
        items=(
            ('AVG', "Average", "Average all channels"),
            ('RED', "Red", "Pass red channel"),
            ('GRE', "Green", "Pass green channel"),
            ('BLU', "Blue", "Pass blue channel"),
        ),
        default='AVG',
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and \
            len(context.selected_editable_objects) > 0

    def execute(self, context):
        if self.method == 'RED':
            meth = get_red
        elif self.method == 'GRE':
            meth = get_green
        elif self.method == 'BLU':
            meth = get_blue
        else:
            meth = avg_rgb

        for o in context.selected_editable_objects:
            if o.type != 'MESH':
                continue

            cols = o.data.vertex_colors.active
            if not cols:
                continue

            # Get colors of all mesh loops
            # These loops don't always match the vertex count and
            # are not stored at the correct vertex indices.
            cs = get_vecs(cols.data, attr='color', vecsize=4)

            # For every loop, get its vertex index
            lops = o.data.loops
            vindcs = get_scalars(lops, attr='vertex_index', dtype=np.int)

            # Find the indices of 'vindcs' at which a unique entry is
            # found for the first time.
            _, i_vindcs = np.unique(vindcs, return_index=True)

            # This index list 'i_vindcs' filters out all redundant
            # entries in 'cs' and sorts them so each color lands at
            # the index of its corresponding vertex.
            # Then calculate the (unique) weights of the colors via
            # the chosen method.
            weights = meth(cs[i_vindcs])
            u_weights = np.unique(weights)

            vg = o.vertex_groups.new(name=cols.name)
            for w in u_weights:
                # Get the indices of one weight value and add it to
                # the vertex group.
                indcs = np.where(weights == w)[0]
                vg.add(indcs.tolist(), w, 'REPLACE')

        return {'FINISHED'}
        # This is an example calculation of the above execute function.
        # cs =
        # [[0,0,0],
        #  [1,0,0],
        #  [0,1,0],
        #  [1,0,0],
        #  [1,1,0]]

        # vindcs = [1, 3, 2, 3, 0]
        # _, i_vindcs = [0, 1, 2, 3] [4, 0, 2, 1]
        # cs[i_vindcs] =
        # [[1,1,0],
        #  [0,0,0],
        #  [0,1,0],
        #  [1,0,0]]

        # weights = [.6, 0, .3, .3]
        # u_weights = [0, .3, .6]

        # for 0 in u_weights:
        #     indcs = [1]
        #     vg.add(indcs, 0)

        # for .3 in u_weights:
        #     indcs = [2, 3]
        #     vg.add(indcs, .3)

        # for .6 in u_weights:
        #     indcs = [0]
        #     vg.add(indcs, .6)
