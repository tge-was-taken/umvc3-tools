# high level/intermediate material representation for serialization    
       
import os
import yaml
from mtrmaterial import *
import mvc3materialdb
import mvc3shaderdb
from mtncl import *
              
class imConstantBufferCBMaterial:
    def __init__( self ):
        # todo
        pass

class imMaterialTextureInfo:
    def __init__( self ):
        self.type = ""
        self.path = ""
        
class imMaterialCmd:
    Types = ['flag', 'cbuffer', 'samplerstate', 'texture']
    
    def __init__( self ):
        self.type = ""
        self.name = ""
        self.data = None
        
class imMaterialInfo:
    def __init__( self ):
        self.type = ""
        self.name = ""
        self.blendState = ""
        self.depthStencilState = ""
        self.rasterizerState = ""
        self.cmdListFlags = 0
        self.matFlags = 0
        self.cmds = []
        
    @staticmethod
    def createDefault( self ):
        pass
    
    def fixTextureMapPath( self, basePath, path ):
        return basePath + '/' + os.path.basename(path) + ".241f5deb.dds"

    def getTextureAssignedToSlot( self, cmdName ):
        for cmd in self.cmds:
            if cmd.type == 'texture':
                if cmd.name == cmdName:
                    return cmd.data
        return ""
        
