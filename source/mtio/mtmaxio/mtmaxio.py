# TODO
# - display msg box with errors during import
# - investigate createMaxPoint3 access violation

import sys
import os

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))
    
def addSysPath( *paths ):
    for path in paths:
        normalizedPath = os.path.realpath( path )
        if not normalizedPath in sys.path:
            sys.path.append( normalizedPath )
            
def dumpSysInfo():
    print( 'PYTHON SYSTEM INFO' )
    print( sys.version )
    print( sys.version_info )
    print( sys.path )

# really good code right here
mtmaxioDir = getScriptDir()
mtioDir = getScriptDir() + '/../'
mtlibDir = getScriptDir() + '/../mtlib'
addSysPath( mtmaxioDir, mtioDir, mtlibDir )
dumpSysInfo()


from mtlib import *
from mtrtexture import *
import mtmaxioconfig
from mtmetadata import *

import pymxs
rt = pymxs.runtime

lastWindowUpdateTime = rt.timestamp()
def lazyUpdateUI():
    global lastWindowUpdateTime
    if rt.timestamp() - lastWindowUpdateTime > 1000:
        rt.windows.processPostedMessages()
        lastWindowUpdateTime = rt.timestamp()

def isDebugEnv():
    return True
    
def clearLog():
    rt.clearListener()
    try:
        rt.mtLogRollout.edtLog.text = ''
    except:
        pass
    
def logDebug( msg, *args ):
    if isDebugEnv():
        print( msg, *args )
        
def logInfo( msg, *args ):
    print( msg, *args )
    rt.mtLogRollout.edtLog.text += msg + '\n'
    
def selectOpenFile( category, ext ):
    return rt.getOpenFileName(
        caption=("Open " + category + " file"),
        types=( category + " (*." + ext + ")|*." + ext ),
        historyCategory=( category + " Object Presets" ) )
    
def transformImportTranslation( t, convertToZUp, scl ):
    nt = rt.copy( t )
    if convertToZUp:
        nt.x = -t.x
        nt.y = -t.z
        nt.z = t.y
    nt *= scl
    return nt

def transformImportRotation( r, convertToZUp ):
    nr = rt.copy( r )
    if convertToZUp:
        aa = rt.AngleAxis( r )
        newAA = rt.AngleAxis( aa.angle, rt.Point3( aa.axis.x, aa.axis.z, -aa.axis.y ) )
        nr = rt.Quat( newAA )
    return nr

def transformExportRotation( r, convertToYUp ):
    nr = rt.copy( r )
    if convertToYUp:
        aa = rt.AngleAxis( r )
        newAA = rt.AngleAxis( aa.angle, [aa.axis.x, -aa.axis.z, aa.axis.y] )
        nr = rt.Quat( newAA )
    return nr

def transformImportScale( s, convertToZUp ):
    ns = rt.copy( s )
    if convertToZUp:
        ns.y = s.z
        ns.z = s.y
    return ns

def transformImportMatrix( m, convertToZUp, scl ):
    t = m.translationpart
    r = m.rotationpart
    s = m.scalepart
    
    t = transformImportTranslation( t, convertToZUp, scl )
    r = transformImportRotation( r, convertToZUp )
    s = transformImportScale( s, convertToZUp )
    
    m = rt.Matrix3( r )
    m.translation = t
    m *= rt.ScaleMatrix( s )
    return m  

def transformExportTranslation( t, convertToZUp, scl ):
    nt = rt.copy( t )
    if convertToZUp:
        nt.x = -t.x
        nt.y = t.z
        nt.z = -t.y
    nt /= scl
    return nt

