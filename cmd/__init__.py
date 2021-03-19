"""
Print attributes of 'target' whose name contains the given string

Parameters
----------
target : Any
    The object to search

substr : str
    Search phrase
"""
def print_attr(target, substr):
    for a in dir(target):
        if substr in a:
            print(a)


"""
Print types in bpy.types whose name contains the given string

Parameters
----------
substr : str
    Search phrase
"""
def print_types(substr):
    import bpy
    for t in dir(bpy.types):
        if substr in t:
            print(t)
