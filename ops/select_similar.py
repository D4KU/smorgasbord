import bpy
from math import ceil, sqrt
import numpy as np

from smorgasbord.common.io import get_bounds_and_center
from smorgasbord.common.transf import transf_vecs
from smorgasbord.common.decorate import register
from smorgasbord.common.draw import draw_points, View3DDrawer
from smorgasbord.common.sample import sample_surf, get_shape_distrib
from smorgasbord.debug.plot import save_barplot


@register
class SelectSimilar(bpy.types.Operator):
    bl_idname = "select.select_similar"
    bl_label = "Select Similar"
    bl_description = ""
    bl_options = {'REGISTER', 'UNDO'}
    menus = [bpy.types.VIEW3D_MT_select_object]

    def _get_sel_limits(self):
        return SelectSimilar._sel_limits

    def _set_sel_limits(self, val):
        # Clamp min to max
        SelectSimilar._sel_limits = (min(val), val[1])

    def _get_samplecnt(self):
        return SelectSimilar._samplcnt

    def _set_samplecnt(self, val):
        SelectSimilar._samplcnt = val
        SelectSimilar.bincnt = ceil(sqrt(val))

    def _update_sim_limits(self, context):
        SelectSimilar._resampl = False

    def _update_samplecnt(self, context):
        SelectSimilar._resampl = True

    _sel_limits = (0, 1)
    sel_limits: bpy.props.FloatVectorProperty(
        name="Similarity limits",
        description=(
            "Select objects whose shape differs more than min and less "
            "than max from the active objects' shape"
        ),
        size=2,
        step=10,
        default=_sel_limits,
        min=0,
        get=_get_sel_limits,
        set=_set_sel_limits,
        update=_update_sim_limits,
    )
    _samplcnt = 512
    samplcnt: bpy.props.IntProperty(
        name="Sample count",
        description=(
            "Number of samples taken to compute a simple shape "
            "representation for every object to be compared. More "
            "samples improve accuracy, at the expense of computation "
            "time"
        ),
        default=_samplcnt,
        min=16,
        max=16384,
        soft_min=64,
        soft_max=1024,
        step=2,
        set=_set_samplecnt,
        get=_get_samplecnt,
        update=_update_samplecnt,
    )
    # Number of bins in the shape distribution histogram
    bincnt = ceil(sqrt(_samplcnt))
    # The shape difference of every selected object to the active one
    # Key is the objects name, value the shape difference
    svals = {}
    # Switch between a mode in which samples are recalculated and one
    # in which only the selection limits can be adjusted
    _resampl = True
    # Stores bgl handles for drawing the sample positions
    _gl_handls = []
    # Save a plot of every calculated shape distribution to disk?
    _save_plot = False

    def __del__(self):
        self._gl_handls.clear()

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT'
            and context.object is not None
            and context.object.type == 'MESH'
            )

    def _save_bar_plot(self, ob, xvals, yvals):
        """
        Helper for saving a plot of an object's shape distribution
        to disk.
        :param ob: The object to draw the plot for
        :param xvals: Values on the plot's x-axis
        :param yvals: Values on the plot's y-axis
        """
        bounds, _ = get_bounds_and_center(ob.bound_box)
        maxdist = np.linalg.norm(bounds)
        save_barplot(
            xvals=xvals,
            yvals=yvals[:-1],
            barwidth=maxdist / self.bincnt,
            # xmax=maxdist,
            title=(
                f"Samples: {self._samplcnt}, "
                f"Bins: {self.bincnt}, "
                f"Diaglength: {maxdist}"
            ),
            filename=ob.name,
            )

    def _get_shape_distrib(self, ob):
        """
        Sample an object's surface, draw the samples in the 3D view,
        return the object's shape distribution, and optionally save it
        as a plot to disk.
        """
        points = sample_surf(ob.data, self._samplcnt)

        # Draw samples
        tpoints = transf_vecs(ob.matrix_world, points)
        drawer = View3DDrawer(draw_points)
        self._gl_handls.append(drawer)
        try:
            drawer(tuple(tpoints))
        except RuntimeError:
            # Swallow it, it's just a visual cue after all.
            pass

        # Calc and plot shape distribution
        hist, bins = get_shape_distrib(points, self.bincnt)
        if self._save_plot:
            self._save_bar_plot(ob, hist, bins)
        return hist

    def _comp_shape_distribs(self, context):
        """
        Compare the shape distribution of the active object to every
        selected one. If there are none selected aside from the active
        object, compare it against the whole active collection.
        """
        self.svals.clear()
        # Don't show the sampled points anymore
        self._gl_handls.clear()
        # For handling errors if no object has mesh data
        all_type_err = True
        ob = context.object
        # Get shape distribution of active object
        adis = self._get_shape_distrib(ob)

        # Compare active with the rest of the selection if a selection
        # exists, compare all objects in the active collection if not.
        selobs = context.selected_objects
        # 2 because the active object is also seen as selected by
        # Blender, but is not counted in here
        if len(selobs) < 2:
            selobs = context.collection.objects
        for o in selobs:
            if o.type != 'MESH' or o is ob:
                continue
            all_type_err = False
            odis = self._get_shape_distrib(o)
            # Calculate similarity value to active object and store it.
            # Sadly we can't store a reference to 'o' directly, because
            # those references become invalid on undo, which is
            # triggered every time this operator is re-executed with
            # different parameters
            self.svals[o.name] = np.linalg.norm(odis - adis, ord=1)

        if all_type_err:
            self.report({'ERROR_INVALID_INPUT'},
                        "Only mesh objects can be compared")
            return False
        return True

    def cancel(self, context):
        # Don't show the sampled points anymore
        self._gl_handls.clear()

    def execute(self, context):
        # Switch between a mode in which samples are recalculated and
        # one in which only the selection limits are updated. In the
        # latter case we don't need to re-sample, which saves time.
        if self._resampl:
            if not self._comp_shape_distribs(context):
                return {'CANCELLED'}
        else:
            # Don't show the sampled points anymore
            self._gl_handls.clear()

        # Select every object within the set similarity limits,
        # unselect all the others that we calculated a similarity value
        # for.
        mins, maxs = self.sel_limits
        for name, simval in self.svals.items():
            bpy.data.objects[name].select_set(mins <= simval < maxs)
        return {'FINISHED'}


if __name__ == "__main__":
    register()
