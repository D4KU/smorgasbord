import bpy
from smorgasbord.common.decorate import register


@register
class ForceJoin(bpy.types.Operator):
    bl_idname = "object.force_join"
    bl_label = "Force Join"
    bl_description = (
        "Join operation that treats non-mesh objects like zero-vertex "
        "mesh objects instead of ignoring them"
    )
    bl_options = {'REGISTER', 'UNDO'}
    try:
        menus = [bpy.types.OUTLINER_MT_object]
    except AttributeError:
        # type got renamed somewhere before Blender 2.92
        menus = [bpy.types.OUTLINER_MT_context]

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object

    def execute(self, context):
        ob = context.object
        mob = None  # some mesh object
        nmobs = []  # non-mesh objects

        # Find all selected non-mesh objects and some mesh object
        for o in context.selected_editable_objects:
            if o.type == 'MESH':
                mob = o
            else:
                nmobs.append(o)

        if mob:
            if ob.type != 'MESH':
                # If the active object is a non-mesh which will later
                # be deleted, we appoint some mesh object as active
                # object and pass along the name
                name = ob.name
                ob.name = "d"
                mob.name = name
                context.view_layer.objects.active = mob
            bpy.ops.object.join()
        else:
            # No mesh selected. Make sure we don't delete all of the
            # selected objects. Spare the active one.
            nmobs.remove(ob)

        # Delete non-mesh objects
        for o in nmobs:
            bpy.data.objects.remove(o, do_unlink=True)

        return {'FINISHED'}