def transformExportScale( s, convertToYUp ):
	ns = rt.copy( s )
	if convertToYUp:
		ns.y = s.z
		ns.z = s.y
	return ns

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
        
    def convertNclMat4ToMaxMatrix3( self, nclMtx ):
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
            x, y, z = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            return self.createMaxPoint3( x, y, z )
        else:
            assert( inputInfo.componentCount >= 3 )
            x = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            y = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            z = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            return self.createMaxPoint3( x, y, z )
        
    def decodeInputToMaxPoint2( self, inputInfo, vertexStream ):
        assert( inputInfo.componentCount >= 2 )
        x = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        y = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        return self.createMaxPoint2( x, y )
        
    def decodeInputToMaxPoint3UV( self, inputInfo, vertexStream ):
        assert( inputInfo.componentCount >= 2 )
        x = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        y = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
        
        z = 0
        if inputInfo.componentCount > 2:
            z = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )[0]
            
        return self.createMaxPoint3( x, 1 - y, z )
        
    def decodeInputToMaxArray( self, inputInfo, vertexStream, maxArray, converter ):
        result = maxArray
        for i in range( 0, inputInfo.componentCount ):
            dec = mtvertexcodec.decodeVertexComponent( inputInfo.type, vertexStream )
            assert( len( dec ) == 1 )
            rt.append( result, converter( dec[0] ) )
        return result
            
    def loadTextureSlot( self, material, slot ):
        texturePath = material.getTextureAssignedToSlot( slot )
        if texturePath == '':
            return None
        else:
            textureTEXPath, textureDDSPath = mtutil.resolveTexturePath( self.basePath, texturePath )
            
            if mtmaxioconfig.importConvertTexturesToDDS:
                texture = rTextureData()
                texture.loadBinaryFile( textureTEXPath )
                textureDDS = texture.toDDS()
                try:
                    textureDDS.saveFile( textureDDSPath )
                except:
                    logInfo( f"ERROR: failed to save TEX file to DDS, make sure you have write permissions to: {textureDDSPath}" )
                        
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
        model.read( NclBitStream( mtutil.loadIntoByteArray( path ) ) )
        mvc3materialdb.addNames( model.materials )
        return model
    
    def calcTransformMtx( self ):
        mtx = NclMat43()
        if mtmaxioconfig.convertToZUp:
            mtx *= mtutil.Y_TO_Z_UP_MATRIX
        if mtmaxioconfig.scale > 1:
            mtx *= NclMat43.createScale( mtmaxioconfig.scale )
        return mtx
        
    def calcModelMtx( self, model: rModelData ):
        modelMtx = model.calcModelMtx() * self.transformMtx
        return self.convertNclMat4ToMaxMatrix3( modelMtx )
            
    def importGroups( self ):
        self.maxGroupArray = []
        self.maxGroupLookup = dict()
        for i, group in enumerate( self.model.groups ):
            maxGroup = rt.dummy()
            #maxGroup.pos = rt.Point3( group.boundingSphere[0], group.boundingSphere[1], group.boundingSphere[2] )
            maxGroup.name = self.metadata.getGroupName( group.id )
            rt.custAttributes.add( maxGroup, rt.mtModelGroupAttributesInstance )
            maxGroup.mtModelGroupAttributes.id = group.id
            maxGroup.mtModelGroupAttributes.field04 = group.field04
            maxGroup.mtModelGroupAttributes.field08 = group.field08
            maxGroup.mtModelGroupAttributes.field0c = group.field0c
            maxGroup.mtModelGroupAttributes.bsphere = group.boundingSphere
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
        #for j in range( 0, len( maxNormalArray ) ):
        #    rt.setNormal( maxMesh, j + 1, maxNormalArray[j] )
            
        maxMesh.material = self.maxMaterialArray[ primitive.indices.getMaterialIndex() ]
        rt.custAttributes.add( maxMesh.baseObject, rt.mtPrimitiveAttributesInstance )
        maxMesh.mtPrimitiveAttributes.flags = hex( primitive.flags )
        maxMesh.mtPrimitiveAttributes.lodIndex = primitive.indices.getLodIndex() 
        if maxMesh.mtPrimitiveAttributes.lodIndex in [-1, 255]:
            maxMesh.mtPrimitiveAttributes.lodIndex = -1

        maxMesh.mtPrimitiveAttributes.vertexFlags = hex( primitive.vertexFlags )
        maxMesh.mtPrimitiveAttributes.renderFlags = hex( primitive.renderFlags )
        maxMesh.mtPrimitiveAttributes.shaderName = shaderInfo.name
        maxMesh.mtPrimitiveAttributes.id = primitive.id
        maxMesh.mtPrimitiveAttributes.field2c = primitive.field2c

        # parent to group
        if primitive.indices.getGroupId() in self.maxGroupLookup:
            maxMesh.parent = self.maxGroupLookup[ primitive.indices.getGroupId() ]

        # parent pjl to mesh
        #for j in range( 0, primitive.primitiveJointLinkCount ):
        #    self.maxPrimitiveJointLinks[ primitiveJointLinkIndex + j ].parent = maxMesh

        # apply weights
        if len( maxJointArray ) > 0 and mtmaxioconfig.importWeights:
            rt.resumeEditing()
            rt.execute('max modify mode')
            
            rt.select( maxMesh )
            maxSkin = rt.skin()
            rt.addModifier( maxMesh, maxSkin )
            
            # add bones
            for maxBone in self.maxBoneArray:
                rt.skinOps.addBone( maxSkin, maxBone, 0 )
                
            # set weights
            rt.modPanel.setCurrentObject( maxSkin )
            for j in range( 0, primitive.vertexCount ):
                lazyUpdateUI()
                
                maxVtxJointArray = maxJointArray[j]
                if j + 1 > len( maxWeightArray ):
                    rt.append( maxWeightArray, rt.Array() )
                maxVtxWeightArray = maxWeightArray[j] 
                
                if len( maxVtxJointArray ) != len( maxVtxWeightArray ):
                    # calculate remaining weights
                    assert( len( maxVtxJointArray ) > len( maxVtxWeightArray ) )
                    numMissingWeights = len( maxVtxJointArray ) - len( maxVtxWeightArray )
                    weightSum = 0
                    for w in maxVtxWeightArray:
                        weightSum += w
                    weightRemainder = 1 - weightSum
                    weightDelta = weightRemainder / numMissingWeights
                    for k in range( 0, numMissingWeights ):
                        rt.append( maxVtxWeightArray, weightDelta )
                
                rt.skinOps.setVertexWeights( maxSkin, j + 1, maxJointArray[j], maxWeightArray[j] )
            
    def importPrimitives( self ):
        indexStream = NclBitStream( self.model.indexBuffer )
        vertexStream = NclBitStream( self.model.vertexBuffer )
        primitiveJointLinkIndex = 0
        for i in range( len( self.model.primitives ) ):
            logInfo( "loading primitive " + str(i) )
            lazyUpdateUI()
            
            primitive = self.model.primitives[i]
            self.importPrimitive( primitive, primitiveJointLinkIndex, indexStream, vertexStream )
            primitiveJointLinkIndex += primitive.primitiveJointLinkCount
            
    def importSkeleton( self ):
        self.maxBoneArray = []
        self.maxBoneLookup = dict()
        for i, joint in enumerate( self.model.joints ):
            localMtx = self.model.jointLocalMtx[i].toMat43()
            if not mtutil.isValidByteIndex( joint.parentIndex ):
                # only transform root
                localMtx *= self.transformMtx
            
            tfm = self.convertNclMat43ToMaxMatrix3( localMtx )
            maxParentBone = None
            if mtutil.isValidByteIndex( joint.parentIndex ):
                maxParentBone = self.maxBoneArray[ joint.parentIndex ]
                tfm *= maxParentBone.Transform
                    
            jointName = self.metadata.getJointName( joint.id )            
            maxBone = self.createMaxBone( jointName, tfm, maxParentBone )        
            self.maxBoneArray.append( maxBone )
            self.maxBoneLookup[ joint.id ] = maxBone
            
        # add custom attributes
        for i, joint in enumerate( self.model.joints ):
            maxBone = self.maxBoneArray[ i ]
            rt.custAttributes.add( maxBone.baseObject, rt.mtJointAttributesInstance )
            maxBone.mtJointAttributes.id = joint.id
            if joint.symmetryIndex not in [-1, 255]:
                maxBone.mtJointAttributes.symmetryName = self.maxBoneArray[ joint.symmetryIndex ].name
            maxBone.mtJointAttributes.field03 = joint.field03
            maxBone.mtJointAttributes.field04 = joint.field04        
            
    def importMaterials( self ):
        # load mtl
        mtl = imMaterialLib()
        mrlName, _ = mtutil.getExtractedResourceFilePath( self.basePath + '/' + self.baseName, '2749c8a8', 'mrl' )
        if mrlName != None and os.path.exists( mrlName ):
            mtl.loadBinary(NclBitStream(mtutil.loadIntoByteArray(mrlName)))
            if mtmaxioconfig.importSaveMrlYml:
                mtl.saveYamlFile( mrlName + '.yml' )
        
        self.maxMaterialArray = []
        for i, materialName in enumerate( self.model.materials ):
            material = mtl.getMaterialByName( materialName )
            maxMaterial = rt.PBRSpecGloss()
            maxMaterial.name = materialName
            maxMaterial.showInViewport = True
            maxMaterial.backfaceCull = True
        
            if material == None:
                logInfo( "WARNING: model references material {} that does not exist in the mrl".format( materialName ) )
            else:
                maxMaterial.base_color_map = self.loadTextureSlot( material, 'tAlbedoMap' )
                maxMaterial.specular_map = self.loadTextureSlot( material, 'tSpecularMap' )
                maxMaterial.norm_map = self.loadTextureSlot( material, 'tNormalMap' )
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
            #~ maxPjl.transform = convertNclMat4ToMaxMatrix3( pjl.localMtx ) * maxBoneArray[ pjl.jointIndex ].transform
            #~ maxPrimitiveJointLinks.append( maxPjl )
        pass
            
    def importModel( self, modFilePath ):
        startTime = rt.timeStamp()
        
        if not isDebugEnv():
            rt.disableSceneRedraw()
        
        self.filePath = modFilePath
        self.baseName = os.path.basename( modFilePath ).split('.')[0]
        self.basePath = os.path.dirname( modFilePath )
        
        self.metadata = self.loadMetadata( ModelMetadata.getDefaultFilePath( mtmaxioconfig.importProfile ) )
        self.model = self.loadModel( self.filePath )
        self.transformMtx = self.calcTransformMtx()
        self.maxModelMtx = self.calcModelMtx( self.model )
        self.importMaterials()
        if mtmaxioconfig.importSkeleton:
            self.importSkeleton()
        if mtmaxioconfig.importGroups:
            self.importGroups()
        self.importPrimitiveJointLinks() 
        if mtmaxioconfig.importPrimitives:
            self.importPrimitives()
        
        if not isDebugEnv():
            rt.enableSceneRedraw()
            
        endTime = rt.timeStamp()
        logInfo( 'Import done in ' + str( endTime - startTime ) + ' ms' )
        
    def selectImportModel( self ):
        filePath = self.selectOpenFile( 'UMVC3 model', 'mod' )
        if filePath != None:
            self.importModel( filePath )
        
