import os
import bgl
import bpy
import gpu
import numpy as np

from mathutils import Matrix
from gpu_extras.batch import batch_for_shader

from smorgasbord.common.decorate import register
from smorgasbord.common.mesh_manip import get_combined_geo, add_box_to_scene
from smorgasbord.common.sample import sample_hemisphere
from smorgasbord.common.transf import transf_pts_unsliced
from smorgasbord.common.io import get_bounds_and_center
from smorgasbord.common.mat_manip import (
    make_transf_mat,
    make_proj_mat,
    )


shader = None
def read_shader(name):
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
    dim: bpy.props.IntProperty(
            name="Resolution",
            description="",
            default=256,
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
        global shader
        dim = self.dim
        dimhalf = dim * .5
        if not shader:
            shader = read_shader("depthpass")
        shader.bind()
        offbuf = gpu.types.GPUOffScreen(dim, dim)

        # Create batch
        ob = context.object
        obs = [ob]
        for o in context.selected_editable_objects:
            if o.type == 'MESH' and o is not ob:
                obs.append(o)
        verts, indcs, info = get_combined_geo(obs)
        batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": verts},
            indices=indcs,
        )

        bounds, center = get_bounds_and_center(verts)
        rad = np.linalg.norm(bounds[:2]) * .5 + 1
        # bpy.ops.mesh.primitive_circle_add(location=center, radius=rad)

        # Isolate active objects' vertices
        verts = verts[:info[0][0]]
        del indcs, info

        # Generate random points on a hemisphere
        for i in range(self.samplecnt):
            x, y, z, phi, theta = sample_hemisphere(rad)
            transf = make_transf_mat((x, y, z), (theta, 0, phi + np.pi * .5))

            # bpy.ops.object.camera_add()
            # bpy.context.object.matrix_world = Matrix(transf)

            mvp = make_proj_mat(
                fov=90,
                clip_start=rad * .33,
                clip_end=rad * 1.5,
                dimx=dim,
                dimy=dim,
                ) @ np.linalg.inv(transf)
            shader.uniform_float("mvp", Matrix(mvp))
            del transf, x, y, z, phi, theta

            with offbuf.bind():
                bgl.glClearColor(1, 1, 1, 0)
                bgl.glClear(bgl.GL_COLOR_BUFFER_BIT |
                            bgl.GL_DEPTH_BUFFER_BIT)
                bgl.glEnable(bgl.GL_DEPTH_TEST)
                batch.draw(shader)

                # Write texture back to CPU
                pxbuf = bgl.Buffer(bgl.GL_BYTE, dim * dim)
                bgl.glReadBuffer(bgl.GL_BACK)
                bgl.glReadPixels(0, 0, dim, dim, bgl.GL_RED,
                                 bgl.GL_UNSIGNED_BYTE, pxbuf)
                pxbuf = np.array(pxbuf) / 128 - 1
                pxbuf.shape = (dim, dim)

            # Transform verts of active object to clip space
            vcs = transf_pts_unsliced(mvp, verts)
            # Perspective divide to transform to NDC
            vcs /= vcs[:, 3:]

            # Remap from NDC to pixel coordinates, or in other words
            # from [-1,1] to [0, dim]
            # Add .5 to make sure the flooring from conversion to int
            # is actually rounding
            uvs = vcs[:, :2] * dimhalf + (dimhalf + .5)
            uvs = uvs.astype(np.int32)
            invalid = np.any((uvs < 0) | (dim <= uvs), axis=1)
            uvs[invalid] = (0, 0)
            uvs = (uvs[:, 1:2], uvs[:, :1])

            dpth_img = pxbuf[uvs].ravel()
            dpth_verts = vcs[:, 2:3].ravel()
            dpth_verts[invalid] = 2
            sel = dpth_verts < (dpth_img - .001)
            ob.data.vertices.foreach_set('select', sel)

            # pxbuf = np.repeat(pxbuf, 4)
            # pxbuf.shape = (dim, dim, 4)
            # pxbuf *= .5
            # pxbuf += .5
            # pxbuf[:, :, 3:] = 1
            # pxbuf[uvs] = (1, 0, 0, 1)
            # imgname = "Debug"
            # if imgname not in bpy.data.images:
            #     bpy.data.images.new(imgname, dim, dim)
            # image = bpy.data.images[imgname]
            # image.scale(dim, dim)
            # image.pixels = pxbuf.ravel()

        offbuf.free()
        # context.view_layer.objects.active = ob
        # bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
