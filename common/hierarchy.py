def get_lvl(ob):
    """
    Returns the number of parents of a given object, or, in other words,
    it's level of deepness in the scene tree.

    Parameters
    ----------
    ob : bpy.types.object
        Blender object

    Returns
    -------
    lvl : int
        The number of parents of the object. For 'None' -1 is returned.
    """
    lvl = -1
    while ob:
        ob = ob.parent
        lvl += 1
    return lvl


def set_parent(ob, parent, set_inverse = True):
    """
    Parent 'ob' to 'parent'.

    Parameters
    ----------
    ob : bpy.types.object
    parent : bpy.types.object
    """
    ob.parent = parent
    if set_inverse:
        ob.matrix_parent_inverse = parent.matrix_world.inverted()

    # Make sure reparenting doesn't make 'ob' jump
    # Works because matrix_world isn't updated after setting new
    # parent
    ob.matrix_world = ob.matrix_world
