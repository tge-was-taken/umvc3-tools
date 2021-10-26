'''
Intermediate model representation to simplify model conversion from foreign data structures
'''

from mtncl import *
from mtrmodel import *
import mtvertexcodec
import mtmodelutil
from mtimmaterial import *
import re

class imModelMaterial:
    def __init__( self ):
        self.name = ''
        self.diffuseTex = ''
        
class imVertexWeight:
    def __init__( self ):
        self.weights = []
        self.indices = []

class imPrimitive:
    def __init__( self ):
        self.name = ''
        self.matName = ''
        self.positions = []
        self.tangents = []
        self.normals = []
        self.uvs = []
        self.weights = []
        self.indices = []
        
class imJoint:
    def __init__( self ):
        self.name = ''
        self.worldMtx = nclCreateMat44()
        self.parentIndex = -1  
        self.id = -1
        self.symmetryId = -1
        self.field03 = 0
        self.field04 = 0
        self.length = 0
        
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
        self.tangent = NclVec3()
        self.jointIds = [0,0,0,0]
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUByte( mtvertexcodec.encodeU8( self.jointIds[0] ) )
        stream.writeUByte( mtvertexcodec.encodeU8( self.jointIds[1] ) )
        stream.writeUByte( mtvertexcodec.encodeU8( self.jointIds[2] ) )
        stream.writeUByte( mtvertexcodec.encodeU8( self.jointIds[3] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.texCoord[1] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.weights[1] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.weights[2] ) )
        
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
        self.tangent = NclVec3()
        self.jointIds = [0,0]
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.texCoord[1] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.jointIds[0] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.jointIds[1] ) )
        
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
        self.tangent = NclVec3()
        self.jointId = 0
        self.texCoord = NclVec2()
        
    def write( self, stream ):
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( mtvertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( mtvertexcodec.encodeU16( self.jointId ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( mtvertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.texCoord[0] ) )
        stream.writeUShort( mtvertexcodec.encodeF16( self.texCoord[1] ) )
        
class imTag:
    PATTERN = re.compile(r"""@(.+?)(?!=\()\((.+?(?!=\)))\)""")
    
    def iterTags( name ):
        for tag, value in re.findall(imTag.PATTERN, name):
            yield tag, value
        
class imModel:
    def __init__( self ):
        self.primitives = []
        self.joints = []
        self.materials = []
        
    def fromBinaryModel( self, mod ):
        pass
        
    def toBinaryModel( self, ref: rModelData = None ):
        mod = rModelData()
        
        if ref != None:
            mod.groups = ref.groups
            mod.primitiveJointLinks = ref.primitiveJointLinks
            mod.joints = ref.joints
            #mod.jointInvBindMtx = ref.jointInvBindMtx
            mod.jointLocalMtx = ref.jointLocalMtx
        
        for i in range(0, 256):
            mod.boneMap.append(-1)
            
        # create id -> index map
        for i, joint in enumerate( self.joints ):
            mod.boneMap[ joint.id ] = i
        
        # convert joints
        if ref == None:
            for i, joint in enumerate( self.joints ):     
                worldMtx = joint.worldMtx
                localMtx = worldMtx
                parentWorldMtx = nclCreateMat44()
                if joint.parentIndex != -1:
                    parentWorldMtx = self.joints[ joint.parentIndex ].worldMtx
                   # localMtx = worldMtx * nclInverse( parentWorldMtx )
                    localMtx = nclInverse( parentWorldMtx ) * worldMtx
                    
                modJoint = rModelJoint()
                modJoint.id = joint.id
                modJoint.parentIndex = joint.parentIndex
                modJoint.symmetryIndex = mod.boneMap[ joint.symmetryId ] # improper index causes animation glitches
                modJoint.field03 = joint.field03
                modJoint.field04 = joint.field04
                modJoint.offset = localMtx[3]
                modJoint.length = nclLength( modJoint.offset ) if not (modJoint.offset[0] == 0 and modJoint.offset[1] == 0 and modJoint.offset[2] == 0) else 0
                
                mod.joints.append( modJoint )
                mod.jointLocalMtx.append( nclCreateMat44( localMtx ) )
                # inverse bind matrix is calculated after processing vertices
            
        
        nextVertexOffset = 0
        nextTriangleIndex = 0
        vertices = []
        indices = []
        
        for meshIndex, mesh in enumerate( self.primitives ):
            # find material
            meshMatIndex = -1
            for matIndex, mat in enumerate( mod.materials ):
                if mat == mesh.matName:
                    meshMatIndex = matIndex
                    break
                
            if meshMatIndex == -1:
                # add material
                meshMatIndex = len( mod.materials )
                mod.materials.append( mesh.matName )
                
            # calculate statistics used for determining best vertex format
            maxUsedBoneCount = 0
            boneWeightTotals = dict()
            for w in mesh.weights:
                usedBoneCount = 0
                for j in range( 0, len( w.weights ) ):
                    weight = w.weights[ j ]
                    if weight > 0.001:
                        usedBoneCount += 1
                        
                        if not w.indices[j] in boneWeightTotals:
                            boneWeightTotals[ w.indices[j] ] = weight
                        else:
                            boneWeightTotals[ w.indices[j] ] += weight
                        
                maxUsedBoneCount = max( usedBoneCount, maxUsedBoneCount )
            
            # determine main joint index for primitive
            primJointIndex = 0
            # lastWeightTotal = 0
            # for key, value in boneWeightTotals.items():
            #     if value > lastWeightTotal:
            #         primJointIndex = key
                
            # determine vertex format   
            hasOcclusion = True
            hasTangent = True
            hasTexCoord = True 


            if maxUsedBoneCount > 4:
                # pick 4 most influential weights and remove the others
                for k, w in enumerate( mesh.weights ):
                    weightIndex = []
                    for k in range( 0, len(w.weights) ):
                        weightIndex.append((w.weights[k], w.indices[k]))
                    weightIndex = sorted(weightIndex, key=lambda x: x[0])

                    weightTotal = 0
                    w.weights = []
                    w.indices = []
                    for k in range( 0, len(weightIndex) ):
                        weight, index = weightIndex[k]
                        weightTotal += weight
                        w.weights.append( weight )
                        w.indices.append( index )

                    # average out the weights
                    weightRemainder = 1 - weightTotal
                    weightAvgStep = weightRemainder / len(w.weights)
                    for k in range( 0, len(w.weights) ):
                        w.weights[k] += weightAvgStep
                maxUsedBoneCount = 4
                
            if maxUsedBoneCount > 2 and maxUsedBoneCount <= 4:
                vertexShaderName = 'IASkinTB4wt'
                maxWeightCount = 4
                vertexStride = imVertexIASkinTB4wt.SIZE 
            elif maxUsedBoneCount == 2:
                vertexShaderName = 'IASkinTB2wt'
                maxWeightCount = 2
                vertexStride = imVertexIASkinTB2wt.SIZE
            elif maxUsedBoneCount == 1:
                vertexShaderName = 'IASkinTB1wt'
                maxWeightCount = 1
                vertexStride = imVertexIASkinTB1wt.SIZE
            else:
                # TODO fixme
                vertexShaderName = 'IASkinTB1wt'
                maxWeightCount = 0
                vertexStride = imVertexIASkinTB1wt.SIZE
            
            # convert vertices
            for i in range(0, len(mesh.positions)):
                t = mesh.tangents[i]
                
                if vertexShaderName == 'IASkinTB4wt':            
                    vtx = imVertexIASkinTB4wt()
                elif vertexShaderName == 'IASkinTB2wt':            
                    vtx = imVertexIASkinTB2wt()
                elif vertexShaderName == 'IASkinTB1wt':            
                    vtx = imVertexIASkinTB1wt()
                else:
                    raise NotImplementedError()
                
                vtx.position = mesh.positions[i]
                vtx.normal = mesh.normals[i]
                
                if hasOcclusion:    
                    vtx.occlusion = 1
                
                if hasTangent:
                    vtx.tangent = NclVec4( ( t[0], t[1], t[2], 1 ) )
                
                if hasTexCoord:    
                    vtx.texCoord = mesh.uvs[i]
                
                if maxWeightCount == 0:
                    # TODO fixme
                    jointIndex = 0
                    primJointIndex = jointIndex
                    vtx.jointId = jointIndex
                elif maxWeightCount == 1:
                    assert ( len(mesh.weights[ i ].indices) > 0 ), 'mesh {} has unrigged vertex at index {}'.format(mesh.name, i)
                    jointIndex = mesh.weights[ i ].indices[ 0 ]
                    primJointIndex = jointIndex
                    vtx.jointId = jointIndex
                else:            
                    lastJointId = 0
                    weightSum = 0
                    usedBoneCount = 0
                    for j in range( 0, maxWeightCount ):
                        if j >= len( mesh.weights[ i ].weights ):
                            vtx.jointIds[ j ] = lastJointId
                            vtx.weights[ j ] = 0
                            continue
                        
                        weight = mesh.weights[ i ].weights[ j ]
                        if weight < 0.001:
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

                    # adjust for floating point error
                    weightError = 1 - weightSum
                    weightErrorDelta = weightError / usedBoneCount
                    for j in range( usedBoneCount ):
                        vtx.weights[ j ] += weightErrorDelta
                
                vertices.append( vtx )
                
            # convert indices
            for i in range(0, len( mesh.indices ) ):
                indices.append( mesh.indices[ i ] )
                
            # create primitive
            primType = 0xFFFF
            lodIdx = 0xFF
            #flags = 33
            flags = 0x19
            if maxUsedBoneCount == 2:
                flags = 0x11
            elif maxUsedBoneCount == 1:
                flags = 0x09
            
            renderMode = 67
            primId = meshIndex
            
            # parse primitive name tags
            for tag, value in imTag.iterTags( mesh.name ):
                if tag == 'TYP':
                    primType = int(value)  
                elif tag == 'FLG':
                    values = value.split(',')
                    flags = int(values[0])
                elif tag == 'LOD':
                    lodIdx = int(value)
                elif tag == 'RM':
                    renderMode = int(value)
                elif tag == 'JNT':
                    primJointIndex = int(value)
                    pass
                elif tag == 'ID':
                    primId = int( value )
            
            prim = rModelPrimitive()
            prim.flags = primType # no obvious effect
            prim.vertexCount = len( mesh.positions )
            prim.indices.setGroupId( primJointIndex ) # used for single bind meshes like head, used for visibility
            prim.indices.setLodIndex( lodIdx )
            prim.indices.setMaterialIndex( meshMatIndex )
            prim.vertexFlags = flags
            prim.vertexStride = vertexStride
            prim.renderFlags = renderMode
            prim.vertexStartIndex = 0
            prim.vertexBufferOffset = nextVertexOffset
            prim.vertexShader = mtutil.getShaderObjectIdFromName( vertexShaderName )
            prim.indexBufferOffset = nextTriangleIndex
            prim.indexCount = len( mesh.indices )
            prim.indexStartIndex = 0
            prim.boneIdStart = 0
            prim.primitiveJointLinkCount = 0
            prim.id = primId
            prim.minVertexIndex = 0
            prim.maxVertexIndex = prim.minVertexIndex + prim.vertexCount
            prim.field2c = 0
            prim.primitiveJointLinkPtr = 0
            
            # if ref != None:
            #     for ogprim in ref.primitives:
            #         if ogprim.index == prim.index:
            #             prim.type = ogprim.type
            #             prim.indices.setGroupId( ogprim.indices.getGroupId() )
            #             prim.indices.setLodIndex( ogprim.indices.getLodIndex() )
            #             prim.flags = ogprim.flags
            #             prim.flags2 = ogprim.flags2
            #             prim.renderMode = ogprim.renderMode
            #             prim.primitiveJointLinkCount = ogprim.primitiveJointLinkCount
            #             break
    
            mod.primitives.append( prim )
            
            nextVertexOffset += prim.vertexCount * prim.vertexStride
            nextTriangleIndex += prim.indexCount 
        
        bounds = mtmodelutil.calcBounds( vertices )
        
        # calculate distance between 2 furthest points
        # will be used as the vertex scale
        vscale = -bounds.vminpoint + bounds.vmaxpoint
        vbias = bounds.vmin * -1
        
        print("vscale {}".format(vscale))
        print("vbias {}".format(vbias))
        
        # # set up model matrix
        # modelMtx = nclCreateMat44()
        # modelMtx[3] = NclVec4((vbias[0], vbias[1], vbias[2], 1))
        # modelMtx *= (1/vscale)
        
        # if len( mod.jointInvBindMtx ) == 0:
        #     # calculate joint inverse bind matrices
        #     for boneIndex, bone in enumerate( self.joints ):   
        #         # apply model matrix to world transform of each joint
        #         invBindMtx = nclInverse( bone.worldMtx * modelMtx )
        #         mod.jointInvBindMtx.append( nclCreateMat44( invBindMtx ) )
        
        # # normalize vertices
        # modelMtxNormal = nclTranspose( nclInverse( modelMtx ) )
        
        # for v in vertices:
        #     v.position = nclTransform( v.position, modelMtx )
            
        #     # slightly dim...?
        #     v.normal = nclNormalize( nclTransform( v.normal, modelMtxNormal  ) )
        
        #
        
        # set up model matrix
        modelMtx = nclCreateMat43()
        modelMtx[3] = vbias
        modelMtx *= (1/vscale)
        print(modelMtx)
        modelMtx = nclCreateMat44(modelMtx)
        print(modelMtx)
        
        if len( mod.jointInvBindMtx ) == 0:
            # calculate joint inverse bind matrices
            for i, joint in enumerate( self.joints ):   
                # apply model matrix to world transform of each joint
                invBindMtx = nclInverse( nclMultiply( joint.worldMtx, modelMtx ) )
                finalInvBindMtx = nclCreateMat44( invBindMtx )
                mod.jointInvBindMtx.append( finalInvBindMtx )
        
        # normalize vertices
        modelMtxNormal = nclTranspose( nclInverse( modelMtx ) )
        
        for v in vertices:
            v.position = nclTransform( v.position, modelMtx )

            # slightly dim...?
            v.normal = nclNormalize( nclTransform( v.normal, modelMtxNormal ) )
        
        # create buffers
        vertexBufferStream = NclBitStream()
        for v in vertices:
            v.write( vertexBufferStream )
        mod.vertexBuffer = vertexBufferStream.getBuffer()
            
        indexBufferStream = NclBitStream()
        for i in indices:
            indexBufferStream.writeShort( i )
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
        mod.header.center = bounds.center
        mod.header.radius = bounds.radius
        mod.header.min = nclCreateVec4( bounds.vmin )
        mod.header.max = nclCreateVec4( bounds.vmax )
        mod.header.field90 = 1000
        mod.header.field94 = 3000
        mod.header.field98 = 1
        mod.header.field9c = 0
        mod.header.primitiveJointLinkCount = len( mod.primitiveJointLinks )
        return mod
        
    def saveBinaryStream( self, stream ):
        mod = self.toBinaryModel()
        mod.write( stream )