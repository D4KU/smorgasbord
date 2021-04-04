import bmesh as bm
import bpy
from bpy_extras import object_utils
from mathutils import Matrix
import numpy as np

from smorgasbord.common.io import get_scalars
from smorgasbord.common.mat_manip import make_transf_mat
from smorgasbord.common.transf import transf_pts


def combine_meshes(obs):
    vtotlen = 0
    itotlen = 0
    info = []
    for o in obs:
        mesh = o.data
        mesh.calc_loop_triangles()
        vtotlen += len(mesh.vertices)
        itotlen += len(mesh.loop_triangles)
        info.append((vtotlen, itotlen))

    verts = np.empty(vtotlen * 3, dtype=np.float32)
    indcs = np.empty(itotlen * 3, dtype=np.int32)
    vstart = 0
    istart = 0

    for o in obs:
        mesh = o.data
        vend = vstart + len(mesh.vertices) * 3
        iend = istart + len(mesh.loop_triangles) * 3
        vslice = verts[vstart:vend]
        islice = indcs[istart:iend]

        # Vertices
        mesh.vertices.foreach_get('co', vslice)
        verts[vstart:vend] = transf_pts(
            o.matrix_world,
            vslice.reshape(-1, 3),
            ).ravel()

        # Indices
        mesh.loop_triangles.foreach_get('vertices', islice)
        islice += int(vstart / 3)

        vstart = vend
        istart = iend

    verts.shape = (-1, 3)
    indcs.shape = (-1, 3)
    return verts, indcs, info


def get_unit_cube():
    """
    Returns vertex coordinates and face indices for a unit cube.

    Returns
    -------
    verts : numpy.ndarray
        3x8 float array of XYZ vertex coordinates.
    quads : numpy.ndarray
        4x6 array of vertex indices for each quad face. Each 4-value tuple
        holds the indices of the vertices in the verts array the
        corresponding quad is connected to.
    """

    verts = np.array([
        (+0.5, +0.5, -0.5),
        (+0.5, -0.5, -0.5),
        (-0.5, -0.5, -0.5),
        (-0.5, +0.5, -0.5),
        (+0.5, +0.5, +0.5),
        (+0.5, -0.5, +0.5),
        (-0.5, -0.5, +0.5),
        (-0.5, +0.5, +0.5),
    ])

    quads = np.array([
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ])

    return verts, quads


def add_geom_to_bmesh(bob, verts, faces, select=True):
    """
    Add geometry to a bmesh object.

    Parameters
    ----------
    bob : bmesh.BMesh
        The object to add the geometry to
    verts : numpy.ndarray
        3xN array of XYZ coordinates for N vertices to add.
    quads : numpy.ndarray
        Array of vertex indices for each face. Each entry holds the
        indices of the vertices in the verts array the corresponding face
        gets connected to.
    select : Bool = True
        Should the newly added vertices be selected? If yes, any other
        vertex gets deselected
    """
    bverts = bob.verts
    bfaces = bob.faces
    bverts_new = []

    # Vertex indices need to be offset by the number of verts already
    # present in the mesh before anything is done.
    for i, v in enumerate(verts, start=len(bverts)):
        # Add new vert and select it
        bv = bverts.new(v)
        bv.index = i
        bv.select = select
        bverts_new.append(bv)

    bverts.ensure_lookup_table()
    for f in faces:
        # Push list of BVert objects to bfaces that make up face f
        bfaces.new([bverts_new[v_idx] for v_idx in f])

    if select:
        bob.select_flush(True)


def add_box_to_scene(
        context,
        location=np.zeros(3),
        rotation=np.zeros(3),
        size=np.ones(3),
        name='Box'):
    """
    Add a box mesh to a given context.

    Parameters
    ----------
    context : bpy.context
        Blender context to add the box to
    location : numpy.ndarray = (0, 0, 0)
        World location of the box
    rotation : numpy.ndarray = (0, 0, 0)
        World rotation of the box in Euler angles
    size : numpy.ndarray = (1, 1, 1)
        Length, height, and depth of the box, respectively
    name : String
        Name of the box
    """
    bob = bm.new()
    verts, faces = get_unit_cube()
    add_geom_to_bmesh(bob, verts, faces)
    mesh = bpy.data.meshes.new(name)
    bob.to_mesh(mesh)
    mesh.update()

    # Add the mesh as an object into the scene
    ob = object_utils.object_data_add(context, mesh)
    mat = make_transf_mat(location, rotation, size)
    ob.matrix_world = Matrix(mat)


def add_box_to_obj(
        ob,
        location=np.zeros(3),
        rotation=np.zeros(3),
        size=np.ones(3),
        select=True,
        deselect=True):
    """
    Add a box mesh to a given Blender object.

    Parameters
    ----------
    ob : bpy.object
        Blender object to add the box to
    location : numpy.ndarray = (0, 0, 0)
        World location of the box
    rotation : numpy.ndarray = (0, 0, 0)
        World rotation of the box in Euler angles
    size : numpy.ndarray = (1, 1, 1)
        Length, height, and depth of the box, respectively
    select_new : Bool = True
        Should the newly added vertices be selected?
    deselect : Bool = True
        Should already existing vertices be deselected?
    """
    bob = bm.from_edit_mesh(ob.data)

    # If box should be selected, deselect everything else
    if deselect:
        for v in bob.verts:
            v.select = False
        bob.select_flush(False)

    verts, faces = get_unit_cube()

    # First apply given box transform, then transform it from world to
    # local space
    mat = np.array(ob.matrix_world.inverted()) @ \
        make_transf_mat(location, rotation, size)
    verts = transf_pts(mat, verts)

    add_geom_to_bmesh(bob, verts, faces, select)
    bm.update_edit_mesh(ob.data)


def remove_selection(data, type='VERTS'):
    """
    Delete selected geometry from an object

    Parameters
    ----------
    data : bpy.object.data
        Blender object data to add the box to
    type : String = 'VERTS'
        Which geometry to delete: 'VERTS', 'EDGES', or 'FACES'?
    """
    bob = bm.from_edit_mesh(data)

    if type == 'EDGES':
        geom = data.edges
        bgeom = bob.edges
    elif type == 'FACES':
        geom = data.polygons
        bgeom = bob.faces
    else:
        geom = data.vertices
        bgeom = bob.verts

    flags = get_scalars(geom)
    to_del = np.array(bgeom)[flags]
    bm.ops.delete(bob, geom=to_del, context=type)

    bm.update_edit_mesh(data)