# Maxscript rollout event handlers        
class MtSettingsRollout:
    @staticmethod
    def sync():
        rt.MtSettingsRollout.chkConvertToZUp.checked = mtmaxioconfig.convertToZUp
        rt.MtSettingsRollout.spnScale.value = mtmaxioconfig.scale
    
    @staticmethod
    def chkConvertToZUpChanged( state ):
        mtmaxioconfig.convertToZUp = state
        
    @staticmethod
    def spnScaleChanged( state ):
        mtmaxioconfig.scale = state
    
class MtModelImportRollout:
    @staticmethod
    def updateVisibility():
        rt.MtModelImportRollout.btnImport.enabled = \
            os.path.isfile( mtmaxioconfig.importFilePath )
            
    @staticmethod
    def sync():
        rt.MtModelImportRollout.edtFile.text = mtmaxioconfig.importFilePath
        rt.MtModelImportRollout.edtProfile.text = mtmaxioconfig.importProfile
        rt.MtModelImportRollout.chkImportWeights.checked = mtmaxioconfig.importWeights
        rt.MtModelImportRollout.chkImportNormals.checked = mtmaxioconfig.importNormals
        rt.MtModelImportRollout.chkImportGroups.checked = mtmaxioconfig.importGroups
        rt.MtModelImportRollout.chkImportSkeleton.checked = mtmaxioconfig.importSkeleton
        rt.MtModelImportRollout.chkImportPrimitives.checked = mtmaxioconfig.importPrimitives
        rt.MtModelImportRollout.chkConvertDDS.checked = mtmaxioconfig.importConvertTexturesToDDS
        rt.MtModelImportRollout.chkSaveMrlYml.checked = mtmaxioconfig.importSaveMrlYml
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        mtmaxioconfig.importFilePath = path
        mtmaxioconfig.importProfile = os.path.basename( mtmaxioconfig.importFilePath ).split('.')[0]
        MtModelImportRollout.sync()
    
    @staticmethod
    def chkImportWeightsChanged( state ):
        mtmaxioconfig.importWeights = state
        MtModelImportRollout.updateVisibility()
    
    @staticmethod
    def btnImportPressed():
        clearLog()
        importer = MtModelImporter()
        importer.importModel( mtmaxioconfig.importFilePath )
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def btnFilePressed():
        path = selectOpenFile( 'UMVC3 model', 'mod' )
        if path == None:
            path = ''
        
        MtModelImportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtModelImportRollout.setFilePath( state )
        
    @staticmethod
    def edtProfileChanged( state ):
        mtmaxioconfig.importProfile = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkImportNormalsChanged( state ):
        mtmaxioconfig.importNormals = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkImportGroupsChanged( state ):
        mtmaxioconfig.importGroups = state
        MtModelImportRollout.updateVisibility()
    
    @staticmethod
    def chkImportSkeletonChanged( state ):
        mtmaxioconfig.importSkeleton = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkConvertDDSChanged( state ):
        mtmaxioconfig.importConvertTexturesToDDS = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkSaveMrlYmlChanged( state ):
        mtmaxioconfig.importSaveMrlYml = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkImportPrimitivesChanged( state ):
        mtmaxioconfig.importPrimitives = state
        MtModelImportRollout.updateVisibility()
        
