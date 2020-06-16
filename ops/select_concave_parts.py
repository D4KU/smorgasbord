import bmesh as bm
import bpy
from math import pi
import numpy as np

from smorgasbord.common.io import (
    get_bounds_and_center,
    get_scalars,
    get_vecs,
)
from smorgasbord.common.transf import normalize
from smorgasbord.common.decorate import register


pihalf = pi * 0.5


def _select(x):
    x.select = True
_selall = np.vectorize(_select)


def _deselect(x):
    x.select = False
_deselall = np.vectorize(_deselect)


@register
class SelectConcaveParts(bpy.types.Operator):
    bl_idname = "object.select_concave"
    bl_label = "Select Concave Parts"
    bl_description = "Select concave patches of a mesh"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    def _get_limits(self):
        return SelectConcaveParts._limits

    def _set_limits(self, value):
        # clamp min to max
        SelectConcaveParts._limits = (min(value), value[1])

    # to prevent infinite recursion in getter and setter
    _limits = (0, 0.1)
    limits: bpy.props.FloatVectorProperty(
        name="Size Limits",
        description=(
            "Only select patches whose bounding box's diameter lies "
            "between (min, max]"
        ),
        size=2,
        step=0.1,
        default=_limits,
        unit='LENGTH',
        min=0,
        get=_get_limits,
        set=_set_limits,
    )
    minangl: bpy.props.FloatProperty(
        name="Min Angle",
        description=(
            "Only select patches containing a face angled to its "
            "neighbor by at least this angle"
        ),
        subtype='ANGLE',
        default=0.1,
        min=0,
        max=pihalf,
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
            # Bool array of vertex indices already visited.
            # Unselected faces will be True already.
            flags = get_scalars(polys)
            # Will contain a list of tuples. First entry is the list of
            # face indices of the patch. Second is the maximum angle
            # between two neighboring faces in the patch.
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
                # Maximum dot product between two neighboring faces in
                # the patch.
                maxdot = 0

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
                        angl = n.dot(normalize(centrs[i2] - c))
                        # but only if not already checked and f and f2
                        # are not convex (don't face away from each 
                        # other)
                        if flags[i2] and angl > -1e-3:
                            maxdot = max(maxdot, angl)
                            flags[i2] = False
                            stack.append(f2)

                if len(findcs) > 2:
                    # pihalf: transform dot product result to rad angle
                    patches.append((findcs, maxdot * pihalf))

            del flags
            # second representation of patches, this time as a tuple of
            # face indices, max angle, and diameter
            patches2 = []
            normals = get_vecs(polys, attr='normal')

            for findcs, maxangl in patches:
                bounds, _ = get_bounds_and_center(centrs[findcs])
                patches2.append((findcs, maxangl, np.linalg.norm(bounds)))
            self._meshes.append((data, patches2))

    def execute(self, context):
        mind, maxd = self._limits

        # Iterate over results computed during invoke()
        for mesh, patches in self._meshes:
            bob = bm.from_edit_mesh(mesh)
            bfaces = np.array(bob.faces)
            _deselall(bfaces)
            for findcs, maxangl, diam in patches:
                # Only select patches whose diameter lies within limits
                # and biggest angle between two neighboring faces is
                # big enough
                if mind < diam <= maxd and maxangl > self.minangl:
                    _selall(bfaces[findcs])
            bm.update_edit_mesh(mesh)
        return {'FINISHED'}


if __name__ == "__main__":
    register()
