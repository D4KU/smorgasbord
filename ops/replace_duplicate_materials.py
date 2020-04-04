import bpy
import mathutils as mu
import re

from smorgasbord.common.decorate import register


@register
class ReplaceDuplicateMaterials(bpy.types.Operator):
    bl_idname = "object.replace_duplicate_materials"
    bl_label = "Replace Duplicate Materials"
    bl_description = "Tries to replace materials of selected objects by their original through name matching. E.g. Metal.001 would be replaced by Metal, if existent"
    bl_options = {'REGISTER', 'UNDO'}
    menus = [
        bpy.types.MATERIAL_MT_context_menu
    ]

    pattern: bpy.props.StringProperty(
        name = 'Regex pattern',
        description = 'The regular expression used to match duplicate materials',
        default = '.*(?=\.[0-9]+)'
    )


    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0


    def execute(self, context):
        pat = re.compile(self.pattern)
        for o in context.selected_objects:
            for slot in o.material_slots:
                match = pat.match(slot.name)

                try:
                    trunc_name = slot.name[match.start() : match.end()]
                except AttributeError:
                    continue

                try:
                    orig_mat = bpy.data.materials[trunc_name]
                except KeyError:
                    continue

                slot.material = orig_mat

        return {'FINISHED'}


if __name__ == "__main__":
    register()
