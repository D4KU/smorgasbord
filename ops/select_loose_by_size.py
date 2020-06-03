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
    bl_description = "Select loose mesh parts in a given size range"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    def _get_method(self):
        return SelectLooseBySize._method

    def _set_method(self, value):
        cls = SelectLooseBySize
        if cls._method != value:
            # Method changed, persistent data is outdated now
            cls._method = value
            cls._data.clear()

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
            "Loose parts whose calculated comparison value lies "
            "between [min, max), get selected. Calculations are "
            "done in local space and units depend on the chosen "
            "comparison method"
        ),
        size=2,
        step=10,
        default=_vol_limits,
        min=0.0,
        get=_get_vol_limits,
        set=_set_vol_limits,
    )

    _method = 0
    _methods = (
        ('DIAG', "Diagonal", "Compare the diagonal length of each "
         "part's bounding box, in meters"),
        ('VOL', "Volume", "Compare each part's bounding box volume, in "
         "cubic meters")
    )
    method: bpy.props.EnumProperty(
        name="Comparison Method",
        description="Decides how a part's size is calculated",
        items=_methods,
        default=_methods[_method][0],
        get=_get_method,
        set=_set_method,
    )

    # Loose parts data to store between executions. List of tuples.
    # First tuple entry is the reference to a mesh's vertex collection,
    # second the mesh's list of loose parts, which in turn is a TreeDict
    # with the vertex indices as values and the compare method's result
    # for those indices as key.
    _data = []
    # Number of digits the compare method's result is rounded to in
    # order to improve binning performance in the TreeDict.
    _resolution = 5

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def _find_parts(self, context):
        for o in context.objects_in_mode:
            data = o.data
            parts = TreeDict(acc=concat)
            coords = get_vecs(data.vertices)
            # choose comparison method
            method = np.linalg.norm if self._method == 0 else np.prod

            for indcs in get_parts(from_edit_mesh(data).verts):
                bounds, _ = get_bounds_and_center(coords[indcs])
                # calculate comparison value from bounding box,
                # round to create less bins in dict for better
                # performance
                key = round(method(bounds), self._resolution)
                parts[key] = indcs

            self._data.append((data.vertices, parts))

    def invoke(self, context, event):
        # Without invoke(), executing this operation several times
        # without changing parameters would make execute() use an
        # outdated parts list on a modified mesh.
        # However this breaks when this operator is called from script
        # without passing 'INVOKE_DEFAULT' as execution context.
        self._data.clear()
        return self.execute(context)

    def execute(self, context):
        if not self._data:
            self._find_parts(context)

        # the mesh doesn't update if we stay in edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        minv, maxv = self._vol_limits
        try:
            for verts, parts in self._data:
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

