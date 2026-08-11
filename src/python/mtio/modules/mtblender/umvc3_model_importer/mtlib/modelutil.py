'''
Various model-related utility functions.
'''

from .ncl import *

class imModelBounds:
    def __init__( self ):
        self.vmin = NclVec3()
        self.vmax = NclVec3()
        self.vminpoint = float()
        self.vmaxpoint = float()
        self.center = NclVec3()
        self.radius = float()

def calcWorldMtx( boneList, bone ):
    mtx = bone.getMatrix()
    parentWorldMtx = nclCreateMat44()
    if bone.parentIndex != -1:
        parentWorldMtx, _ = calcWorldMtx( boneList, boneList[ bone.parentIndex ] )
        mtx *= parentWorldMtx
    return ( mtx, parentWorldMtx )

def calcDistance( a, b ):
    #(a-b).magnitude
    return nclLength( a - b )

def calcBounds( vertices ) -> imModelBounds:
    if vertices is None:
        return imModelBounds()

    # calculate boundsa
    vmin = NclVec3()
    vmin[0] = 99999999
    vmin[1] = 99999999
    vmin[2] = 99999999
    
    vmax = NclVec3()
    vmax[0] = -99999999
    vmax[1] = -99999999
    vmax[2] = -99999999
    count = 0
    points = []
    for v in vertices:
        count += 1
        points.append( v )
        #print(v.position)
        if v[0] < vmin[0]: vmin[0] = v[0]
        if v[1] < vmin[1]: vmin[1] = v[1]
        if v[2] < vmin[2]: vmin[2] = v[2]
        
        if v[0] > vmax[0]: vmax[0] = v[0]
        if v[1] > vmax[1]: vmax[1] = v[1]
        if v[2] > vmax[2]: vmax[2] = v[2]

    if count == 0:
        # nothing came through, so the sentinels are still in place and would
        # give a radius of about 1.7e8. hand back an empty bounds instead.
        return imModelBounds()
    
    center = NclVec3()
    center[0] = ( vmin[0] + vmax[0] ) / 2
    center[1] = ( vmin[1] + vmax[1] ) / 2
    center[2] = ( vmin[2] + vmax[2] ) / 2  
    # Radius is the distance to the furthest point, not to the corner of the bounding
    # box. Retail stores the tight value and the corner over estimates it badly on
    # anything that isn't a cube. Ryu came out at 128.72 against a stored 105.41.
    radius = 0.0
    for v in points:
        d = calcDistance( center, v )
        if d > radius: radius = d
    
    # find furthest negative point
    vminpoint = vmin[0]
    if vmin[1] < vminpoint: vminpoint = vmin[1]
    if vmin[2] < vminpoint: vminpoint = vmin[2]
    
    # find furthest positive point
    vmaxpoint = vmax[0]
    if vmax[1] > vmaxpoint: vmaxpoint = vmax[1]
    if vmax[2] > vmaxpoint: vmaxpoint = vmax[2]
    
    b = imModelBounds()
    b.vmin = vmin
    b.vmax = vmax
    b.center = center
    b.radius = radius
    b.vminpoint = vminpoint
    b.vmaxpoint = vmaxpoint
    return b