import bpy
from mathutils.kdtree import KDTree
import numpy as np

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_vecs, get_scalars, set_vals
from smorgasbord.common.transf import transf_vecs


@register
class MaterialTransfer(bpy.types.Operator):
    bl_idname = "object.material_transfer"
    bl_label = "Transfer Materials"
    bl_description = (
        "For each polygon in the active object, transfer its material "
        "index to the closest polygon in each selected object"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_object_relations]

    in_wrld_crds: bpy.props.BoolProperty(
        name="In world coordinates",
        description="Find nearest geometry in global, not in local space",
        default=True,
    )

    assign_mat: bpy.props.BoolProperty(
        name="Transfer material assignments",
        description=(
            "Not only transfer material indices, but also the "
            "corresponding material assignments"
        ),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return (
             context.mode == 'OBJECT'
             and context.object
             and len(context.selected_objects) > 1
        )

    def execute(self, context):
        source = context.object
        try:
            sdata = source.data
            sgeom = sdata.polygons
        except AttributeError:
            self.report(
                {'ERROR_INVALID_INPUT'},
                "The active object needs to have a mesh data block.",
            )
            return {'CANCELLED'}

        # get comparison values for source
        scvals = get_vecs(sgeom, 'center')
        if self.in_wrld_crds:
            # transform source to world coordinates
            mat = np.array(source.matrix_world)
            scvals = transf_vecs(mat, scvals)

        # build KD-Tree from comparison values
        kd = KDTree(len(sgeom))
        for i, v in enumerate(scvals):
            kd.insert(v, i)
        kd.balance()

        # get values to transfer from source
        stvals = get_scalars(sgeom, 'material_index', np.int8)

        all_meshless = True  # for error-reporting
        for target in context.selected_objects:
            if target is source:
                continue

            try:
                tdata = target.data
                tgeom = tdata.polygons
                all_meshless = False
            except AttributeError:
                continue

            # get comparison values for target
            tcvals = get_vecs(tgeom, 'center')

            if self.in_wrld_crds:
                # transform target to world coordinates
                mat = np.array(target.matrix_world)
                tcvals = transf_vecs(mat, tcvals)
                ttvals = np.empty(len(tgeom), dtype=np.int32)

            # for every comparison point in target, find closest in
            # source and copy over its transfer value
            for ti, tv in enumerate(tcvals):
                _, si, _ = kd.find(tv)
                ttvals[ti] = stvals[si]

            # set values to transfer to target
            set_vals(tgeom, ttvals, 'material_index')

            tmats = tdata.materials
            if self.assign_mat:
                # transfer assigned materials
                for i, m in enumerate(sdata.materials):
                    if i < len(tmats):
                        tmats[i] = m
                    else:
                        tmats.append(m)

        if all_meshless:
            self.report(
                {'ERROR_INVALID_INPUT'},
                "No selected target object has a mesh data block.",
            )
            return {'CANCELLED'}
        return {'FINISHED'}


if __name__ == "__main__":
    register()
