# MT framework model loader
import yaml
import io
import os

# noesis imports
from inc_noesis import *
from mtlib import *

def registerNoesisTypes():
    handle = noesis.register("MT Framework Model", ".mod")
    noesis.setHandlerTypeCheck(handle, modCheckType)
    noesis.setHandlerLoadModel(handle, modLoadModel)
    noesis.setHandlerWriteModel(handle, modWriteModel)
    return 1

def modCheckType(data):
    reader = rModelStreamReader(NoeBitStream(data))
    return reader.isValid()

# typedef enum<u32>
# {
#     rShaderInputLayoutElementType_F32 = 1, // 32 bit single precision float
#     rShaderInputLayoutElementType_F16 = 2, // 16 bit half precision float
#     rShaderInputLayoutElementType_IU16 = 3, // guess, 16 bit integer (joint index)
#     rShaderInputLayoutElementType_IS16 = 4, // guess, 16 bit integer (joint index)
#     rShaderInputLayoutElementType_FS16 = 5, // guess, 16 bit normalized compressed float, divisor = 1 << 15 - 1
#     rShaderInputLayoutElementType_IS8 = 7, // guess
#     rShaderInputLayoutElementType_IU8 = 8, // guess, 8 bit unsigned joint index
#     rShaderInputLayoutElementType_FU8  = 9, // guess, 8 bit normalized compressed float, divisor = 255
#     rShaderInputLayoutElementType_FS8 = 10, // guess,  8 bit normalized compressed float, divisor = 127
#     rShaderInputLayoutElementType_11_11_11_10 = 11, // guess, 4 bytes, used for normals
#     rShaderInputLayoutElementType_RGB = 13, // guess, 1 byte, used for colors without alpha
#     rShaderInputLayoutElementType_RGBA = 14, // guess
# } rShaderInputLayoutElementType;

def convertInputTypeToRPGEODATA( t ):
    if t == 1: return noesis.RPGEODATA_FLOAT
    if t == 2: return noesis.RPGEODATA_HALFFLOAT
    if t == 3: return noesis.RPGEODATA_USHORT
    #if t == 4: return noesis.RPGEODATA_HALFFLOAT
    if t == 5: return noesis.RPGEODATA_SHORT
    if t == 7: return noesis.RPGEODATA_BYTE
    if t == 8: return noesis.RPGEODATA_UBYTE
    if t == 9: return noesis.RPGEODATA_UBYTE
    if t == 10: return noesis.RPGEODATA_BYTE
    if t == 11: return noesis.RPGEODATA_UBYTE # 11_11_11_10
    if t == 13: return noesis.RPGEODATA_BYTE
    if t == 14: return noesis.RPGEODATA_BYTE
    raise Exception("Unknown input type: " + str(t))
       
def tryBindShaderInput( shaderInfo, name, func, vertexBuffer, stride, useCount = False ):
    if shaderInfo.hasInput(name):
        inputInfos = shaderInfo.getInput( name )
        for inputInfo in inputInfos:
            print( "input name: " + inputInfo.name )
            print( "input type: " + str( inputInfo.type ) )
            if not useCount: func( vertexBuffer, convertInputTypeToRPGEODATA( inputInfo.type ), stride, inputInfo.offset )
            else:            func( vertexBuffer, convertInputTypeToRPGEODATA( inputInfo.type ), stride, inputInfo.offset, inputInfo.componentCount )

def rebaseIndexBuffer( model, primitive, indexReadStream ):
    '''
    fix index buffer for drawing by subtracting the vertex start index from the indices
    '''
    indexStart = ( primitive.indexBufferOffset + primitive.indexStartIndex ) * 2
    indexEnd = indexStart + ( primitive.indexCount * 2 )
    indexReadStream.seek( indexStart )
    indexWriteStream = NoeBitStream()
    badIdx = -1
    for i in range(primitive.indexCount):
        idx = indexReadStream.readUShort()
        fixedIdx = idx - primitive.vertexStartIndex
        assert( idx >= 0 )
        if (fixedIdx < 0):
            badIdx = i
        indexWriteStream.writeUShort( fixedIdx )
    if badIdx != -1: print("Bad indices at " + str(badIdx) + " indexStart: " + str(indexStart) + " vertexStartIndex: " + str(primitive.vertexStartIndex))
    indexBufferBytes = indexWriteStream.getBuffer()
    return indexBufferBytes

def fixTextureMapPath( basePath, path ):
    return basePath + '/' + os.path.basename(path) + ".241f5deb.dds"

def getTextureAssignedToSlot( mat, cmdName, basePath ):
    textureName = ""
    for cmd in mat.cmds:
        if cmd.type == 'texture':
            if cmd.name == cmdName:
                textureName = cmd.data
                break
        if textureName != "":
            break
        
    if textureName == "":
        return ""
    else:
        return fixTextureMapPath( basePath, textureName )

