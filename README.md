This repository contains some functions (operators) for Blender that I wrote
to make my life easier. I hope they do so for someone else as well.


# Installation

In Blender, navigate to `Edit > Preferences > Add-ons` and hit the *Install*
button. If you downloaded this repository as a zip file, select that. If you
cloned it, select the __init__.py file in the Add-ons' root directory. After
you hit *Install Add-on*, make sure to tick the Add-on in the list and save
your preferences. Enjoy!


# Content

### Replace by Primitive

In Object Mode: `Object > Transform > Replace by Primitive`

In Edit Mode: `Mesh > Transform > Replace by Primitive`

Replace selected objects or vertices by a chosen geometric primitive. This
primitive is transformed so its bounding box fits the bounding box of the
corresponding selected object or vertex selection as closely as possible.
Because this method only compares bounding boxes and does not use a full-blown
registration method, an object's apparent rotation can only be matched if it
is still accessible via the object's properties and wasn't already applied
directly to the mesh data.

![](https://github.com/D4KU/smorgasbord/blob/master/media/ReplaceByPrimitive.gif)


### Align Bounds

In Object Mode: `Object > Transform > Align Bounds`

In Edit Mode: `Mesh > Transform > Align Bounds`

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

In Edit Mode: `Select > Select Loose by Size` 

Select loose parts in the currently edited meshes whose bounding box volume is
greater than a given minimum threshold and less or equal than a given maximum
threshold.


### Set Parent Advanced 

`Object > Parent > Set Parent Advanced`

Adds more options to parent one object to another:

- *No Inverse, Keep Transform:* Keep no inverse parent correction (the child's
origin is the parent's position), but recalculate the transform values so that
the child keeps it's world transform.

- *No Inverse, Keep Basis:* Keep no inverse parent correction, but keep the
transform values set in the property panel. The child object moves.

- *World to Local Origin:* The inverse Parent correction is set so that the
child's world position before re-parenting becomes its new origin.


### Apply Name

`Object > Apply > Apply Name`

Set the name of an selected object's data block equal to the object name. If
several objects link to the same data block, its name is set to the one of the
last linked object in the scene hierarchy.


### Select All by Name

`Select > Select All by Name`

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

`Object > Transform > Prepare Export to Unity`

A crude script that applies a rotation and scaling to every selected object to
transform the coordinate system and units used in Blender to those used in the
Unity Game Engine. This script uses the `Apply Transform` function, which
makes it destructive and fail on shared mesh data.
