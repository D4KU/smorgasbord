import numpy as np


def get_vecs(geom, attr='co', vecsize=3, dtype=np.float64):
    """
    Return vector values of a Blender property collection
    as a numpy array.

    Parameters
    ----------
    geom : bpy.types.bpy_prop_collection
        Geometry to get vectors from (vertices, edges, ...)
    attr : string = 'co'
        Vector vertex attribute to get. Defaults to coordinates.
    vecsize : int = 3
        Size of vectors to get.
    dtype : numpy.dtype
        Numpy data type to store the values in

    Returns
    -------
    vs : numpy.ndarray
        Array of vectors.
    """
    vs = np.empty(len(geom) * vecsize, dtype=dtype)
    geom.foreach_get(attr, vs)
    vs.shape = (-1, vecsize)
    return vs


def set_vals(geom, vals, attr='co'):
    """
    Set each element in a Blender property collection.

    Parameters
    ----------
    geom : bpy.types.bpy_prop_collection
        Geometry to change (vertices, edges, ...)
    vals : Iterable
        Values to write into the collection
    attr : string = 'co'
        Attribute to set. Defaults to coordinates.
    """
    geom.foreach_set(attr, np.asarray(vals).ravel())
    geom.data.update()


def get_scalars(geom, attr='select', dtype=np.bool):
    """
    Return Boolean values of a Blender property collection
    as a numpy array.

    Parameters
    ----------
    geom : bpy.types.bpy_prop_collection
        Geometry to get bools from (vertices, edges, ...)
    attr : string = 'select'
        Boolean attribute to get. Defaults to selection state.
    dtype : numpy.dtype
        Numpy data type to store the values in

    Returns
    -------
    bs : numpy.ndarray
        Array of Booleans
    """
    bs = np.empty(len(geom), dtype=dtype)
    geom.foreach_get(attr, bs)
    return bs


def get_bounds_and_center(points):
    """
    Calculate the bounds and center for a given set of points.

    Parameters
    ----------
    points : numpy.ndarray
        Points to calculate the bounds and center of.

    Returns
    -------
    bounds : numpy.ndarray
        Vector whose coordinates, in each dimension, hold the extents
        of the minimal bounding volume encompassing every input point
    center : numpy.ndarray
        Average point of the input points. This point may not be in the
        input list.
    """
    co_min = np.amin(points, axis=0)
    co_max = np.amax(points, axis=0)
    bounds = co_max - co_min
    center = (co_max + co_min) * 0.5
    return bounds, center
