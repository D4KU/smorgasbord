import os
import bgl
import bpy
import gpu
import numpy as np

from mathutils import Matrix
from gpu_extras.batch import batch_for_shader

from smorgasbord.common.decorate import register
from smorgasbord.common.mesh_manip import get_combined_geo
from smorgasbord.common.sample import sample_hemisphere
from smorgasbord.common.transf import transf_pts_unsliced
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
        global shader
        dimx, dimy = self.res
        if not shader:
            shader = read_shader("depthpass")
        shader.bind()
        offbuf = gpu.types.GPUOffScreen(*self.res)

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

        # Isolate active objects' vertices
        verts = verts[:info[0][0]]
        del indcs, info

        # Generate random points on a hemisphere
        rad = 4
        for i in range(self.samplecnt):
            x, y, z, phi, theta = sample_hemisphere(rad)
            transf = make_transf_mat((x, y, z), (theta, 0, phi + np.pi * .5))

            # bpy.ops.object.camera_add()
            # bpy.context.object.matrix_world = Matrix(transf)

            mvp = make_proj_mat(
                clip_start=rad * .75,
                clip_end=rad * 1.5,
                dimx=dimx,
                dimy=dimy,
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
                pxbuf = bgl.Buffer(bgl.GL_BYTE, dimx * dimy)
                bgl.glReadBuffer(bgl.GL_BACK)
                bgl.glReadPixels(0, 0, dimx, dimy, bgl.GL_RED,
                                 bgl.GL_UNSIGNED_BYTE, pxbuf)
                pxbuf = np.array(pxbuf) / 255
                pxbuf.shape = (dimx, dimy)

            # Transform verts of active object to clip space
            # TODO create in Fortran order or sth
            verts_cs = transf_pts_unsliced(mvp, verts)
            # Perspective divide to transform to NDC
            verts_cs /= verts_cs[:, 3:]
            verts_cs *= .5
            verts_cs += .5

            # Remap from NDC to pixel coordinates, or in other words
            # from [-1,1] to [0, dimx] for all x coords and [0, dimy]
            # for all y coords
            # Add .5 to make sure the flooring from conversion to int
            # is actually rounding
            uvs = verts_cs[:, :2] * self.res + .5
            uvs = uvs.astype(np.int32)
            uvs = (uvs[:, 1:2], uvs[:, :1])

            dpth_img = pxbuf[uvs].ravel()
            dpth_verts = verts_cs[:, 2:3].ravel()
            sel = dpth_verts < (dpth_img - .001)
            ob.data.vertices.foreach_set('select', sel)

            # pxbuf = np.repeat(pxbuf, 4)
            # pxbuf.shape = (dimx, dimy, 4)
            # pxbuf[:, :, 3:] = 1
            # pxbuf[uvs] = (1, 0, 0, 1)
            # imgname = "Debug"
            # if imgname not in bpy.data.images:
            #     bpy.data.images.new(imgname, dimx, dimy)
            # image = bpy.data.images[imgname]
            # image.pixels = pxbuf.ravel()

        offbuf.free()
        # context.view_layer.objects.active = ob
        # bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
