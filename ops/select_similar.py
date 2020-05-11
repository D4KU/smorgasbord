import bpy
from bpy_extras import object_utils
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import numpy as np

from smorgasbord.common.io import get_scalars, get_vecs, get_bounds_and_center
from smorgasbord.common.transf import transf_vecs
from smorgasbord.common.decorate import register
from smorgasbord.common.mesh_manip import add_geom_to_bmesh
from smorgasbord.common.spatial_hasher import quantize


def sample_surf(mesh, samplecnt=1000):
    """
    Draw N random samples on the surface of a triangle mesh.

    Parameters
    ----------
    mesh : bpy.types.Mesh
        Blender triangle mesh to sample from.
    samplecnt : int = 1000
        Number of samples to draw.

    Returns
    -------
    out : numpy.ndarray
        2D array with shape (N, 3), containing the coordinates of the
        N drawn sample points.
    """
    # Accumulate all triangle areas in the mesh to sample each triangle 
    # with a probability proportional to its surface area.
    areas = get_scalars(mesh.polygons, 'area', np.float64)
    areas = np.cumsum(areas)
    # Choose N random floats between 0 and the sum of all areas.
    rdareas = np.random.uniform(0., areas[-1], samplecnt)
    # For each random float, find the index of the triangle with the
    # highest, but less equal cumulative area (the left neighbor of the
    # randomly drawn area).
    rdindcs = np.searchsorted(areas, rdareas)
    # These vectorized calculations eat up a lot of memory. Make some
    # unneeded data applicable for garbage collection.
    del areas, rdareas

    # Get the vertex coordinates.
    pts = get_vecs(mesh.vertices)
    # Get the vertex indices for each triangle.
    tris = get_vecs(mesh.polygons, 'vertices', dtype=np.int32)
    # Inner indexing operation: For each randomly chosen triangle index,
    # insert the actual vertex indices of the corresponding triangle
    # into the array.
    # Outer indexing operation: For each vertex index in the triangle
    # array, insert its actual vertex coordinates.
    # This 3D array holds a lot of redundant data now, this probably
    # scales pretty badly with the sample count and the number of
    # triangles.
    tris = pts[tris[rdindcs,:]]
    del rdindcs, pts

    # For each sample, draw two random floats that determine where on
    # the triangle the sample point is placed.
    # This is done via the following formula, with the triangle's
    # vertex coordinate vectors A, B, C:
    # P = (1 - sqrt(r1))*A + sqrt(r1)*(1 - r2)*B + sqrt(r1)*r2*C
    r1 = np.sqrt(np.random.rand(samplecnt))
    r2 = np.random.rand(samplecnt)
    # Calculate coefficients for each vertex A, B, C
    coef = np.stack(
        (1 - r1, r1 * (1 - r2), r1 * r2),
        axis=1,
        ).reshape(-1, 3, 1)
    del r1, r2
    # For each triangle sum up A, B, and C, leaving one point per
    # sample. Remember, one triangle can be several times in 'tris',
    # but a different sample is drawn from its surface every time.
    return np.sum(coef * tris, axis=1)


def create_debug_mesh(context, pts):
    import bmesh as bm
    bob = bm.new()
    add_geom_to_bmesh(bob, pts, [])
    mesh = bpy.data.meshes.new("Samples")
    bob.to_mesh(mesh)
    mesh.update()
    object_utils.object_data_add(context, mesh)


def save_barplot(xvals, yvals, barwidth, xmax, title, filename):
    import matplotlib.pyplot as plt
    plt.clf()
    plt.xlim(right=xmax)
    plt.title(title)
    plt.bar(xvals, yvals, barwidth)
    plt.savefig(filename + ".png")


def draw_points(pts):
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": tuple(pts)})
    shader.bind()
    shader.uniform_float("color", (0.8, 0.3, 0.4, 1))
    batch.draw(shader)


@register
class ReplaceDuplicateMaterials(bpy.types.Operator):
    bl_idname = "select.select_similar"
    bl_label = "Select Similar"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_object]

    samplecnt: bpy.props.IntProperty(
        name="Sample count, even number",
        description="",
        default=512,
        min=16,
        max=16384,
        soft_min=64,
        soft_max=1024,
        step=2,
    )
    bincnt: bpy.props.IntProperty(
        name="Bin count",
        description="",
        default=64,
        min=2,
        max=8192,
        soft_min=16,
        soft_max=512,
    )
    # vertcnt: bpy.props.IntProperty(
    #     name="Vertex count",
    #     description="",
    #     default=4,
    #     min=2,
    #     max=16,
    # )
    # norm: bpy.props.IntProperty(
    #     name="Distance Norm",
    #     description="",
    #     default=1,
    #     min=1,
    #     max=4,
    # )
    handle = None

    def __del__(self):
        self.remove_handle()

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def remove_handle(self):
        if self.handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                self.handle,
                'WINDOW',
                )

    def draw_samples(self, context, pts):
        if context.area.type != 'VIEW_3D':
            self.report(
                {'WARNING'},
                "Samples can only be drawn in the 3D View",
                )
            return

        self.remove_handle()
        self.handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_points,
            (pts,),
            'WINDOW',
            'POST_VIEW',
            )
        context.area.tag_redraw()

    def execute(self, context):
        for o in context.selected_objects:
            if o.type != 'MESH':
                continue
            pts = sample_surf(o.data, self.samplecnt)
            self.draw_samples(context, transf_vecs(o.matrix_world, pts))

            # k=1 eliminates diagonal indices
            i, j = np.triu_indices(self.samplecnt, k=1)
            dist = np.linalg.norm(pts[i] - pts[j], axis=1).ravel()
            del i, j

            bounds, _ = get_bounds_and_center(o.bound_box)
            maxdist = np.ceil(np.linalg.norm(bounds))
            dist = quantize(dist, maxdist / self.bincnt)
            unique, counts = np.unique(dist, return_counts=True)

            save_barplot(
                xvals=unique,
                yvals=counts / self.samplecnt,
                barwidth=maxdist / self.bincnt,
                xmax=maxdist,
                title=(
                    f"Samples: {self.samplecnt}, "
                    f"Bins: {self.bincnt}, "
                    f"Diaglength: {maxdist}",
                ),
                filename=o.name,
                )
        return {'FINISHED'}


if __name__ == "__main__":
    register()
