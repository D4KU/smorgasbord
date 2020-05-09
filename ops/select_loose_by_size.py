import bpy
import bmesh as bm
import mathutils as mu
import numpy as np
from operator import concat

from smorgasbord.common.io import get_bounds_and_center
from smorgasbord.common.decorate import register
from smorgasbord.thirdparty.redblack.redblack import TreeDict


def _get_vol_limits(self):
    return SelectLooseBySize._vol_limits


def _set_vol_limits(self, value):
    # clamp min to max
    SelectLooseBySize._vol_limits = (min(value), value[1])


@register
class SelectLooseBySize(bpy.types.Operator):
    bl_idname = "select.select_loose_by_size"
    bl_label = "Select Loose by Size"
    bl_description = (
        "Select loose parts of a mesh with a smaller bounding box "
        "volume than a given threshold."
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_select_edit_mesh
    ]

    # to prevent infinite recursion in getter and setter
    _vol_limits = mu.Vector((0.0, 1.0))

    vol_limits: bpy.props.FloatVectorProperty(
        name="Bounding Volume Limits",
        description=(
            "Loose parts whose bounding box's volume lies "
            "between [min, max) get selected"
        ),
        size=2,
        unit='VOLUME',
        step=10,
        default=(0.0, 1.0),
        min=0.0,
        get=_get_vol_limits,
        set=_set_vol_limits,
    )

    # contains one list of loose parts per selected object
    _obs = []
    _resolution = 5

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and \
            len(context.selected_editable_objects) > 0

    def invoke(self, context, event):
        self._find_parts(context)
        return self.execute(context)

    def _find_parts(self, context):
        self._obs.clear()
        all_type_err = True  # no obj is of type mesh

        for o in context.selected_editable_objects:
            data = o.data          # bpy representation of object data
            verts = data.vertices  # bpy representation of vertices
            vert_count = len(verts)

            if o.type == 'MESH':
                all_type_err = False
            else:
                continue

            parts = TreeDict(acc=concat)
            bdata = bm.from_edit_mesh(data) # bmesh representation of object data
            bverts = bdata.verts            # bmesh representation of vertices
            bverts.ensure_lookup_table()

            # bool array of vertex indices already put on stack 'to_visit'
            checked_indcs = np.zeros(vert_count, dtype=bool)

            # find loose parts in mesh
            for idx, checked in enumerate(checked_indcs):
                if checked:
                    continue

                # indices of verts of one loose part
                indcs = []
                # coords of verts of one loose part
                coords = []
                # bmesh vertices to be traversed
                to_visit = [bverts[idx]]
                checked_indcs[idx] = True

                while to_visit:
                    v = to_visit.pop()
                    coords.append(verts[v.index].co)
                    indcs.append(v.index)

                    # push all vertices connected to v on stack
                    for e in v.link_edges:
                        v2 = e.other_vert(v)

                        # but only if not already checked
                        if not checked_indcs[v2.index]:
                            to_visit.append(v2)
                            checked_indcs[v2.index] = True

                bounds, _ = get_bounds_and_center(coords)
                # calculate volume of bounding box
                # round to create less bins in dict for better performance
                key = round(np.prod(bounds), self._resolution)
                parts[key] = indcs
            self._obs.append((verts, parts))

        if all_type_err:
            self.report({'ERROR_INVALID_INPUT'},
                        "An object must be of type mesh")
            return {'CANCELLED'}

    def execute(self, context):
        # in case operator is called via console, where invoke() isn't
        # execute
        if not self._obs:
            self._find_parts(context)

        # the mesh doesn't update if we stay in edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        minv, maxv = self._vol_limits
        try:
            for verts, parts in self._obs:
                # bool array of vertex indices storing whether
                # the vert at that index needs to get selected
                sel_flags = np.zeros(len(verts), dtype=bool)
                # set flag for every vertex in a part with right volume
                for node in parts[minv:maxv]:
                    sel_flags[node.val] = True

                verts.foreach_set('select', sel_flags)
        finally:
            bpy.ops.object.mode_set(mode='EDIT')

        # because only vertices are updated, ensure selection is also
        # seen in edge and face mode
        sel_mode = context.tool_settings.mesh_select_mode
        if sel_mode[1] or sel_mode[2]:
            bpy.ops.mesh.select_mode(use_extend=True, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, type='VERT')

        return {'FINISHED'}


if __name__ == "__main__":
    register()

