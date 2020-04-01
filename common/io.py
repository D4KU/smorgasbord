import numpy as np


def get_verts(data):
    """
    Return vertex coordinates of a Blender object as a numpy array.

    Parameters
    ----------
    data : bpy.object.data
        Object data to get vertices from.

    Returns
    -------
    verts : numpy.ndarray
        Array of vertices.
    """
    count = len(data.vertices)
    verts = np.empty(count * 3, dtype=np.float64)
    data.vertices.foreach_get('co', verts)
    verts.shape = (count, 3)
    return verts


def set_verts(data, verts):
    """
    Set vertex coordinates of a Blender object from a numpy array.

    Parameters
    ----------
    data : bpy.object.data
        Object data whose vertices to set.
    verts : numpy.ndarray
        Array of vertex coordinates.
    """
    data.vertices.foreach_set("co", verts.ravel())
    data.update()


def get_sel_flags(geom):
    """
    Get a numpy bool array indicating the selection state of every item in a
    given Blender struct.

    Parameters
    ----------
    geom : bpy.struct
        Geometry to get the selection state from. E.g. vertices, edges, ...

    Returns
    -------
    flags : numpy.ndarray
        Bool array with an entry set to True for every item in geom selected.
    """
    flags = np.zeros(len(geom), dtype=np.bool)
    geom.foreach_get('select', flags)
    return flags


def get_vert_sel_flags(data):
    """
    Get a numpy bool array indicating every vertex' selection state of a given
    Blender object.

    Parameters
    ----------
    data : bpy.object.data
        Object data to get vertex selection from.

    Returns
    -------
    flags : numpy.ndarray
        Bool array with an entry set to True for every vertex in data selected.
    """
    return get_sel_flags(data.vertices)


def get_bounds_and_center(verts):
    """
    Calculate the bounds and center for a given set of vertices.

    Parameters
    ----------
    verts : numpy.ndarray
        Vertices to calculate the bounds and center of.

    Returns
    -------
    bounds : numpy.ndarray
        Vector whose coordinates, in each dimension, hold the extents of the
        minimal bounding volume encompassing every input vertex in 'verts'.
    center : numpy.ndarray
        Average point of the input vertices 'verts'. Note that this point may
        not be part of 'verts'.
    """
    co_min = np.amin(verts, axis=0)
    co_max = np.amax(verts, axis=0)
    bounds = co_max - co_min
    center = (co_max + co_min) * 0.5
    return bounds, center

