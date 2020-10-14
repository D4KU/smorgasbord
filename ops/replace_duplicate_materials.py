import bpy
import mathutils as mu
import re

from smorgasbord.common.decorate import register


@register
class ReplaceDuplicateMaterials(bpy.types.Operator):
    bl_idname = "object.replace_duplicate_materials"
    bl_label = "Replace Duplicate Materials"
    bl_description = (
        "Tries to replace materials of selected "
        "objects by their original through name matching. E.g. "
        "Metal.001 would be replaced by Metal, if existent"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.MATERIAL_MT_context_menu]

    pattern: bpy.props.StringProperty(
        name='Regex pattern',
        description=(
            "The regular expression used to match duplicate "
            "materials"
        ),
        default='.*(?=\.[0-9]+)',
    )

    create_material: bpy.props.BoolProperty(
        name="Create material",
        description=(
            "When no material with a shortened name exists, create it."
        ),
        default=True,
    )

    merge_slots: bpy.props.BoolProperty(
        name="Merge equal slots",
        description="Merge slots ending up with the same material",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        cmats = bpy.data.materials
        pat = re.compile(self.pattern)
        for o in context.selected_objects:
            for slot in o.material_slots:
                if not slot.material:
                    continue  # next slot

                match = pat.match(slot.name)

                try:
                    trunc_name = slot.name[match.start():match.end()]
                except AttributeError:
                    continue  # next slot

                try:
                    orig_mat = cmats[trunc_name]
                except KeyError:
                    if self.create_material:
                        orig_mat = slot.material.copy()
                        orig_mat.name = trunc_name
                    else:
                        continue  # next slot

                slot.material = orig_mat

            if not self.merge_slots:
                continue  # next object

            # Can't use o.data.materials.values() for comparison
            # because of empty slots not having a material
            slotnames = o.material_slots.keys()
            for i, slot in enumerate(o.material_slots):
                # Find index of first key list entry with name same
                first = slotnames.index(slot.name)
                if first >= i:
                    continue  # next slot

                # If an eponymous slot before the current index is
                # found, merge the current slot with the found one by
                # moving the former below the latter and ...
                o.active_material_index = i
                for _ in range(i - first - 1):
                    bpy.ops.object.material_slot_move()
                # removing the current slot
                bpy.ops.object.material_slot_remove()

        return {'FINISHED'}


if __name__ == "__main__":
    register()
