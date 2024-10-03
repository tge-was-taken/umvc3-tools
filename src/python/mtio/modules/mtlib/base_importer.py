from abc import ABC, abstractmethod
import os
from dataclasses import dataclass
import copy
import yaml

import vertexcodec
from rmodel import *
from base_editor import *
from base_editor import EditorPluginBase
from shaderinfo import *
from rtexture import *
from metadata import *
import mvc3materialnamedb
from immaterial import *

@dataclass
class DecodedVertexData:
    vertexArray: EditorArrayProxy
    normalArray: EditorArrayProxy
    uvPrimaryArray: EditorArrayProxy
    uvSecondaryArray: EditorArrayProxy
    uvUniqueArray: EditorArrayProxy
    uvExtendArray: EditorArrayProxy
    weightArray: EditorArrayProxy
    jointArray: EditorArrayProxy

@dataclass
class PreprocessedWeightData:
    usedBones: list
    jointArray: list
    weightArray: list
        
class ModelImporterBase(ABC):
    def __init__(self, plugin: EditorPluginBase) -> None:
        self.plugin = plugin
        self.config = self.plugin.config
        self.logger = self.plugin.logger
        self.filePath = ''
        self.baseName = ''
        self.basePath = ''
        self.metadataFilePath = ''
        self.metadata = None
        self.model = None
        self.editorMaterialArray = []
        self.editorBoneArray = []
        self.editorBoneLookup = dict()
        self.editorGroupArray = []
        self.editorGroupLookup = dict()
        self.layer = None

    # Shared functions
    def decodeInputToPoint3( self, inputInfo, vertexStream ):
        if inputInfo.type == 11:
            # special case for compressed normals
            x, y, z, w = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            return NclVec3((x,y,z))
        else:
            assert( inputInfo.componentCount >= 3 )
            x = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            y = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            z = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            return NclVec3((x,y,z))

    def decodeInputToPoint2( self, inputInfo, vertexStream ):
        assert( inputInfo.componentCount >= 2 )
        x = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        y = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        return NclVec2((x,y))

    def decodeInputToUV( self, inputInfo, vertexStream ):
        assert( inputInfo.componentCount >= 2 )
        x = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        y = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        
        z = 0
        if inputInfo.componentCount > 2:
            z = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            
        return NclVec3((x,1 - y,z))
        
    def decodeInputToBoneIndexArray( self, inputInfo, vertexStream, editorArray ):
        result = editorArray
        for i in range( 0, inputInfo.componentCount ):
            dec = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            assert( len( dec ) == 1 )
            val = dec[0] 
            if val < 0:
                # type 4 s16 has this issue
                val = int( val ) & 0xFF
            result.append( int( val ) + self.plugin.getIndexBase() )
        return result
    
    def decodeInputToBoneWeightArray( self, inputInfo, vertexStream, editorArray ):
        result = editorArray
        for i in range( 0, inputInfo.componentCount ):
            dec = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            assert( len( dec ) == 1 )
            result.append( float( dec[0] ) )
        return result

    def decodeVertices( self, primitive: rModelPrimitive, shaderInfo: ShaderObjectInfo, vertexStream: NclBitStream ) -> DecodedVertexData:
        editorVertexArray = self.createArray()
        editorNormalArray = self.createArray()
        editorUVPrimaryArray = self.createArray()
        editorUVSecondaryArray = self.createArray()
        editorUVUniqueArray = self.createArray()
        editorUVExtendArray = self.createArray()
        editorWeightArray = self.createArray()
        editorJointArray = self.createArray()

        self.logger.debug( 'decoding vertices' )
        vertexBufferStart = primitive.vertexBufferOffset + (primitive.vertexStartIndex * primitive.vertexStride)
        for j in range( 0, primitive.vertexCount ):
            vertexStart = vertexBufferStart + ( j * primitive.vertexStride )
            
            # decode each vertex input
            editorVtxWeightArray = None
            editorVtxJointArray = None
            for key, value in shaderInfo.inputsByName.items():
                for inputInfo in value:
                    vertexStream.setOffset( vertexStart + inputInfo.offset )

                    if key == 'Position':
                        pos = self.decodeInputToPoint3( inputInfo, vertexStream )
                        if not self.config.debugDisableTransform:
                            pos = nclTransform(pos, self.modelMtx )
                        editorVertexArray.append( self.convertNclVec3ToPoint3( pos ) )
                    elif key == 'Normal':
                        nrm = self.decodeInputToPoint3( inputInfo, vertexStream )
                        if not self.config.debugDisableTransform:
                            nrm = nclNormalize( nclTransform( nrm, self.modelMtxNormal ) )
                        editorNormalArray.append( self.convertNclVec3ToPoint3( nrm ) )
                    elif key == 'Joint':
                        if editorVtxJointArray == None:
                            editorVtxJointArray = self.createArray()
                        self.decodeInputToBoneIndexArray( inputInfo, vertexStream, editorVtxJointArray ) 
                    elif key == 'Weight':
                        if editorVtxWeightArray == None:
                            editorVtxWeightArray = self.createArray()
                        self.decodeInputToBoneWeightArray( inputInfo, vertexStream, editorVtxWeightArray )
                    elif key == 'UV_Primary':
                        editorUVPrimaryArray.append( self.convertNclVec3ToPoint3( self.decodeInputToUV( inputInfo, vertexStream ) ) )
                    elif key == 'UV_Secondary':
                        editorUVSecondaryArray.append( self.convertNclVec3ToPoint3( self.decodeInputToUV( inputInfo, vertexStream ) ) )
                    elif key == 'UV_Unique':
                        editorUVUniqueArray.append( self.convertNclVec3ToPoint3( self.decodeInputToUV( inputInfo, vertexStream ) ) )
                    elif key == 'UV_Extend':
                        editorUVExtendArray.append( self.convertNclVec3ToPoint3( self.decodeInputToUV( inputInfo, vertexStream ) ) )
                        
            if editorVtxWeightArray != None:
                editorWeightArray.append( editorVtxWeightArray )
            if editorVtxJointArray != None:
                editorJointArray.append( editorVtxJointArray )

        return DecodedVertexData(
            editorVertexArray,
            editorNormalArray,
            editorUVPrimaryArray,
            editorUVSecondaryArray,
            editorUVUniqueArray,
            editorUVExtendArray,
            editorWeightArray,
            editorJointArray
        )
            

    def decodeFaces( self, primitive: rModelPrimitive, indexStream: NclBitStream ) -> EditorArrayProxy:
        self.logger.debug( 'decoding faces')
        editorFaceArray = self.createArray()
        indexStart = ( primitive.indexBufferOffset + primitive.indexStartIndex ) * 2
        indexStream.setOffset( indexStart )
        if not target.current.useTriStrips:   
            for j in range( 0, primitive.indexCount, 3 ):
                face = self.createPoint3( 
                    indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase(), 
                    indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase(), 
                    indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase() )
                editorFaceArray.append( face )
        else:    
            a = indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase()
            b = indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase()
            flip = True
            j = 2
            while j < primitive.indexCount:
                c = indexStream.readUShort()
                if c == 0xffff:
                    a = indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase()
                    b = indexStream.readUShort() - primitive.vertexStartIndex + self.plugin.getIndexBase()
                    flip = True
                    j += 3
                else:
                    c = c - primitive.vertexStartIndex + self.plugin.getIndexBase()
                    flip = not flip
                    if flip:
                        face = self.createPoint3( c,b,a )  
                    else:
                        face = self.createPoint3( a,b,c )
                    
                    editorFaceArray.append( face )
                    a = b
                    b = c
                    j += 1
        return editorFaceArray

    def loadTextureSlot( self, material, slot ):
        texturePath = material.getTextureAssignedToSlot( slot )
        if texturePath in [None, '']:
            return None
        else:
            textureTEXPath, textureDDSPath = util.resolveTexturePath( self.basePath, texturePath )
            
            if self.config.importConvertTexturesToDDS and textureTEXPath != None and os.path.exists( textureTEXPath ):
                self.logger.info( f'converting TEX file {textureTEXPath} to DDS {textureDDSPath}' )
                
                try:
                    texture = rTextureData()
                    texture.loadBinaryFile( textureTEXPath )
                    textureDDS = texture.toDDS()
                    try:
                        textureDDS.saveFile( textureDDSPath )
                    except PermissionError:
                        self.logger.error( f"failed to save TEX file to DDS, make sure you have write permissions to: {textureDDSPath}" )
                except Exception as e:
                    self.logger.error( 'failed to convert TEX file to DDS' )
                    self.logger.exception( e )
                        
            return self.createTexture( textureDDSPath )

    def loadMetadata( self, path ):
        metadata = ModelMetadata()
        if os.path.exists( path ):
            self.logger.info(f'loading metadata file from {path}')
            metadata.loadFile( path )
        return metadata

    def loadModel( self, path ):
        model = rModelData()
        self.logger.info(f'loading model from {path}')
        model.read( NclBitStream( util.loadIntoByteArray( path ) ) )
        mvc3materialnamedb.registerMaterialNames( model.materials )
        if target.current.useTriStrips != model.usesTriStrips():
            raise RuntimeError('File format does not match the current game target. Please pick the correct game target')
        return model

    def importGroups( self ):
        self.logger.info('importing groups')
        
        self.editorGroupArray = []
        self.editorGroupLookup = dict()
        for i, group in enumerate( self.model.groups ):
            self.updateProgress( 'Importing groups', i, len( self.model.groups ) )
            
            editorGroup = self.createDummy( self.metadata.getGroupName( group.id ), group.boundingSphere )
            if self.layer != None:
                self.layer.addNode( editorGroup )
            
            self.setGroupCustomAttributes( group, editorGroup )
            self.editorGroupArray.append( editorGroup )
            self.editorGroupLookup[ group.id ] = editorGroup

    def importPrimitives( self ):
        self.logger.info('importing primitives')
        
        indexStream = NclBitStream( self.model.indexBuffer )
        vertexStream = NclBitStream( self.model.vertexBuffer )
        envelopeIndex = 0
        for i in range( len( self.model.primitives ) ):
            self.updateProgress( 'Importing primitives', i, len( self.model.primitives ) )
            
            primitive = self.model.primitives[i]
            
            if len(self.config.debugImportPrimitiveIdFilter) > 0 and primitive.id not in self.config.debugImportPrimitiveIdFilter:
                self.logger.debug(f'skipped importing primitive {self.metadata.getPrimitiveName( primitive.id )} (id {primitive.id}) because it does not match the filter')
                continue

            self.logger.info( "importing primitive " + str(i) + " " + self.metadata.getPrimitiveName( primitive.id ) )
            self.plugin.updateUI()
            
            self.importPrimitive( primitive, envelopeIndex, indexStream, vertexStream )
            envelopeIndex += primitive.envelopeCount

    def importSkeleton( self ):
        self.logger.info('importing skeleton')
        
        self.editorRootBone = None
        if self.config.lukasCompat:
            self.editorRootBone = self.createBone('bone255', self.convertNclMat44ToMatrix( self.transformMtx ), None)
        
        self.editorBoneArray = []
        self.editorBoneLookup = dict()
        for i, joint in enumerate( self.model.joints ):
            self.updateProgress( 'Importing skeleton', i, len( self.model.joints ) )
            
            localMtx = self.model.jointLocalMtx[i]
            
            if not self.config.lukasCompat:
                if self.config.importBakeScale:
                    # transform position by scale
                    localMtx = copy.deepcopy(localMtx)
                    localMtx[3] *= NclVec4((self.config.importScale, self.config.importScale, self.config.importScale, 1))
                    if joint.parentIndex == 255:
                        # flip up axis if necessary
                        localMtx = self.transformMtxNoScale * localMtx
                else:        
                    if joint.parentIndex == 255:
                        # only transform root
                        localMtx = self.transformMtx * localMtx         

            worldMtx = localMtx
            jointName = self.metadata.getJointName( joint.id )           
            editorParentBone = None
            if joint.parentIndex != 255:
                editorParentBone = self.editorBoneArray[ joint.parentIndex ]
                worldMtx = nclMultiply( worldMtx, editorParentBone.getTransform() )
            elif self.editorRootBone is not None:
                editorParentBone = self.editorRootBone
                worldMtx = nclMultiply( worldMtx, editorParentBone.getTransform() )
         
            editorBone = self.createBone( joint, jointName, worldMtx, editorParentBone ) 
            self.editorBoneArray.append( editorBone )
            self.editorBoneLookup[ joint.id ] = editorBone

    def fixupSkeleton( self ):
        if self.config.lukasCompat and self.editorRootBone is not None:
            self.setUserProp( self.editorRootBone, 'LMTBone', 255 )

        for i, joint in enumerate( self.model.joints ):
            editorBone = self.editorBoneArray[ i ]
            # for compat. with Lukas' Mt Framework animation importing script  
            self.setInheritanceFlags( editorBone, (1,2,3,4,5,6) )
            self.setUserProp( editorBone, 'LMTBone', joint.id )        
            self.setJointCustomAttributes( joint, editorBone )

    def importMaterials( self ):
        self.logger.info('importing materials')
        
        # load mtl
        mtl = imMaterialLib()
        mrlName, _ = util.getExtractedResourceFilePath( self.basePath + '/' + self.baseName, '2749c8a8', 'mrl' )
        if mrlName != None and os.path.exists( mrlName ):
            self.logger.info(f'loading mrl file from {mrlName}')
            mtl.loadBinaryStream(NclBitStream(util.loadIntoByteArray(mrlName)))
            if self.config.importSaveMrlYml:
                mrlYmlPath =  mrlName + '.yml'
                self.logger.info(f'saving mrl yml to {mrlYmlPath}')
                try:
                    mtl.saveYamlFile( mrlYmlPath )
                except PermissionError as e:
                    self.logger.error( f"unable to save mrl yml file, make sure you have write permissions to {mrlYmlPath}" )
        else:
            self.logger.warn(f'skipped loading mrl from {mrlName} because the file does not exist')
        
        self.editorMaterialArray = []
        for i, materialName in enumerate( self.model.materials ):
            self.logger.info(f'importing material {materialName}')
            self.updateProgress( 'Importing materials', i, len( self.model.materials ) )
            
            material = mtl.getMaterialByName( materialName )
            if material == None:
                self.logger.warn( "model references material {} that does not exist in the mrl".format( materialName ) )
            
            editorMaterial = self.convertMaterial( material, materialName )
            if material != None:    
                self.setMaterialCustomAttributes( editorMaterial, material )                
                
            self.editorMaterialArray.append( editorMaterial )


    def importEnvelopes( self ):
        self.logger.warn('importing envelopes skipped')
        
        # build envelopes
        #~ editorEnvelopes = []
        #~ for i, envelope in enumerate( model.envelopes ):
            #~ editorEnvelope = rt.dummy()
            #~ editorEnvelope.name = "env_" + str( i )
            #~ editorEnvelope.transform = convertNclMat44ToMatrix( envelope.localMtx ) * editorBoneArray[ envelope.jointIndex ].getTransform()
            #~ editorEnvelopes.append( editorEnvelope )
        pass

    def calcMatrices( self ):
        self.transformMtx = nclCreateMat44()
        if self.config.flipUpAxis:
            self.transformMtx *= util.Y_TO_Z_UP_MATRIX
            
        self.scaleMtx = nclScale( self.config.importScale )
        self.transformMtxNoScale = copy.deepcopy(self.transformMtx)
        self.transformMtx *= self.scaleMtx
            
        self.modelMtx = self.transformMtx * self.model.calcModelMtx()
        self.editorModelMtx = self.convertNclMat44ToMatrix( self.modelMtx )
        self.modelMtxNormal = nclTranspose( nclInverse( self.modelMtx ) )
        self.editorModelMtxNormal = self.convertNclMat44ToMatrix( self.modelMtxNormal )

    def importModel( self, modFilePath ):
        self.logger.info(f'script version: {self.plugin.version}')
        self.logger.info(f'import model from {modFilePath}')
        
        startTime = self.plugin.timeStamp()
        
        if not self.plugin.isDebugEnv():
            self.plugin.disableSceneRedraw()
        
        self.filePath = modFilePath
        self.baseName = os.path.basename( modFilePath ).split('.')[0]
        self.basePath = os.path.dirname( modFilePath )
        self.metadata = self.loadMetadata( self.config.importMetadataPath )
        self.model = self.loadModel( self.filePath )
        self.calcMatrices()

        if self.config.importCreateLayer:
            self.layer = self.newLayerFromName( self.baseName )
            if self.layer == None:
                self.layer = self.getLayerFromName( self.baseName )
        
        self.importMaterials()
        if self.config.importSkeleton:
            self.importSkeleton()
            self.fixupSkeleton()
        if self.config.importGroups:
            self.importGroups()
        self.importEnvelopes() 
        if self.config.importPrimitives:
            self.importPrimitives()
        
        if not self.plugin.isDebugEnv():
            self.plugin.enableSceneRedraw()
            
        endTime = self.plugin.timeStamp()
        self.updateProgress( 'Done', 0 )
        self.updateSubProgress( '', 0 )
        self.logger.info( 'Import done in ' + str( endTime - startTime ) + ' ms' )

    def selectImportModel( self ):
        filePath = self.selectOpenFile( 'UMVC3 model', 'mod' )
        if filePath != None:
            self.importModel( filePath )

    # Attributes
    def setGroupCustomAttributes( self, group, editorGroup ):
        attribs = self.createGroupCustomAttribute( editorGroup )
        attribs.id = group.id
        attribs.field04 = group.field04
        attribs.field08 = group.field08
        attribs.field0c = group.field0c
        attribs.bsphere = group.boundingSphere
        attribs.index = str( self.model.groups.index( group ) )

    def setJointCustomAttributes(self, joint, editorBone ):
        attribs = self.createJointCustomAttribute( editorBone )
        attribs.id = joint.id
        attribs.parentIndex = str(joint.parentIndex)
        attribs.symmetryIndex = str(joint.symmetryIndex)
        attribs.symmetryName = self.editorBoneArray[ joint.symmetryIndex ].getName() if joint.symmetryIndex != 255 else ""
        attribs.field03 = joint.field03
        attribs.field04 = joint.field04
        attribs.length = str(joint.length)
        attribs.offsetX = str(joint.offset[0])
        attribs.offsetY = str(joint.offset[1])
        attribs.offsetZ = str(joint.offset[2])
        attribs.index = str( self.model.joints.index( joint ) )

    def setMaterialCustomAttributes(self, editorMaterial, material: imMaterialInfo):
        attribs = self.createMaterialCustomAttribute( editorMaterial )
        attribs.type = material.type
        attribs.depthStencilState = material.depthStencilState
        attribs.rasterizerState = material.rasterizerState
        attribs.cmdListFlags = hex( material.cmdListFlags )
        attribs.matFlags = hex( material.matFlags )

    def setPrimitiveCustomAttributes( self, primitive, shaderInfo, editorMesh, envelopeIndex ):
        attribs = self.createPrimitiveCustomAttribute( editorMesh )
        attribs.flags = hex( primitive.flags )
        attribs.groupId = "inherit" # inherited from parent
        attribs.lodIndex = primitive.indices.getLodIndex()
        attribs.matIndex = str( primitive.indices.getMaterialIndex() )
        attribs.vertexFlags = hex( primitive.vertexFlags )
        attribs.vertexStride = str( primitive.vertexStride )
        attribs.renderFlags = hex( primitive.renderFlags )
        attribs.vertexStartIndex = str( primitive.vertexStartIndex )
        attribs.vertexBufferOffset = hex( primitive.vertexBufferOffset )
        attribs.shaderName = shaderInfo.name
        attribs.indexBufferOffset = hex( primitive.indexBufferOffset )
        attribs.indexCount = str( primitive.indexCount )
        attribs.indexStartIndex = str( primitive.indexStartIndex )
        attribs.boneMapStartIndex = str( primitive.boneIdStart )
        attribs.envelopeCount = str( primitive.envelopeCount )
        attribs.envelopeIndex = str( envelopeIndex )
        attribs.id = primitive.id
        attribs.minVertexIndex = str( primitive.minVertexIndex )
        attribs.maxVertexIndex = str( primitive.maxVertexIndex )
        attribs.field2c = primitive.field2c
        attribs.envelopePtr = str( primitive.envelopePtr )
        attribs.index = str( self.model.primitives.index( primitive ) )

    def preprocessWeights( self, primitive: rModelPrimitive, vertexData: DecodedVertexData ) -> PreprocessedWeightData:
        usedEditorBones = []
        newEditorJointArray = []
        newEditorWeightArray = []
        for j in range( 0, primitive.vertexCount ):
            # get weights and indices for this vertex
            editorVtxJointArray = vertexData.jointArray[j]
            assert ( len(editorVtxJointArray) > 0 )
            if j + 1 > len( vertexData.weightArray ):
                editorVtxWeightArray = self.createArray()
            else:
                editorVtxWeightArray = vertexData.weightArray[j] 

            for w in editorVtxWeightArray:
                assert w >= 0, f'vertex {j} has a negative weight: {editorVtxWeightArray}'
            
            # calculate remaining weights
            if len( editorVtxJointArray ) != len( editorVtxWeightArray ):    
                assert( len( editorVtxJointArray ) > len( editorVtxWeightArray ) )
                numMissingWeights = len( editorVtxJointArray ) - len( editorVtxWeightArray )
                weightSum = 0
                for w in editorVtxWeightArray:
                    weightSum += w
                weightRemainder = 1 - weightSum
                weightDelta = weightRemainder / numMissingWeights
                for k in range( 0, numMissingWeights ):
                    editorVtxWeightArray.append( weightDelta )

            # remove useless weights, track used joints and merge weights to the same joint id
            newEditorVtxJointArray = self.createArray()
            newEditorVtxWeightArray = self.createArray()
            jointMap = dict()
            
            for k in range(len(editorVtxJointArray)):
                if editorVtxWeightArray[k] > 0.001:
                    id = editorVtxJointArray[k]
                    weight = editorVtxWeightArray[k]
                    if id in jointMap:
                        # merge weight
                        newEditorVtxWeightArray[jointMap[id]] += weight
                    else:
                        # add weight
                        editorBone = self.editorBoneArray[id - self.plugin.getIndexBase()]
                        if not editorBone in usedEditorBones: 
                            newJointIndex = len( usedEditorBones )
                            usedEditorBones.append( editorBone )
                        else:
                            newJointIndex = usedEditorBones.index( editorBone )
                        jointMap[id] = len(newEditorVtxWeightArray)
                        
                        newEditorVtxJointArray.append( newJointIndex )
                        newEditorVtxWeightArray.append( weight )
                    
            # normalize weights again after removing some
            weightSum = 0
            for w in newEditorVtxWeightArray:
                weightSum += w
            weightRemainder = 1 - weightSum
            weightDelta = weightRemainder / len(newEditorVtxWeightArray)
            for k in range( 0, len( newEditorVtxWeightArray ) ):
                newEditorVtxWeightArray[k] += weightDelta

            newEditorJointArray.append( newEditorVtxJointArray )
            newEditorWeightArray.append( newEditorVtxWeightArray )

        return PreprocessedWeightData(usedEditorBones, newEditorJointArray, newEditorWeightArray)

    # Misc functions
    @abstractmethod
    def setUserProp(self, obj, key, value):
        pass

    @abstractmethod
    def setInheritanceFlags( self, bone, flags ):
        pass

    @abstractmethod
    def normalize( self, value ):
        pass

    @abstractmethod
    def transformPoint( self, point, matrix ):
        pass

    # Progress functions
    @abstractmethod
    def updateProgress( self, what, value, count = 0 ):
        pass

    @abstractmethod
    def updateSubProgress( self, what, value, count = 0 ):
        pass

    # Layer functions
    @abstractmethod
    def newLayerFromName(self, name) -> EditorLayerProxy:
        pass

    @abstractmethod
    def getLayerFromName(self, name) -> EditorLayerProxy:
        pass

    # Convert functions
    @abstractmethod
    def convertNclVec3ToPoint3( self, nclVec3 ):
        pass
        
    @abstractmethod
    def convertNclMat44ToMatrix( self, nclMtx ):
        pass
    
    @abstractmethod
    def convertNclMat43ToMatrix( self, nclMtx ):
        pass

    # Import functions
    @abstractmethod
    def importPrimitive( self, primitive, envelopeIndex, indexStream, vertexStream ):
        pass

    @abstractmethod
    def importWeights( self, editorMesh, primitive, editorJointArray, editorWeightArray ):
        pass

    # Create functions
    @abstractmethod
    def createArray( self ) -> EditorArrayProxy:
        pass

    @abstractmethod
    def createPoint3( self, x, y, z ):
        pass
    
    @abstractmethod
    def createPoint2( self, x, y ):
        pass

    @abstractmethod
    def createDummy( self, name, pos ):
        pass

    @abstractmethod
    def createTexture( self, filename ):
        pass

    @abstractmethod
    def createBone( self, joint, name, tfm, parentBone ):
        pass

    # Materials
    @abstractmethod
    def convertMaterial( self, material: imMaterialInfo, materialName: str ):
        pass

    # Attributes
    @abstractmethod
    def createGroupCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        pass

    @abstractmethod
    def createMaterialCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        pass

    @abstractmethod
    def createPrimitiveCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        pass

    @abstractmethod
    def createJointCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        pass