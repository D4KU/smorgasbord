from smorgasbord.ops import (
    align_bounds,
    apply_name,
    material_transfer,
    prepare_export_to_unity,
    replace_by_primitive,
    replace_duplicate_materials,
    select_by_name,
    select_loose_by_size,
    select_similar,
    set_parent_advanced,
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

