import numpy as np


def to_transl_mat(vec):
    """
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
    >>> to_transl_mat(np.array([7, 8, 9]))
    array([[1, 0, 0, 7],
           [0, 1, 0, 8],
           [0, 0, 1, 9],
           [0, 0, 0, 1]])
    """
    mat = np.identity(4)
    mat[:-1,-1:] = vec.reshape(3,1)
    return mat


def to_scale_mat(vec):
    """
    Return a scale matrix for a given scale vector.

    Parameters
    ----------
    vec : numpy.ndarray
        Vector of x,y,z scale factors.

    Returns
    -------
    mat : numpy.ndarray
        3x3 scale matrix.

    Examples
    --------
    >>> to_scale_mat(np.array([7, 8, 9]))
    array([[7, 0, 0],
           [0, 8, 0],
           [0, 0, 9]])
    """
    return np.identity(vec.shape[0]) * vec


def euler_to_rot_mat(thetas):
    """
    Return a 3D rotation matrix for a given vector of angles in radians

    Parameters
    ----------
    thetas : numpy.ndarray
        3D vector with rotation along X, Y, Z axes respectively in radians

    Returns
    -------
    mat : numpy.ndarray
        3x3 rotation matrix
    """
    cx, cy, cz = np.cos(thetas)
    sx, sy, sz = np.sin(thetas)
    return np.array([[cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx],
                     [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx],
                     [-sy,   cy*sx,            cy*cx]])


def make_transf_mat(transl=np.zeros(3), rot=np.zeros(3), scale=np.ones(3)):
    """
    Construct a 4x4 transformation matrix from 3 vectors for translation,
    rotation, and scale, respectively.

    Parameters
    ----------
    transl : numpy.ndarray = (0, 0, 0)
        3D vector with translation offsets along the X, Y, Z axes respectively
    rot: numpy.ndarray = (0, 0, 0)
        3D vector with rotation angles along the X, Y, Z axes respectively in
        radians
    scale : numpy.ndarray = (1, 1, 1)
        3D vector with scale factors along the X, Y, Z axes respectively

    Returns
    -------
    mat : numpy.ndarray
        4x4 transformation matrix
    """
    return to_transl_mat(transl) @ append_row_and_col( \
        euler_to_rot_mat(rot) @ to_scale_mat(scale))


def append_row_and_col(mat):
    """
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

