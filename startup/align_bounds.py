import bmesh
import bpy
from mathutils import Matrix
import numpy as np
import os
import sys

# make sure blender sees custom modules
dir = os.path.join(bpy.utils.script_path_pref(), 'modules')
if not dir in sys.path:
    sys.path.append(dir)

import common
# force reload in case source was edited after blender session started
import imp
imp.reload(common)
# optional
from common import *


class AlignBounds(bpy.types.Operator):
    bl_idname = "transform.align_bounds"
    bl_label = "Align Bounds"
    bl_description = "Transform selected objects so that their bounds match the active object"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_transform_object,
        bpy.types.VIEW3D_MT_transform
    ]

    align_to_axes: bpy.props.BoolProperty(
        name = "Align to Axes",
        description = "Align the source objects/vertices to the world axes instead of the target object rotation",
        default = False
    )

    delete_target: bpy.props.BoolProperty(
        name = "Delete Target",
        description = "Delete target object/vertices after operation finished",
        default = False
    )

    @classmethod
    def description(cls, context, properties):
        if context.mode == 'EDIT_MESH':
            return "Transform selected vertices of selected objects so that their bounds match the selected vertices of the active object"
        else:
            return cls.bl_description

    @classmethod
    def poll(cls, context):
        a = context.object is not None
        b = len(context.selected_objects) >= 2
        return a and b

    def execute(self, context):
        # TARGET
        target = context.object

        if target.data.is_editmode:
            # make sure newest changes from edit mode are visible to Blender's
            # data
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()

            sel_flags_target = get_vert_sel_flags(target)
            verts_target = get_verts(target)
            verts_target = verts_target[sel_flags_target]

            if len(verts_target) < 3:
                self.report({'ERROR_INVALID_INPUT'}, "Select at least 3 vertices")
                return {'CANCELLED'}
        else:
            verts_target = np.array(target.bound_box)

        mat_world_target = np.array(target.matrix_world)

        if self.align_to_axes:
            # if we align sources to world axes, we are interested in the
            # target bounds in world coordinates
            verts_target = transf_verts(mat_world_target, verts_target)

        bounds_target, center_target = get_bounds_and_center(verts_target)

        if not self.align_to_axes:
            # even though we want the target bounds in object space if align
            # to axes is false, we still are interested in world scale and
            # center
            bounds_target *= np.array(target.matrix_world.to_scale())
            center_target = transf_point(mat_world_target, center_target)

        # SOURCE
        for source in context.selected_objects:
            if source is target:
                continue

            if target.data.is_editmode:
                if len(source.data.vertices) < 3:
                   continue

                all_verts_source = get_verts(source)
                sel_flags_source = get_vert_sel_flags(source)
                sel_verts_source = all_verts_source[sel_flags_source]
            else:
                sel_verts_source = np.array(source.bound_box)

            bounds_source, center_source = get_bounds_and_center(sel_verts_source)

            # prevent division by zero if source bounds are zero in at least
            # one dimension
            bounds_source[bounds_source == 0] = 1

            # source scale so that source bounds match target bounds
            scale = bounds_target / bounds_source
            # offset from the target center so that the source pivot is set to
            # a position that make the source and target centers match
            offset = center_source * scale

            if self.align_to_axes:
                rot_mat = np.identity(3)
            else:
                rot_mat = np.array(target.matrix_world.to_euler().to_matrix())
                offset = rot_mat @ offset

            pos_mat = to_transl_mat(center_target - offset)
            sc_mat = np.identity(3) * scale
            transf_mat = pos_mat @ append_row_and_col(rot_mat @ sc_mat)

            if target.data.is_editmode:
                # somehow the mesh doesn't update if we stay in edit mode
                bpy.ops.object.mode_set(mode='OBJECT')
                # transform transformation matrix from world to object space
                transf_mat = np.array(source.matrix_world.inverted()) @ transf_mat
                # update every selected vertex with transformed coordinates
                all_verts_source[sel_flags_source] = transf_verts(transf_mat, sel_verts_source)
                # overwrite complete vertex list (also non-selected)
                set_verts(source, all_verts_source)
                bpy.ops.object.mode_set(mode='EDIT')
            else:
                source.matrix_world = Matrix(transf_mat)

        # DELETION
        if self.delete_target:
            if target.data.is_editmode:
                bm = bmesh.from_edit_mesh(target.data)
                del_verts = np.array(bm.verts)[sel_flags_target]
                bmesh.ops.delete(bm, geom=del_verts.tolist(), context='VERTS')
                bmesh.update_edit_mesh(target.data)
            else:
                bpy.data.objects.remove(target)

        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(AlignBounds.bl_idname)

def register():
    bpy.utils.register_class(AlignBounds)
    for m in AlignBounds.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(AlignBounds)
    for m in AlignBounds.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
