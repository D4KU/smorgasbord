import bgl
import bpy
import gpu
import numpy as np

from mathutils import Matrix
from gpu_extras.batch import batch_for_shader

from smorgasbord.common.decorate import register
from smorgasbord.common.mesh_manip import combine_meshes
from smorgasbord.common.sample import sample_sphere, sample_hemisphere
from smorgasbord.common.transf import append_one
from smorgasbord.common.io import get_bounds_and_center
from smorgasbord.common.mat_manip import make_transf_mat, make_proj_mat


@register
class SelectVisible(bpy.types.Operator):
    bl_idname = "mesh.select_visible"
    bl_label = "Select Visible"
    bl_description = (
        "Renders edited objects from random positions around them and "
        "selects vertices seen from any position, leaving occluded "
        "vertices unselected"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    samplecnt: bpy.props.IntProperty(
            name="Sample Count",
            description=(
                "Number of times the objects are rendered from "
                "different angles. Lower values decrease calculation "
                "time, but increase the change that visible vertices "
                "are missed"
            ),
            default=16,
    )
    dim: bpy.props.IntProperty(
            name="Resolution",
            description=(
                "Pixel count of the rendered images along one axis. "
                "Lower values decrease calculation time, but increase "
                "the change that a vertex is declared occluded when it "
                "barely peeks out behind an occluder"
            ),
            default=128,
    )
    dom: bpy.props.EnumProperty(
            name="Domain",
            description=(
                "On which surface to sample the render positions. The "
                "radius is chosen adaptively from the bounds of the "
                "objects"
            ),
            items=(
                ('SPHERE', "Sphere", "Also render from the bottom"),
                ('HEMI', "Hemisphere", "Render only from above"),
            )
    )
    _debug_create_img = False
    _debug_spawn_cams = False
    _debug_spawn_sphere = False

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obs = context.objects_in_mode
        # Mesh can't be updated in edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        try:
            self._execute_inner(obs)
        finally:
            if not (self._debug_spawn_cams or self._debug_spawn_sphere):
                bpy.ops.object.mode_set(mode='EDIT')

        # because only vertices are updated, ensure selection is also
        # seen in edge and face mode
        sel_mode = context.tool_settings.mesh_select_mode
        if sel_mode[1] or sel_mode[2]:
            bpy.ops.mesh.select_mode(use_extend=True, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, type='VERT')

        return {'FINISHED'}

    def _execute_inner(self, obs):
        dim = self.dim
        dimhalf = dim * .5
        offbuf = gpu.types.GPUOffScreen(dim, dim)
        sample = sample_sphere if self.dom == 'SPHERE' \
            else sample_hemisphere

        # Construct depthpass shader
        shader = gpu.types.GPUShader(
            vertexcode='''
            uniform mat4 mvp;
            in vec3 pos;
            void main() {
                gl_Position = mvp * vec4(pos, 1);
            }''',
            fragcode='''
            out vec4 col;
            void main() {
                col = vec4(0, 0, 1, 1);
            }'''
        )
        shader.bind()

        # Create batch from all objects in edit mode
        verts, indcs, geoinfo = combine_meshes(obs)
        batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": verts},
            indices=indcs,
        )
        batch.program_set(shader)

        # Find the center and bounds of all objects to calculate the
        # encompassing radius of the (hemi-)sphere on which render
        # positions will be sampled
        bounds, centr = get_bounds_and_center(verts)
        rad = np.linalg.norm(bounds[:2]) * .5 + 1
        del indcs, bounds

        # Spawn debug sphere with calculated radius
        if self._debug_spawn_sphere:
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=rad,
                location=centr,
                )

        # Render the objects from several views and mark seen vertices
        visibl = np.zeros(len(verts), dtype=np.bool)
        for _ in range(self.samplecnt):
            # Generate random points on the chosen domain from which
            # to render the objects
            # Chose rotation so the 'camera' looks to the center
            samplepos, (theta, phi) = sample(rad)
            view_mat_inv = make_transf_mat(
                transl=samplepos + centr,
                rot=(phi, 0, theta + np.pi * .5),
                )

            # Spawn debug camera at sampled position
            if self._debug_spawn_cams:
                bpy.ops.object.camera_add()
                bpy.context.object.matrix_world = Matrix(view_mat_inv)

            # Build the Model View Projection matrix from chosen
            # render position and radius
            # The model matrix has already been applied to the vertices
            # befor creating the batch
            mvp = make_proj_mat(
                fov=90,
                clip_start=rad * .25,
                clip_end=rad * 1.5,
                dimx=dim,
                dimy=dim,
                ) @ np.linalg.inv(view_mat_inv)
            shader.uniform_float("mvp", Matrix(mvp))
            del view_mat_inv, samplepos, theta, phi

            with offbuf.bind():
                # Render the selected objects into the offscreen buffer
                bgl.glDepthMask(bgl.GL_TRUE)
                bgl.glClear(bgl.GL_DEPTH_BUFFER_BIT)
                bgl.glEnable(bgl.GL_DEPTH_TEST)
                batch.draw()

                # Write texture back to CPU
                pxbuf = bgl.Buffer(bgl.GL_FLOAT, dim * dim)
                bgl.glReadBuffer(bgl.GL_BACK)
                bgl.glReadPixels(0, 0, dim, dim, bgl.GL_DEPTH_COMPONENT,
                                 bgl.GL_FLOAT, pxbuf)

            # Map depth values from [0, 1] to [-1, 1]
            pxbuf = np.asanyarray(pxbuf) * 2 - 1
            pxbuf.shape = (dim, dim)

            # Transform verts of active object to clip space
            tverts = mvp @ append_one(verts).T
            # Perspective divide to transform to NDCs [-1, 1]
            tverts /= tverts[3]

            # Find pixel coordinates of each vertex' projected position
            # by remapping x and y coordinates from NDCs to [0, dim]
            # Add .5 to make sure the flooring from conversion to int
            # is actually rounding
            uvs = tverts[:2] * dimhalf + (dimhalf + .5)
            uvs = uvs.astype(np.int32)

            # Map all vertices outside the view frustum to (0, 0)
            # so they don't sample the pixel array out of bounds
            invalid = np.any((uvs < 0) | (dim <= uvs), axis=0)
            uvs.T[invalid] = (0, 0)

            # For each vertex, get the depth at its projected pixel
            # and its distance to the render position
            imgdpth = pxbuf[(uvs[1], uvs[0])]
            camdist = tverts[2]
            # Set the distance of invalid vertices past [-1, 1] so they
            # won't be selected
            camdist[invalid] = 2

            # A vertex is visible if it's inside the view frustum
            # (valid) and not occluded by any face.
            # A vertex is occluded when its depth sampled from the
            # image is smaller than its distance to the camera.
            # A small error margin is added to prevent self-occlusion.
            # The result is logically or-ed with the result from other
            # render positions.
            visibl |= camdist <= (imgdpth + .001)

            # Create debug image of the rendered view
            if self._debug_create_img:
                # Grayscale to RGBA and [-1, 1] to [0, 1]
                pxbuf = np.repeat(pxbuf, 4) * .5 + .5
                pxbuf.shape = (dim, dim, 4)
                # Alpha channel is 1
                pxbuf[:, :, 3] = 1
                # Mark projected vertex positions in red
                pxbuf[(uvs[1], uvs[0])] = (1, 0, 0, 1)

                imgname = "Debug"
                if imgname not in bpy.data.images:
                    bpy.data.images.new(imgname, dim, dim)
                image = bpy.data.images[imgname]
                image.scale(dim, dim)
                image.pixels = pxbuf.ravel()

        # Split visible flag list back in original objects
        offbuf.free()
        start = 0
        for o, (end, _) in zip(obs, geoinfo):
            o.data.vertices.foreach_set('select', visibl[start:end])
            start = end
