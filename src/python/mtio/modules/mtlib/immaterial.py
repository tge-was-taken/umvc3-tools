'''
Intermediate material library representation for easier editing
'''
       
from argparse import ArgumentError
from dataclasses import dataclass
from email.policy import default
import os
from typing import List, Tuple
from venv import create
import yaml
from rmaterial import *
import mvc3materialnamedb
import mvc3shaderdb
from ncl import *
import log
              
class imConstantBufferCBMaterial:
    def __init__( self ):
        # todo
        pass

class imMaterialTextureInfo:
    def __init__( self ):
        self.type = ""
        self.path = ""
        
class imMaterialCmd:
    TYPES = ['flag', 'cbuffer', 'samplerstate', 'texture']
    
    def __init__( self, type="", name="", data=None ):
        self.type = type
        self.name = name
        self.data = data
        
@dataclass
class imMaterialInfo(object):
    DEFAULT_NORMAL_MAP: str = "default_NM"
    DEFAULT_ALBEDO_MAP: str = "default_BM"
    DEFAULT_SPECULAR_MAP: str = "default_MM"
    TEMPLATE_MATERIALS: Tuple[str] = (
        "nDraw::MaterialChar",
        "nDraw::MaterialCharAlpha",
        'nDraw::MaterialStgSimple',
        'nDraw::MaterialStdEst'
    )
    
    type: str = ''
    name: str = ''
    blendState: str = ''
    depthStencilState: str = ''
    rasterizerState: str = ''
    cmdListFlags: int = 0
    matFlags: int = 0
    cmds: List[imMaterialCmd] = None
    
    def __post_init__( self ):
        if self.cmds is None: self.cmds = []
        
    @staticmethod
    def isDefaultTextureMap( map ):
        imMaterialInfo()
        return os.path.basename( map ) in [imMaterialInfo.DEFAULT_NORMAL_MAP, imMaterialInfo.DEFAULT_ALBEDO_MAP, imMaterialInfo.DEFAULT_SPECULAR_MAP]
        
    @staticmethod
    def _createFromTemplate_MaterialChar( name = "default_material", normalMap=DEFAULT_NORMAL_MAP, albedoMap=DEFAULT_ALBEDO_MAP, specularMap=DEFAULT_SPECULAR_MAP ):
        mat = imMaterialInfo()
        mat.type = 'nDraw::MaterialChar'
        mat.name = name
        mat.blendState = 'BSSolid'
        mat.depthStencilState = 'DSZTestWriteStencilWrite'
        mat.rasterizerState = 'RSMesh'
        mat.cmdListFlags = 0x0
        mat.matFlags = 0x8c800803
        mat.cmds = [
            imMaterialCmd( 'flag', 'FVertexDisplacement', 'FVertexDisplacement' ),
            imMaterialCmd( 'flag', 'FUVTransformPrimary', 'FUVTransformPrimary' ),
            imMaterialCmd( 'flag', 'FUVTransformSecondary', 'FUVTransformSecondary' ),
            imMaterialCmd( 'flag', 'FUVTransformUnique', 'FUVTransformUnique' ),
            imMaterialCmd( 'flag', 'FUVTransformExtend', 'FUVTransformExtend' ),
            imMaterialCmd( 'flag', 'FBump', 'FBumpNormalMap' ),
            imMaterialCmd( 'texture', 'tNormalMap', normalMap ),
            imMaterialCmd( 'samplerstate', 'SSNormalMap', 'SSNormalMap' ),
            imMaterialCmd( 'flag', 'FUVNormalMap', 'FUVPrimary' ),
            imMaterialCmd( 'flag', 'FAlbedo', 'FAlbedoMap' ),
            imMaterialCmd( 'cbuffer', '$Globals', [
                0.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 1.0, 
                0.0, 0.6000000238418579, 0.009999999776482582, 1.0, 
                4.0, 64.0, 0.0, 0.0, 
                1.0, 1.0, 1.0, 0.0, 
                1.0, 1.0, 1.0, 0.10000000149011612, 
                1.0, 1.0, 0.0, 0.0, 
                0.0, 0.0, 0.05000000074505806, 0.05000000074505806, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 16.0, 
                0.5, 0.5, 0.5, 0.0, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 0.32899999618530273, 0.4746600091457367, 0.382999986410141, 
                0.0, 1.0, 0.0, 1.0, 
                0.33329999446868896, 1.0, 1.0, 0.20000000298023224, 
                1.0, 1.0, 1.0, 0.0, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 0.0, 0.0, 0.0,  ]),
            imMaterialCmd( 'texture', 'tAlbedoMap', albedoMap ),
            imMaterialCmd( 'samplerstate', 'SSAlbedoMap', 'SSAlbedoMap' ),
            imMaterialCmd( 'flag', 'FUVAlbedoMap', 'FUVPrimary' ),
            imMaterialCmd( 'flag', 'FShininess', 'FShininess' ),
            imMaterialCmd( 'flag', 'FLighting', 'FLighting' ),
            imMaterialCmd( 'flag', 'FBRDF', 'FToonShaderHigh' ),
            imMaterialCmd( 'cbuffer', 'CBToon2', [-0.3599950075149536, 80.0, 15.0, 0.0] ),
            imMaterialCmd( 'flag', 'FToonLightCalc', 'FToonLightCalc' ),
            imMaterialCmd( 'texture', 'tToonMap', 'UserShader\\toon_BM_HQ' ),
            imMaterialCmd( 'flag', 'FCalcRimLight', 'FCalcRimLight' ),
            imMaterialCmd( 'flag', 'FToonLightRevCalc', 'FToonLightRevCalc' ),
            imMaterialCmd( 'texture', 'tToonRevMap', 'UserShader\\toonRev_BM_HQ' ),
            imMaterialCmd( 'flag', 'FDiffuse', 'FDiffuseColorCorect' ),
            imMaterialCmd( 'cbuffer', 'CBDiffuseColorCorect', [1.2200000286102295, 0.0, 0.0, 0.0] ),
            imMaterialCmd( 'cbuffer', 'CBMaterial', [
                1.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 10.0, 
                1.0, 0.0, 0.0, 0.0, 
                0.0, 1.0, 0.0, 0.0, 
                1.0, 0.0, 0.0, 0.0, 
                0.0, 1.0, 0.0, 0.0, 
                1.0, 0.0, 0.0, 0.0, 
                0.0, 1.0, 0.0, 0.0, ]),
            imMaterialCmd( 'flag', 'FSpecular', 'FSpecularMaskToon' ),
            imMaterialCmd( 'texture', 'tSpecularMap', specularMap ),
            imMaterialCmd( 'samplerstate', 'SSSpecularMap', 'SSSpecularMap' ),
            imMaterialCmd( 'flag', 'FUVSpecularMap', 'FUVPrimary' ),
            imMaterialCmd( 'flag', 'FReflect', 'FReflect' ),
            imMaterialCmd( 'flag', 'FFresnel', 'FFresnel' ),
            imMaterialCmd( 'flag', 'FDistortion', 'FDistortion' ),
            imMaterialCmd( 'flag', 'FTransparency', 'FTransparency' ),
        ]
        return mat
    
    @staticmethod
    def _createFromTemplate_MaterialCharAlpha( name = "default_material", normalMap=DEFAULT_NORMAL_MAP, albedoMap=DEFAULT_ALBEDO_MAP, specularMap=DEFAULT_SPECULAR_MAP ):
        mat = imMaterialInfo(
            name=name,
            type="nDraw::MaterialCharAlpha",
            blendState="BSBlendAlpha",
            depthStencilState="DSZTestWriteStencilWrite",
            rasterizerState="RSMesh",
            cmdListFlags=0x0,
            matFlags=0x91900003,
            cmds=[
                imMaterialCmd("flag", "FVertexDisplacement", "FVertexDisplacement"),
                imMaterialCmd("flag", "FUVTransformPrimary", "FUVTransformPrimary"),
                imMaterialCmd("flag", "FUVTransformSecondary", "FUVTransformSecondary"),
                imMaterialCmd("flag", "FUVTransformUnique", "FUVTransformUnique"),
                imMaterialCmd("flag", "FUVTransformExtend", "FUVTransformExtend"),
                imMaterialCmd("flag", "FBump", "FBumpNormalMap"),
                imMaterialCmd("texture", "tNormalMap", normalMap ),
                imMaterialCmd("samplerstate", "SSNormalMap", "SSNormalMap"),
                imMaterialCmd("flag", "FUVNormalMap", "FUVPrimary"),
                imMaterialCmd("flag", "FAlbedo", "FAlbedoMap"),
                imMaterialCmd("cbuffer", "$Globals", [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.6000000238418579, 0.009999999776482582, 1.0, 4.0, 64.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.10000000149011612, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.05000000074505806, 0.05000000074505806, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 25.0, 0.5, 0.5, 0.5, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.32899999618530273, 0.4746600091457367, 0.382999986410141, 0.0, 1.0, 0.0, 1.0, 0.33329999446868896, 1.0, 1.0, 0.20000000298023224, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]),
                imMaterialCmd("texture", "tAlbedoMap", albedoMap ),
                imMaterialCmd("samplerstate", "SSAlbedoMap", "SSAlbedoMap"),
                imMaterialCmd("flag", "FUVAlbedoMap", "FUVPrimary"),
                imMaterialCmd("flag", "FTransparency", "FTransparencyAlpha"),
                imMaterialCmd("cbuffer", "CBMaterial", [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 10.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]),
                imMaterialCmd("flag", "FShininess", "FShininess"),
                imMaterialCmd("flag", "FLighting", "FLighting"),
                imMaterialCmd("flag", "FBRDF", "FToonShader"),
                imMaterialCmd("flag", "FToonLightCalc", "FToonLightCalc"),
                imMaterialCmd("texture", "tToonMap", "UserShader\\toon_BM_HQ"),
                imMaterialCmd("flag", "FCalcRimLight", "FCalcRimLight"),
                imMaterialCmd("flag", "FToonLightRevCalc", "FToonLightRevCalc"),
                imMaterialCmd("texture", "tToonRevMap", "UserShader\\toonRev_BM_HQ"),
                imMaterialCmd("flag", "FDiffuse", "FDiffuseColorCorect"),
                imMaterialCmd("cbuffer", "CBDiffuseColorCorect", [1.2200000286102295, 0.0, 0.0, 0.0]),
                imMaterialCmd("flag", "FSpecular", "FSpecularMaskToon"),
                imMaterialCmd("texture", "tSpecularMap", specularMap ),
                imMaterialCmd("samplerstate", "SSSpecularMap", "SSSpecularMap"),
                imMaterialCmd("flag", "FUVSpecularMap", "FUVPrimary"),
                imMaterialCmd("flag", "FReflect", "FReflect"),
                imMaterialCmd("flag", "FFresnel", "FFresnel"),
                imMaterialCmd("flag", "FDistortion", "FDistortion"),
            ]
        )
        return mat
    
    @staticmethod
    def _createFromTemplate_MaterialStgSimple( name = "default_material", normalMap=DEFAULT_NORMAL_MAP, albedoMap=DEFAULT_ALBEDO_MAP, specularMap=DEFAULT_SPECULAR_MAP ):
        mat = imMaterialInfo()
        mat.type = 'nDraw::MaterialStgSimple'
        mat.name = name
        mat.blendState = 'BSSolid'
        mat.depthStencilState = 'DSZTestWrite'
        mat.rasterizerState = 'RSMesh'
        mat.cmdListFlags = 0x20000
        mat.matFlags = 0x8c800000
        mat.cmds = [
            imMaterialCmd( 'flag', 'FVertexDisplacement', 'FVertexDisplacement' ),
            imMaterialCmd( 'flag', 'FUVTransformPrimary', 'FUVTransformOffset' ),
            imMaterialCmd( 'cbuffer', 'CBMaterial', [
                1.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 10.0, 
                1.0, -0.0, 0.0, 0.0, 
                0.0, 1.0, 0.0, 0.0, 
                1.0, 0.0, 0.0, 0.0, 
                0.0, 1.0, 0.0, 0.0, 
                1.0, 0.0, 0.0, 0.0, 
                0.0, 1.0, 0.0, 0.0,                 
            ]),
            imMaterialCmd( 'flag', 'FUVTransformSecondary', 'FUVTransformSecondary' ),
            imMaterialCmd( 'flag', 'FUVTransformUnique', 'FUVTransformUnique' ),
            imMaterialCmd( 'flag', 'FUVTransformExtend', 'FUVTransformExtend' ),
            imMaterialCmd( 'flag', 'FOcclusion', 'FOcclusion' ),
            imMaterialCmd( 'flag', 'FAlbedo', 'FAlbedo' ),      
            imMaterialCmd( 'cbuffer', '$Globals', [
                0.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 1.0, 
                0.0, 0.6000000238418579, 0.009999999776482582, 1.0, 
                4.0, 64.0, 0.0, 0.0, 
                1.0, 1.0, 1.0, 0.0, 
                1.0, 1.0, 1.0, 0.10000000149011612, 
                1.0, 1.0, 0.0, 0.0, 
                0.0, 0.0, 0.05000000074505806, 0.05000000074505806, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 1.0, 1.0, 16.0, 
                0.5, 0.5, 0.5, 0.0, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 0.32899999618530273, 0.4746600091457367, 0.382999986410141, 
                0.0, 1.0, 0.0, 1.0, 
                0.33329999446868896, 1.0, 1.0, 0.20000000298023224, 
                1.0, 1.0, 1.0, 0.0, 
                1.0, 1.0, 1.0, 1.0, 
                1.0, 0.0, 0.0, 0.0,                
            ]),   
            imMaterialCmd( 'texture', 'tAlbedoMap', albedoMap ),
            imMaterialCmd( 'samplerstate', 'SSAlbedoMap', 'SSAlbedoMap' ),
            imMaterialCmd( 'flag', 'FUVAlbedoMap', 'FUVPrimary' ),
            imMaterialCmd( 'flag', 'FTransparency', 'FTransparency' ),
            imMaterialCmd( 'flag', 'FDiffuse', 'FDiffuseConstant' ),
            imMaterialCmd( 'flag', 'FBump', 'FBump' ),
            imMaterialCmd( 'flag', 'FShininess', 'FShininess' ),
        ]
        return mat
    
    @staticmethod
    def _createFromTemplate_MaterialStdEst( name = "default_material", normalMap=DEFAULT_NORMAL_MAP, albedoMap=DEFAULT_ALBEDO_MAP, specularMap=DEFAULT_SPECULAR_MAP ):
        mat = imMaterialInfo(
            name=name,
            type="nDraw::MaterialStdEst",
            blendState="BSBlendAlpha",
            depthStencilState="DSZTestWrite",
            rasterizerState="RSMesh",
            cmdListFlags=0x0,
            matFlags=0x91900000,
            cmds=[
                imMaterialCmd("flag", "FVertexDisplacement", "FVertexDisplacement"),
                imMaterialCmd("flag", "FUVTransformPrimary", "FUVTransformOffset"),
                imMaterialCmd("cbuffer", "CBMaterial", [1.0, 1.0, 1.0, 1.0, 0.2479339987039566, 0.2479339987039566, 0.2479339987039566, 10.0, 1.0, -0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, -0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]),
                imMaterialCmd("flag", "FUVTransformSecondary", "FUVTransformOffset2"),
                imMaterialCmd("flag", "FUVTransformUnique", "FUVTransformUnique"),
                imMaterialCmd("flag", "FUVTransformExtend", "FUVTransformExtend"),
                imMaterialCmd("flag", "FOcclusion", "FOcclusion"),
                imMaterialCmd("flag", "FBump", "FBumpNormalMap"),
                imMaterialCmd("texture", "tNormalMap", normalMap ),
                imMaterialCmd("samplerstate", "SSNormalMap", "SSNormalMap"),
                imMaterialCmd("flag", "FUVNormalMap", "FUVPrimary"),
                imMaterialCmd("flag", "FAlbedo", "FAlbedoMap"),
                imMaterialCmd("cbuffer", "$Globals", [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.6000000238418579, 0.009999999776482582, 1.0, 4.0, 64.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.10000000149011612, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.05000000074505806, 0.05000000074505806, 1.0, 1.0, 1.0, 1.0, 0.40229499340057373, 0.2695620059967041, 0.22580400109291077, 16.0, 0.5, 0.5, 0.5, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.32899999618530273, 0.4746600091457367, 0.382999986410141, 0.0, 1.0, 0.0, 1.0, 0.33329999446868896, 1.0, 1.0, 0.20000000298023224, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
                imMaterialCmd("texture", "tAlbedoMap", albedoMap ),
                imMaterialCmd("samplerstate", "SSAlbedoMap", "SSAlbedoMap"),
                imMaterialCmd("flag", "FUVAlbedoMap", "FUVPrimary"),
                imMaterialCmd("flag", "FTransparency", "FTransparencyAlpha"),
                imMaterialCmd("flag", "FShininess", "FShininess"),
                imMaterialCmd("flag", "FLighting", "FLighting"),
                imMaterialCmd("flag", "FBRDF", "FBRDF"),
                imMaterialCmd("flag", "FDiffuse", "FDiffuse"),
                imMaterialCmd("flag", "FAmbient", "FAmbient"),
                imMaterialCmd("flag", "FSpecular", "FSpecularMap"),
                imMaterialCmd("flag", "FReflect", "FReflectGlobalCubeMap"),
                imMaterialCmd("samplerstate", "SSEnvMap", "SSEnvMap"),
                imMaterialCmd("texture", "tSpecularMap", specularMap ),
                imMaterialCmd("samplerstate", "SSSpecularMap", "SSSpecularMap"),
                imMaterialCmd("flag", "FUVSpecularMap", "FUVPrimary"),
                imMaterialCmd("flag", "FChannelSpecularMap", "FChannelSpecularMap"),
                imMaterialCmd("flag", "FFresnel", "FFresnelLegacy"),
                imMaterialCmd("flag", "FEmission", "FEmission"),
                imMaterialCmd("flag", "FDistortion", "FDistortion"),
            ]
        )
        return mat
    
    @staticmethod
    def createFromTemplate( type: str, name: str = "default_material", normalMap: str=DEFAULT_NORMAL_MAP, albedoMap: str=DEFAULT_ALBEDO_MAP, specularMap:str =DEFAULT_SPECULAR_MAP ):
        createFunc = getattr( imMaterialInfo, '_createFromTemplate_' + type.replace( "nDraw::", "" ), None )
        if createFunc == None:
            raise ArgumentError( message=type )
        
        return createFunc( name, 
                          normalMap=normalMap, 
                          albedoMap=albedoMap, 
                          specularMap=specularMap )
    
    def fixTextureMapPath( self, basePath, path ):
        return basePath + '/' + os.path.basename(path) + ".241f5deb.dds"

    def getCommandByName( self, cmdName ):
        for cmd in self.cmds:
            if cmd.name == cmdName:
                return cmd
        return None

    def getTextureAssignedToSlot( self, cmdName ):
        for cmd in self.cmds:
            if cmd.type == 'texture':
                if cmd.name == cmdName:
                    return cmd.data
        return None
    
    def iterTextures( self ):
        for cmd in self.cmds:
            if cmd.type == 'texture':
                yield cmd.data
                        
class imMaterialLib:
    VERSION = 1
    
    def __init__( self ):
        self.textures: List[imMaterialTextureInfo] = []
        self.materials: List[imMaterialInfo] = []
     
    def loadBinaryFile( self, path ):
        self.loadBinaryStream( NclBitStream( util.loadIntoByteArray( path ) ) )
        
    def loadBinaryStream( self, stream ):
        reader = rMaterialStreamReader( stream )
        header = reader.getHeader()
        assert( util.u32( header.hash ) == util.u32( 0xE588940A ) )
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
                matInfo.name = mvc3materialnamedb.getMaterialName( binMatInfo.nameHash )
            except Exception as e:
                log.error("unknown material name hash: {}".format( hex( binMatInfo.nameHash ) ) )
                matInfo.name = '_' + hex( binMatInfo.nameHash )
                
            matInfo.blendState = mvc3shaderdb.shaderObjectsByHash[ binMatInfo.blendState.getHash() ].name
            matInfo.depthStencilState = mvc3shaderdb.shaderObjectsByHash[ binMatInfo.depthStencilState.getHash() ].name
            matInfo.rasterizerState = mvc3shaderdb.shaderObjectsByHash[ binMatInfo.rasterizerState.getHash() ].name
            matInfo.cmdListFlags = binMatInfo.cmdListInfo.getFlags()
            matInfo.matFlags = binMatInfo.flags

            for binMatCmd in reader.iterMaterialCmd( binMatInfo ):
                matCmd = imMaterialCmd()
                matCmd.type = imMaterialCmd.TYPES[ binMatCmd.info.getType() ]
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
            f.write( "        cmdListFlags: {}\n".format( util.hex32( mat.cmdListFlags ) ) )
            f.write( "        matFlags: {}\n".format( util.hex32( mat.matFlags ) ) )
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
        if os.path.dirname( path ) != '':
            os.makedirs( os.path.dirname( path ), exist_ok=True )     
        with open( path, "w" ) as f:
            self.saveYamlIO( f )

    def loadYamlString( self, yamlText ):
        self.textures: List[imMaterialTextureInfo] = []
        self.materials: List[imMaterialInfo] = []
        
        yamlObj = yaml.load( yamlText, Loader=yaml.FullLoader )
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
                    if yamlMat["cmds"] is not None:
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
            binMatInfo.typeHash = util.computeHash( matInfo.type ) & ~0x80000000
            
            if matInfo.name.startswith( "_0x" ):
                binMatInfo.nameHash = int( matInfo.name[1:], 16 )
            else:
                binMatInfo.nameHash = util.computeHash( matInfo.name )     
            
            binMatInfo.blendState = util.getShaderObjectIdFromName( matInfo.blendState )
            binMatInfo.depthStencilState = util.getShaderObjectIdFromName( matInfo.depthStencilState )
            binMatInfo.rasterizerState = util.getShaderObjectIdFromName( matInfo.rasterizerState )
            binMatInfo.cmdListInfo.setFlags( matInfo.cmdListFlags )
            binMatInfo.flags = matInfo.matFlags   
              
            writer.beginMaterialInfo( binMatInfo )
            for cmd in matInfo.cmds:
                binCmd = rMaterialCmd()
                binCmd.shaderObjectId = util.getShaderObjectIdFromName( cmd.name )
                binCmd.info.setType( imMaterialCmd.TYPES.index( cmd.type ) )
                binCmd.info.setShaderObjectIndex( binCmd.shaderObjectId.getIndex() )
                
                binCmdData = None
                if cmd.type == 'texture':
                    if cmd.data == None or len( cmd.data ) == 0:
                        binCmdData = 0
                    else:
                        binCmdData = ( 1 + ( texturePathToIndex[ cmd.data ] ) )
                elif cmd.type in ['flag', 'samplerstate']:
                    binCmdData = util.getShaderObjectIdFromName( cmd.data )
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
    
    def updateTextureList( self ):
        texturePathSet = set()
        for t in self.textures:
            texturePathSet.add( t.path )
        
        for m in self.materials:
            for cmd in m.cmds:
                if cmd.type == 'texture' and cmd.data != None and len( cmd.data ) > 0 and not cmd.data in texturePathSet:
                    tex = imMaterialTextureInfo()
                    tex.path = cmd.data
                    tex.type = 'rTexture'
                    texturePathSet.add( tex.path )
                    self.textures.append( tex )