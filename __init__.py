import sys
from smorgasbord import ops


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


def _flush_modules(pkg_name):
    pkg_name = pkg_name.lower()
    for k in tuple(sys.modules.keys()):
        if k.lower().startswith(pkg_name):
            del sys.modules[k]


def register():
    ops.register()


def unregister():
    ops.unregister()
    _flush_modules("smorgasbord")


if __name__ == '__main__':
    register()

