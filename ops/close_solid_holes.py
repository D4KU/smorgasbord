import bmesh as bm
import bpy
import numpy as np

from smorgasbord.common.io import (
    get_bounds_and_center,
    get_scalars,
    get_vecs,
)
from smorgasbord.common.decorate import register


@register
class CloseSolidHoles(bpy.types.Operator):
    bl_idname = "object.close_solid_holes"
    bl_label = "Close Solid Holes"
    bl_description = (
        "Close through-going or blind holes in the selected geometry. "
        "These are aren't holes caused by missing faces, but valid "
        "geometry. Think of holes in a cheese."
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_transform]

    def _get_limits(self):
        return CloseSolidHoles._limits

    def _set_limits(self, value):
        # clamp min to max
        CloseSolidHoles._limits = (min(value), value[1])

    # to prevent infinite recursion in getter and setter
    _limits = (0, 1)
    limits: bpy.props.FloatVectorProperty(
        name="Size Limits",
        description=(
            "Holes whose diameter lies between (min, max] get closed"
        ),
        size=2,
        step=10,
        default=_limits,
        min=0,
        get=_get_limits,
        set=_set_limits,
    )
    _meshes = []

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def invoke(self, context, event):
        self._find_concave_patches(context)
        return self.execute(context)

    def _find_concave_patches(self, context):
        """
        A patch is a set of connected faces. For each patch containing
        at least two faces facing each other, return a list of vertex
        indices making up such a patch, together with its center point
        and diameter. A patch's border is along edges between faces
        facing away from each other (think ridges).
        """
        self._meshes.clear()
        for o in context.objects_in_mode_unique_data:
            o.update_from_editmode()
            data = o.data
            polys = data.polygons
            bob = bm.from_edit_mesh(data)
            bfaces = bob.faces
            bfaces.ensure_lookup_table()
            # bmesh has to recalculate face centers, so get them
            # directly from the mesh data instead
            centrs = get_vecs(polys, attr='center')
            # Bool array of vertex indices already visited
            # Unselected faces will be True already
            flags = get_scalars(polys)
            # Will contain a list of tuples. First entry is the list of
            # face indices of the patch. Second is the dimension it's
            # facing.
            # This list is only needed to not delete vertices while we
            # iterate the mesh.
            patches = []

            for i, new in enumerate(flags):
                if not new:
                    continue

                flags[i] = False
                # Faces to visit
                stack = [bfaces[i]]
                # Face indices of the patch
                findcs = []
                concave = False

                while stack:
                    f = stack.pop()
                    n = f.normal
                    c = centrs[f.index]
                    findcs.append(f.index)

                    # Push all faces connected to f on stack...
                    for l in f.loops:
                        f2 = l.link_loop_radial_next.face
                        i2 = f2.index
                        # The dot product between f's normal and the
                        # vector between both face's centers is a
                        # simple way to measure if they are parallel
                        # (=0), concave (>0), or convex (<0).
                        angl = n.dot(centrs[i2] - c)
                        # but only if not already checked and f and f2
                        # are not convex (don't face away from each 
                        # other), but...
                        if flags[i2] and angl > -1e-3:
                            # at least two faces have to face each
                            # other, allowing for some error margin.
                            if angl > 1e-4:
                                concave = True
                            flags[i2] = False
                            stack.append(f2)

                if len(findcs) > 2 and concave:
                    patches.append(findcs)

            del flags
            # second representation of patches, this time as a tuple of
            # vertex indices, center, and diameter
            patches2 = []
            normals = get_vecs(polys, attr='normal')

            for findcs in patches:
                # get verts of faces in patch
                vindcs = []
                for fidx in findcs:
                    vindcs += list(polys[fidx].vertices)
                # remove duplicate elements
                vindcs = list(set(vindcs))

                # for every face in the patch, get the dimension it's
                # facing most (x = 0, y = 1, z = 2)
                dirs = np.argmax(np.abs(normals[findcs]), axis=1)
                # get the direction most of the faces face
                direc = dirs[np.bincount(dirs).argmax()]

                bounds, centr = get_bounds_and_center(centrs[findcs])
                patches2.append((vindcs, centr, bounds[direc]))
            self._meshes.append((data, patches2))

    def execute(self, context):
        mind, maxd = self._limits
        # Vertex indices already deleted in earlier patches that we
        # can't delete again.
        dvindcs = np.empty(0, dtype=int)

        # Iterate over results computed during invoke()
        for mesh, patches in self._meshes:
            bob = bm.from_edit_mesh(mesh)
            bverts = np.array(bob.verts)
            for vindcs, centr, diam in patches:
                # Only close holes whose diameter lies within limits
                if not mind < diam <= maxd:
                    continue

                # Remove all vertices that already got deleted
                vindcs = np.setdiff1d(vindcs, dvindcs)
                # Merge all vertices of patch to first vertex in list
                vs = bverts[vindcs]
                bm.ops.pointmerge(bob, verts=vs, merge_co=centr)
                # Dissolve last remaining vertex of patch
                bm.ops.dissolve_verts(bob, verts=[vs[0]])
                del vs
                dvindcs = np.concatenate((dvindcs, vindcs))
            bm.update_edit_mesh(mesh)
        return {'FINISHED'}


if __name__ == "__main__":
    register()
