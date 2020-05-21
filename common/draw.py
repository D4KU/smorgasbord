import bgl
import bpy
import gpu
from gpu_extras.batch import batch_for_shader


def draw_points(points, size=1, color=(1, 1, 1, 1)):
    """
    Draw an array of 3D points in OpenGL point mode with a uniform,
    unshaded color.
    :param points: Nx3-dimensional, list-like object of N 3D points to
        draw.
    :param size: The point's size in pixel. Default is 1.
    :param color: The point's rgba color. Each value should be in the
        [0, 1] range. Default is white.
    """
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": points})
    shader.bind()
    bgl.glPointSize(size)
    shader.uniform_float("color", color)
    batch.draw(shader)


class View3DDrawer():
    """
    Wraps a draw function so that draw handlers to Blender's 3D View
    are automatically managed. If an object of this class is deleted,
    the handler is removed. All positional arguments are passed along,
    keyword arguments are not supported.
    """
    def __init__(self, draw_func):
        """
        Constructor
        :param draw_func: Draw function passed to Blender's draw
            handler when an instance of this class is called.
        """
        self.handle = None
        self.func = draw_func

    def __del__(self):
        self._remove_handle()

    def _remove_handle(self):
        if self.handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None

    def __call__(self, *args):
        if bpy.context.area.type != 'VIEW_3D':
            raise RuntimeError(
                "Incorrect context: only in the 3D view can be drawn.")
        self._remove_handle()
        self.handle = bpy.types.SpaceView3D.draw_handler_add(
            self.func,
            args,
            'WINDOW',
            'POST_VIEW',
            )
        bpy.context.area.tag_redraw()
