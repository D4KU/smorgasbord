import bpy
import mathutils as mu
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
    )

    rotation_offset: bpy.props.FloatVectorProperty(
        name = "Rotation Offset",
        description = "Rotational offset from source to target",
        subtype = 'EULER',
        step = 9000.0,          # 90 deg
        soft_min = -4.71239,    # -270 deg in rad
        soft_max = 4.71239,     # 270 deg in rad
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
        euler_target = target.matrix_world.to_euler()

        if target.data.is_editmode:
            # ensure newest changes from edit mode are visible to data
            target.update_from_editmode()

            # get selected vertices in target
            sel_flags_target = get_vert_sel_flags(target)
            verts_target = get_verts(target)
            verts_target = verts_target[sel_flags_target]
        else:
            rot_target = np.array(euler_target)

            # If we align to axes and the target is rotated, we can't use
            # Blender's bounding box. Instead, we have to find the global
            # bounds from all global vertex positions.
            # This is because for a rotated object, the global bounds of its
            # local bounding box aren't always equal to the global bounds of
            # all its vertices.
            # If we don't align to axes, we aren't interested in the global
            # target bounds anyway.
            verts_target = get_verts(target) \
                if self.align_to_axes \
                and rot_target.dot(rot_target) > 0.001 \
                else np.array(target.bound_box)

        if len(verts_target) < 2:
            self.report({'ERROR_INVALID_INPUT'},
                        "Select at least 2 vertices")
            return {'CANCELLED'}

        mat_world_target = np.array(target.matrix_world)

        if self.align_to_axes:
            # If we align sources to world axes, we are interested in the
            # target bounds in world coordinates.
            verts_target = transf_verts(mat_world_target, verts_target)
            # If we align sources to axes, we ignore target's rotation.
            rot_mat_target = np.identity(3)

        bounds_target, center_target = get_bounds_and_center(verts_target)

        if not self.align_to_axes:
            # Even though we want the target bounds in object space if align
            # to axes is false, we still are interested in world scale and
            # center.
            bounds_target *= np.array(target.matrix_world.to_scale())
            center_target = transf_point(mat_world_target, center_target)
            # target rotation to later apply to all sources
            rot_mat_target = np.array(euler_target.to_matrix())

        # SOURCE
        error_happened = False
        for source in context.selected_objects:
            if source is target:
                continue

            if source.data.is_editmode:
                # get selected vertices in source
                source.update_from_editmode()
                all_verts_source = get_verts(source)
                sel_flags_source = get_vert_sel_flags(source)
                sel_verts_source = all_verts_source[sel_flags_source]

                if len(sel_verts_source) < 2:
                    error_happened = True
                    continue
            else:
                sel_verts_source = np.array(source.bound_box)

            bounds_source, center_source = get_bounds_and_center(sel_verts_source)

            # prevent division by 0
            bounds_source[bounds_source == 0] = 1

            # assemble transformation matrix later applied to source
            transf_mat = \
                to_transl_mat(center_target) @ \
                append_row_and_col( \
                    rot_mat_target @ \
                    to_scale_mat(bounds_target) @ \
                    euler_to_rot_mat(np.array(self.rotation_offset)) @ \
                    to_scale_mat(1 / bounds_source)) @ \
                to_transl_mat(-center_source)

            if source.data.is_editmode:
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
                source.matrix_world = mu.Matrix(transf_mat)

        if error_happened:
            self.report({'ERROR_INVALID_INPUT'},
                        "Select at least 2 vertices per selected source object")
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
