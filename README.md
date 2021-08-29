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
2.5 [Select Visible](#select-visible)  
2.6 [Transfer Materials](#transfer-materials)  
2.7 [Select Concave Parts](#select-concave-partsselect-concave-parts)  
2.8 [Lerp Weights](#lerp-weights)  
2.9 [Set Parent Advanced](#set-parent-advanced)  
2.10 [Apply Name](#apply-name)  
2.11 [Select All by Name](#select-all-byname)  
2.12 [Replace Duplicate Materials](#replace-duplicate-materials)  
2.13 [Prepare Export to Unity](#prepare-export-to-unity)  
2.14 [Vertex Color to Group](#vertex-color-to-group)  
2.15 [Remove Empty Vertex Groups](#remove-empty-vertex-groups)  
2.16 [Remove Similar UV Maps](#remove-similar-uv-maps)  
2.17 [Force Apply Transform](#force-apply-transform)  
2.18 [Force Apply Modifier](#force-apply-modifier)  
2.19 [Select N Instances](#select-n-instances)  
2.20 [Viewport Display from Shader](#viewport-display-from-shader)


# Installation

The existence of submodules makes it unfortunately not possible to completely
download the repository as a zip file. Do this instead:

* Navigate to Blender's *addons* directory. If you don't know the path, type
`bpy.utils.user_resource('SCRIPTS', "addons")` into Blender's Python Console
to see it.
* Clone via `git clone --recurse-submodules https://github.com/D4KU/smorgasbord.git`
* In Blender, navigate to `Edit > Preferences > Add-ons`
* Hit the *Refresh* button
* Search for the add-on and tick it in the list.


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

This is an implementation of *Osada et al.'s* paper *Matching 3D Models with
Shape Distributions*. By selecting an object and choosing similarity measure
limits, one can find objects with a similar shape in the scene. The method is
scale- and rotation-invariant, but it is pretty simple, without any usage of
Machine Learning, so similarities between strongly deformed or complex objects
can't be reliably detected.

![](https://github.com/D4KU/smorgasbord/blob/master/media/SelectSimilar.gif)


### Select Visible

`[Edit mode] Select > Select Visible`

Renders edited objects from random positions around them and selects vertices
seen from any of those positions, leaving occluded vertices unselected. This
is useful to remove hidden inside parts of a CAD model, for example. A good
workflow following this function is to select linked vertices (Ctrl-L) to
catch the ones this operator missed, and then to invert the selection. This is
shown in the animation below.

![](https://github.com/D4KU/smorgasbord/blob/master/media/SelectVisible.gif)


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

Applies a rotation to every selected object so that when imported to Unity,
the Y and Z axis are swapped and no unwanted transformations are applied. The
result from applying this operator twice is the same as not applying it at
all.


### Vertex Color to Group

`[Object mode] Object Data Properties > Vertex Group Context Menu`

For every selected object, convert the active vertex color layer into a
eponymous vertex group. To convert from RGB values to scalar weights either
all channels are averaged or only individual ones are passed through.


### Remove Empty Vertex Groups

`[Object mode] Object Data Properties > Vertex Group Context Menu`

For every vertex group of every selected object, delete all groups not
containing any weights above a given threshold.


### Remove Similar UV Maps

`[Object mode] Search`

For every active UV map of every selected object, calculate the similarity to
other maps and remove them if they fall under a given threshold. Similarity is
computed by summing the absolute distances between each pair of UV coordinates
in both compared maps.


### Force Apply Transform

`[Object mode] Object > Apply`

Circumvents the restriction that an object's transform can't be applied to
its mesh if that mesh is shared with other objects. After applying the active
object's transform to the mesh, the local transform of other instances is
updated so that they stay in place. If other objects are selected besides
the active one, this compensation transformation is only applied to instances
within the selection.

Instead of setting the pivot point to the world origin, it can alternatively
be set to the cursor. This results in the same behaviour as the built-in
`Set origin to 3D cursor` operator, with the distinction that other instances
are updated so that they don't jump around.


### Force Apply Modifier

`[Object mode] Object > Apply`

Circumvents the restriction that modifiers can't be applied to linked data.
The data block is copied, the given modifier applied to it, and then the
original data block is overwritten with the copy for every selected object.
If no object is selected in addition to the active one, all objects in the
scene are considered selected.

### Select N Instances

`[Object mode] Select > Select N Instances`

For each data of selected objects, select N objects sharing the same data.
This can be mesh-, light-, curve-, camera-, armature-data, etc. Even
Empties are considered instances of another, since they all share 'None'
as common data.

N is set by a lower and upper bound. Negative values count from the end of the
instance list. For the upper bound, non-negative values less equal the lower
bound are considered as infinity. The order of instances is determined by
their occurrence in the scene hierarchy. A few examples:

- from 0 to 0: select all
- from 0 to 1: select first instance
- from 1 to 2: select second instance
- from 0 to -1: select all but the last instance
- from 5 to 0: select all from the fifth instance onward
- from 5 to 1: likewise
- from 5 to 5: likewise
- from -1 to 0: select nothing (not supported)
- from -1 to 3: likewise
- from -2 to -1: select last instance

### Viewport Display from Shader

`Material Properties > Material Context Menu (v-shape under minus-sign)`

For each active material of each selected object, search its node tree for a
shader node and apply its properties to the material's viewport display
properties. Optionally, do it the other way around: apply the viewport display
properties to the shader node.
