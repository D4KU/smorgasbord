[![Buy me a coffee](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/d4ku)

This repository contains various Blender operators to assist with the
simplification, skinning, and material assignment of CAD-derived meshes. It is
implemented in pure Python and therefore not always fast in handling
high-polygonal meshes. It is also under development, so beware of bugs!

1. [Installation](#installation)
2. [Operators](#operators)  
2.1 [Replace by Primitive](#replace-by-primitive)  
2.2 [Align Bounds](#align-bounds)  
2.3 [Select Loose by Size](#select-loose-by-size)  
2.4 [Select Similar](#select-similar)  
2.5 [Transfer Materials](#transfer-materials)  
2.6 [Select Concave Parts](#select-concave-partsselect-concave-parts)  
2.7 [Lerp Weights](#lerp-weights)  
2.8 [Set Parent Advanced](#set-parent-advanced)  
2.9 [Apply Name](#apply-name)  
2.10 [Select All by Name](#select-all-byname)  
2.11 [Replace Duplicate Materials](#replace-duplicate-materials)  
2.12 [Prepare Export to Unity](#prepare-export-to-unity)  


# Installation

Clone the repository to the **addons** directory in your script path with the
command `git clone --recurse-submodules
https://github.com/D4KU/smorgasboard.git`.  You can type
`bpy.utils.script_path_user()` into Blender's Python Console to find the path.
The existence of submodules makes it unfortunately not possible to obtain the
add-on as zip download.

In Blender, navigate to `Edit > Preferences > Add-ons` and hit the **Install**
button. Navigate to the cloned folder and select the *\_\_init__.py* file.
Make sure to also tick the add-on in the list and save your preferences.
Enjoy!


# Operators

### Replace by Primitive

`[Object mode] Object > Transform > Replace by Primitive`  
`[Edit mode] Mesh > Transform > Replace by Primitive`

Replace selected objects or vertices by a chosen geometric primitive. This
primitive is transformed so its bounding box fits the bounding box of the
corresponding selected object or vertex selection as closely as possible.
Because this method only compares bounding boxes and does not use a full-blown
registration method, an object's apparent rotation can only be matched if it
is still accessible via the object's properties and wasn't already applied
directly to the mesh data.

![](https://github.com/D4KU/smorgasbord/blob/master/media/ReplaceByPrimitive.gif)


### Align Bounds

`[Object mode] Object > Transform > Align Bounds`  
`[Edit mode] Mesh > Transform > Align Bounds`

In Object mode, align any number of selected objects to the active one. As in
the `Replace by Primitive` function, only the object's bounding boxes are
aligned, so the same restrictions regarding rotations apply.

In Edit mode this function aligns the bounds around the vertex selection of
each individual object to the vertex selection of the active object.

The method ignores pivot points and instead matches the bounding box centers
of all meshes/vertex selections. This, and the fact that also rotation and
scale are aligned, distinguishes this method from the built-in `Align Objects`
Blender function.

![](https://github.com/D4KU/smorgasbord/blob/master/media/AlignBounds.gif)


### Select Loose by Size

`[Edit mode] Select > Select Loose by Size` 

Select loose parts in the currently edited meshes whose bounding box volume
(or diagonal) is greater than a given minimum threshold and less or equal than
a given maximum threshold.

![](https://github.com/D4KU/smorgasbord/blob/master/media/SelectLooseBySize.gif)

### Select Similar

`[Object mode] Select > Select Similar`

This in an implementation of *Osada et al.'s* paper *Matching 3D Models with
Shape Distributions*. By selecting an object and choosing similarity measure
limits, one can find objects with a similar shape in the scene. The method is
scale- and rotation-invariant, but it is pretty simple, without any usage of
Machine Learning, so similarities between strongly deformed or complex objects
can't be reliably detected.

![](https://github.com/D4KU/smorgasbord/blob/master/media/SelectSimilar.gif)


### Transfer Materials

`[Object mode] Object > Relations > Transfer materials`

This operator only exists to compensate the fact that the Data Transfer
modifier can't transfer material slots. In every selected target mesh, it
finds the closest polygon in the active source mesh and copies over the
assigned material.

![](https://github.com/D4KU/smorgasbord/blob/master/media/TransferMaterials.gif)


### Select Concave Parts

`[Edit mode] Select > Select Concave Parts`

By comparing normals of adjacent faces, this operator is able to select
concave mesh parts. It defines a concave patch as a set of connected polygons
in which at least two polygons face each other by a given angle. The border to
neighboring patches is set along edges whose adjacent polygons face away from
each other.

![](https://github.com/D4KU/smorgasbord/blob/master/media/SelectConcaveParts.gif)


### Lerp Weights

`[Weight Paint mode] Weights > Lerp Weights`

By selecting two bones in an armature and vertices in a mesh, this operator is
able to linearly interpolate the bones' weights based on the distance between
them.

![](https://github.com/D4KU/smorgasbord/blob/master/media/LerpWeights.gif)


### Set Parent Advanced

`[Object mode] Object > Parent > Set Parent Advanced`

Adds more options to parent one object to another:

- *No Inverse, Keep Transform:* Keep no inverse parent correction (the child's
origin is the parent's position), but recalculate the transform values so that
the child keeps it's world transform.

- *No Inverse, Keep Basis:* Keep no inverse parent correction, but keep the
transform values set in the property panel. The child object moves.

- *World to Local Origin:* The inverse Parent correction is set so that the
child's world position before re-parenting becomes its new origin.


### Apply Name

`[Object mode] Object > Apply > Apply Name`

Set the name of an selected object's data block equal to the object name. If
several objects link to the same data block, its name is set to the one of the
last linked object in the scene hierarchy.


### Select All by Name

`[Object mode] Select > Select All by Name`

Select all objects in the scene whose name either contains, equals, starts
with, or ends with a given phrase.


### Replace Duplicate Materials

`Material Properties > Material Context Menu (v-shape under minus-sign)`

For every selected object's material slot, try to replace all assigned
duplicate materials with their original by comparing their names. A regular
expression, which can be passed to the function as input, specifies how
material names are matched. The default expression, `.*(?=\.[0-9]+)`, replaces
a material with a suffix containing a dot and a number by the corresponding
material without such a suffix, if such a material exists. For example,
*Plastic_black.001* would be replaced by *Plastic_black*, if existent.


### Prepare Export to Unity

`[Object mode] Object > Transform > Prepare Export to Unity`

A crude script that applies a rotation and scaling to every selected object to
transform the coordinate system and units used in Blender to those used in the
Unity Game Engine. This script uses the `Apply Transform` function, which
makes it destructive and fail on shared mesh data.
