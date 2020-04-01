import numpy as np


def homogenize(verts):
    """
    homogenize(verts)
    Transform a vertex list from Cartesian into homogeneous coordinates by
    adding a coordinate to every vertex, which is equal to one.

    Parameters
    ----------
    verts : numpy.ndarray
        Vertex list to homogenize.

    Returns
    -------
    verts_homog : numpy.ndarray
        Copy of 'verts' with homogenized coordinates.

    Examples
    --------
    >>> homogenize(np.array([[0, 1, 2], [3, 4, 5]]))
    array([[0, 1, 2, 1], [3, 4, 5, 1]])
    """
    verts_homog = np.ones(np.add(verts.shape, (0,1)), dtype=verts.dtype)
    verts_homog[:,:-1] = verts
    return verts_homog


def transf_verts(mat, verts):
    """
    transf_verts(mat, verts)
    Apply a transformation matrix to every vertex in a list.

    Parameters
    ----------
    mat : numpy.ndarray
        4x4 transformation matrix to apply to every vertex.
    verts : numpy.ndarray
        List of 3D vertices

    Returns
    -------
    verts : numpy.ndarray
        Copy of 'verts' with transformed vertex coordinates.
    """
    return (mat @ homogenize(verts).T).T[:,:3]


def transf_point(mat, point):
    """
    transf_point(mat, point)
    Apply a transformation matrix to a point.

    Parameters
    ----------
    mat : numpy.ndarray
        4x4 transformation matrix to apply.
    point : numpy.ndarray
        3D point to transform.

    Returns
    -------
    verts : numpy.ndarray
        Copy of 'point' with transformed coordinates.
    """
    return (mat @ np.append(point, 1))[:3]


def transf_dist(mat, dist):
    """
    transf_point(mat, point)
    Apply a transformation matrix to a distance vector.

    Parameters
    ----------
    mat : numpy.ndarray
        4x4 transformation matrix to apply.
    point : numpy.ndarray
        3D vector of distance to transform.

    Returns
    -------
    verts : numpy.ndarray
        Copy of 'dist' with transformed coordinates.
    """
    return mat[:3,:3] @ dist