def getMaterialByName( mtl, materialName ):
    for material in mtl.materials:
        if material.name == materialName:
            return material
    return None

DEBUG_INVERSE_BIND_MATRIX = False

def modLoadModel(data, mdlList):
    ctx = rapi.rpgCreateContext()
    
    baseName = os.path.basename(rapi.getInputName()).split('.')[0]
    basePath = os.path.dirname(rapi.getInputName())
    
    model = rModelData()
    model.read(NoeBitStream(data))
    mvc3materialnamedb.registerMaterialNames( model.materials )
    
    mtl = imMaterialLib()
    mrlName, _ = util.getExtractedResourceFilePath( basePath + '/' + baseName, '2749c8a8', 'mrl' )
    if mrlName != None and os.path.exists( mrlName ):
        mtl.loadBinaryStream(NoeBitStream(rapi.loadIntoByteArray(mrlName)))
        mtl.saveYamlFile( mrlName + '.yml' )
    
    #scale = NoeVec3( ( 1, 1, 1 ) )
    #if len( model.joints ) > 0:
    #    scale = NoeVec3( ( model.jointInvBindMtx[0][0][0], model.jointInvBindMtx[0][1][1], model.jointInvBindMtx[0][2][2] ) ) 
    #    
    #rapi.rpgSetPosScaleBias( NoeVec3( ( 1, 1, 1 ) ), model.header.min )
    
    # set model transform
    # restore bind pose (undo world transform & reapply local transform)
    modelMtx = NoeMat44()
    if len( model.joints ) > 0:
        modelMtx = model.jointInvBindMtx[0] * model.jointLocalMtx[0]
        rapi.rpgSetTransform( modelMtx.toMat43() )
        
    # build materials
    noeMatList = []    
    noeTexList = []
    for modelMaterialIndex in range(len(model.materials)):
        # create material
        materialName = model.materials[modelMaterialIndex]
        material = getMaterialByName( mtl, materialName )
        if material == None:
            print( "model references material {} that does not exist in the mrl".format( materialName ) )
            
        albedoMap = None 
        specularMap = None
        normalMap = None
        if material != None:
            albedoMap = getTextureAssignedToSlot( material, 'tAlbedoMap', basePath )
            specularMap = getTextureAssignedToSlot( material, 'tSpecularMap', basePath )
            normalMap = getTextureAssignedToSlot( material, 'tNormalMap', basePath )
        
        noeMat = NoeMaterial( materialName, albedoMap )
        noeMat.setSpecularTexture( specularMap )
        noeMat.setNormalTexture( normalMap )
        noeMat.flags2 |= noesis.NMATFLAG2_PREFERPPL
        #flip gloss into roughness
        glossScale = 0.3
        defaultSpec = 0.1
        #noeMat.setSpecularColor((defaultSpec, defaultSpec, defaultSpec, 1.0))
        noeMat.pbrFresnelScale = defaultSpec
        noeMat.setRoughness(-glossScale, 1.0)				
        #noeMat.setEnvTexture(noesis.getScenesPath() + "sample_pbr_e4.dds")
        noeMatList.append(noeMat)
    
    # build model meshes
    indexBs = NoeBitStream(model.indexBuffer)
    primitiveJointLinkIdx = 0
    for i in range(len(model.primitives)):
        print("loading primitive " + str(i))
        primitive = model.primitives[i]
        shaderInfo = mvc3shaderdb.shaderObjectsByHash[ primitive.vertexShader.getHash() ]
        print("shader name: " + shaderInfo.name)
        
        materialIndex = primitive.indices.getMaterialIndex()
        meshName = 'prm_{}'.format( i )
        meshName += '_@SDR({})'.format( shaderInfo.name )
        if primitive.flags != 0xFFFF:
            meshName += '_@TYP({})'.format( primitive.flags )
        if primitive.indices.getLodIndex() != 0xFF:
            meshName += '_@LOD({})'.format( primitive.indices.getLodIndex() )
        #if not ( primitive.flags == 33 and primitive.flags2 == 0 ):
        meshName += "_@FLG({})".format( primitive.vertexFlags )
        #if primitive.renderMode != 67:
        meshName += "_@RM({})".format( primitive.renderFlags )
        meshName += "_@JNT({})".format(primitive.indices.getGroupId())
        meshName += "_@ID({})".format( primitive.id )

        rapi.rpgSetName( meshName )
        rapi.rpgSetMaterial( noeMatList[materialIndex].name )

        # decode vertex buffer
        vertexStart = primitive.vertexBufferOffset + (primitive.vertexStartIndex * primitive.vertexStride)
        vertexEnd = vertexStart + (primitive.vertexCount * primitive.vertexStride)
        vertexBuffer = model.vertexBuffer[vertexStart:vertexEnd]
        decVertexBuffer, decStride, decInputs = vertexcodec.decodeVertexBuffer( shaderInfo, vertexBuffer, primitive.vertexCount, primitive.vertexStride )       
        for inputName, inputOffset, inputComponentCount in decInputs:
            if   inputName == "Position":     rapi.rpgBindPositionBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )
            elif inputName == "Normal":       rapi.rpgBindNormalBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )  
            elif inputName == "Joint":        rapi.rpgBindBoneIndexBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset, inputComponentCount )  
            elif inputName == "Weight":       rapi.rpgBindBoneWeightBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset, inputComponentCount )
            elif inputName == "UV_Primary":   rapi.rpgBindUV1BufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )
            elif inputName == "UV_Secondary": rapi.rpgBindUV2BufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )
 
        indexBufferBytes = rebaseIndexBuffer( model, primitive, indexBs )
            
        rapi.rpgCommitTriangles( indexBufferBytes, noesis.RPGEODATA_SHORT, primitive.indexCount, noesis.RPGEO_TRIANGLE, 1 )
        rapi.rpgClearBufferBinds()
        primitiveJointLinkIdx += primitive.primitiveJointLinkCount

    mdl = rapi.rpgConstructModel()                                                          
    
    if len( model.joints ) > 0:
        # build bones
        noeBones = []
        for i in range(len(model.joints)):
            joint = model.joints[i]
            
            symmetryId = -1
            if joint.symmetryIndex != 255:
                symmetryId = model.joints[ joint.symmetryIndex ].id
                
            name = "bone_{}_sym_{}".format( joint.id, symmetryId )
            
            jointInfo = jointInfoDb.getJointInfoById( joint.id )
            #name = jointInfo.name if jointInfo != None else jointInfoDb.getDefaultJointName( joint.id )
            #print(name)
            matrix = model.jointLocalMtx[i]
            
            if DEBUG_INVERSE_BIND_MATRIX:
                matrix = ( model.jointInvBindMtx[i] ) # model-to-world space conversion
                
            #print(matrix)
            
            parent = -1
            if ( joint.parentIndex != 255 ):
                parent = joint.parentIndex
                
                if DEBUG_INVERSE_BIND_MATRIX:
                    matrix *= model.jointInvBindMtx[i]
                
            if DEBUG_INVERSE_BIND_MATRIX:
                # undo transform
                parent = -1
            
            noeBone = NoeBone(i, name, matrix.toMat43(), None, parent)
            noeBones.append(noeBone)
        
        noeBones = rapi.multiplyBones(noeBones)
        mdl.setBones(noeBones)
    mdl.setModelMaterials(NoeModelMaterials(noeTexList, noeMatList))
    
    mdlList.append(mdl)
    rapi.rpgClearBufferBinds()
    return 1

