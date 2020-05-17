import bpy
import numpy as np
from bmesh import from_edit_mesh
from operator import concat

from smorgasbord.common.decorate import register
from smorgasbord.common.io import (
    get_parts,
    get_vecs,
    get_bounds_and_center,
)
from smorgasbord.thirdparty.redblack.redblack import TreeDict


@register
class SelectLooseBySize(bpy.types.Operator):
    bl_idname = "select.select_loose_by_size"
    bl_label = "Select Loose by Size"
    bl_description = (
        "Select loose parts of a mesh with a smaller bounding box "
        "volume than a given threshold."
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    def _get_vol_limits(self):
        return SelectLooseBySize._vol_limits

    def _set_vol_limits(self, value):
        # clamp min to max
        SelectLooseBySize._vol_limits = (min(value), value[1])

    # to prevent infinite recursion in getter and setter
    _vol_limits = (0.0, 1.0)
    vol_limits: bpy.props.FloatVectorProperty(
        name="Bounding Volume Limits",
        description=(
            "Loose parts whose bounding box's volume lies "
            "between [min, max) get selected"
        ),
        size=2,
        unit='VOLUME',
        step=10,
        default=_vol_limits,
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
        if self._find_parts(context):
            return self.execute(context)
        else:
            return {'CANCELLED'}

    def _find_parts(self, context):
        self._obs.clear()
        all_type_err = True  # no obj is of type mesh

        for o in context.selected_editable_objects:
            if o.type != 'MESH':
                continue
            all_type_err = False
            parts = TreeDict(acc=concat)
            data = o.data
            coords = get_vecs(data.vertices)
            bverts = from_edit_mesh(data).verts

            for indcs in get_parts(bverts):
                bounds, _ = get_bounds_and_center(coords[indcs])
                # Calculate volume of bounding box round to create less
                # bins in dict for better performance.
                key = round(np.prod(bounds), self._resolution)
                parts[key] = indcs

            self._obs.append((data.vertices, parts))

        if all_type_err:
            self.report({'ERROR_INVALID_INPUT'},
                        "An object must be of type mesh")
            return False
        return True

    def execute(self, context):
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

