import bpy
from mathutils import Matrix
import numpy as np

import smorgasbord.common.io as sbio
import smorgasbord.common.mat_manip as sbmm
import smorgasbord.common.transf as sbt
import smorgasbord.common.decorate as sbd


@sbd.register
class AlignBounds(bpy.types.Operator):
    bl_idname = "transform.align_bounds"
    bl_label = "Align Bounds"
    bl_description = (
        "Transform selected objects so that their bounds "
        "match the active object"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_transform_object,
        bpy.types.VIEW3D_MT_transform
    ]

    axes_align: bpy.props.BoolProperty(
        name="Align to Axes",
        description=(
            "Align the source objects/vertices to the world "
            "axes instead of the target object rotation"
        )
    )

    rot_offset: bpy.props.FloatVectorProperty(
        name="Rotation Offset",
        description="Rotational offset from source to target",
        subtype='EULER',
        step=9000.0,          # 90 deg
        soft_min=-4.71239,    # -270 deg in rad
        soft_max=4.71239,     # 270 deg in rad
    )

    @classmethod
    def description(cls, context, properties):
        if context.mode == 'EDIT_MESH':
            return (
                "Transform selected vertices of selected objects "
                "so that their bounds match the selected vertices of "
                "the active object"
            )
        else:
            return cls.bl_description

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False

        a = len(context.selected_objects) > 1
        b = context.object.type == 'MESH'
        return a and b

    def execute(self, context):
        # TARGET
        target = context.object
        tdata = target.data
        tverts = tdata.vertices
        teuler = target.matrix_world.to_euler()

        if tdata.is_editmode:
            # ensure newest changes from edit mode are visible to data
            target.update_from_editmode()

            # get selected vertices in target
            sel_flags_target = sbio.get_scalars(tdata.vertices)
            tcoords = sbio.get_vecs(tverts)[sel_flags_target]
        else:
            trot = np.array(teuler)

            # If we align to axes and the target is rotated, we can't
            # use Blender's bounding box. Instead, we have to find the
            # global bounds from all global vertex positions.
            # This is because for a rotated object, the global bounds of
            # its local bounding box aren't always equal to the global
            # bounds of all its vertices.
            # If we don't align to axes, we aren't interested in the
            # global target bounds anyway.
            tcoords = sbio.get_vecs(tverts) \
                if self.axes_align \
                and trot.dot(trot) > 0.001 \
                else np.array(target.bound_box)

        if len(tcoords) < 2:
            self.report({'ERROR_INVALID_INPUT'},
                        "Select at least 2 vertices")
            return {'CANCELLED'}

        tworldmat = np.array(target.matrix_world)

        if self.axes_align:
            # If we align sources to world axes, we are interested in
            # the target bounds in world coordinates.
            tcoords = sbt.transf_vecs(tworldmat, tcoords)
            # If we align sources to axes, we ignore target's rotation.
            trotmat = np.identity(3)

        tbounds, tcenter = sbio.get_bounds_and_center(tcoords)

        if not self.axes_align:
            # Even though we want the target bounds in object space if
            # align to axes is false, we still are interested in world
            # scale and center.
            tbounds *= np.array(target.matrix_world.to_scale())
            tcenter = sbt.transf_point(tworldmat, tcenter)
            # target rotation to later apply to all sources
            trotmat = np.array(teuler.to_matrix())

        # SOURCE
        error_happened = False
        for source in context.selected_objects:
            if source is target:
                continue

            if source.type != 'MESH':
                continue

            sdata = source.data
            sverts = sdata.vertices

            if sdata.is_editmode:
                # get selected vertices in source
                source.update_from_editmode()
                sverts_all = sbio.get_vecs(sdata.vertices)
                sselflags = sbio.get_scalars(sdata.vertices)
                sverts_sel = sverts_all[sselflags]

                if len(sverts_sel) < 2:
                    error_happened = True
                    continue
            else:
                sverts_sel = np.array(source.bound_box)

            sbounds, scenter = sbio.get_bounds_and_center(sverts_sel)
            sbounds_recpr = np.reciprocal(
                sbounds,
                # prevent division by 0
                out=np.ones_like(sbounds),
                where=sbounds != 0,
                )

            # assemble transformation matrix later applied to source
            transf_mat = \
                sbmm.to_transl_mat(tcenter) @ \
                sbmm.append_row_and_col(
                    trotmat @
                    sbmm.to_scale_mat(tbounds) @
                    sbmm.euler_to_rot_mat(np.array(self.rot_offset)) @
                    sbmm.to_scale_mat(sbounds_recpr)
                ) @ \
                sbmm.to_transl_mat(-scenter)

            if sdata.is_editmode:
                # somehow the mesh doesn't update if we stay in edit
                # mode
                bpy.ops.object.mode_set(mode='OBJECT')
                # transform transformation matrix from world to object
                # space
                transf_mat = np.array(source.matrix_world.inverted()) \
                    @ transf_mat
                # update every selected vertex with transformed
                # coordinates
                sverts_all[sselflags] = \
                    sbt.transf_vecs(transf_mat, sverts_sel)
                # overwrite complete vertex list (also non-selected)
                sbio.set_vals(sverts, sverts_all)
                bpy.ops.object.mode_set(mode='EDIT')
            else:
                source.matrix_world = Matrix(transf_mat)

        if error_happened:
            self.report(
                {'ERROR_INVALID_INPUT'},
                "Select at least 2 vertices per selected source object"
            )
        return {'FINISHED'}


if __name__ == "__main__":
    register()
