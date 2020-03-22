import sys

from smorgasbord.operators import (
    align_bounds,
    apply_name,
    prepare_export_to_unity,
    replace_by_primitive,
    replace_duplicate_materials,
    select_by_name,
    select_loose_by_size,
    set_parent_advanced,
    )


bl_info = {
    "name": "Smorgasbord",
    "author": "David Kutschke",
    "category": "Object",
    "version": (0, 1, 0),
    "blender": (2, 82, 0),
    "location": "View 3D",
    "description": "A variety of operators to make your life easier. Tasty like a smorgas.",
    "warning": "",
    "wiki_url": "https://github.com/D4KU/smorgasbord",
}


def _call_globals(attr_name):
    for m in globals().values():
        if hasattr(m, attr_name):
            getattr(m, attr_name)()


def _flush_modules(pkg_name):
    pkg_name = pkg_name.lower()
    for k in tuple(sys.modules.keys()):
        if k.lower().startswith(pkg_name):
            del sys.modules[k]


def register():
    _call_globals("register")


def unregister():
    _call_globals("unregister")
    _flush_modules("smorgasbord")


if __name__ == '__main__':
    register()
