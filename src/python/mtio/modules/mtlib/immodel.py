'''
Intermediate (im) model representation to simplify model conversion from foreign data structures
'''

from dataclasses import dataclass
from ncl import *
from rmodel import *
import vertexcodec
import modelutil
from immaterial import *
import re
from copy import copy, deepcopy

class imModelMaterial:
    def __init__( self ):
        self.name = ''
        self.diffuseTex = ''
        
class imVertexWeight:
    def __init__( self ):
        self.weights = []
        self.indices = []

class imPrimitiveJointLink:
    def __init__( self, name, joint, field04, field08, field0c, 
        boundingSphere, min, max, localMtx, field80 ):
        self.name = name
        self.joint = joint
        self.field04 = field04
        self.field08 = field08
        self.field0c = field0c
        self.boundingSphere = deepcopy(boundingSphere)
        self.min = deepcopy(min)
        self.max = deepcopy(max)
        self.localMtx = deepcopy(localMtx)
        self.field80 = deepcopy(field80)
        
class imCacheVertex:
    '''Trivially hash-able container for optimizing the vertex cache'''
    def __init__( self ):
        self.position = ()
        self.normal = ()
        self.tangent = ()
        self.uv = ()
        self.weights = ()
        self.weightIndices = ()
        
    def __eq__(self, o: object) -> bool:
        if isinstance( o, imCacheVertex ):
            return self.position == o.position and \
                   self.normal == o.normal and \
                   self.tangent == o.tangent and \
                   self.uv == o.uv and \
                   self.weights == o.weights and \
                   self.weightIndices == o.weightIndices
                   
    def __hash__( self ):
        return hash((self.position, self.normal, self.tangent, self.uv, self.weights, self.weightIndices))
    
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); fs16 Position[3];
 FSeek( p + 6 ); fs16 Weight[1];
 FSeek( p + 8 ); fs8 Normal[3];
 FSeek( p + 11 ); fs8 Occlusion[1];
 FSeek( p + 12 ); fs8 Tangent[4];
 FSeek( p + 16 ); u8 Joint[4];
 FSeek( p + 20 ); f16 TexCoord[2];
 FSeek( p + 24 ); f16 Weight_2[2];
 FSeek( p + 20 ); f16 UV_Primary[2];
 FSeek( p + 20 ); f16 UV_Secondary[2];
 FSeek( p + 20 ); f16 UV_Unique[2];
 FSeek( p + 20 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IASkinTB4wt;
'''    
        
class imVertexIASkinTB4wt:
    # fs16 5
    # fs8 9
    # u8 8
    # f16 2
    
    SIZE = 28
    
    def __init__( self ):
        self.position = NclVec3()
        self.weights = [0,0,0,0]
        self.normal = NclVec3()
        self.occlusion = 0
        self.tangent = NclVec4()
        self.jointIds = [0,0,0,0]
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[0] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[1] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[2] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[3] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.weights[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.weights[2] ) )
        
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); fs16 Position[3];
 FSeek( p + 6 ); fs16 Weight[1];
 FSeek( p + 8 ); fu8 Normal[3];
 FSeek( p + 11 ); fu8 Occlusion[1];
 FSeek( p + 12 ); fu8 Tangent[4];
 FSeek( p + 16 ); f16 TexCoord[2];
 FSeek( p + 20 ); f16 Joint[2];
 FSeek( p + 16 ); f16 UV_Primary[2];
 FSeek( p + 16 ); f16 UV_Secondary[2];
 FSeek( p + 16 ); f16 UV_Unique[2];
 FSeek( p + 16 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IASkinTB2wt;
'''        

class imVertexIASkinTB2wt:
    SIZE = 24
    
    def __init__( self ):
        self.position = NclVec3()
        self.weights = [0,0]
        self.normal = NclVec3()
        self.occlusion = 0
        self.tangent = NclVec4()
        self.jointIds = [0,0]
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.jointIds[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.jointIds[1] ) )
        
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); fs16 Position[3];
 FSeek( p + 6 ); u16 Joint[1];
 FSeek( p + 8 ); fu8 Normal[3];
 FSeek( p + 11 ); fu8 Occlusion[1];
 FSeek( p + 12 ); fu8 Tangent[4];
 FSeek( p + 16 ); f16 TexCoord[2];
 FSeek( p + 16 ); f16 UV_Primary[2];
 FSeek( p + 16 ); f16 UV_Secondary[2];
 FSeek( p + 16 ); f16 UV_Unique[2];
 FSeek( p + 16 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IASkinTB1wt;
'''
        
class imVertexIASkinTB1wt:
    SIZE = 20
    
    def __init__( self ):
        self.position = NclVec3()
        self.normal = NclVec3()
        self.occlusion = 0
        self.tangent = NclVec4()
        self.jointId = 0
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeU16( self.jointId ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[1] ) )
        
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); f32 Position[3];
 FSeek( p + 12 ); fu8 Normal[3];
 FSeek( p + 15 ); fs8 Occlusion[1];
 FSeek( p + 16 ); fu8 Tangent[4];
 FSeek( p + 20 ); f16 TexCoord[2];
 FSeek( p + 20 ); f16 UV_Primary[2];
 FSeek( p + 20 ); f16 UV_Secondary[2];
 FSeek( p + 20 ); f16 UV_Unique[2];
 FSeek( p + 20 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IANonSkinTB;
'''
class imVertexIANonSkinTB:
    SIZE = 24
    
    def __init__( self ):
        self.position = NclVec3()
        self.normal = NclVec3()
        self.occlusion = 0
        self.tangent = NclVec4()
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeFloat( vertexcodec.encodeF32( self.position[0] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[1] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.texCoord[1] ) )
        
@dataclass()
class imVertexFormat(object):
    vertexFlags: int = None
    vertexStride: int = None
    vertexShader: str = None
    maxWeightCount: int = None
    hasOcclusion: bool = None
    hasTangent: bool = None
    hasTexCoord: bool = None
    vertexType: type = None
    isCompressed: bool = False
    
    @staticmethod
    def determineBestVertexFormat( model, prim ):
        '''
        Determine the best vertex format according to the data contained in the primitive.
        '''
   
        fmt = imVertexFormat()
        fmt.hasOcclusion = True
        fmt.hasTangent = True
        fmt.hasTexCoord = True    

        maxUsedBoneCount = prim.getMaxUsedBoneCount()

        if maxUsedBoneCount > 2 and maxUsedBoneCount <= 4:
            fmt.vertexShader = 'IASkinTB4wt'
            fmt.maxWeightCount = 4
            fmt.vertexStride = imVertexIASkinTB4wt.SIZE
            fmt.vertexFlags = 0x19
            fmt.vertexType = imVertexIASkinTB4wt
            fmt.isCompressed = True
        elif maxUsedBoneCount == 2:
            fmt.vertexShader  = 'IASkinTB2wt'
            fmt.maxWeightCount = 2
            fmt.vertexStride = imVertexIASkinTB2wt.SIZE
            fmt.vertexFlags = 0x11
            fmt.vertexType = imVertexIASkinTB2wt
            fmt.isCompressed = True
        elif maxUsedBoneCount == 1:
            fmt.vertexShader  = 'IASkinTB1wt'
            fmt.maxWeightCount = 1
            fmt.vertexStride = imVertexIASkinTB1wt.SIZE
            fmt.vertexFlags = 0x09
            fmt.vertexType = imVertexIASkinTB1wt
            fmt.isCompressed = True
        else:
            if len( model.joints ) > 0:
                # assume that when the model has joints, it's a character model
                # that uses compressed vertices
                fmt.vertexShader  = 'IASkinTB1wt'
                fmt.maxWeightCount = 1
                fmt.vertexStride = imVertexIASkinTB1wt.SIZE
                fmt.vertexFlags = 0x09
                fmt.vertexType = imVertexIASkinTB1wt
                fmt.isCompressed = True
            else:
                fmt.vertexShader  = 'IANonSkinTB'
                fmt.maxWeightCount = 0
                fmt.vertexStride = imVertexIANonSkinTB.SIZE
                fmt.vertexFlags = 0x01
                fmt.vertexType = imVertexIANonSkinTB
                fmt.isCompressed = False
             
        return fmt

# TODO refactor vertex format into its own class
class imPrimitive:
    '''
    Intermediate primitive data container intended to be used for generating optimized data for export
    '''
    
    def __init__( self, name, materialName, flags=0xFFFF, group=None, 
            lodIndex=0xFF, vertexFlags=None, vertexStride=None, renderFlags=67, 
            vertexShader=None, id=None, field2c=0, 
            positions=None, tangents=None, normals=None, uvs=None, weights=None, indices=None ):
        self.name = name
        self.materialName = materialName
        self.flags = flags
        self.group = group
        self.lodIndex = lodIndex
        self.renderFlags = renderFlags
        self.id = id
        self.field2c = field2c
        self.positions = positions if positions != None else []
        self.tangents = tangents if tangents != None else []
        self.normals = normals if normals != None else []
        self.uvs = uvs if uvs != None else []
        self.weights = weights
        self.indices = indices
        self.bitangents = []
        self.vertexFormat = imVertexFormat( vertexFlags, vertexStride, vertexShader )

    def getMaxUsedBoneCount( self ):
        '''
        Get the max. number of used bones in the primitive
        '''
        totalMaxUsedBoneCount = 0
        if self.isSkinned():
            for w in self.weights:
                usedBoneCount = 0
                for j in range( 0, len( w.weights ) ):
                    weight = w.weights[ j ]
                    if weight > 0.001:
                        usedBoneCount += 1            
                totalMaxUsedBoneCount = max( usedBoneCount, totalMaxUsedBoneCount )
        return totalMaxUsedBoneCount

    def reduceWeights( self, maxWeightsPerVertex ):
        '''
        Reduce the weights in the primitive to be less or equal to the given max weights per vertex.
        The most influential weights are kept, and the remainder is equally distributed.
        '''
        
        # pick 4 most influential weights and remove the others
        if self.isSkinned():
            for k, w in enumerate( self.weights ):
                weightIndex = []
                for k in range( 0, len(w.weights) ):
                    weightIndex.append((w.weights[k], w.indices[k]))
                weightIndex = sorted(weightIndex, key=lambda x: x[0])

                weightTotal = 0
                w.weights = []
                w.indices = []
                for k in range( 0, min(len(weightIndex), maxWeightsPerVertex) ):
                    weight, index = weightIndex[k]
                    weightTotal += weight
                    w.weights.append( weight )
                    w.indices.append( index )

                # average out the weights
                weightRemainder = 1 - weightTotal
                weightAvgStep = weightRemainder / len(w.weights)
                for k in range( 0, len(w.weights) ):
                    w.weights[k] += weightAvgStep
                    
    def updateVertexFormat( self, model ):
        self.vertexFormat = imVertexFormat.determineBestVertexFormat( model, self )

    def isIndexed( self ):
        return self.indices != None
    
    def isSkinned( self ):
        return self.weights != None
    
    def makeDirect( self ):
        '''
        Removes the need for the index buffer by duplicating all the vertex data according to it.
        '''
        if self.indices == None:
            return
        else:
            raise NotImplementedError()
    
    def makeIndexed( self, progressCb = None ):
        '''
        Makes the model indexed by removing all duplicate vertex data and generating an index buffer that refers to each vertex component by index.
        '''
        self.makeDirect()
        
        # copy vertex data
        positions = self.positions
        normals = self.normals
        uvs = self.uvs
        weights = self.weights
        tangents = self.tangents
        isSkinned = self.isSkinned()
        
        # clear vertex data
        self.positions = []
        self.normals = []
        self.uvs = []
        self.weights = [] if weights != None else None
        self.tangents = [] if tangents != None else None
        self.indices = []
        
        # optimize vertex buffer
        vertexIdxLookup = dict()
        nextVertexIdx = 0
        for i in range( 0, len( positions ) ):
            if progressCb != None: progressCb( i/len(positions) )
            
            cv = imCacheVertex()
            cv.position = (positions[i][0], positions[i][1], positions[i][2])
            cv.normal = (normals[i][0], normals[i][1], normals[i][2])
            cv.uv = (uvs[i][0], uvs[i][1])
            cv.tangent = (tangents[i][0], tangents[i][1], tangents[i][2], tangents[i][3]) if tangents != None else None

            if isSkinned:
                cv.weights = tuple(weights[i].weights)
                cv.weightIndices = tuple(weights[i].indices)    

            if cv not in vertexIdxLookup:
                idx = nextVertexIdx
                nextVertexIdx += 1
                vertexIdxLookup[cv] = idx

                self.positions.append( NclVec3( cv.position ) )
                self.normals.append( NclVec3( cv.normal ) )
                self.uvs.append( NclVec2( cv.uv ) ) 
                self.tangents.append( NclVec4( cv.tangent ) )

                vtxWeight = imVertexWeight()
                vtxWeight.indices = cv.weightIndices
                
                if isSkinned:
                    vtxWeight.weights = cv.weights
                    self.weights.append( vtxWeight )
            else:
                idx = vertexIdxLookup.get(cv)

            self.indices.append(idx)
            
    def generateTangents( self, progressCb=None ):
        tangents = [NclVec3()] * len(self.positions)
        bitangents = [NclVec3()] * len(self.positions)
        self.tangents = []
        count = len( self.indices ) if self.isIndexed() else len( self.positions )
        
        for i in range( 0, count, 3 ):
            if progressCb != None: progressCb( i/count )
            triangleA = self.indices[i] if self.isIndexed() else i
            triangleB = self.indices[i+1] if self.isIndexed() else i+1
            triangleC = self.indices[i+2] if self.isIndexed() else i+2
            positionA = self.positions[ triangleC ] - self.positions[ triangleA ]
            positionB = self.positions[ triangleB ] - self.positions[ triangleA ]

            texCoordA = self.uvs[ triangleC ] - self.uvs[ triangleA ]
            texCoordB = self.uvs[ triangleB ] - self.uvs[ triangleA ]

            direction = texCoordA[0] * texCoordB[1] - texCoordA[1] * (1.0 if texCoordB[0] > 0.0 else -1.0)
            #EDIT
            direction *= -1

            tangent = ( positionA * texCoordB[1] - positionB * texCoordA[1] ) * direction
            bitangent = ( positionB * texCoordA[0] - positionA * texCoordB[0] ) * direction

            tangents[ triangleA ] += tangent
            tangents[ triangleB ] += tangent
            tangents[ triangleC ] += tangent

            bitangents[ triangleA ] += bitangent
            bitangents[ triangleB ] += bitangent
            bitangents[ triangleC ] += bitangent
            
        for i in range( 0, len( tangents ) ):
            if progressCb != None: progressCb( i/len( tangents ) )
            normal = self.normals[ i ]

            tangent = nclNormalize( tangents[ i ] )
            bitangent = nclNormalize( bitangents[ i ] )

            tangent = nclNormalize( tangent - normal * nclDot( tangent, normal ) )
            bitangent = nclNormalize( bitangent - normal * nclDot( bitangent, normal ) )

            directionCheck = nclDot( nclNormalize( nclCross( normal, tangent ) ), bitangent )
            self.tangents.append( NclVec4( ( tangent[0], tangent[1], tangent[2], (1.0 if directionCheck > 0.0 else -1.0 ) ) ) )

        # Look for NaNs
        for i in range( 0, len( self.positions ) ):
            if progressCb != None: progressCb( i/len( self.positions ) )
            position = self.positions[ i ]
            tangent = self.tangents[ i ]

            if not math.isnan( tangent[0] ) and not math.isnan( tangent[1] ) and not math.isnan( tangent[2] ):
                continue

            nearestVertexIndex = -1
            currentDistance = float("+inf")

            for j in range( 0, len( self.positions ) ):
                positionToCompare = self.positions[ j ]
                tangentToCompare = self.tangents[ j ]

                if i == j or math.isnan( tangentToCompare[0] ) or math.isnan( tangentToCompare[1] ) or math.isnan( tangentToCompare[2] ):
                    continue

                #distance = nclDistanceSq( position, positionToCompare );
                temp = position - positionToCompare
                distance = nclDot(temp, temp)

                if distance > currentDistance: 
                    continue

                nearestVertexIndex = j
                currentDistance = distance

            if nearestVertexIndex != -1:
                self.tangents[ i ] = self.tangents[ nearestVertexIndex ]
        
class imJoint:
    def __init__( self, name='', id=None, localMtx=None, worldMtx=None, 
        invBindMtx=None, parent=None, symmetry=None, field03=0, 
        field04=0, offset=None, length=None ):

        assert localMtx is None or isinstance(localMtx, NclMat44)
        assert worldMtx is None or isinstance(worldMtx, NclMat44)
        assert invBindMtx is None or isinstance(invBindMtx, NclMat44)

        self.name = name
        self.invBindMtx = deepcopy(invBindMtx)
        self.id = 0 if id == None else id
        self.symmetry = symmetry
        self.field03 = 0 if field03 == None else field03
        self.field04 = 0 if field04 == None else field04

        self.localMtx = deepcopy(localMtx)
        self.worldMtx = deepcopy(worldMtx)
        self.parent = parent
        if self.localMtx == None:
            assert self.worldMtx != None
            self.updateLocalFromWorld()
        elif self.worldMtx == None:
            assert self.localMtx != None
            self.updateWorldFromLocal()

        self.offset = deepcopy(offset)
        if self.offset == None:
            self.updateOffsetFromLocal()

        self.length = length
        if self.length == None:
            self.updateLength()
        
        assert self.worldMtx != None
        assert self.localMtx != None
        assert self.id != None
        assert self.length != None
        assert self.offset != None

    def getWorldMtx( self ):
        if self.worldMtx == None:
            self.updateWorldFromLocal()
    
        return self.worldMtx

    def updateWorldFromLocal( self ):
        self.worldMtx = deepcopy(self.localMtx)
        if self.parent != None:
            self.worldMtx = self.parent.getWorldMtx() * self.worldMtx

    def updateLocalFromWorld( self ):
        # calculate local matrix if only world matrix is given
        self.localMtx = deepcopy(self.getWorldMtx())
        parentWorldMtx = nclCreateMat44()
        if self.parent != None:
            parentWorldMtx = self.parent.getWorldMtx()
            # localMtx = worldMtx * nclInverse( parentWorldMtx )
            self.localMtx = nclInverse( parentWorldMtx ) * self.localMtx
        return self.localMtx

    def updateOffsetFromLocal( self ):
        # take translation component of local matrix as offset
        self.offset = deepcopy(self.localMtx[3])

    def updateLength( self ):
        # calculate length
        self.length = nclLength( self.offset ) if not ( self.offset[0] == 0 and  self.offset[1] == 0 and  self.offset[2] == 0) else 0

class imGroup:
    def __init__( self, name, id, field04 = 0, field08 = 0, field0c = 0, boundingSphere = None ):
        assert id != None
        
        self.name = name
        self.id = id
        self.field04 = 0 if field04 == None else field04
        self.field08 = 0 if field08 == None else field08
        self.field0c = 0 if field0c == None else field0c
        self.boundingSphere = deepcopy(boundingSphere) # can be zero, in which case it is calculated later
        
class imTag:
    PATTERN = re.compile(r"""@(.+?)(?!=\()\((.+?(?!=\)))\)""")
    
    def iterTags( name ):
        for tag, value in re.findall(imTag.PATTERN, name):
            yield tag, value
        
class imModel:
    '''Intermediate model data'''

    def __init__( self, primitives=None, joints=None, materials=None, groups=None, primitiveJointLinks=None, 
        center=None, radius=None, min=None, max=None, 
        field90=1000, field94=3000, field98=1, field9c=0 ):
        self.primitives = primitives if primitives != None else []
        self.joints = joints if joints != None else []
        self.materials = materials if materials != None else []
        self.groups = groups if groups != None else []
        self.primitiveJointLinks = primitiveJointLinks if primitiveJointLinks != None else []
        self.center = deepcopy(center)
        self.radius = radius
        self.min = deepcopy(min)
        self.max = deepcopy(max)
        self.field90 = field90
        self.field94 = field94
        self.field98 = field98
        self.field9c = field9c

    def getGroupById( self, id ):
        for group in self.groups:
            if group.id == id:
                return group
        return None

    def getJointById( self, id ):
        for joint in self.joints:
            if joint.id == id:
                return joint
        return None
        
    def fromBinaryModel( self, mod ):
        pass
        
    def toBinaryModel( self ):
        mod = rModelData()
        
        for i in range(0, 256):
            mod.boneMap.append(-1)
            
        # create id -> index map
        if len( self.joints ) > 255:
            raise RuntimeError( f"Too many bones. (max 256, got {len(self.joints)})" )
        
        for i, joint in enumerate( self.joints ):
            mod.boneMap[ joint.id ] = i
        
        # convert joints
        for i, joint in enumerate( self.joints ):                   
            modJoint = rModelJoint()
            modJoint.id = joint.id
            modJoint.parentIndex = self.joints.index( joint.parent ) if joint.parent != None else -1
            modJoint.symmetryIndex = self.joints.index( joint.symmetry ) if joint.symmetry != None else -1 # improper index causes animation glitches
            modJoint.field03 = joint.field03
            modJoint.field04 = joint.field04
            modJoint.offset = joint.offset
            modJoint.length = joint.length
            mod.joints.append( modJoint )
            mod.jointLocalMtx.append( joint.localMtx )

            if joint.invBindMtx != None:
                # TODO: can this possibly be made to work?
                # mod.jointInvBindMtx.append( joint.invBindMtx )
                pass
            else:
                # inverse bind matrix is calculated after processing vertices because it includes the model matrix
                pass

        # convert groups
        for i, group in enumerate( self.groups ):
            modGroup = rModelGroup()
            modGroup.boundingSphere = group.boundingSphere
            modGroup.field04 = group.field04
            modGroup.field08 = group.field08
            modGroup.field0c = group.field0c
            modGroup.id = group.id
            mod.groups.append( modGroup )

        # convert pml
        for i, pml in enumerate( self.primitiveJointLinks ):
            modPml = rModelPrimitiveJointLink()
            modPml.jointIndex = self.joints.index( pml.joint )
            modPml.field04 = pml.field04
            modPml.field08 = pml.field08
            modPml.field0c = pml.field0c
            modPml.boundingSphere = pml.boundingSphere
            modPml.min = pml.min
            modPml.max = pml.max
            modPml.localMtx = pml.localMtx
            modPml.field80 = pml.field80
            mod.primitiveJointLinks.append(modPml)
        
        nextVertexOffset = 0
        nextTriangleIndex = 0
        vertices = []
        indices = []
        
        for meshIndex, mesh in enumerate( self.primitives ):
            mesh: imPrimitive
            
            # find material
            meshMatIndex = -1
            for matIndex, mat in enumerate( mod.materials ):
                if mat == mesh.materialName:
                    meshMatIndex = matIndex
                    break
                
            if meshMatIndex == -1:
                # add material
                meshMatIndex = len( mod.materials )
                mod.materials.append( mesh.materialName )
                
            if mesh.getMaxUsedBoneCount() > 4:
                mesh.reduceWeights( 4 )

            # determine vertex format 
            mesh.updateVertexFormat( self )
            
            # convert vertices
            for i in range(0, len(mesh.positions)):
                t = mesh.tangents[i]
                vtx = mesh.vertexFormat.vertexType()                
                vtx.position = mesh.positions[i]
                vtx.normal = mesh.normals[i]
                
                if mesh.vertexFormat.hasOcclusion:    
                    vtx.occlusion = 1
                
                if mesh.vertexFormat.hasTangent:
                    vtx.tangent = NclVec4( ( t[0], t[1], t[2], t[3] ) )
                
                if mesh.vertexFormat.hasTexCoord:    
                    vtx.texCoord = mesh.uvs[i]
                
                if mesh.vertexFormat.maxWeightCount == 0:
                    pass
                elif mesh.vertexFormat.maxWeightCount == 1:
                    # HACK assume that when the vertex has no indices but is assigned a vertex format with 1 weight, that it's an unrigged mesh
                    # for a skeleton mesh model
                    if mesh.weights == None or len( mesh.weights[i].indices ) == 0:
                        jointIndex = 0
                    else:
                        jointIndex = mesh.weights[ i ].indices[ 0 ]

                    vtx.jointId = jointIndex
                else:            
                    lastJointId = 0
                    weightSum = 0
                    usedBoneCount = 0
                    for j in range( 0, mesh.vertexFormat.maxWeightCount ):
                        if j >= len( mesh.weights[ i ].weights ):
                            # vanilla models repeat the last joint id with a weight of 0
                            vtx.jointIds[ j ] = lastJointId
                            vtx.weights[ j ] = 0
                            continue
                        
                        weight = mesh.weights[ i ].weights[ j ]
                        if weight < 0.001:
                            # remove very small weights
                            weight = 0
                        
                        jointIndex = mesh.weights[ i ].indices[ j ]
                        joint = mod.joints[ jointIndex ]
                        boneId = jointIndex
                        
                        vtx.weights[ j ] = weight
                        weightSum += weight
                        
                        vtx.jointIds[ j ] = boneId
                        lastJointId = boneId
                        
                        if weight > 0.001:
                            usedBoneCount += 1
                        
                    assert usedBoneCount > 0, 'mesh {} has unrigged vertex at index {}'.format(mesh.name, i)

                    # adjust for floating point error by averaging out the weights
                    weightError = 1 - weightSum
                    weightAvgStep = weightError / usedBoneCount
                    for j in range( usedBoneCount ):
                        vtx.weights[ j ] += weightAvgStep
                
                vertices.append( vtx )
                
            # convert indices
            for i in range(0, len( mesh.indices ) ):
                indices.append( mesh.indices[ i ] )
                
            # create primitive
            prim = rModelPrimitive()
            prim.flags = mesh.flags # no obvious effect
            prim.vertexCount = len( mesh.positions )
            prim.indices.setGroupId( mesh.group.id if mesh.group != None else 0 )
            prim.indices.setLodIndex( mesh.lodIndex )
            prim.indices.setMaterialIndex( meshMatIndex )

            # set vertex flags based on bone count
            prim.vertexFlags = mesh.vertexFormat.vertexFlags
            prim.vertexStride = mesh.vertexFormat.vertexStride
            prim.renderFlags = mesh.renderFlags
            prim.vertexStartIndex = 0
            prim.vertexBufferOffset = nextVertexOffset
            prim.vertexShader = util.getShaderObjectIdFromName( mesh.vertexFormat.vertexShader )
            prim.indexBufferOffset = nextTriangleIndex
            prim.indexCount = len( mesh.indices )
            prim.indexStartIndex = 0
            prim.boneIdStart = 0
            prim.primitiveJointLinkCount = 0
            prim.id = meshIndex
            prim.minVertexIndex = 0
            prim.maxVertexIndex = prim.minVertexIndex + prim.vertexCount
            prim.field2c = 0
            prim.primitiveJointLinkPtr = 0
            mod.primitives.append( prim )
            
            nextVertexOffset += prim.vertexCount * prim.vertexStride
            nextTriangleIndex += prim.indexCount 
        
        bounds = modelutil.calcBounds( vertices )

        if len( self.joints ) > 0:
            # compress vertices
            
            if len(mod.jointInvBindMtx) == 0:
                # calculate distance between 2 furthest points
                # will be used as the vertex scale
                vscale = -bounds.vminpoint + bounds.vmaxpoint
                vbias = bounds.vmin * -1
                
                # set up model matrix
                modelMtx = nclCreateMat43()
                modelMtx[3] = vbias
                modelMtx *= (1/vscale)
                modelMtx = nclCreateMat44(modelMtx)
                
                # calculate joint inverse bind matrices
                for i, joint in enumerate( self.joints ):   
                    # apply model matrix to world transform of each joint
                    invBindMtx = nclInverse( nclMultiply( joint.getWorldMtx(), modelMtx ) )
                    finalInvBindMtx = nclCreateMat44( invBindMtx )
                    mod.jointInvBindMtx.append( finalInvBindMtx )
            else:
                # extract the model matrix from the inverse bind matrix of the root bone
                modelMtx = nclInverse( mod.jointInvBindMtx[0] )
            
            # normalize vertices
            modelMtxNormal = nclTranspose( nclInverse( modelMtx ) )
            
            for v in vertices:
                v.position = nclTransform( v.position, modelMtx )
                v.normal = nclNormalize( nclTransform( v.normal, modelMtxNormal ) )
        
        # create buffers
        vertexBufferStream = NclBitStream()
        for v in vertices:
            v.write( vertexBufferStream )
        mod.vertexBuffer = vertexBufferStream.getBuffer()
            
        indexBufferStream = NclBitStream()
        for i in indices:
            indexBufferStream.writeUShort( i )
        mod.indexBuffer = indexBufferStream.getBuffer()
            
        # fill out header
        mod.header.jointCount = len( mod.joints )
        mod.header.primitiveCount = len( mod.primitives )
        mod.header.materialCount = len( mod.materials )
        mod.header.vertexCount = len( vertices )
        mod.header.indexCount = len( indices )
        mod.header.polygonCount = mod.header.indexCount // 3
        mod.header.vertexBufferSize = len( mod.vertexBuffer )
        mod.header.vertexBuffer2Size = 0
        mod.header.groupCount = len( mod.groups )
        mod.header.center = bounds.center if self.center == None else self.center
        mod.header.radius = bounds.radius if self.radius == None else self.radius
        mod.header.min = nclCreateVec4( bounds.vmin ) if self.min == None else self.min
        mod.header.max = nclCreateVec4( bounds.vmax ) if self.max == None else self.max
        mod.header.field90 = self.field90
        mod.header.field94 = self.field94
        mod.header.field98 = self.field98
        mod.header.field9c = self.field9c
        mod.header.primitiveJointLinkCount = len( mod.primitiveJointLinks )
        return mod
        
    def saveBinaryStream( self, stream ):
        mod = self.toBinaryModel()
        mod.write( stream )