from smorgasbord.ops import (
    align_bounds,
    apply_name,
    force_apply_modifier,
    force_apply_transform,
    join_as_vertex_group,
    lerp_weight,
    material_transfer,
    prepare_export_to_unity,
    prepend_name_to_children,
    quick_fix_objects,
    remove_similar_uv_maps,
    remove_empty_vertex_groups,
    replace_by_primitive,
    replace_duplicate_materials,
    select_by_name,
    select_concave_parts,
    select_visible,
    select_loose_by_size,
    select_n_instances,
    select_similar,
    set_parent_advanced,
    smart_parent_to_empty,
    vertex_color_to_group,
)


def _call_globals(attr_name):
    for m in globals().values():
        if hasattr(m, attr_name):
            getattr(m, attr_name)()


def register():
    _call_globals("register")


def unregister():
    _call_globals("unregister")


if __name__ == '__main__':
    register()
