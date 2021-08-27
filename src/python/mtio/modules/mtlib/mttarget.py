
noesis = False

try:
    import inc_noesis
    noesis = True
except:
    pass

numpy = False
try:
    import numpy
    numpy = True
except:
    pass

max = False
try:
    import pymxs
    max = True
except:
    pass