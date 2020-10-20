import bpy
import sys


def register(cls):
    """
    Class decorator which adds Blender's register and unregister functions to
    the module in which the decorated class is defined.

    Parameters
    ----------
    cls : class
        Operator class defined in smorgasbord.ops

    Returns
    -------
    cls : class
        Passed class, without even decorating it

    """
    def draw_menu(self, context):
        self.layout.operator(cls.bl_idname)

    def register():
        bpy.utils.register_class(cls)
        for m in cls.menus:
            m.append(draw_menu)

    def unregister():
        bpy.utils.unregister_class(cls)
        for m in cls.menus:
            m.remove(draw_menu)

    modl = sys.modules[cls.__module__]
    setattr(modl, 'register', register)
    setattr(modl, 'unregister', unregister)
    return cls
