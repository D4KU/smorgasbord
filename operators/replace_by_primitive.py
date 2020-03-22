import bpy
import smorgasbord.functions.common as sb
import mathutils as mu
import numpy as np
import statistics as st


class ReplaceByPrimitive(bpy.types.Operator):
    bl_idname = "mesh.replace_by_primitive"
    bl_label = "Replace By Primitive"
    bl_description = "Replace an object by a geometric primitive with identical transform"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_transform_object,
        bpy.types.VIEW3D_MT_transform
    ]
    metric = max

    replace_by: bpy.props.EnumProperty(
        name = "Replace By",
        description = "By which geometric primitive should the selected object/vertices be replaced?",
        items = (
            ('CUBOID', "Cuboid", "Replace selected object by a cuboid"),
            ('CYLINDER_Z', "Cylinder Z", "Replace selected object by a cylinder in Z direction"),
            ('CYLINDER_Y', "Cylinder Y", "Replace selected object by a cylinder in Y direction"),
            ('CYLINDER_X', "Cylinder X", "Replace selected object by a cylinder in X direction"),
            ('SPHERE', "Sphere", "Replace selected object by a UV-sphere")
        ),
        default = 'CUBOID',
    )

    fit_metric: bpy.props.EnumProperty(
        name = "Fit Metric",
        description = "Metric used to fit the primitive to the object",
        items = (
            ('MIN', "Minimum", "The primitive is inside the object's bounds for certain, but may be smaller"),
            ('MAX', "Maximum", "The primitive's bounds enclose the object's bounds for certain, but may be bigger"),
            ('AVG', "Average", "Blend between Min and Max metric"),
        ),
        default = 'MAX',
    )

    resolution: bpy.props.IntProperty(
        name = "Resolution",
        description = "Subdivisions of the created primitive. Does not effect all choices.",
        subtype = 'UNSIGNED',
        soft_min = 3,
        default = 8,
    )

    align_to_axes: bpy.props.BoolProperty(
        name = "Align to Axes",
        description = "Align the primitive to the world axes instead of the selected objects' rotation",
    )

    delete_original: bpy.props.BoolProperty(
        name = "Delete Original",
        description = "Delete selected object/vertices after operation finished",
        default = False,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    @classmethod
    def description(cls, context, properties):
        if context.mode == 'EDIT_MESH':
            return "Replace selected vertices by a geometric primitive with identical transform as the active object"
        else:
            return cls.bl_description

    def execute(self, context):
        if self.fit_metric == 'MIN':
            self.metric = min
        elif self.fit_metric == 'MAX':
            self.metric = max
        else:
            self.metric = st.mean

        all_type_err = True # no obj is of type mesh

        for target in context.selected_objects:
            if target.type == 'MESH':
                all_type_err = False
            else:
                continue

            rotation = target.matrix_world.to_euler()

            if target.data.is_editmode:
                # ensure newest changes from edit mode are visible to data
                target.update_from_editmode()

                # get selected vertices in target
                sel_flags_target = sb.get_vert_sel_flags(target)
                verts_target = sb.get_verts(target)
                verts_target = verts_target[sel_flags_target]
            else:
                rot_target = np.array(rotation)

                # If we align to axes and the target is rotated, we can't use
                # Blender's bounding box. Instead, we have to find the global
                # bounds from all global vertex positions.
                # This is because for a rotated object, the global bounds of its
                # local bounding box aren't always equal to the global bounds of
                # all its vertices.
                # If we don't align to axes, we aren't interested in the global
                # target bounds anyway.
                verts_target = sb.get_verts(target) \
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
                verts_target = sb.transf_verts(mat_world_target, verts_target)
                # If we align sources to axes, we ignore target's rotation.
                rotation = mu.Euler()

            bounds, center = sb.get_bounds_and_center(verts_target)

            if not self.align_to_axes:
                # Even though we want the target bounds in object space if align
                # to axes is false, we still are interested in world scale and
                # center.
                bounds *= np.array(target.matrix_world.to_scale())
                center = sb.transf_point(mat_world_target, center)

            if self.delete_original:
                if target.data.is_editmode:
                    bpy.ops.mesh.delete()
                else:
                    bpy.data.objects.remove(target)

            if self.replace_by == 'CYLINDER_Z':
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=self.resolution,
                    radius=self.metric(bounds[:2]) * 0.5,
                    depth=bounds[2],
                    end_fill_type='TRIFAN',
                    location=center,
                    rotation=rotation)
            elif self.replace_by == 'CYLINDER_Y':
                rotation.rotate(mu.Euler((1.57, 0.0, 0.0)))
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=self.resolution,
                    radius=self.metric(bounds[::2]) * 0.5,
                    depth=bounds[1],
                    end_fill_type='TRIFAN',
                    location=center,
                    rotation=rotation)
            elif self.replace_by == 'CYLINDER_X':
                rotation.rotate(mu.Euler((0.0, 1.57, 0.0)))
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=self.resolution,
                    radius=self.metric(bounds[1:]) * 0.5,
                    depth=bounds[0],
                    end_fill_type='TRIFAN',
                    location=center,
                    rotation=rotation)
            elif self.replace_by == 'CUBOID':
                bpy.ops.mesh.primitive_cube_add(
                    size=1,
                    location=center,
                    rotation=rotation)
                bpy.ops.transform.resize(
                    value=bounds,
                    orient_type='GLOBAL' if self.align_to_axes else 'LOCAL')
            elif self.replace_by == 'SPHERE':
                bpy.ops.mesh.primitive_uv_sphere_add(
                    segments=self.resolution * 2,
                    ring_count=self.resolution,
                    radius=self.metric(bounds) * 0.5,
                    location=center,
                    rotation=rotation)

        if all_type_err:
            self.report({'ERROR_INVALID_INPUT'},
                        "An object must be of type mesh")
            return {'CANCELLED'}
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(ReplaceByPrimitive.bl_idname)

def register():
    bpy.utils.register_class(ReplaceByPrimitive)
    for m in ReplaceByPrimitive.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(ReplaceByPrimitive)
    for m in ReplaceByPrimitive.menus:
        m.remove(draw_menu)

if __name__ == "__main__":
    register()

