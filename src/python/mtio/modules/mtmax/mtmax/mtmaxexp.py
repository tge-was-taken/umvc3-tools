import os
import sys
from typing import List, Tuple

def _fixImports():
    curDir = os.path.dirname( __file__ ) 
    if not curDir in sys.path: sys.path.append( curDir )
    packageDir = os.path.realpath( curDir + '/../../' )
    if not packageDir in sys.path: sys.path.append( packageDir )
    
def _attachDebugger():
    import ptvsd
    ptvsd.enable_attach()
        
_fixImports()
#_attachDebugger()

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
import mtmaxutil

class CacheVertex:
    def __init__( self ):
        self.position = NclVec3()
        self.normal = NclVec3()
        self.tangent = NclVec3()
        self.uv = NclVec3()
        self.weights = ()
        self.indices = ()
        
    def __eq__(self, o: object) -> bool:
        if isinstance( o, CacheVertex ):
            return self.position == o.position and \
                   self.normal == o.normal and \
                   self.tangent == o.tangent and \
                   self.uv == o.uv and \
                   self.weights == o.weights and \
                   self.indices == o.indices
                   
    def __hash__( self ):
        return hash((self.position, self.normal, self.tangent, self.uv, self.weights, self.indices))

class MtModelExporter:
    def __init__( self ):
        pass
    
    def convertMaxPoint3ToNclVec3( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], v[1], v[2]))
    
    def convertMaxMatrix3ToNclMat43( self, v: rt.Matrix3 ) -> NclMat43:
        return NclMat43((self.convertMaxPoint3ToNclVec3(v[0]), 
                         self.convertMaxPoint3ToNclVec3(v[1]), 
                         self.convertMaxPoint3ToNclVec3(v[2]), 
                         self.convertMaxPoint3ToNclVec3(v[3])))
        
    def getJointIdFromNode( self, node ):
        if node.name.startswith('bone_') and node.name.contains('_sym_'):
            # old format
            splitName = node.name.split('_')
            return int(splitName[1])
        else:
            raise NotImplementedError
        
    def getJointSymmetryIdFromNode( self, node ):
        if node.name.startswith('bone_') and node.name.contains('_sym_'):
            # old format
            splitName = node.name.split('_')
            return int(splitName[3])
        else:
            raise NotImplementedError
        
    '''
    void CalculateTangentsBitangents(
    Point3 pos[3], Point3 norm[3], Point3 uv[3],
    Point3 tangent[3], Point3 bitangent[3])
    {
        float uv1x = uv[1].x - uv[0].x;
        float uv2x = uv[2].x - uv[0].x;
        float uv1y = uv[1].y - uv[0].y;
        float uv2y = uv[2].y - uv[0].y;
        float uvk = uv2x * uv1y - uv1x * uv2y;

        Point3 v1 = pos[1] - pos[0];
        Point3 v2 = pos[2] - pos[0];

        Point3 faceTangent;
        if (uvk != 0) {
        faceTangent = (uv1y * v2 - uv2y * v1) / uvk;
        } else {
        if (uv1x != 0) faceTangent = v1 / uv1x;
        else if (uv2x != 0) faceTangent = v2 / uv2x;
        else faceTangent = Point3(0.0f, 0.0f, 0.0f);
        }
        Normalize(faceTangent);

        Point3 mapNormal = CrossProduct(uv[1] - uv[0], uv[2] - uv[1]);
        bool flip = mapNormal.z < 0;

        for (int i = 0; i < 3; ++i)
        {
        // Make tangent perpendicular to normal
        tangent[i] = faceTangent - DotProduct(norm[i], faceTangent) * norm[i];
        Normalize(tangent[i]);

        bitangent[i] = CrossProduct(norm[i], tangent[i]);
        if (flip) bitangent[i] = -bitangent[i];
        }
    }
    '''
    def calcTangentBasis( self, pos: List[NclVec3], norm: List[NclVec3], uv: List[NclVec3] ) -> Tuple[List[NclVec3], List[NclVec3]]:
        '''Based off CalculateTangentsBitangents from 3ds Max SDK sample code'''
        uv1x = uv[1].x - uv[0].x
        uv2x = uv[2].x - uv[0].x
        uv1y = uv[1].y - uv[0].y
        uv2y = uv[2].y - uv[0].y
        uvk = uv2x * uv1y - uv1x * uv2y

        v1 = pos[1] - pos[0]
        v2 = pos[2] - pos[0]

        faceTangent = None
        if uvk != 0:
            faceTangent = (uv1y * v2 - uv2y * v1) / uvk
        else:
            if (uv1x != 0):   faceTangent = v1 / uv1x
            elif (uv2x != 0): faceTangent = v2 / uv2x
            else:             faceTangent = NclVec3((0, 0, 0))
        faceTangent.normalize()

        mapNormal = NclVec3.cross(uv[1] - uv[0], uv[2] - uv[1])
        flip = mapNormal.z < 0

        tangent = [NclVec3(), NclVec3(), NclVec3()]
        bitangent = [NclVec3(), NclVec3(), NclVec3()]
        for i in range( 0, 3 ):
            # Make tangent perpendicular to normal
            tangent[i] = faceTangent - NclVec3.dot(norm[i], faceTangent) * norm[i]
            tangent[i].normalize()

            bitangent[i] = NclVec3.cross(norm[i], tangent[i])
            if flip: bitangent[i] = -bitangent[i]
        return tangent, bitangent
    
    def exportModel( self, path ):
        print(f'exporting to {path}')
        
        # start building intermediate model data for conversion
        model = imModel()
        
        # convert all joints first
        # so we can reference them when building the primitives
        maxNodeToJointMap = dict()
        jointToMaxNodeMap = dict()
        for maxNode in rt.objects:
            maxNodeSuperClass = rt.superClassOf( maxNode )
            if maxNodeSuperClass != rt.Helper:
                continue
            
            print(f'processing bone: {maxNode.name}')
            joint = imJoint()
            joint.name = maxNode.name
            joint.worldMtx = self.convertMaxMatrix3ToNclMat43( maxNode.transform )
            joint.parentIndex = -1 # fix up later
            #joint.id = self.getJointIdFromNode( maxNode )
            #joint.symmetryId = self.getJointSymmetryIdFromNode( maxNode )
            # TODO field03, field04, length from metadata or custom attributes
            
            maxNodeToJointMap[maxNode] = joint
            jointToMaxNodeMap[joint] = maxNode
            model.joints.append( joint )
            
        # fix up indices
        for joint in model.joints:
            maxNode = jointToMaxNodeMap[joint]
            if maxNode.parent != None:
                parentJoint = maxNodeToJointMap[maxNode.parent]
                joint.parentIndex = model.joints.index( parentJoint )
                
        # convert meshes
        for maxNode in rt.objects:
            maxNodeSuperClass = rt.superClassOf( maxNode )
            if maxNodeSuperClass != rt.GeometryClass:
                continue
            
            print(f'processing mesh: {maxNode.name}')
            prim = imPrimitive()
            prim.name = maxNode.name
            prim.matName = 'defaultMaterial'
            if maxNode.material != None:
                prim.matName = maxNode.material.name
            
            # get vertex data
            maxMesh = rt.snapshotAsMesh( maxNode )
            faceCount = rt.getNumFaces( maxMesh )
            #vertexCache: List[CacheVertex] = []
            vertexIdxLookup = dict()
            nextVertexIdx = 0
            for i in range( 0, faceCount ):
                face = rt.getFace( maxMesh, i + 1 )
                tvFace = rt.getTVFace( maxMesh, i + 1 )
                
                # collect all position, normal, and uv data for the face to generate tangents 
                facePos = []
                faceNorm = []
                faceUv = []
                
                for j in range( 0, 3 ):
                    vertIdx = face[j]
                    tvertIdx = tvFace[j]
                    facePos.append( self.convertMaxPoint3ToNclVec3( rt.getVert( maxMesh, vertIdx ) ) )
                    faceNorm.append( self.convertMaxPoint3ToNclVec3( rt.getNormal( maxMesh, vertIdx ) ) )
                    faceUv.append( self.convertMaxPoint3ToNclVec3( rt.getTVert( maxMesh, tvertIdx ) ) )
                    
                faceTangent, faceBitangent = self.calcTangentBasis( facePos, faceNorm, faceUv )
                
                # build cache vertex
                for j in range( 0, 3 ):
                    cv = CacheVertex()
                    cv.position = facePos[j]
                    cv.normal = faceNorm[j]
                    cv.uv = faceUv[j]
                    cv.tangent = faceTangent[j]
                    
                    # find existing vertex in cache
                    # idx = None
                    # try:
                    #     idx = vertexCache.index( cv )
                    # except ValueError:
                    #     idx = len( vertexCache )
                    #     vertexCache.append( cv )
                    if cv not in vertexIdxLookup:
                        idx = nextVertexIdx
                        nextVertexIdx += 1
                        vertexIdxLookup[cv] = idx
                    else:
                        idx = vertexIdxLookup.get(cv)
                    
                    prim.positions.append( cv.position )
                    prim.tangents.append( cv.tangent )
                    prim.normals.append( cv.normal )
                    prim.uvs.append( cv.uv )     
                    prim.indices.append( idx )
                    # TODO weights
                    
            model.primitives.append( prim )
        
        binMod = model.toBinaryModel()
        stream = NclBitStream()
        binMod.write( stream )
        mtutil.saveByteArrayToFile( path, stream.getBuffer() )

        print('writing file')
        print('done')
        
            
def _test():
    rt.clearListener()
    
    exp = MtModelExporter()
    exp.exportModel( 'X:/work/umvc3_model/test.mod' )
            
if __name__ == '__main__':
    _test()