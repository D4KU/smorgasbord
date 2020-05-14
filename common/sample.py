import bpy
import numpy as np

from smorgasbord.common.io import get_scalars, get_vecs


def sample_surf(mesh, samplecnt=1024):
    """
    Draw N random samples on the surface of a triangle mesh.

    Parameters
    ----------
    mesh : bpy.types.Mesh
        Blender triangle mesh to sample from.
    samplecnt : int = 1024
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
    tris = pts[tris[rdindcs, :]]
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


def get_shape_distrib(points, bincnt=32):
    """
    Calculate a shape distribution from a set of points.
    :param points: List-like object of points to calculate the
        distribution for.
    :param bincnt: Resolution of the distribution: the bin count
        of the histogram representing the distribution.
    """
    points = np.asanyarray(points)
    # k=1 eliminates diagonal indices
    i, j = np.triu_indices(len(points), k=1)
    return np.histogram(
        np.linalg.norm(points[i] - points[j], axis=1),
        bins=bincnt,
        density=True,
        )
