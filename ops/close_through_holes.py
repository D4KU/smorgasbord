import bmesh as bm
import bpy
from itertools import compress
import numpy as np

from smorgasbord.common.io import get_vecs, get_bounds_and_center
from smorgasbord.common.decorate import register

from time import time


@register
class CloseThroughHoles(bpy.types.Operator):
    bl_idname = "object.close_through_holes"
    bl_label = "Close Through Holes"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_edit_mesh]

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        for o in context.objects_in_mode_unique_data:
            data = o.data
            bo = bm.from_edit_mesh(data)
            bfaces = bo.faces
            bfaces.ensure_lookup_table()

            # Bool array of vertex indices already visited
            flags = np.zeros(len(bfaces), dtype=bool)
            # Will contain a list of face indices for each patch found.
            # A patch is a set of connected faces concave to each other.
            # This list is only needed to not delete vertices while we
            # iterate the mesh.
            patches = []
            # bmesh has to recalculate face centers, so get them
            # directly from the mesh data instead
            centrs = get_vecs(data.polygons, attr='center')

            for i, visited in enumerate(flags):
                if visited:
                    continue

                flags[i] = True
                # Faces to visit
                stack = [bfaces[i]]
                # See 'patches' list
                patch = []

                while stack:
                    f = stack.pop()
                    n = f.normal
                    c = centrs[f.index]
                    patch.append(f.index)

                    # Push all faces connected to f on stack...
                    for l in f.loops:
                        f2 = l.link_loop_radial_next.face
                        i2 = f2.index
                        # but only if not already checked, and...
                        if flags[i2]:
                            continue
                        # f and f2 are concave to each other
                        c2 = centrs[i2]
                        if round(n.dot(c2 - c), 6) > 0:
                            flags[i2] = True
                            stack.append(f2)

                if len(patch) > 1:
                    patches.append(patch)

            del flags
            for p in patches:
                bounds, centr = get_bounds_and_center(centrs[p])

                # get verts of faces in patch
                bverts = []
                for fidx in p:
                    bverts += bfaces[fidx].verts
                # remove duplicate elements
                bverts = list(set(bverts))

                # Merge all vertices of patch to first vertex in list
                bm.ops.pointmerge(bo, verts=bverts, merge_co=centr)
                # Dissolve last remaining vertex of patch
                bm.ops.dissolve_verts(bo, verts=[bverts[0]])

            bm.update_edit_mesh(data)
        return {'FINISHED'}


if __name__ == "__main__":
    register()
