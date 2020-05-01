import numpy as np


def homog_vecs(vecs):
    """
    Transform a vector list from Cartesian into homogeneous coordinates
    by adding a coordinate equal to one to every vector.

    Parameters
    ----------
    vecs : Iterable
        Vector list to homogenize.

    Returns
    -------
    hvecs : numpy.ndarray
        Copy of 'vecs' with homogenized coordinates.

    Examples
    --------
    >>> homog_vecs([[0, 1, 2], [3, 4, 5]])
    array([[0, 1, 2, 1], [3, 4, 5, 1]])
    """
    vs = np.asanyarray(vecs)
    hvecs = np.ones(np.add(vs.shape, (0, 1)), dtype=vs.dtype)
    hvecs[:, :-1] = vs
    return hvecs


def transf_vecs(mat, vecs):
    """
    Apply a transformation matrix to every vector in a list.

    Parameters
    ----------
    mat : Iterable
        4x4 transformation matrix to apply to every vector
    vecs : Iterable
        List of 3D vertices

    Returns
    -------
    vecs : numpy.ndarray
        Copy of 'vecs' with transformed coordinates
    """
    return (mat @ homog_vecs(vecs).T).T[:, :3]


def transf_point(mat, point):
    """
    Apply a transformation matrix to a point.

    Parameters
    ----------
    mat : Iterable
        4x4 transformation matrix to apply.
    point : Iterable
        3D point to transform.

    Returns
    -------
    vecs : numpy.ndarray
        Copy of 'point' with transformed coordinates.
    """
    return (mat @ np.append(point, 1))[:3]


def transf_dist(mat, dist):
    """
    Apply a transformation matrix to a distance vector.

    Parameters
    ----------
    mat : Iterable
        4x4 transformation matrix to apply.
    point : Iterable
        3D vector of distance to transform.

    Returns
    -------
    vecs : numpy.ndarray
        Copy of 'dist' with transformed coordinates.
    """
    return np.asanyarray(mat)[:3, :3] @ dist
