import bpy
from smorgasbord.common.decorate import register


@register
class OffsetSelection(bpy.types.Operator):
    bl_idname = "outliner.offset_selection"
    bl_label = "Offset Selection"
    bl_description = "Offset each selection by N entries up or down"
    bl_options = {'REGISTER', 'UNDO'}
    try:
        menus = [bpy.types.OUTLINER_MT_object]
    except AttributeError:
        # type got renamed somewhere before Blender 2.92
        menus = [bpy.types.OUTLINER_MT_context]

    step: bpy.props.IntProperty(
        name="Step",
        description=(
            "Selection offset. Positive values move down, negative up"
        ),
        default=1,
    )
    active_too: bpy.props.BoolProperty(
        name="Offset active",
        description="If true, offset active object state",
        default=True,
    )

    def execute(self, context):
        obs = sorted(context.view_layer.objects, key=lambda o: o.name)

        for o in context.selected_objects:
            o.select_set(False)
            idx = obs.index(o) + self.step
            if 0 <= idx < len(obs):
                obs[idx].select_set(True)

        if self.active_too and context.object:
            idx = obs.index(context.object) + self.step
            context.view_layer.objects.active = \
                obs[idx] if 0 <= idx < len(obs) else None

        return {'FINISHED'}
