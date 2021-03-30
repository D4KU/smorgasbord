import os
import bgl
import bpy
import gpu
import numpy as np

from mathutils import Matrix
from random import random
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_texture_2d

from smorgasbord.common.decorate import register
from smorgasbord.common.io import get_vecs
from smorgasbord.common.mesh_manip import get_combined_geo
from smorgasbord.common.transf import transf_pts_unsliced
from smorgasbord.common.mat_manip import (
    make_proj_mat,
    to_transl_mat,
    euler_to_rot_mat,
    append_row_and_col,
    )


def get_shader(name):
    path = os.path.realpath(__file__)
    path = os.path.dirname(path) + "/../shader/" + name
    with open(path + ".vert") as f:
        vert = f.read()
    with open(path + ".frag") as f:
        frag = f.read()

    return gpu.types.GPUShader(vert, frag)


@register
class SelectHidden(bpy.types.Operator):
    bl_idname = "mesh.select_hidden"
    bl_label = "Select Hidden"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_select_object,
        bpy.types.VIEW3D_MT_select_edit_mesh,
    ]

    samplecnt: bpy.props.IntProperty(
            name="Sample Count",
            description="",
            default=1,
    )
    res: bpy.props.IntVectorProperty(
            name="Resolution",
            description="",
            size=2,
            default=(256, 256),
    )
    onsphere: bpy.props.BoolProperty(
            name="Sample whole sphere",
            description="",
            default=False,
    )

    @classmethod
    def poll(cls, context):
        a = context.mode == 'OBJECT'
        b = context.object is not None
        return a and b and context.object.type == 'MESH'

    def execute(self, context):
        dimx, dimy = self.res
        reshalf = np.array(self.res) * .5
        depth_shader = get_shader("depthpass")
        depth_shader.bind()
        # comp_shader = get_shader("compare")
        offbuf = gpu.types.GPUOffScreen(*self.res)

        # Create batch
        ob = context.object
        obs = context.selected_editable_objects
        obs = [o for o in obs if o is not ob and o.type == 'MESH']
        # TODO remember which ones are ob's vertices
        obs.append(ob)
        verts, indcs = get_combined_geo(obs)
        batch = batch_for_shader(
            depth_shader, 'TRIS',
            {"pos": verts},
            indices=indcs,
        )

        # Generate random points on a hemisphere
        rad = 4
        sel = None
        for i in range(self.samplecnt):
            costheta = np.sqrt(random())
            theta = np.arccos(costheta)
            sintheta = rad * np.sin(theta)
            phi = 2 * np.pi * random()

            x = sintheta * np.cos(phi)
            y = sintheta * np.sin(phi)
            z = rad * costheta

            rot = euler_to_rot_mat((0, theta, phi)) \
                @ euler_to_rot_mat((0, 0, np.pi * .5))
            tranf = to_transl_mat((x, y, z)) @ append_row_and_col(rot)

            view_mat = np.linalg.inv(tranf)
            proj_mat = make_proj_mat(
                clip_start=rad * .75,
                clip_end=rad,
                dimx=dimx,
                dimy=dimy,
                )
            mvp = proj_mat @ view_mat
            depth_shader.uniform_float("mvp", Matrix(mvp))
            # comp_shader.bind()
            # comp_shader.uniform_float("mvp", mvp)

            # bpy.ops.object.camera_add()
            # bpy.context.object.matrix_world = Matrix(tranf)

            offbuf.bind()
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            batch.draw(depth_shader)
            # bgl.glActiveTexture(bgl.GL_TEXTURE0)
            # bgl.glBindTexture(bgl.GL_TEXTURE_2D, offbuf.color_texture)
            # comp_shader.uniform_int("depthtex", 0)
            # batch.draw(comp_shader)
            bgl.glDisable(bgl.GL_DEPTH_TEST)

            # Write texture back to CPU
            pxbuf = bgl.Buffer(bgl.GL_BYTE, dimx * dimy * 4)
            bgl.glReadBuffer(bgl.GL_BACK)
            bgl.glReadPixels(0, 0, dimx, dimy, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, pxbuf)
            pxbuf = np.array(pxbuf)
            pxbuf.shape = (dimx, dimy, 4)

            # Filter out red channel
            pxbuf = pxbuf[:, :, :1]
            pxbuf.shape = (dimx, dimy)

            # Transform verts to clip space
            # TODO create in Fortran order or sth
            verts_cs = transf_pts_unsliced(mvp, verts)
            # Perspective divide to transform to NDC
            uvs = verts_cs[:, :2] / verts_cs[:, 3:]

            # Remap from NDC to pixel coordinates, or in other words
            # from [-1,1] to [0, dimx] for all x coords and [0, dimy]
            # for all y coords
            # Finally add .5 to make sure the flooring from conversion
            # to int is actually rounding
            # This is '(a * .5 + .5) * res + .5' rearranged to
            # 'a * (res * .5) + (res * .5 + .5)' to save instructions
            uvs *= reshalf
            uvs += reshalf + .5
            uvs = uvs.astype(np.int32)

            # Sample pixel corresponding to each vertex
            # Convert from numpy array indexing to tuple indexing
            pxs = pxbuf[tuple(uvs.T)]
            pxs = pxs.ravel()
            depths = verts_cs[:, 2:3]
            depths = depths.ravel()
            sel = depths > pxs
            breakpoint()
            del pxbuf

            ta = i * 10
            tb = ta + 10
            def draw():
                draw_texture_2d(offbuf.color_texture, (ta, ta), tb, tb)
            bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')



        # offbuf.free()
        return {'FINISHED'}
