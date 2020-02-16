import numpy as np

def get_verts(ob):
    """
    get_verts(ob)
    Return vertex coordinates of a Blender object as a numpy array.

    Parameters
    ----------
    ob : bpy.data.object
        Object to get vertices from.

    Returns
    -------
    verts : numpy.ndarray
        Array of vertices.
    """
    count = len(ob.data.vertices)
    verts = np.empty(count * 3, dtype=np.float64)
    ob.data.vertices.foreach_get('co', verts)
    verts.shape = (count, 3)
    return verts

def set_verts(ob, verts):
    """
    set_verts(ob, verts)
    Set vertex coordinates of a Blender object from a numpy array.

    Parameters
    ----------
    ob : bpy.data.object
        Object whose vertices to set.
    verts : numpy.ndarray
        Array of vertex coordinates.
    """
    ob.data.vertices.foreach_set("co", verts.ravel())
    ob.data.update()

def get_vert_sel_flags(ob):
    """
    get_vert_sel_flags(ob)
    Return a numpy bool array indicating every vertex' selection state
    of a given Blender object.

    Parameters
    ----------
    ob : bpy.data.object
        Object to get vertex selection from.

    Returns
    -------
    sel : numpy.ndarray
        Bool array with an entry set to True for every vertex in ob selected.
    """
    verts = ob.data.vertices
    sel = np.zeros(len(verts), dtype=np.bool)
    verts.foreach_get('select', sel)
    return sel

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

def to_transl_mat(vec):
    """
    to_transl_mat(vec)
    Return a translation matrix for a given translation vector.

    Parameters
    ----------
    vec : numpy.ndarray
        Vector of x,y,z coordinates.

    Returns
    -------
    mat : numpy.ndarray
        4x4 translation matrix.

    Examples
    --------
    >>> make_transl_mat(np.array([7, 8, 9]))
    array([[1, 0, 0, 7],
           [0, 1, 0, 8],
           [0, 0, 1, 9],
           [0, 0, 0, 1]])
    """
    mat = np.identity(4)
    mat[:-1,-1:] = vec.reshape(3,1)
    return mat

def append_row_and_col(mat):
    """
    append_row_and_col(mat)
    For a given Matrix, return a copy with one column and one row more,
    which are filled with zeros, except for a one in the bottom-right entry.

    Parameters
    ----------
    mat : numpy.ndarray
        Matrix to append a row and column to.

    Returns
    -------
    new_mat : numpy.ndarray
        Copy of 'mat' with one column and one row more.

    Examples
    --------
    >>> append_row_and_col(np.array([[2, 3], [4, 5]]))
    array([[2, 3, 0],
           [4, 5, 0],
           [0, 0, 1]])
    """
    new_mat = np.eye(*np.add(mat.shape, 1))
    new_mat[:-1,:-1] = mat
    return new_mat

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

def get_bounds_and_center(verts):
    """
    get_bounds_and_center(verts)
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
