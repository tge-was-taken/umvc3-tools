__package__ = 'modules.mtmax.src'

import copy
from pymxs import runtime as rt
from ...mtlib import *
from ...mtlib.base_importer import *
import max_plugin
from max_plugin import *

class MaxModelImporter(ModelImporterBase):
    def __init__(self):
        super().__init__(max_plugin.plugin)

    def setUserProp(self, obj: EditorNodeProxy, key, value):
        rt.setUserProp( obj.unwrap(), key, value )

    def setInheritanceFlags( self, bone: EditorNodeProxy, flags ):
        rt.setInheritanceFlags( bone.unwrap(), rt.BitArray(*flags) )

    def normalize( self, value ):
        return rt.normalize( value )

    def transformPoint( self, point, matrix ):
        return matrix * point

    # Progress functions
    def updateProgress( self, what, value, count = 0 ):
        from mtmax.src import MtMaxModelImportRollout
        rollout = MtMaxModelImportRollout.getMxsVar()
        rollout.pbImport.value = value if count == 0 else (value/count) * 100
        rollout.lblImportProgressCategory.text = what 
        
    def updateSubProgress( self, what, value, count = 0 ):
        from mtmax.src import MtMaxModelImportRollout
        rollout = MtMaxModelImportRollout.getMxsVar()
        rollout.pbImportSub.value = value if count == 0 else (value/count) * 100
        rollout.lblImportProgressSubCategory.text = what

    # Layer functions
    def newLayerFromName( self, name ):
        return rt.LayerManager.newLayerFromName( name )
        
    def getLayerFromName( self, name ):
        return rt.LayerManager.getLayerFromName( name)

    # Convert functions
    def convertNclVec3ToPoint3( self, nclVec3 ):
        return rt.Point3( rt.Float( nclVec3[0] ), rt.Float( nclVec3[1] ), rt.Float( nclVec3[2] ) )
        
    def convertNclMat44ToMatrix( self, nclMtx ):
        return rt.Matrix3( self.convertNclVec3ToPoint3( nclMtx[0] ), 
                           self.convertNclVec3ToPoint3( nclMtx[1] ), 
                           self.convertNclVec3ToPoint3( nclMtx[2] ), 
                           self.convertNclVec3ToPoint3( nclMtx[3] ) )
        
    def convertNclMat43ToMatrix( self, nclMtx ):
        return rt.Matrix3( self.convertNclVec3ToPoint3( nclMtx[0] ), 
                           self.convertNclVec3ToPoint3( nclMtx[1] ), 
                           self.convertNclVec3ToPoint3( nclMtx[2] ), 
                           self.convertNclVec3ToPoint3( nclMtx[3] ) )

    # Import functions
    def importPrimitive( self, primitive, envelopeIndex, indexStream, vertexStream ):
        shaderInfo: ShaderObjectInfo = mvc3shaderdb.shaderObjectsByHash[ primitive.vertexShader.getHash() ]
        self.logger.debug( f'shader {shaderInfo.name} ({hex(shaderInfo.hash)})')

        # read vertices
        vertexData = self.decodeVertices( primitive, shaderInfo, 
            vertexStream )

        # read faces
        maxFaceArray = self.decodeFaces( primitive, indexStream )
           
        # build mesh object
        self.logger.debug( 'creating mesh' )
        hasUvs = len( vertexData.uvPrimaryArray ) > 0
        meshName = self.metadata.getPrimitiveName( primitive.id )
        maxMesh = rt.Mesh(vertices=vertexData.vertexArray.unwrap(), faces=maxFaceArray.unwrap())
        maxMesh.backfacecull = True
        maxMesh.name = meshName
        
        if hasUvs:
            # TODO other uv maps
            maxMesh.numTVerts = len( vertexData.vertexArray )
            rt.buildTVFaces( maxMesh )
            
            for j in range( 0, len( maxFaceArray ) ):
                rt.setTVFace( maxMesh, j + 1, maxFaceArray[j] )
                
            for j in range( 0, len( vertexData.uvPrimaryArray ) ):
                rt.setTVert( maxMesh, j + 1, vertexData.uvPrimaryArray[j] )
        
        if self.config.importNormals:
            for j in range( 0, len( vertexData.normalArray ) ):
                rt.setNormal( maxMesh, j + 1, vertexData.normalArray[j] )
            
        maxMesh.material = self.editorMaterialArray[ primitive.indices.getMaterialIndex() ].unwrap()
        self.setPrimitiveCustomAttributes( primitive, shaderInfo, MaxMeshProxy( maxMesh ), envelopeIndex )

        # parent to group
        if primitive.indices.getGroupId() in self.editorGroupLookup:
            maxMesh.parent = self.editorGroupLookup[ primitive.indices.getGroupId() ]

        # parent envelope to mesh
        # TODO envelope
        #for j in range( 0, primitive.envelopeCount ):
        #    self.editorEnvelopes[ envelopeIndex + j ].parent = maxMesh

        # apply weights
        if len( vertexData.jointArray ) > 0 and self.config.importWeights:
            self.importWeights( maxMesh, primitive, vertexData )
        elif len( vertexData.jointArray ) == 0:
            self.logger.debug( f'primitive {maxMesh.name} has no vertex weights' )
            
        if self.layer != None:
            # add to layer
            self.layer.addNode( maxMesh )

    def importWeights( self, maxMesh, primitive, vertexData: DecodedVertexData ):
        self.logger.info( 'importing mesh weights' )
        
        maxSkin = rt.skin()
        rt.addModifier( maxMesh, maxSkin )

        weightData = self.preprocessWeights( primitive, vertexData )
        
        # add used bones to skin modifier
        for i, maxBone in enumerate( weightData.usedBones ):
            update = i == len( weightData.usedBones ) - 1
            rt.skinOps.addBone( maxSkin, maxBone.unwrap(), update, node=maxMesh )
            
        # create mapping for our joint indices to skin modifier bone indices
        maxBoneIndexRemap = dict()
        maxSkinBoneNodes = rt.skinOps.getBoneNodes( maxSkin )
        for i, maxBone in enumerate( weightData.usedBones ):
            for j, maxSkinBoneNode in enumerate( maxSkinBoneNodes ):
                if maxSkinBoneNode == maxBone.unwrap():
                    maxBoneIndexRemap[i] = j
                    break

        # set vertex weights
        for j in range( 0, primitive.vertexCount ):
            newMaxVtxJointArray = weightData.jointArray[j]
            newMaxVtxWeightArray = weightData.weightArray[j]
            for k, joint in enumerate( newMaxVtxJointArray ):
                # remap the joint indices to the skin modifier bone indices
                newMaxVtxJointArray[k] = maxBoneIndexRemap[joint] + 1  

            assert len( newMaxVtxJointArray ) > 0 
            assert len( newMaxVtxWeightArray ) > 0
            rt.skinOps.replaceVertexWeights( maxSkin, j + 1, newMaxVtxJointArray.unwrap(), newMaxVtxWeightArray.unwrap(), node=maxMesh )

    # Create functions

    def createArray( self ):
        return MaxArrayProxy()
          
    def createPoint3( self, x, y, z ):
        return rt.Point3( rt.Float( float( x ) ), rt.Float( float( y ) ), rt.Float( float( z ) ) )
    
    def createPoint2( self, x, y ):
        return rt.Point2( rt.Float( x ), rt.Float( y ) )
        
    def createTexture( self, filename ):
        return rt.BitmapTexture( filename=filename )

    def createDummy( self, name, pos ):
        maxGroup = rt.dummy()
        #maxGroup.pos = rt.Point3( pos[0], pos[1], pos[2] )
        maxGroup.name = name
        return maxGroup

    def createBone( self, joint, name, tfm, parentBone ):
        tfm = self.convertNclMat44ToMatrix( tfm )
        bone = rt.boneSys.createBone( tfm.row4, ( tfm.row4 + 0.01 * rt.normalize( tfm.row1 ) ), rt.normalize( tfm.row3 ) )
        bone.name = name
        bone.width = 0.001
        bone.height = 0.001
        bone.transform = tfm
        bone.setBoneEnable( False, 0 )
        bone.wireColor = rt.yellow
        bone.showLinks = True
        bone.position.controller = rt.TCB_position()
        bone.rotation.controller = rt.TCB_rotation()
        bone.parent = parentBone.unwrap() if parentBone is not None else None
        
        if self.layer != None:
            self.layer.addNode( bone )
        
        return MaxNodeProxy(bone)
    
    # Material functions
    def convertMaterial( self, material: imMaterialInfo, materialName: str ):
        if self.supportsPhysicalMaterial() and not self.config.debugForcePhysicalMaterial:
            # sometimes not available? reported to be missing on 2022 24.0.0.923
            editorMaterial = self.convertMaterial_PBRSpecGloss( material, materialName )
        else:
            editorMaterial = self.convertMaterial_PhysicalMaterial( material, materialName )
        return MaxMaterialProxy(editorMaterial)

    # Attribute functions
    def createGroupCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        rt.custAttributes.add( obj, rt.MtMaxGroupAttributesInstance )
        attribs = obj.MtMaxGroupAttributes
        return MaxCustomAttributeSetProxy(attribs)

    def createMaterialCustomAttribute( self, obj: EditorMaterialProxy )-> EditorCustomAttributeSetProxy:
        rt.custAttributes.add( obj.unwrap(), rt.MtMaxMaterialAttributesInstance )
        attribs = obj.unwrap().MtMaxMaterialAttributes
        return MaxCustomAttributeSetProxy(attribs)

    def createPrimitiveCustomAttribute( self, obj: EditorMeshProxy ) -> EditorCustomAttributeSetProxy:
        rt.custAttributes.add( obj.unwrap().baseObject, rt.MtMaxPrimitiveAttributesInstance )
        attribs = obj.unwrap().MtPrimitiveAttributes
        return MaxCustomAttributeSetProxy(attribs)

    def createJointCustomAttribute( self, obj: EditorNodeProxy ) -> EditorCustomAttributeSetProxy:
        rt.custAttributes.add( obj.unwrap().baseObject, rt.MtMaxJointAttributesInstance )
        attribs = obj.unwrap().MtMaxJointAttributes
        return MaxCustomAttributeSetProxy(attribs)

    # Max specific functions

    def convertMaterial_PhysicalMaterial( self, material: imMaterialInfo, materialName: str ):
        editorMaterial =  rt.PhysicalMaterial()
        editorMaterial.name = materialName
        editorMaterial.showInViewport = True
        editorMaterial.backfaceCull = True
    
        if material != None:
            editorMaterial.base_color_map = self.loadTextureSlot( material, 'tAlbedoMap' )
            editorMaterial.metalness_map = self.loadTextureSlot( material, 'tSpecularMap' )
            editorMaterial.bump_map = rt.Normal_Bump()
            editorMaterial.bump_map.normal = self.loadTextureSlot( material, 'tNormalMap' )
            editorMaterial.bump_map.mult_spin = 0 # don't display because it won't look right due to swapped channels
        return editorMaterial

    def convertMaterial_PBRSpecGloss( self, material: imMaterialInfo, materialName: str ): 
        editorMaterial =  rt.PBRSpecGloss()
        editorMaterial.name = materialName
        editorMaterial.showInViewport = True
        editorMaterial.backfaceCull = True
    
        if material != None:
            editorMaterial.base_color_map = self.loadTextureSlot( material, 'tAlbedoMap' )
            editorMaterial.specular_map = self.loadTextureSlot( material, 'tSpecularMap' )
            editorMaterial.norm_map = self.loadTextureSlot( material, 'tNormalMap' )
            editorMaterial.bump_map_amt = 0 # don't display because it won't look right due to swapped channels
        return editorMaterial

    def supportsPhysicalMaterial( self ):
        return hasattr(rt, 'PBRSpecGloss')
