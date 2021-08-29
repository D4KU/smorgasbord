import bpy
from smorgasbord.common.decorate import register


@register
class ViewportDisplayFromShader(bpy.types.Operator):
    bl_idname = "object.viewport_display_from_shader"
    bl_label = "Viewport Display from Shader"
    bl_description = (
        "For each active material of each selected object, search its "
        "node tree for a shader node and apply its properties to the "
        "material's viewport display properties")
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.MATERIAL_MT_context_menu]

    # each supported shader node, ordered by decreasing priority.
    # key: node name, value: inputs to read
    shader_props = {
        "Principled BSDF": ('Base Color', 'Roughness', 'Metallic'),
        "Diffuse BSDF": ('Color', 'Roughness'),
        "Glass BSDF": ('Color', 'Roughness'),
        "Emission": ('Color'),
    }

    # viewport display attributes of materials
    viewport_props = ('diffuse_color', 'roughness', 'metallic')

    reverse: bpy.props.BoolProperty(
        name="Reverse",
        description="Instead, apply to shader node from viewport display",
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_editable_objects)

    def execute(self, context):
        for o in context.selected_editable_objects:
            mat = o.active_material
            if not (mat and mat.node_tree):
                continue

            for node_name, input_names in self.shader_props.items():
                try:
                    # get shader node
                    node = mat.node_tree.nodes[node_name]
                except KeyError:
                    # try shader node with next-highest priority
                    continue

                # get input references from their names
                inputs = (node.inputs[x] for x in input_names)

                # apply matching properties from viewport display to
                # shader node, or vice versa
                for input, vp_prop in zip(inputs, self.viewport_props):
                    if self.reverse:
                        input.default_value = getattr(mat, vp_prop)
                    else:
                        setattr(mat, vp_prop, input.default_value)

                # we found a fitting shader node, no need to search for
                # more
                break

        return {'FINISHED'}
