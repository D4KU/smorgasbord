import bpy
from smorgasbord.common.decorate import register


@register
class ToggleMaterialLinks(bpy.types.Operator):
    bl_idname = "collection.toggle_material_links"
    bl_label = "Toggle material links"
    bl_description = (
        "Toggle the link type of each material slot of each selected "
        "object and synchronize materials assigned to each object with "
        "the ones assigned to its respective data"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.MATERIAL_MT_context_menu]

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_objects) > 0

    def execute(self, context):
        for o in context.selected_editable_objects:
            if not o.data:
                continue

            for i in range(min(len(o.material_slots), len(o.data.materials))):
                slot = o.material_slots[i]

                if slot.link == 'DATA':
                    slot.link = 'OBJECT'
                    slot.material = o.data.materials[i]
                else:
                    o.data.materials[i] = slot.material
                    slot.link = 'DATA'

        return {'FINISHED'}


if __name__ == "__main__":
    register()
