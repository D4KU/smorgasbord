import bmesh as bm
import smorgasbord.functions.common as sb
import bpy
import mathutils as mu
import numpy as np


class SelectLooseBySize(bpy.types.Operator):
    bl_idname = "select.select_loose_by_size"
    bl_label = "Select Loose by Size"
    bl_description = "Select loose parts of a mesh with a smaller bounding box volume than a given threshold."
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.VIEW3D_MT_select_edit_mesh
    ]

    # to prevent infinite recursion in getter and setter
    _vol_limits = mu.Vector((0.0, 1.0))

    def _get_vol_limits(self):
        return SelectLooseBySize._vol_limits

    def _set_vol_limits(self, value):
        # clamp min to max
        SelectLooseBySize._vol_limits = (min(value), value[1])

    vol_limits: bpy.props.FloatVectorProperty(
        name = "Bounding Volume Limits",
        description = "Loose parts whose bounding box's volume lies between (min, max] get selected",
        size = 2,
        unit = 'VOLUME',
        step = 10,
        default = (0.0, 1.0),
        min = 0.0,
        get = _get_vol_limits,
        set = _set_vol_limits,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and len(context.selected_objects) > 0

    def execute(self, context):
        all_type_err = True # no obj is of type mesh

        for ob in context.selected_objects:
            data = ob.data        # bpy representation of object data
            verts = data.vertices # bpy representation of vertices
            vert_count = len(verts)

            if ob.type == 'MESH':
                all_type_err = False
            else:
                continue

            parts = []                      # loose parts of mesh
            bdata = bm.from_edit_mesh(data) # bmesh representation of object data
            bverts = bdata.verts            # bmesh representation of vertices
            bverts.ensure_lookup_table()

            # bool array of vertex indices already put on stack 'to_visit'
            checked_indcs = np.zeros(vert_count, dtype=bool)

            # 1. find loose parts in mesh
            for idx, checked in enumerate(checked_indcs):
                if checked:
                    continue

                indcs = []               # indices of verts of one loose part
                coords = []              # coords of verts of one loose part
                to_visit = [bverts[idx]] # bmesh vertices to be traversed
                checked_indcs[idx] = True

                while to_visit:
                    v = to_visit.pop()
                    coords.append(verts[v.index].co)
                    indcs.append(v.index)

                    # push all vertices connected to v on stack
                    for e in v.link_edges:
                        v2 = e.other_vert(v)

                        # but only if not already checked
                        if not checked_indcs[v2.index]:
                            to_visit.append(v2)
                            checked_indcs[v2.index] = True

                parts.append((indcs, coords))

            # repurpose bool array, this time storing whether
            # the vert at that index needs to get selected
            checked_indcs.fill(False)

            # 2. select small enough loose parts
            for indcs, coords in parts:
                bounds, _ = sb.get_bounds_and_center(coords)
                vol = np.prod(bounds)

                # only select loose parts with right volume
                if vol > self._vol_limits[0] and vol <= self._vol_limits[1]:
                    checked_indcs[indcs] = True

            # somehow the mesh doesn't update if we stay in edit mode
            bpy.ops.object.mode_set(mode='OBJECT')
            verts.foreach_set('select', checked_indcs)
            bpy.ops.object.mode_set(mode='EDIT')

        if all_type_err:
            self.report({'ERROR_INVALID_INPUT'},
                        "An object must be of type mesh")
            return {'CANCELLED'}
        return {'FINISHED'}

def draw_menu(self, context):
    self.layout.operator(SelectLooseBySize.bl_idname)

def register():
    bpy.utils.register_class(SelectLooseBySize)
    for m in SelectLooseBySize.menus:
        m.append(draw_menu)

def unregister():
    bpy.utils.unregister_class(SelectLooseBySize)
    for m in SelectLooseBySize.menus:
        m.remove(draw_menu)

# for convenience when script is run inside Blender's text editor
if __name__ == "__main__":
    register()
