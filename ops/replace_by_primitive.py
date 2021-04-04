import bpy
import bmesh as bm
from functools import partial
from mathutils import Euler
import numpy as np
from statistics import mean

import smorgasbord.common.io as sbio
import smorgasbord.common.mesh_manip as sbmm
import smorgasbord.common.transf as sbt
import smorgasbord.common.decorate as sbd


@sbd.register
class ReplaceByPrimitive(bpy.types.Operator):
    bl_idname = "mesh.replace_by_primitive"
    bl_label = "Replace By Primitive"
    bl_description = (
        "Replace an object by a geometric primitive with "
        "identical transform"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_transform_object,
        bpy.types.VIEW3D_MT_transform
    ]
    metric = max

    replace_by: bpy.props.EnumProperty(
        name="Replace By",
        description="By which geometric primitive should the selected "
        "object/vertices be replaced?",
        items=(
            ('CUBOID', "Cuboid", "Replace selected object by a cuboid"),
            ('CYLINDER_Z', "Cylinder Z", "Replace selected object by "
             "a cylinder in Z direction"),
            ('CYLINDER_Y', "Cylinder Y", "Replace selected object by "
             "a cylinder in Y direction"),
            ('CYLINDER_X', "Cylinder X", "Replace selected object by "
             "a cylinder in X direction"),
            ('SPHERE', "Sphere", "Replace selected object by a UV-sphere")
        ),
        default='CUBOID',
    )

    fit_metric: bpy.props.EnumProperty(
        name="Fit Metric",
        description="Metric used to fit the primitive to the object",
        items=(
            ('MIN', "Minimum", "The primitive is inside the object's "
             "bounds for certain, but may be smaller"),
            ('MAX', "Maximum", "The primitive's bounds enclose the "
             "object's bounds for certain, but may be bigger"),
            ('AVG', "Average", "Blend between Min and Max metric"),
        ),
        default='MAX',
    )

    resolution: bpy.props.IntProperty(
        name="Resolution",
        description="Subdivisions of the created primitive. Does not "
        "affect all choices",
        subtype='UNSIGNED',
        soft_min=3,
        default=8,
    )

    align_to_axes: bpy.props.BoolProperty(
        name="Align to Axes",
        description="Align the primitive to the world axes instead of "
        "the active objects' rotation",
    )

    join_select: bpy.props.BoolProperty(
        name="Join Multi-Selection",
        description="When (vertices of) several objects are "
        "selected, join selection into one primitive",
    )

    delete_original: bpy.props.BoolProperty(
        name="Delete Original",
        description="Delete selected object/vertices after operation "
        "finished",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    @classmethod
    def description(cls, context, properties):
        if context.mode == 'EDIT_MESH':
            return (
                "Replace selected vertices by a geometric "
                "primitive with identical transform as the active "
                "object"
            )
        else:
            return cls.bl_description

    def _core(self, context, ob, verts, to_del=[]):
        if len(verts) < 2:
            self.report({'ERROR_INVALID_INPUT'},
                        "Select at least 2 vertices")
            return

        mat_wrld = np.array(ob.matrix_world)
        in_editmode = context.mode == 'EDIT_MESH'

        if self.align_to_axes:
            # If we align sources to world axes, we are interested in
            # the bounds in world coordinates.
            verts = sbt.transf_pts(mat_wrld, verts)
            # If we align sources to axes, we ignore ob's rotation.
            rotation = Euler()

        bounds, center = sbio.get_bounds_and_center(verts)

        if not self.align_to_axes:
            # Even though we want the ob bounds in object space if align
            # to axes is false, we still are interested in world scale
            # and center.
            bounds *= np.array(ob.matrix_world.to_scale())
            center = sbt.transf_point(mat_wrld, center)
            rotation = ob.matrix_world.to_euler()

        if self.delete_original and in_editmode:
            mode = context.tool_settings.mesh_select_mode
            if mode[0]:
                del_type = 'VERTS'
            elif mode[1]:
                del_type = 'EDGES'
            else:
                del_type = 'FACES'
            for o in to_del:
                sbmm.remove_selection(o.data, type=del_type)

        if self.replace_by == 'CYLINDER_Z':
            bpy.ops.mesh.primitive_cylinder_add(
                {'active_object': ob},
                vertices=self.resolution,
                radius=self.metric(bounds[:2]) * 0.5,
                depth=bounds[2],
                end_fill_type='TRIFAN',
                location=center,
                rotation=rotation)
        elif self.replace_by == 'CYLINDER_Y':
            rotation.rotate(Euler((1.57, 0.0, 0.0)))
            bpy.ops.mesh.primitive_cylinder_add(
                {'active_object': ob},
                vertices=self.resolution,
                radius=self.metric(bounds[::2]) * 0.5,
                depth=bounds[1],
                end_fill_type='TRIFAN',
                location=center,
                rotation=rotation)
        elif self.replace_by == 'CYLINDER_X':
            rotation.rotate(Euler((0.0, 1.57, 0.0)))
            bpy.ops.mesh.primitive_cylinder_add(
                {'active_object': ob},
                vertices=self.resolution,
                radius=self.metric(bounds[1:]) * 0.5,
                depth=bounds[0],
                end_fill_type='TRIFAN',
                location=center,
                rotation=rotation)
        elif self.replace_by == 'CUBOID':
            if in_editmode:
                sbmm.add_box_to_obj(
                    ob=ob,
                    location=center,
                    rotation=rotation,
                    size=bounds)
            else:
                sbmm.add_box_to_scene(context, center, rotation, bounds)
        elif self.replace_by == 'SPHERE':
            bpy.ops.mesh.primitive_uv_sphere_add(
                {'active_object': ob},
                segments=self.resolution * 2,
                ring_count=self.resolution,
                radius=self.metric(bounds) * 0.5,
                location=center,
                rotation=rotation)

        if not in_editmode:
            # apply material if existent in original
            try:
                mat = ob.data.materials[0]
            except IndexError:
                pass
            else:
                context.object.data.materials.append(mat)

            if self.delete_original:
                for o in to_del:
                    bpy.data.objects.remove(o)

    def _exec_obj_mode(self, context):
        all_type_err = True  # no obj is of type mesh

        if self.join_select:
            coords = np.empty((0, 3), dtype=float)
            ob = context.object if context.object else \
                context.selected_objects[0]
            mat_wrld_inv = np.array(ob.matrix_world.inverted())

            for o in context.selected_objects:
                if o.type == 'MESH':
                    all_type_err = False
                else:
                    continue

                ocoords = sbio.get_vecs(o.data.vertices)

                if o is not ob:
                    mat = mat_wrld_inv @ np.array(o.matrix_world)
                    ocoords = sbt.transf_pts(mat, ocoords)

                coords = np.concatenate((coords, ocoords))

            self._core(context, ob, coords, context.selected_objects)
        else:
            for o in context.selected_objects:
                if o.type == 'MESH':
                    all_type_err = False
                else:
                    continue

                # If we align to axes and the ob is rotated, we can't
                # use Blender's bounding box. Instead, we have to find
                # the global bounds from all global vertex positions.
                # This is because for a rotated object, the global
                # bounds of its local bounding box aren't always equal
                # to the global bounds of all its vertices.
                # If we don't align to axes, we aren't interested in the
                # global ob bounds anyway.
                rot = np.array(o.matrix_world.to_euler())
                coords = sbio.get_vecs(o.data.vertices) \
                    if self.align_to_axes and rot.dot(rot) > 0.001 \
                    else np.array(o.bound_box)

                self._core(context, o, coords, [o])

        if all_type_err:
            self.report({'ERROR_INVALID_INPUT'},
                        "An object must be of type mesh")
            return {'CANCELLED'}

    def _exec_edit_mode(self, context):
        sel_obs = context.selected_objects

        def wrap_core(core, ob, sel_flags):
            """
            Do stuff before and after core function call
            """
            # get first material index of selected mesh part
            bob = bm.from_edit_mesh(ob.data)
            matidx = 0
            vindcs = np.nonzero(sel_flags)[0]
            bverts = bob.verts
            bverts.ensure_lookup_table()
            for vidx in vindcs:
                bvert = bverts[vidx]
                try:
                    matidx = bvert.link_faces[0].material_index
                except IndexError:
                    pass
                else:
                    break

            core()

            # apply material index to newly added faces
            ob.update_from_editmode()
            sel_flags = sbio.get_scalars(ob.data.polygons)
            bfaces = bob.faces
            bfaces.ensure_lookup_table()
            for fidx in np.nonzero(sel_flags)[0]:
                bfaces[fidx].material_index = matidx
            bm.update_edit_mesh(ob.data)

        def get_sel_verts(o):
            # ensure newest changes from edit mode are
            # visible to data
            o.update_from_editmode()
            sel_flags = sbio.get_scalars(o.data.vertices)
            return sbio.get_vecs(o.data.vertices)[sel_flags], sel_flags

        if self.join_select:
            verts = np.empty((0, 3), dtype=float)
            ob = context.object if context.object else sel_obs[0]
            mat_wrld_inv = np.array(ob.matrix_world.inverted())

            # concatenate verts from all selected objects
            for o in sel_obs:
                verts_o, sel_flags = get_sel_verts(o)

                # transform every vertex into coord system of active
                # object
                if o is not ob:
                    mat = mat_wrld_inv @ np.array(o.matrix_world)
                    verts_o = sbt.transf_pts(mat, verts_o)

                verts = np.concatenate((verts, verts_o))

            core = partial(self._core, context, ob, verts, sel_obs)
            wrap_core(core, ob, sel_flags)
        else:
            for o in sel_obs:
                verts, sel_flags = get_sel_verts(o)
                core = partial(self._core, context, o, verts, [o])
                wrap_core(core, o, sel_flags)

    def execute(self, context):
        if self.fit_metric == 'MIN':
            self.metric = min
        elif self.fit_metric == 'MAX':
            self.metric = max
        else:
            self.metric = mean

        if context.mode == 'EDIT_MESH':
            self._exec_edit_mode(context)
        else:
            self._exec_obj_mode(context)

        return {'FINISHED'}


if __name__ == "__main__":
    register()
