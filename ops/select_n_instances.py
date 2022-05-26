import bpy

from smorgasbord.common.decorate import register


@register
class SelectNInstances(bpy.types.Operator):
    bl_idname = "object.select_n_instances"
    bl_label = "Select N Instances"
    bl_description = (
        "For each data of selected objects, select N objects sharing "
        "the same data. N is set by a lower and upper bound"
    )
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_object]

    n_from: bpy.props.IntProperty(
        name="From",
        description=(
            "Lower index bound to select from. Inclusive. Negative "
            "values count from the end of the instance list"
        ),
        default=1,
    )

    n_to: bpy.props.IntProperty(
        name="To",
        description=(
            "Upper index bound to select. Not inclusive. Negative "
            "values count from the end of the instance list. Non-"
            "negative values less equal the lower bound are "
            "considered as infinity"
        ),
        default=0,
    )

    # Examples:
    # from 0 to 0: select all
    # from 0 to 1: select first instance
    # from 1 to 2: select second instance
    # from 0 to -1: select all but the last instance
    # from 5 to 0: select all from the fifth instance onward
    # from 5 to 1: likewise
    # from 5 to 5: likewise
    # from -1 to 0: select nothing (not supported)
    # from -1 to 3: likewise
    # from -2 to -1: select last instance

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        # Find all datas we want to find instances of
        datas = set()
        for o in context.selected_objects:
            o.select_set(False)
            datas.add(o.data)

        # For each data, find all linked objects in the collection.
        # The dict is initialized with all relevant datas as keys.
        datas = {key: [] for key in datas}
        for o in context.view_layer.objects:
            # If data isn't found, ignore object by appending to a new
            # list that is tossed away.
            datas.get(o.data, []).append(o)

        # One loop iteration handles one data
        for objects in datas.values():
            # Set upper bound to infinity if its non-negative and smaller
            # than the lower bound.
            # Negative values count from end of the list of instances
            to = None if 0 <= self.n_to <= self.n_from else self.n_to

            # Select instances of current data according to set bounds
            for o in objects[self.n_from:to]:
                o.select_set(True)

        return {'FINISHED'}
