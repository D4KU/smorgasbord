from collections import defaultdict
from math import floor
import numpy as np

from smorgasbord.common.io import get_bounds_and_center


def _res_heur(data, *args, **kwargs):
    """
    Returns, for the given data, the heuristic determining the
    resolution of the voxel grid and correspondingly, how many
    points get hashed to the same value.
    """
    return 3 * len(data) ** 0.33333333


class SpatialHasher:
    """
    A spatial hash for 3D coordinates, allowing fast look-up of
    neighboring data.
    """

    def __init__(self, data, res_heuristic=_res_heur):
        """
        @TODO document
        """
        self.data = data
        bounds, center = get_bounds_and_center(data)

        # Determine the voxel edge length
        self.celllen = np.average(np.divide(
            res_heuristic(data, bounds, center),
            bounds,
            # Prevent division by zero
            out=np.zeros_like(bounds, dtype=float),
            where=bounds != 0,
            ))

        # Quantize data and bring in a form that can be broadcast by
        # NumPy. For N vertices, this transforms the array from
        # (N, 3) to (N, 1, 3) dimensions.
        qdata = self.quantize(data)[:, np.newaxis]

        # Generate voxel kernel from all 3**3 = 27 combinations of
        # -1, 0, and 1.
        o = np.array((-1, 0, 1)) * self.celllen
        kern = np.array(np.meshgrid(o, o, o)).T.reshape(-1, 3)

        # Generate array that not only contains every quantized point,
        # but also the points offset by the voxel cell size along each
        # axis in +/- direction. For each original data entry, that
        # yields 3**3 = 27 entries.
        kdata = (kern + qdata).reshape(-1, 3)

        # Build hash. Every data point gets linked to the cell it's
        # in as well as all 26 neighboring cells. This overlap is what
        # guarantees fast "closest vertex" lookup at the cost of higher
        # memory consumption.
        self.hash = defaultdict(list)
        for i, c in enumerate(kdata):
            # Store index in data array for each of the 27 entries.
            self.hash[tuple(c)] += [floor(i / 27)]

    def quantize(self, p):
        """
        Quantizes a given point according to the voxel grid resolution.
        """
        return np.round(np.asarray(p) * self.celllen)

    def find_close(self, p):
        """
        Returns a list of data indices in the vicinity of the given
        point.
        """
        return self.hash(tuple(self.quantize(p)))

    def find_closest(self, p):
        """
        Returns the index of the closest data index to the given point.
        """
        close = self.find_close(p)
        # Search through all data if hash misses
        vs = close if close else self.data
        return np.argmin(np.linalg.norm(vs - np.asarray(p)))
