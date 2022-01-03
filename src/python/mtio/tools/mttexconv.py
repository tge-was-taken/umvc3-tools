import os
import sys
import argparse

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

sys.path.append( os.path.realpath( os.path.dirname( __file__ ) + "/../" ) )
from modules.mtlib import *
from modules.mtlib import texconv

def processFile( inPath, outPath, origPath, forcedFormat ):
    basePath, baseName, exts = util.splitPath( inPath )
    inExt = exts[len(exts) - 1]
    
    inDDSBasePath = basePath
    inDDSPath = os.path.join( basePath, baseName )
    if len(exts) > 1:
        for i in range(0, len(exts) - 1):
            inDDSPath += '.' + exts[i]
    inDDSPath += '.DDS'
    
    if outPath == None:
        outPath = os.path.join( basePath, baseName )
        if len(exts) > 1:
            for i in range(0, len(exts) - 1):
                outPath += '.' + exts[i]
        
        outExt = 'tex'
        if inExt == 'tex':
            outExt = 'dds'
        outPath += '.' + outExt
            
    outBasePath, outBaseName, outExts = util.splitPath( outPath )

    
    outExt = outExts[len(outExts) - 1]
    
    origTex = None
    if origPath != None and origPath != '':
        origTex = rTextureData()
        origTex.loadBinaryFile( origPath )
    
    if inExt == 'tex':
        # convert tex to dds
        print('converting TEX {} to DDS {}'.format(inPath, outPath))
        tex = rTextureData()
        tex.loadBinaryFile( inPath )
        tex.toDDS().saveFile( outPath )
        
        if outExt != 'dds':
            # try to convert with texconv
            print('\texconv start')
            texconv.texconv( outPath, outPath=outBasePath, fileType=outExt, pow2=False, fmt='RGBA', srgb=True)
            print('texconv end\n')
    else:
        if outExt != 'tex':
            raise Exception( "Unsupported output format: " + outExt )
        
        # detect format from name
        fmt = forcedFormat
        if fmt == '' or fmt == None:
            if origTex != None:
                fmt = origTex.header.fmt.surfaceFmt
            else:
                fmt = rTextureSurfaceFmt.getFormatFromTextureName( baseName, True )
                if fmt == None:
                    # not detected, fallback
                    fmt = rTextureSurfaceFmt.BM_OPA
        
        convert = True
        if inExt.lower() == 'dds':
            # check if DDS format matches
            fmtDDS = rTextureSurfaceFmt.getDDSFormat( fmt )
            dds = DDSFile.fromFile( inPath )
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
            else:
                raise Exception("Unhandled dds format: " + str(fmtDDS))
            
            print( 'converting input {} to DDS {}'.format(inPath, inDDSPath))
            print( 'DDS format: {}'.format( fmtDDSName ) )
            print( '\ntexconv start')
            texconv.texconv( inPath, outPath=inDDSBasePath, fileType='DDS', featureLevel=9.1, pow2=True, fmt=fmtDDSName, overwrite=True, srgb=True )
            print( 'texconv end\n')
        
        print('converting DDS {} to TEX {}'.format( inDDSPath, outPath ))
        print('TEX format: {}'.format(fmt))
        dds = DDSFile.fromFile( inDDSPath )
        tex = rTextureData.fromDDS( dds )
        tex.header.fmt.surfaceFmt = fmt
        
        # copy faces from original cubemap if needed
        if origTex != None: 
            for face in origTex.faces:
                tex.faces.append( face )
        
        tex.saveBinaryFile( outPath )
        

def hexOrDecimalInt( s ):
    return int( s, 0 )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "input", type=str, help='the input TEX/DDS/PNG/TGA/other file path' )
    parser.add_argument( "output", type=str, nargs='?', help='the output TEX/DDS/PNG/TGA/other file path' )
    parser.add_argument( '-orig', '--original', type=str, default=None, required=False, help='the path to the original texture file to use as reference' )
    parser.add_argument( '-fmt', '--format', type=hexOrDecimalInt, default=None, required=False, help='forces the texture format for conversion' )
    args = parser.parse_args()
    processFile( args.input, args.output, args.original, args.format )
    pass

if __name__ == '__main__':
    main()