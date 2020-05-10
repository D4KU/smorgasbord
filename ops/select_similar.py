import bpy
from bpy_extras import object_utils
import numpy as np
import matplotlib
import sys
# sys.path.append('/usr/lib/python3.7/tkinter/')
# matplotlib.use('TKAgg', warn=True, force=True)
import matplotlib.pyplot as plt

from smorgasbord.common.io import get_scalars, get_vecs, get_bounds_and_center
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


def create_debug_mesh(pts):
    bob = bm.new()
    add_geom_to_bmesh(bob, pts, [])
    mesh = bpy.data.meshes.new("Samples")
    bob.to_mesh(mesh)
    mesh.update()
    object_utils.object_data_add(context, mesh)


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
        default=10000,
        min=2,
        max=10000,
        step=2,
    )
    bincnt: bpy.props.IntProperty(
        name="Bin count",
        description="",
        default=1024,
        min=1,
        max=1024,
    )
    # vertcnt: bpy.props.IntProperty(
    #     name="Vertex count",
    #     description="",
    #     default=4,
    #     min=2,
    #     max=16,
    # )
    norm: bpy.props.IntProperty(
        name="Distance Norm",
        description="",
        default=1,
        min=1,
        max=4,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for o in context.selected_objects:
            if o.type != 'MESH':
                continue
            pts = sample_surf(o.data, self.samplecnt)
            dist = np.diff(pts.reshape(-1, 2, 3), axis=1)
            dist = np.linalg.norm(dist, ord=self.norm, axis=2).ravel()

            bounds, _ = get_bounds_and_center(o.bound_box)
            maxdist = np.ceil(np.linalg.norm(bounds, ord=self.norm))
            dist = quantize(dist, maxdist / self.bincnt)
            unique, counts = np.unique(dist, return_counts=True)

            plt.clf()
            plt.xlim(right=maxdist)
            plt.title((
                f"Samples: {self.samplecnt}, "
                f"Bins: {self.bincnt}, "
                f"Diaglength: {maxdist}",
            ))
            plt.bar(
                unique,
                counts / self.samplecnt,
                maxdist / self.bincnt,
                )
            plt.savefig(o.name + ".png")

        return {'FINISHED'}


if __name__ == "__main__":
    register()