def runMaxScript( name ):
    rt.fileIn( getScriptDir() + '/maxscript/' + name  )
    
def getMainWindow():
    return rt.g_mtWindow
    
def createMainWindow():
    # get coords of window if it's already opened
    x = 30
    y = 100
    w = 250
    h = 700
    
    # ensure a variable exists even if it hasnt been created yet
    rt.execute( 'g_mtWindow2 = g_mtWindow' )
    if rt.g_mtWindow2 != None:
        x = rt.g_mtWindow2.pos.x
        y = rt.g_mtWindow2.pos.y
        w = rt.g_mtWindow2.size.x
        h = rt.g_mtWindow2.size.y
        rt.closeRolloutFloater( rt.g_mtWindow2 )
        
    # create plugin window
    rt.g_mtWindow = rt.newRolloutFloater( "MT Framework Max IO Plugin", w, h, x, y )
    for rollout in [rt.MtInfoRollout, rt.MtSettingsRollout, rt.MtModelImportRollout, rt.MtLogRollout]:
        rt.addRollout( rollout, rt.g_mtWindow )
        
    # sync config with UI
    MtSettingsRollout.sync()
    MtModelImportRollout.sync()

def main():
    rt.gc()
    rt.gc()
    
    clearLog()
    
    # import maxscript files
    runMaxScript( 'customattributes.ms' )
    runMaxScript( 'rollouts.ms' )
    createMainWindow()
    
    rt.gc()
    rt.gc()
    
main()