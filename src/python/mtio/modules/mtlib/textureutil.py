import os

import util
from rtexture import *
import texconv
import log
from PIL import Image

def doesTextureUseAlpha( textureFilePath: str ) -> bool:
    fileName: str
    fileExt: str
    
    fileName, fileExt = os.path.splitext( textureFilePath )
    fileExt = fileExt.lower()
    
    if fileExt == '.dds':
        # if it's a dds, load it and determine if it uses a known encoding
        # that supports alpha
        dds = DDSFile.fromFile( textureFilePath )
        if dds.header.ddspf.dwFourCC in [DDS_FOURCC_DXT2, DDS_FOURCC_DXT3, DDS_FOURCC_DXT4, DDS_FOURCC_DXT5]:
            return True
        else:
            # likely DXT1 or other
            return False
    else:
        try:
            im = Image.open( textureFilePath )
            return im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
        except Exception as e:
            # failed to load the image, so assume it uses alpha as to not lose any potential 
            # alpha information that may exist in the file
            return True

def convertTexture( srcTexturePath: str, dstTexturePath: str = None, 
                   refTexturePath: str = None, forcedFormat: int = None,
                   swapNormalMapRAChannels: bool = False, invertNormalMapG: bool = False ) -> None:    
    srcBasePath, srcBaseName, srcExts = util.splitPath( srcTexturePath )
    srcExt = srcExts[len(srcExts) - 1]
    
    # determine the intermediate dds file path
    srcDDSBasePath = srcBasePath
    srcDDSPath = os.path.join( srcBasePath, srcBaseName )
    if len(srcExts) > 1:
        for i in range(0, len(srcExts) - 1):
            srcDDSPath += '.' + srcExts[i]
    srcDDSPath += '.DDS'
    
    if dstTexturePath == None:
        # determine the destination file path
        dstTexturePath = os.path.join( srcBasePath, srcBaseName )
        if len(srcExts) > 1:
            for i in range(0, len(srcExts) - 1):
                dstTexturePath += '.' + srcExts[i]
        
        dstExt = 'tex'
        if srcExt == 'tex':
            # convert to dds by default if tex is provided
            dstExt = 'dds'
        dstTexturePath += '.' + dstExt
            
    dstBasePath, dstBaseName, dstExts = util.splitPath( dstTexturePath )
    dstExt = dstExts[len(dstExts) - 1]
    
    refTex = None
    if refTexturePath != None and refTexturePath != '':
        # open reference texture if provided
        refTex = rTextureData()
        refTex.loadBinaryFile( refTexturePath )
    
    if srcExt == 'tex':
        # convert tex to dds first (lossless)
        log.info('converting TEX {} to DDS {}'.format(srcTexturePath, dstTexturePath))
        tex = rTextureData()
        tex.loadBinaryFile( srcTexturePath )
        tex.toDDS().saveFile( dstTexturePath )
        
        if dstExt != 'dds':
            # if the target type is not dds, convert the dds with texconv
            log.info('\texconv start')
            texconv.texconv( dstTexturePath, outPath=dstBasePath, fileType=dstExt, pow2=False, fmt='RGBA', srgb=True)
            log.info('texconv end\n')
    else:
        if dstExt != 'tex':
            raise Exception( "Unsupported output format: " + dstExt )
        
        # determine format
        fmt = forcedFormat
        if fmt == '' or fmt == None:
            if refTex != None:
                # copy format from reference texture
                fmt = refTex.header.fmt.surfaceFmt
            else:
                # detect format from name
                fmt = rTextureSurfaceFmt.getFormatFromTextureName( srcBaseName, doesTextureUseAlpha( srcTexturePath ) )
                if fmt == None:
                    # not detected, fallback
                    fmt = rTextureSurfaceFmt.BM_OPA
        
        convert = True
        isNormal = fmt == rTextureSurfaceFmt.NM
        if srcExt.lower() == 'dds':
            # check if DDS format matches
            fmtDDS = rTextureSurfaceFmt.getDDSFormat( fmt )
            dds = DDSFile.fromFile( srcTexturePath )
            if dds.header.ddspf.dwFourCC == fmtDDS:
                # don't need to convert to proper format
                convert = False
                
        if convert:  
            # convert file to DDS with texconv
            fmtDDS = rTextureSurfaceFmt.getDDSFormat( fmt )
            fmtDDSName = ''
            if fmtDDS == DDS_FOURCC_DXT1:
                fmtDDSName = 'DXT1'
            elif fmtDDS == DDS_FOURCC_DXT2:
                fmtDDSName = 'DXT2'
            elif fmtDDS == DDS_FOURCC_DXT3:
                fmtDDSName = 'DXT3'
            elif fmtDDS == DDS_FOURCC_DXT4:
                fmtDDSName = 'DXT4'
            elif fmtDDS == DDS_FOURCC_DXT5:
                fmtDDSName = 'DXT5'
            elif fmtDDS == DDS_FOURCC_NONE:
                fmtDDSName = 'RGBA'
            else:
                raise Exception("Unhandled dds format: " + str(fmtDDS))
            
            log.info( 'converting input {} to DDS {}'.format(srcTexturePath, srcDDSPath))
            log.debug( 'DDS format: {}'.format( fmtDDSName ) )
            log.debug( 'texconv start')
            texconv.texconv( srcTexturePath, outPath=srcDDSBasePath, fileType='DDS', featureLevel=9.1, pow2=True, fmt=fmtDDSName, overwrite=True, srgb=True )
            log.debug( 'texconv end')
        
        log.info('converting DDS {} to TEX {}'.format( srcDDSPath, dstTexturePath ))
        log.debug('TEX format: {}'.format(fmt))
        dds = DDSFile.fromFile( srcDDSPath )
        tex = rTextureData.fromDDS( dds )
        tex.header.fmt.surfaceFmt = fmt
        
        # copy faces from original cubemap if needed
        if refTex != None: 
            for face in refTex.faces:
                tex.faces.append( face )
        
        tex.saveBinaryFile( dstTexturePath )