class imMaterialLib:
    VERSION = 1
    
    def __init__( self ):
        self.textures = []
        self.materials = []
        
    def loadBinary( self, stream ):
        reader = rMaterialStreamReader( stream )
        header = reader.getHeader()
        assert( mtutil.u32( header.hash ) == mtutil.u32( 0xE588940A ) )
        assert( header.field14 == 0 )
        
        for binTexInfo in reader.iterTextureInfo():
            assert( binTexInfo.field04 == 0 )
            assert( binTexInfo.field08 == 0 )
            assert( binTexInfo.field0c == 0 )
            assert( binTexInfo.field10 == 0 )
            assert( binTexInfo.field14 == 0 )
            
            texInfo = imMaterialTextureInfo()
            texInfo.type = mvc3types.getTypeName( binTexInfo.typeHash )
            texInfo.path = binTexInfo.path  
            self.textures.append( texInfo )
            
        for binMatInfo in reader.iterMaterialInfo():
            assert( binMatInfo.field04 == 0 )
            #assert( binMatInfo.cmdListInfo.getFlags() == 0 )
            assert( binMatInfo.field24 == 0 )
            assert( binMatInfo.field28 == 0 )
            assert( binMatInfo.field2c == 0 )
            assert( binMatInfo.field30 == 0 )
            
            matInfo = imMaterialInfo()
            matInfo.type = mvc3types.getTypeName( binMatInfo.typeHash )

            try:
                matInfo.name = mvc3materialdb.getName( binMatInfo.nameHash )
            except:
                print("unknown material name hash: {}".format( hex( binMatInfo.nameHash ) ) )
                matInfo.name = '_' + hex( binMatInfo.nameHash )
                
            matInfo.blendState = mvc3shaderdb.shaderObjectsByHash[ binMatInfo.blendState.getHash() ].name
            matInfo.depthStencilState = mvc3shaderdb.shaderObjectsByHash[ binMatInfo.depthStencilState.getHash() ].name
            matInfo.rasterizerState = mvc3shaderdb.shaderObjectsByHash[ binMatInfo.rasterizerState.getHash() ].name
            matInfo.cmdListFlags = binMatInfo.cmdListInfo.getFlags()
            matInfo.matFlags = binMatInfo.flags

            for binMatCmd in reader.iterMaterialCmd( binMatInfo ):
                matCmd = imMaterialCmd()
                matCmd.type = imMaterialCmd.Types[ binMatCmd.info.getType() ]
                matCmd.name = mvc3shaderdb.shaderObjectsByHash[ binMatCmd.shaderObjectId.getHash() ].name
                matCmd.data = reader.getMaterialCmdData( binMatInfo, binMatCmd )
                assert( matCmd.data != None )
                if matCmd.type == 'texture':
                    if matCmd.data > 0:
                        matCmd.data = self.textures[ matCmd.data - 1 ].path
                    else:
                        matCmd.data = ""
                elif matCmd.type in ['flag', 'samplerstate']:
                    matCmd.data = mvc3shaderdb.shaderObjectsByHash[ matCmd.data.getHash() ].name
                elif matCmd.type != 'cbuffer':
                    raise Exception("unhandled material cmd type: {}".format( matCmd.type ) )
                    
                matInfo.cmds.append( matCmd )
            self.materials.append( matInfo )
            
    def _needsExplicitTextureList( self ):
        needsTextureList = False
        for tex in self.textures:
            if tex.type != 'rTexture':
                needsTextureList = True
                break
            
        referencedTextures = set()
        for mat in self.materials:
            for cmd in mat.cmds:
                if cmd.type == 'texture':
                    if cmd.data != None and len( cmd.data ) > 0:
                        referencedTextures.add( cmd.data )
            
        if len( referencedTextures ) != len( self.textures ):
            needsTextureList = True
            
        return needsTextureList
                    
    def saveYamlIO( self, f ):
        def sanitize( s ):
            return s
        
        f.write("version: {}\n".format(imMaterialLib.VERSION))
        
        if self._needsExplicitTextureList():
            f.write("textures:\n")
            for tex in self.textures:
                f.write( "    - {}:\n".format( sanitize( tex.path ) ) )
                f.write( "        type: {}\n".format( sanitize( tex.type ) ) )
            
        f.write("materials:\n")
        for mat in self.materials:
            f.write( "    - {}:\n".format( sanitize( mat.name ) ) )
            f.write( "        type: {}\n".format( sanitize( mat.type ) ) )
            f.write( "        blendState: {}\n".format( sanitize( mat.blendState ) ) )
            f.write( "        depthStencilState: {}\n".format( sanitize( mat.depthStencilState ) ) )
            f.write( "        rasterizerState: {}\n".format( sanitize( mat.rasterizerState ) ) )
            f.write( "        cmdListFlags: {}\n".format( mtutil.hex32( mat.cmdListFlags ) ) )
            f.write( "        matFlags: {}\n".format( mtutil.hex32( mat.matFlags ) ) )
            f.write( "        cmds:\n")
            for cmd in mat.cmds:
                if cmd.type == 'cbuffer' and len( cmd.data ) > 4 and len( cmd.data ) % 4 == 0:
                    f.write( "            - [ {}, {}, [\n".format( cmd.type, sanitize( cmd.name ) ) )
                    for i in range(0, len(cmd.data), 4):
                        f.write( "                {}, {}, {}, {}, \n".format(cmd.data[i], cmd.data[i+1], cmd.data[i+2], cmd.data[i+3]) )
                    f.write( "              ]]\n")
                else:
                    f.write( "            - [ {}, {}, {} ]\n".format( cmd.type, sanitize( cmd.name ), sanitize( cmd.data ) ) )
    
    def saveYamlFile( self, path ):
        with open( path, "w" ) as f:
            self.saveYamlIO( f )

    def loadYamlString( self, yamlText ):
        self.textures = []
        self.materials = []
        
        yamlObj = yaml.load( yamlText )
        if yamlObj['version'] > imMaterialLib.VERSION:
            raise Exception('unsupported material library version: {}'.format(yamlObj['version']))
        
        # version 1
        texturePathSet = set()
        if 'textures' in yamlObj and yamlObj['textures'] != None:
            for yamlTexDict in yamlObj[ 'textures' ]:
                for yamlTexName, yamlTex in yamlTexDict.items():
                    tex = imMaterialTextureInfo()
                    tex.path = yamlTexName
                    tex.type = yamlTex[ "type" ]
                    texturePathSet.add( tex.path )
                    self.textures.append( tex )
        
        if 'materials' in yamlObj and yamlObj['materials'] != None:
            for yamlMatDict in yamlObj[ 'materials' ]:
                for yamlMatName, yamlMat in yamlMatDict.items():
                    mat = imMaterialInfo()
                    mat.name = yamlMatName
                    mat.type = yamlMat[ "type" ]
                    mat.blendState = yamlMat[ "blendState" ]
                    mat.depthStencilState = yamlMat[ "depthStencilState" ]
                    mat.rasterizerState = yamlMat[ "rasterizerState" ]
                    mat.cmdListFlags = yamlMat[ "cmdListFlags" ]
                    mat.matFlags = yamlMat[ "matFlags" ]
                    mat.cmds = []
                    for yamlCmd in yamlMat[ "cmds" ]:
                        cmd = imMaterialCmd()
                        cmd.type = yamlCmd[0]
                        cmd.name = yamlCmd[1]
                        cmd.data = None
                        if len( yamlCmd ) > 2:
                            cmd.data = yamlCmd[2]
                            
                        if cmd.type == 'texture' and cmd.data != None and len( cmd.data ) > 0 and not cmd.data in texturePathSet:
                            tex = imMaterialTextureInfo()
                            tex.path = cmd.data
                            tex.type = 'rTexture'
                            texturePathSet.add( tex.path )
                            self.textures.append( tex )
                            
                        mat.cmds.append( cmd )
                    self.materials.append( mat )

    def loadYamlIO( self, f ):
        yamlText = f.read()
        self.loadYamlString( yamlText )

    def loadYamlFile( self, path ):
        with open( path, "r" ) as f:
            self.loadYamlIO( f )
            
    def saveBinaryFile( self, path ):
        with open( path, "wb" ) as f:
            stream = NclBitStream()
            self.saveBinaryStream( stream )
            f.write( stream.getBuffer() )
            
    def saveBinaryStream( self, stream ):
        writer = rMaterialStreamWriter( stream )
        writer.setHash( 0xE588940A )
        writer.setField14( 0 )
        
        writer.beginTextureInfoList()
        texturePathToIndex = dict()
        for i, texInfo in enumerate( self.textures ):
            texturePathToIndex[texInfo.path] = i            
            binTexInfo = rMaterialTextureInfo()
            binTexInfo.typeHash = mvc3types.getTypeHash( texInfo.type )
            binTexInfo.path = texInfo.path
            writer.addTextureInfo( binTexInfo )
        writer.endTextureInfoList()
        
        writer.beginMaterialInfoList()
        for matInfo in self.materials:
            binMatInfo = rMaterialInfo()
            binMatInfo.typeHash = mtutil.computeHash( matInfo.type ) & ~0x80000000
            
            if matInfo.name.startswith( "_0x" ):
                binMatInfo.nameHash = int( matInfo.name[1:], 16 )
            else:
                binMatInfo.nameHash = mtutil.computeHash( matInfo.name )     
            
            binMatInfo.blendState = mtutil.getShaderObjectIdFromName( matInfo.blendState )
            binMatInfo.depthStencilState = mtutil.getShaderObjectIdFromName( matInfo.depthStencilState )
            binMatInfo.rasterizerState = mtutil.getShaderObjectIdFromName( matInfo.rasterizerState )
            binMatInfo.cmdListInfo.setFlags( matInfo.cmdListFlags )
            binMatInfo.flags = matInfo.matFlags   
              
            writer.beginMaterialInfo( binMatInfo )
            for cmd in matInfo.cmds:
                binCmd = rMaterialCmd()
                binCmd.shaderObjectId = mtutil.getShaderObjectIdFromName( cmd.name )
                binCmd.info.setType( imMaterialCmd.Types.index( cmd.type ) )
                binCmd.info.setShaderObjectIndex( binCmd.shaderObjectId.getIndex() )
                
                binCmdData = None
                if cmd.type == 'texture':
                    if cmd.data == None or len( cmd.data ) == 0:
                        binCmdData = 0
                    else:
                        binCmdData = ( 1 + ( texturePathToIndex[ cmd.data ] ) )
                elif cmd.type in ['flag', 'samplerstate']:
                    binCmdData = mtutil.getShaderObjectIdFromName( cmd.data )
                elif cmd.type == 'cbuffer':
                    binCmdData = cmd.data
                else:
                    raise Exception( "unhandled material cmd type: {}".format( cmd.type ) )
                                
                writer.addMaterialCmd( binCmd, binCmdData )
            writer.endMaterialInfo()
        writer.endMaterialInfoList()
        
        writer.flush()
        
    def getMaterialByName( self, materialName ):
        for material in self.materials:
            if material.name == materialName:
                return material
        return None