import bpy
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
    _bug_unreported = True

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
        default=False,
    )

    merge_slots: bpy.props.BoolProperty(
        name="Merge equal slots",
        description="Merge slots ending up with the same material",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_objects) > 0

    def execute(self, context):
        old_active = context.view_layer.objects.active
        cmats = bpy.data.materials
        pat = re.compile(self.pattern)
        for o in context.selected_editable_objects:
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

            # To my knowledge the only way to merge material slots is to
            # call the UI functions from bpy.ops. Because slot indices
            # change during iteration due to removal, only one duplicate
            # is removed before the process is restarted. This is slow,
            # but safe.
            context.view_layer.objects.active = o
            while self.merge_first_equal_slots(o):
                pass

        context.view_layer.objects.active = old_active
        return {'FINISHED'}

    def merge_first_equal_slots(self, ob):
        """
        For a given object, merges the first two eponymous material slots.
        Returns True if there might be more slots to merge and False if all
        are distinct.
        """
        # Can't use o.data.materials.values() for comparison
        # because of empty slots not having a material
        slotnames = ob.material_slots.keys()
        for i, name in enumerate(slotnames):
            # Find index of first key list entry with name same
            first = slotnames.index(name)
            if first >= i:
                continue  # next slot

            # If an eponymous slot before the current index is
            # found, merge the current slot with the found one by
            # moving the current below the found and ...
            ob.active_material_index = i
            for _ in range(i - first - 1):
                bpy.ops.object.material_slot_move()
            # ... removing the current
            bpy.ops.object.material_slot_remove()

            # Somehow material_slot_remove does not work on
            # non-active objects when it is executed from outside the
            # 3D view, even though its poll method returns True.
            if len(slotnames) == len(ob.material_slots.keys()) \
                    and self._bug_unreported:
                self._bug_unreported = False
                self.report({'ERROR'},
                    ("Could only merge material slots on the active "
                     "object. Try executing from the 3D View."))
                return False

            return True
        return False
