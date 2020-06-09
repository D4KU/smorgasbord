import bpy
import numpy as np


def patch_to_rnd_color(data, patches, matname="patch"):
    mats = data.materials
    polys = data.polygons

    for i, patch in enumerate(patches, start=len(mats)):
        mat = bpy.data.materials.new(matname + str(i))
        col = np.random.rand(4)
        col[-1] = 1
        mat.diffuse_color = col
        mats.append(mat)

        for fi in patch:
            polys[fi].material_index = i

