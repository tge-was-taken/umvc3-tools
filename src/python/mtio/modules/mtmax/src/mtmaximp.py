from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
import mtmaxutil
import plugin

class MtModelImporter:
    def __init__( self ):
        self.filePath = ''
        self.baseName = ''
        self.basePath = ''
        self.metadataFilePath = ''
        self.metadata = None
        self.model = None
        self.maxMaterialArray = []
        self.maxBoneArray = []
        self.maxBoneLookup = dict()
        self.maxGroupArray = []
        self.maxGroupLookup = dict()
    
    @staticmethod
    def createMaxBone( name, tfm, parentBone ):
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
        bone.parent = parentBone
        return bone
      
    def convertNclVec3ToMaxPoint3( self, nclVec3 ):
        return rt.Point3( rt.Float( nclVec3[0] ), rt.Float( nclVec3[1] ), rt.Float( nclVec3[2] ) )
    
    def createMaxPoint3( self, x, y, z ):
        return rt.Point3( rt.Float( float( x ) ), rt.Float( float( y ) ), rt.Float( float( z ) ) )
    
    def createMaxPoint2( self, x, y ):
        return rt.Point2( rt.Float( x ), rt.Float( y ) )
        
    def convertNclMat44ToMaxMatrix3( self, nclMtx ):
        return rt.Matrix3( self.convertNclVec3ToMaxPoint3( nclMtx[0] ), 
                           self.convertNclVec3ToMaxPoint3( nclMtx[1] ), 
                           self.convertNclVec3ToMaxPoint3( nclMtx[2] ), 
                           self.convertNclVec3ToMaxPoint3( nclMtx[3] ) )
        
    def convertNclMat43ToMaxMatrix3( self, nclMtx ):
        return rt.Matrix3( self.convertNclVec3ToMaxPoint3( nclMtx[0] ), 
                           self.convertNclVec3ToMaxPoint3( nclMtx[1] ), 
                           self.convertNclVec3ToMaxPoint3( nclMtx[2] ), 
                           self.convertNclVec3ToMaxPoint3( nclMtx[3] ) )
        
    def decodeInputToMaxPoint3( self, inputInfo, vertexStream ):
        if inputInfo.type == 11:
            # special case for compressed normals
            x, y, z = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            return self.createMaxPoint3( x, y, z )
        else:
            assert( inputInfo.componentCount >= 3 )
            x = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            y = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            z = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            return self.createMaxPoint3( x, y, z )
        
    def decodeInputToMaxPoint2( self, inputInfo, vertexStream ):
        assert( inputInfo.componentCount >= 2 )
        x = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        y = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        return self.createMaxPoint2( x, y )
        
    def decodeInputToMaxPoint3UV( self, inputInfo, vertexStream ):
        assert( inputInfo.componentCount >= 2 )
        x = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        y = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        
        z = 0
        if inputInfo.componentCount > 2:
            z = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            
        return self.createMaxPoint3( x, 1 - y, z )
        
    def decodeInputToMaxArray( self, inputInfo, vertexStream, maxArray, converter ):
        result = maxArray
        for i in range( 0, inputInfo.componentCount ):
            dec = vertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            assert( len( dec ) == 1 )
            rt.append( result, converter( dec[0] ) )
        return result
            
    def loadTextureSlot( self, material, slot ):
        texturePath = material.getTextureAssignedToSlot( slot )
        if texturePath == '':
            return None
        else:
            textureTEXPath, textureDDSPath = util.resolveTexturePath( self.basePath, texturePath )
            
            if mtmaxconfig.importConvertTexturesToDDS and textureTEXPath != None and os.path.exists( textureTEXPath ):
                texture = rTextureData()
                texture.loadBinaryFile( textureTEXPath )
                textureDDS = texture.toDDS()
                try:
                    textureDDS.saveFile( textureDDSPath )
                except:
                    mtmaxutil.logInfo( f"ERROR: failed to save TEX file to DDS, make sure you have write permissions to: {textureDDSPath}" )
                        
            return rt.BitmapTexture( filename=textureDDSPath )
       
    @staticmethod     
    def convertToMaxBoneIndex( val ):
        return int( val ) + 1
        
    def loadMetadata( self, path ):
        metadata = ModelMetadata()
        if os.path.exists( path ):
            metadata.loadFile( path )
        return metadata
            
    def loadModel( self, path ):
        model = rModelData()
        model.read( NclBitStream( util.loadIntoByteArray( path ) ) )
        mvc3materialdb.addNames( model.materials )
        return model
    
    def calcTransformMtx( self ):
        mtx = nclCreateMat44()
        if mtmaxconfig.flipUpAxis:
            mtx *= util.Y_TO_Z_UP_MATRIX
        if mtmaxconfig.scale != 1:
            mtx *= nclScale( mtmaxconfig.scale )
        return mtx
        
    def calcModelMtx( self, model: rModelData ):
        modelMtx = self.transformMtx * model.calcModelMtx()
        return self.convertNclMat44ToMaxMatrix3( modelMtx )


    def _addPrimitiveAttribs( self, primitive, shaderInfo, maxMesh ):
        rt.custAttributes.add( maxMesh.baseObject, rt.mtPrimitiveAttributesInstance )
        attribs = maxMesh.mtPrimitiveAttributes
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
        attribs.primitiveJointLinkCount = str( primitive.primitiveJointLinkCount )
        attribs.id = primitive.id
        attribs.minVertexIndex = str( primitive.minVertexIndex )
        attribs.maxVertexIndex = str( primitive.maxVertexIndex )
        attribs.field2c = primitive.field2c
        attribs.primitiveJointLinkPtr = str( primitive.primitiveJointLinkPtr )

    def _addGroupAttribs( self, group, maxGroup ):
        rt.custAttributes.add( maxGroup, rt.mtModelGroupAttributesInstance )
        attribs =  maxGroup.mtModelGroupAttributes
        attribs.id = group.id
        attribs.field04 = group.field04
        attribs.field08 = group.field08
        attribs.field0c = group.field0c
        attribs.bsphere = group.boundingSphere

    def _addJointAttribs( self, joint, maxBone ):
        rt.custAttributes.add( maxBone.baseObject, rt.mtJointAttributesInstance )
        attribs = maxBone.mtJointAttributes
        attribs.id = joint.id
        attribs.parentIndex = joint.parentIndex
        attribs.symmetryIndex = joint.symmetryIndex
        attribs.symmetryName = self.maxBoneArray[ joint.symmetryIndex ].name if joint.symmetryIndex != 255 else ""
        attribs.field03 = joint.field03
        attribs.field04 = joint.field04
        attribs.length = str(joint.length)
        attribs.offsetX = str(joint.offset[0])
        attribs.offsetY = str(joint.offset[1])
        attribs.offsetZ = str(joint.offset[2])
            
    def importGroups( self ):
        self.maxGroupArray = []
        self.maxGroupLookup = dict()
        for i, group in enumerate( self.model.groups ):
            maxGroup = rt.dummy()
            #maxGroup.pos = rt.Point3( group.boundingSphere[0], group.boundingSphere[1], group.boundingSphere[2] )
            maxGroup.name = self.metadata.getGroupName( group.id )
            self._addGroupAttribs( group, maxGroup )
            self.maxGroupArray.append( maxGroup )
            self.maxGroupLookup[ group.id ] = maxGroup
            
    def importPrimitive( self, primitive, primitiveJointLinkIndex, indexStream, vertexStream ):
        shaderInfo = mvc3shaderdb.shaderObjectsByHash[ primitive.vertexShader.getHash() ]

        # read vertices
        maxVertexArray = rt.Array()
        maxNormalArray = rt.Array()
        maxUV1Array = rt.Array()
        maxUV2Array = rt.Array()
        maxWeightArray = rt.Array()
        maxJointArray = rt.Array()

        vertexBufferStart = primitive.vertexBufferOffset + (primitive.vertexStartIndex * primitive.vertexStride)
        for j in range( 0, primitive.vertexCount ):
            vertexStart = vertexBufferStart + ( j * primitive.vertexStride )
            
            # decode each vertex input
            maxVtxWeightArray = None
            maxVtxJointArray = None
            for key, value in shaderInfo.inputsByName.items():
                for inputInfo in value:
                    vertexStream.setOffset( vertexStart + inputInfo.offset )

                    if key == 'Position':
                        rt.append( maxVertexArray, self.decodeInputToMaxPoint3( inputInfo, vertexStream ) * self.maxModelMtx )
                    elif key == 'Normal':
                        rt.append( maxNormalArray, self.decodeInputToMaxPoint3( inputInfo, vertexStream ) * self.maxModelMtx )
                    elif key == 'Joint':
                        if maxVtxJointArray == None:
                            maxVtxJointArray = rt.Array()
                        self.decodeInputToMaxArray( inputInfo, vertexStream, maxVtxJointArray, self.convertToMaxBoneIndex ) 
                    elif key == 'Weight':
                        if maxVtxWeightArray == None:
                            maxVtxWeightArray = rt.Array()
                        self.decodeInputToMaxArray( inputInfo, vertexStream, maxVtxWeightArray, rt.Float )
                    elif key == 'UV_Primary':
                        rt.append( maxUV1Array, self.decodeInputToMaxPoint3UV( inputInfo, vertexStream ) )
                    elif key == 'UV_Secondary':
                        rt.append( maxUV2Array, self.decodeInputToMaxPoint3UV( inputInfo, vertexStream ) )
                        
            if maxVtxWeightArray != None:
                rt.append( maxWeightArray, maxVtxWeightArray ) 
            if maxVtxJointArray != None:
                rt.append( maxJointArray, maxVtxJointArray ) 

        # read faces
        maxFaceArray = rt.Array()
        indexStart = ( primitive.indexBufferOffset + primitive.indexStartIndex ) * 2
        indexStream.setOffset( indexStart )
        for j in range( 0, primitive.indexCount, 3 ):
            face = rt.Point3( 
                indexStream.readUShort() - primitive.vertexStartIndex + 1, 
                indexStream.readUShort() - primitive.vertexStartIndex + 1, 
                indexStream.readUShort() - primitive.vertexStartIndex + 1 )
            rt.append( maxFaceArray, face )
           
        # build mesh object
        meshName = self.metadata.getPrimitiveName( primitive.id )
        maxMesh = rt.Mesh(vertices=maxVertexArray, faces=maxFaceArray, normals=maxNormalArray)
        maxMesh.name = meshName
        maxMesh.numTVerts = len( maxVertexArray )
        rt.buildTVFaces( maxMesh )
        for j in range( 0, len( maxFaceArray ) ):
            rt.setTVFace( maxMesh, j + 1, maxFaceArray[j] )
        for j in range( 0, len( maxUV1Array ) ):
            rt.setTVert( maxMesh, j + 1, maxUV1Array[j] )
        for j in range( 0, len( maxNormalArray ) ):
           rt.setNormal( maxMesh, j + 1, maxNormalArray[j] )
            
        maxMesh.material = self.maxMaterialArray[ primitive.indices.getMaterialIndex() ]
        self._addPrimitiveAttribs( primitive, shaderInfo, maxMesh )

        # parent to group
        if primitive.indices.getGroupId() in self.maxGroupLookup:
            maxMesh.parent = self.maxGroupLookup[ primitive.indices.getGroupId() ]

        # parent pjl to mesh
        #for j in range( 0, primitive.primitiveJointLinkCount ):
        #    self.maxPrimitiveJointLinks[ primitiveJointLinkIndex + j ].parent = maxMesh

        # apply weights
        if len( maxJointArray ) > 0 and mtmaxconfig.importWeights:
            maxSkin = rt.skin()
            rt.addModifier( maxMesh, maxSkin )

            # preprocess weights
            usedMaxBones = []
            newMaxJointArray = []
            newMaxWeightArray = []
            for j in range( 0, primitive.vertexCount ):
                # get weights and indices for this vertex
                maxVtxJointArray = maxJointArray[j]
                assert ( len(maxVtxJointArray) > 0 )
                if j + 1 > len( maxWeightArray ):
                    maxVtxWeightArray = rt.Array()
                else:
                    maxVtxWeightArray = maxWeightArray[j] 

                for w in maxVtxWeightArray:
                    assert w >= 0, f'vertex {j} has a negative weight: {maxVtxWeightArray}'
                
                # calculate remaining weights
                if len( maxVtxJointArray ) != len( maxVtxWeightArray ):    
                    assert( len( maxVtxJointArray ) > len( maxVtxWeightArray ) )
                    numMissingWeights = len( maxVtxJointArray ) - len( maxVtxWeightArray )
                    weightSum = 0
                    for w in maxVtxWeightArray:
                        weightSum += w
                    weightRemainder = 1 - weightSum
                    weightDelta = weightRemainder / numMissingWeights
                    for k in range( 0, numMissingWeights ):
                        rt.append( maxVtxWeightArray, weightDelta )

                # remove useless weights and track used joints
                newMaxVtxJointArray = rt.Array()
                newMaxVtxWeightArray = rt.Array()

                for k in range(len(maxVtxJointArray)):
                    if maxVtxWeightArray[k] > 0.001:
                        maxBone = self.maxBoneArray[maxVtxJointArray[k] - 1]
                        if not maxBone in usedMaxBones: usedMaxBones.append( maxBone )
                        rt.append( newMaxVtxJointArray, maxVtxJointArray[k] )
                        rt.append( newMaxVtxWeightArray, maxVtxWeightArray[k] )

                newMaxJointArray.append( newMaxVtxJointArray )
                newMaxWeightArray.append( newMaxVtxWeightArray )
            
            # add used bones to skin modifier
            for i, maxBone in enumerate( usedMaxBones ):
                update = i == len( usedMaxBones ) - 1
                rt.skinOps.addBone( maxSkin, maxBone, update, node=maxMesh )
                
            # create mapping for our joint indices to skin modifier bone indices
            maxBoneIndexRemap = dict()
            maxSkinBoneNodes = rt.skinOps.getBoneNodes( maxSkin )
            for i, maxBone in enumerate( self.maxBoneArray ):
                for j, maxSkinBoneNode in enumerate( maxSkinBoneNodes ):
                    if maxSkinBoneNode == maxBone:
                        maxBoneIndexRemap[i + 1] = j + 1
                        break

            # set vertex weights
            for j in range( 0, primitive.vertexCount ):
                newMaxVtxJointArray = newMaxJointArray[j]
                newMaxVtxWeightArray = newMaxWeightArray[j]
                for k, joint in enumerate( newMaxVtxJointArray ):
                    # remap the joint indices to the skin modifier bone indices
                    newMaxVtxJointArray[k] = maxBoneIndexRemap[joint]   

                assert len( newMaxVtxJointArray ) > 0 
                assert len( newMaxVtxWeightArray ) > 0
                rt.skinOps.setVertexWeights( maxSkin, j + 1, newMaxVtxJointArray, newMaxVtxWeightArray, node=maxMesh )

        elif len( maxJointArray ) == 0:
            print( 'primitive {maxMesh.name} has no vertex weights' )
            
    def importPrimitives( self ):
        indexStream = NclBitStream( self.model.indexBuffer )
        vertexStream = NclBitStream( self.model.vertexBuffer )
        primitiveJointLinkIndex = 0
        for i in range( len( self.model.primitives ) ):
            primitive = self.model.primitives[i]

            mtmaxutil.logInfo( "loading primitive " + str(i) + " " + self.metadata.getPrimitiveName( primitive.id ) )
            mtmaxutil.updateUI()
            
            self.importPrimitive( primitive, primitiveJointLinkIndex, indexStream, vertexStream )
            primitiveJointLinkIndex += primitive.primitiveJointLinkCount
            
    def importSkeleton( self ):
        self.maxBoneArray = []
        self.maxBoneLookup = dict()
        for i, joint in enumerate( self.model.joints ):
            localMtx = self.model.jointLocalMtx[i]
            if not util.isValidByteIndex( joint.parentIndex ):
                # only transform root
                localMtx = self.transformMtx * localMtx
            
            tfm = self.convertNclMat44ToMaxMatrix3( localMtx )
            maxParentBone = None
            if util.isValidByteIndex( joint.parentIndex ):
                maxParentBone = self.maxBoneArray[ joint.parentIndex ]
                tfm *= maxParentBone.Transform
                    
            jointName = self.metadata.getJointName( joint.id )            
            maxBone = self.createMaxBone( jointName, tfm, maxParentBone )        
            self.maxBoneArray.append( maxBone )
            self.maxBoneLookup[ joint.id ] = maxBone
            
        # add custom attributes
        for i, joint in enumerate( self.model.joints ):
            maxBone = self.maxBoneArray[ i ]
            self._addJointAttribs( joint, maxBone )
            
    def importMaterials( self ):
        # load mtl
        mtl = imMaterialLib()
        mrlName, _ = util.getExtractedResourceFilePath( self.basePath + '/' + self.baseName, '2749c8a8', 'mrl' )
        if mrlName != None and os.path.exists( mrlName ):
            mtl.loadBinary(NclBitStream(util.loadIntoByteArray(mrlName)))
            if mtmaxconfig.importSaveMrlYml:
                mtl.saveYamlFile( mrlName + '.yml' )
        
        self.maxMaterialArray = []
        for i, materialName in enumerate( self.model.materials ):
            material = mtl.getMaterialByName( materialName )
            maxMaterial = rt.PBRSpecGloss()
            maxMaterial.name = materialName
            maxMaterial.showInViewport = True
            maxMaterial.backfaceCull = True
        
            if material == None:
                mtmaxutil.logInfo( "WARNING: model references material {} that does not exist in the mrl".format( materialName ) )
            else:
                maxMaterial.base_color_map = self.loadTextureSlot( material, 'tAlbedoMap' )
                maxMaterial.specular_map = self.loadTextureSlot( material, 'tSpecularMap' )
                # dont assign normal map because it doesn't display properly
                #maxMaterial.norm_map = self.loadTextureSlot( material, 'tNormalMap' )
                rt.custAttributes.add( maxMaterial, rt.mtMaterialAttributesInstance )
                maxMaterial.mtMaterialAttributes.type = material.type
                maxMaterial.mtMaterialAttributes.depthStencilState = material.depthStencilState
                maxMaterial.mtMaterialAttributes.rasterizerState = material.rasterizerState
                maxMaterial.mtMaterialAttributes.cmdListFlags = hex( material.cmdListFlags )
                maxMaterial.mtMaterialAttributes.matFlags = hex( material.matFlags )
                
            self.maxMaterialArray.append( maxMaterial )
            
    def importPrimitiveJointLinks( self ):
        # build primitive joint links
        #~ maxPrimitiveJointLinks = []
        #~ for i, pjl in enumerate( model.primitiveJointLinks ):
            #~ maxPjl = rt.dummy()
            #~ maxPjl.name = "pjl_" + str( i )
            #~ maxPjl.transform = convertNclMat44ToMaxMatrix3( pjl.localMtx ) * maxBoneArray[ pjl.jointIndex ].transform
            #~ maxPrimitiveJointLinks.append( maxPjl )
        pass
            
    def importModel( self, modFilePath ):
        startTime = rt.timeStamp()
        
        if not mtmaxutil.isDebugEnv():
            rt.disableSceneRedraw()
        
        self.filePath = modFilePath
        self.baseName = os.path.basename( modFilePath ).split('.')[0]
        self.basePath = os.path.dirname( modFilePath )
        self.metadata = self.loadMetadata( mtmaxconfig.importMetadataPath )
        self.model = self.loadModel( self.filePath )
        self.transformMtx = self.calcTransformMtx()
        self.maxModelMtx = self.calcModelMtx( self.model )
        #self.maxModelMtx = rt.Matrix3(1)
        self.importMaterials()
        if mtmaxconfig.importSkeleton:
            self.importSkeleton()
        if mtmaxconfig.importGroups:
            self.importGroups()
        self.importPrimitiveJointLinks() 
        if mtmaxconfig.importPrimitives:
            self.importPrimitives()
        
        if not mtmaxutil.isDebugEnv():
            rt.enableSceneRedraw()
            
        endTime = rt.timeStamp()
        mtmaxutil.logInfo( 'Import done in ' + str( endTime - startTime ) + ' ms' )
        
    def selectImportModel( self ):
        filePath = self.selectOpenFile( 'UMVC3 model', 'mod' )
        if filePath != None:
            self.importModel( filePath )
    