def modWriteModel( mdl, bs ):
    inputName = rapi.getInputName()
    inputBaseName = os.path.basename( inputName ).split('.')[0]
    inputBasePath = os.path.dirname( inputName )
    inputMrlYamlPath = inputBasePath + '/' + inputBaseName + ".mrl.yml"
    print( inputMrlYamlPath )
    
    outputName = rapi.getOutputName()
    outputBaseName = os.path.basename( outputName ).split('.')[0]
    outputBasePath = os.path.dirname( outputName )
    outputMrlPath = outputBasePath + '/' + outputBaseName + ".2749c8a8.mrl"
    
    mrl = imMaterialLib()
    if rapi.checkFileExists( inputMrlYamlPath ):
        mrl.loadYamlFile( inputMrlYamlPath )
    
    imMod = imModel()
    for m in mdl.meshes:
        im = imPrimitive()
        im.name = m.name
        im.matName = m.matName
        im.positions = m.positions
        im.tangents = []
        for t in m.tangents:
            im.tangents.append(t[0])
        
        im.normals = m.normals
        im.uvs = m.uvs
        im.weights = m.weights
        im.indices = m.indices
        imMod.primitives.append( im )
        
    for b in mdl.bones:
        ib = imJoint()
        ib.name = b.name
        ib.worldMtx = b.getMatrix().toMat44()
        ib.parentIndex = b.parentIndex
        imMod.joints.append( ib )
     
    # save mod
    ogmod = None
    ogmod = rModelData()  
    ogmod.read( NoeBitStream(rapi.loadIntoByteArray("X:/projects/umvc3_model/samples/UMVC3ModelSamples/Ryu/Ryu.58a15856.mod") ) )
    mod = imMod.toBinaryModel( ogmod ) 
    mod.write( bs )
    
    # save mrl
    mrl.saveBinaryFile( outputMrlPath )
    
    return 1