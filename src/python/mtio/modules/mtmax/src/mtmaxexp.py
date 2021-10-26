import os
import sys
from typing import List, Tuple

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

class MtModelExporter(object):
    def __init__( self ):
        self.model = None
        self.maxNodeToJointMap = None
        self.jointToMaxNodeMap = None
        self.jointIdxByName = None
        self.ref = None
        
    def _convertMaxPoint3ToNclVec3( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], v[1], v[2]))

    def _convertMaxPoint3ToNclVec3UV( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], -v[1], v[2]))
        
    def _convertMaxPoint3ToNclVec4( self, v: rt.Point3, w ) -> NclVec3:
        return NclVec4((v[0], v[1], v[2], w))
    
    def _convertMaxMatrix3ToNclMat43( self, v: rt.Matrix3 ) -> NclMat43:
        return nclCreateMat43((self._convertMaxPoint3ToNclVec3(v[0]), 
                               self._convertMaxPoint3ToNclVec3(v[1]), 
                               self._convertMaxPoint3ToNclVec3(v[2]), 
                               self._convertMaxPoint3ToNclVec3(v[3])))
        
    def _convertMaxMatrix3ToNclMat44( self, v: rt.Matrix3 ) -> nclCreateMat44:
        return nclCreateMat44((self._convertMaxPoint3ToNclVec4(v[0], 0), 
                               self._convertMaxPoint3ToNclVec4(v[1], 0), 
                               self._convertMaxPoint3ToNclVec4(v[2], 0), 
                               self._convertMaxPoint3ToNclVec4(v[3], 1)))
        
    def _getJointIdFromNode( self, node ):
        joint = self.metadata.getJointByName( node.name )
        if joint != None:
            # get id from metadata
            return joint.id
        else:
            if node.name.startswith('bone_') and node.name.contains('_sym_'):
                # old format
                splitName = node.name.split('_')
                return int(splitName[1])
            else:
                raise Exception(f"Unable to determine joint id for node: {node}")
        
    def _getJointSymmetryIdFromNode( self, node ):
        joint = self.metadata.getJointByName( node.name )
        if joint != None:
            # get symmetry id from metadata
            if joint.symmetry != None:
                return joint.symmetry.id
            else:
                return 255
        else:
            if node.name.startswith('bone_') and node.name.contains('_sym_'):
                # old format
                splitName = node.name.split('_')
                return int(splitName[3])
            else:
                raise Exception(f"Unable to determine joint symmetry id for node: {node}")

    def _getRefJoint( self, node ):
        joint = self.metadata.getJointByName( node.name )
        if joint != None and self.ref != None:
            return self.ref.joints[self.ref.boneMap[joint.id]]
        else:
            return None
        
    # '''
    # void CalculateTangentsBitangents(
    # Point3 pos[3], Point3 norm[3], Point3 uv[3],
    # Point3 tangent[3], Point3 bitangent[3])
    # {
    #     float uv1x = uv[1].x - uv[0].x;
    #     float uv2x = uv[2].x - uv[0].x;
    #     float uv1y = uv[1].y - uv[0].y;
    #     float uv2y = uv[2].y - uv[0].y;
    #     float uvk = uv2x * uv1y - uv1x * uv2y;

    #     Point3 v1 = pos[1] - pos[0];
    #     Point3 v2 = pos[2] - pos[0];

    #     Point3 faceTangent;
    #     if (uvk != 0) {
    #     faceTangent = (uv1y * v2 - uv2y * v1) / uvk;
    #     } else {
    #     if (uv1x != 0) faceTangent = v1 / uv1x;
    #     else if (uv2x != 0) faceTangent = v2 / uv2x;
    #     else faceTangent = Point3(0.0f, 0.0f, 0.0f);
    #     }
    #     Normalize(faceTangent);

    #     Point3 mapNormal = CrossProduct(uv[1] - uv[0], uv[2] - uv[1]);
    #     bool flip = mapNormal.z < 0;

    #     for (int i = 0; i < 3; ++i)
    #     {
    #     // Make tangent perpendicular to normal
    #     tangent[i] = faceTangent - DotProduct(norm[i], faceTangent) * norm[i];
    #     Normalize(tangent[i]);

    #     bitangent[i] = CrossProduct(norm[i], tangent[i]);
    #     if (flip) bitangent[i] = -bitangent[i];
    #     }
    # }
    # '''
    # def _calcTangentBasis( self, pos: List[NclVec3], norm: List[NclVec3], uv: List[NclVec3] ) -> Tuple[List[NclVec3], List[NclVec3]]:
    #     '''Based off CalculateTangentsBitangents from 3ds Max SDK sample code'''
    #     uv1x = uv[1].x - uv[0].x
    #     uv2x = uv[2].x - uv[0].x
    #     uv1y = uv[1].y - uv[0].y
    #     uv2y = uv[2].y - uv[0].y
    #     uvk = uv2x * uv1y - uv1x * uv2y

    #     v1 = pos[1] - pos[0]
    #     v2 = pos[2] - pos[0]

    #     faceTangent = None
    #     if uvk != 0:
    #         faceTangent = (uv1y * v2 - uv2y * v1) / uvk
    #     else:
    #         if (uv1x != 0):   faceTangent = v1 / uv1x
    #         elif (uv2x != 0): faceTangent = v2 / uv2x
    #         else:             faceTangent = NclVec3((0, 0, 0))
    #     nclNormalize( faceTangent )

    #     mapNormal = nclCross( uv[1] - uv[0], uv[2] - uv[1] )
    #     flip = mapNormal.z < 0

    #     tangent = [NclVec3(), NclVec3(), NclVec3()]
    #     bitangent = [NclVec3(), NclVec3(), NclVec3()]
    #     for i in range( 0, 3 ):
    #         # Make tangent perpendicular to normal
    #         tangent[i] = faceTangent - nclDot(norm[i], faceTangent) * norm[i]
    #         nclNormalize( tangent[i] )
            
    #         bitangent[i] = nclCross(norm[i], tangent[i])
    #         if flip: bitangent[i] = -bitangent[i]
    #     return tangent, bitangent

    def _computeTangentBasis( self, indices: List[int], vertex: List[NclVec3], texcoord: List[NclVec3], normal: List[NclVec3] ) -> List[NclVec3]:
        tan1 = []
        tan2 = []
        for i in range(len(vertex)):
            tan1.append(glm.vec3())
            tan2.append(glm.vec3())

        
        for i in range(0, len(indices), 3):
            i1 = indices[i+0]
            i2 = indices[i+1]
            i3 = indices[i+2]

            v1 = vertex[i1];
            v2 = vertex[i2];
            v3 = vertex[i3];
        
            w1 = texcoord[i1];
            w2 = texcoord[i2];
            w3 = texcoord[i3];
            
            x1 = v2[0] - v1[0];
            x2 = v3[0] - v1[0];
            y1 = v2[1] - v1[1];
            y2 = v3[1] - v1[1];
            z1 = v2[2] - v1[2];
            z2 = v3[2] - v1[2];
        
            s1 = w2[0] - w1[0];
            s2 = w3[0] - w1[0];
            t1 = w2[1] - w1[1];
            t2 = w3[1] - w1[1];
        
            temp = (s1 * t2 - s2 * t1)
            if temp == 0:
                r = 0
            else:
                r = 1.0 / (s1 * t2 - s2 * t1);
            sdir = glm.vec3((t2 * x1 - t1 * x2) * r, (t2 * y1 - t1 * y2) * r,
                    (t2 * z1 - t1 * z2) * r);
            tdir = glm.vec3((s1 * x2 - s2 * x1) * r, (s1 * y2 - s2 * y1) * r,
                    (s1 * z2 - s2 * z1) * r);
            
            tan1[i1] += sdir;
            tan1[i2] += sdir;
            tan1[i3] += sdir;
            
            tan2[i1] += tdir;
            tan2[i2] += tdir;
            tan2[i3] += tdir;

        tangents = []
        for a in range(len(vertex)):
            n = normal[a];
            t = tan1[a];
            
            # Gram-Schmidt orthogonalize
            tangent = glm.normalize(t - n * glm.dot(n, t))
            
            # Calculate handedness
            tangent = glm.vec4(tangent[0], tangent[1], tangent[2], -1.0 if (glm.dot(glm.cross(n, t), tan2[a]) < 0.0) else 1.0)
            tangents.append(tangent)

        return tangents
        
    def _shouldExportNode( self, node ):
        return not node.isHidden

    def _isMeshNode( self, node ):
        # node is considered a mesh of it is an editable mesh or editable poly
        return rt.classOf( node ) in [rt.Editable_mesh, rt.Editable_poly]

    def _isGroupNode( self, node ):
        # group node only contains meshes
        for child in node.children:
            if not self._isMeshNode( child ):
                return False
        return True

    def _isBoneNode( self, node ):
        # node is considered a bone node of it's bone geometry (helper)
        return rt.classOf( node ) == rt.BoneGeometry 
    
    def processBones( self ):
        # convert all joints first
        # so we can reference them when building the primitives
        self.maxNodeToJointMap = dict()
        self.jointToMaxNodeMap = dict()
        self.jointIdxByName = dict()
        for maxNode in rt.objects:
            if not self._shouldExportNode( maxNode ) or not self._isBoneNode( maxNode ):
                continue
        
            print(f'processing bone: {maxNode.name}')
            joint = imJoint()
            joint.name = maxNode.name
            joint.id = self._getJointIdFromNode( maxNode )
            joint.symmetryId = self._getJointSymmetryIdFromNode( maxNode )
            joint.worldMtx = self._convertMaxMatrix3ToNclMat44( maxNode.transform )
            joint.parentIndex = -1 # fix up later

            self.maxNodeToJointMap[maxNode] = joint
            self.jointToMaxNodeMap[joint] = maxNode
            self.model.joints.append( joint )
            self.jointIdxByName[ joint.name ] = len( self.model.joints ) - 1
            
        # fix up indices
        for joint in self.model.joints:
            maxNode = self.jointToMaxNodeMap[joint]
            if maxNode.parent != None:
                parentJoint = self.maxNodeToJointMap[maxNode.parent]
                joint.parentIndex = self.model.joints.index( parentJoint )
        
    def processMeshes( self ):
        # convert meshes
        for maxNode in rt.objects:
            if not self._shouldExportNode( maxNode ) or not self._isMeshNode( maxNode ):
                continue
            
            print(f'processing mesh: {maxNode.name}')
            prim = imPrimitive()
            prim.name = maxNode.name
            prim.matName = 'defaultMaterial'
            if maxNode.material != None:
                prim.matName = maxNode.material.name
                
            # get skin modifier
            rt.execute('max modify mode')
            rt.select( maxNode )
            maxSkin = rt.modPanel.getCurrentObject()
            hasSkin = rt.isKindOf( maxSkin, rt.Skin )
            print( maxSkin, hasSkin )
            
            # get vertex data
            maxMesh = rt.snapshotAsMesh( maxNode )
            faceCount = rt.getNumFaces( maxMesh )
            vertexIdxLookup = dict()
            nextVertexIdx = 0

            for i in range( 0, faceCount ):
                face = rt.getFace( maxMesh, i + 1 )
                tvFace = rt.getTVFace( maxMesh, i + 1 )
                
                # collect all position, normal, and uv data for the face to generate tangents
                for j in range( 0, 3 ):
                    vertIdx = face[j]
                    tvertIdx = tvFace[j]

                    cv = CacheVertex()
                    cv.position = self._convertMaxPoint3ToNclVec3( rt.getVert( maxMesh, vertIdx ) )
                    cv.normal = self._convertMaxPoint3ToNclVec3( rt.getNormal( maxMesh, vertIdx ) )
                    cv.uv = self._convertMaxPoint3ToNclVec3UV( rt.getTVert( maxMesh, tvertIdx ) )

                    if hasSkin:
                        weights = []
                        indices = []
                        weightCount = rt.skinOps.getVertexWeightCount( maxSkin, vertIdx )
                        for k in range( 0, weightCount ):
                            boneId = rt.skinops.getVertexWeightBoneId( maxSkin, vertIdx, k + 1 )
                            boneWeight = rt.skinOps.getVertexWeight( maxSkin, vertIdx, k + 1 )
                            boneName = rt.skinOps.getBoneName( maxSkin, boneId, 0 )
                            jointIdx = self.jointIdxByName[ boneName ]
                            weights.append( boneWeight )
                            indices.append( jointIdx )

                        cv.weights = tuple( weights )
                        cv.indices = tuple( indices )
                    else:
                        cv.weights = (1, 0, 0, 0)
                        cv.indices = (2, 0, 0, 0)

                    if True or cv not in vertexIdxLookup:
                        idx = nextVertexIdx
                        nextVertexIdx += 1
                        vertexIdxLookup[cv] = idx

                        prim.positions.append( cv.position )
                        prim.normals.append( cv.normal )
                        prim.uvs.append( cv.uv ) 
                        prim.tangents.append( NclVec3(1,1,1))
                        
                        vtxWeight = imVertexWeight()
                        vtxWeight.indices = cv.indices
                        vtxWeight.weights = cv.weights
                        prim.weights.append( vtxWeight )
                    else:
                        idx = vertexIdxLookup.get(cv)
                        
                    prim.indices.append( idx )

            #prim.tangents = self._computeTangentBasis( prim.indices, prim.positions, prim.uvs, prim.normals ) 
            self.model.primitives.append( prim )
    
    def writeBinaries( self ):
        binMod = self.model.toBinaryModel( self.ref )
        stream = NclBitStream()
        binMod.write( stream )
        mtutil.saveByteArrayToFile( self.outPath, stream.getBuffer() )
    
    def exportModel( self, path ):
        print(f'exporting to {path}')
        
        # start building intermediate model data for conversion
        self.model = imModel()
        self.outPath = path
        self.metadata = ModelMetadata()

        if os.path.exists( mtmaxconfig.exportMetadataPath ):
            self.metadata.loadFile( mtmaxconfig.exportMetadataPath )

        if os.path.exists( mtmaxconfig.exportRefPath ):
            self.ref = rModelData()
            self.ref.read( NclBitStream( mtutil.loadIntoByteArray( mtmaxconfig.exportRefPath ) ) )
        
        print('processing scene')
        self.processBones()
        self.processMeshes()
        
        print('writing files')
        self.writeBinaries()
        
        print('export completed successfully')
        
            
def _test():
    rt.clearListener()
    
    exp = MtModelExporter()
    exp.exportModel( 'X:/work/umvc3_model/test.mod' )
            
if __name__ == '__main__':
    _test()