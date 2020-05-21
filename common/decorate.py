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

    def unregster():
        bpy.utils.register_class(cls)
        for m in cls.menus:
            m.remove(draw_menu)

    setattr(sys.modules[cls.__module__], 'register', register)
    return cls


# def pass_to(recipient):
#     def decorator(decoratee):
#         def wrap(*args, **kwargs):
#             ret = decoratee(*args, **kwargs)
#             recipient(ret)
#             return ret
#         return wrap
#     return decorator
