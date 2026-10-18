'''
Module containing various utility functions used throughout the library.
'''

import zlib
import math
import os
import sys
import re

import mvc3shaderdb
from rshader import rShaderObjectId
from ncl import *

def loadIntoByteArray( path ):
    '''Loads the given file into a byte array'''
    
    data = None
    with open( path, "rb" ) as f:
        f.seek( 0, 2 )
        size = f.tell()
        f.seek( 0 )
        data = f.read( size )
    return data

def saveByteArrayToFile( path, buffer ):
    '''Saves the given byte array to the specified file'''
    
    dirName = os.path.dirname( path )
    if dirName != '':
        os.makedirs( os.path.dirname( path ), exist_ok=True )
    with open( path, "wb" ) as f:
        f.write( buffer )

def replaceSuffix( name, suffix, replacement ):
    '''Replaces the specified suffix with a replacement suffix'''
    
    return name[0:len(name) - len(suffix) - 1] + replacement

def readCStringBuffer( stream, length ):
    '''Reads an ASCII C-string buffer from the stream'''
    
    return stream.readBytes( length ).decode( "ASCII" ).rstrip( "\0" )

def writeCStringBuffer( stream, value, length ):
    '''Writes an ASCII C-string buffer to the stream'''
    
    buf = value.encode( "ASCII" )
    rem = length - len(buf)
    assert( rem >= 0 )
    
    # write buffer
    stream.writeBytes( buf )
    
    # write padding
    for i in range(rem):
        stream.writeByte( 0 ) 

def u32( v ):
    '''represents the integer as unsigned 32 bit'''
    return ( v & 0xFFFFFFFF ) 

def computeHash( input ):
    '''Computes CRC32/JAMCRC hash'''
    crc = u32( zlib.crc32( input.encode( "ASCII" ) ) )
    return u32(~crc)

def align( val, alignment ):
    '''Aligns the value to the next multiple of the specified alignment'''
    
    return math.ceil( val / alignment ) * alignment   

def hexN( val, nbits ):
    '''Returns a hex representation of the value with the specified of bits'''
    return hex((val + (1 << nbits)) % (1 << nbits))

def hex32( val ):
    '''Returns a hex representation of the value with 32 bits'''
    return hexN( val, 32 )

def readFloatBuffer( stream, length ):
    '''Reads a float buffer from a stream with the specified length'''
    
    buf = []
    for i in range( length ):
        buf.append( stream.readFloat() )
    return buf

def getShaderObjectIdFromName( name ):
    '''Gets the shader object ID associated with the given shader object name'''
    
    so = mvc3shaderdb.shaderObjectsByName[ name ]
    soId = rShaderObjectId()
    soId.setHash( so.hash )
    soId.setIndex( so.index )
    assert( soId.getValue() <= 0xFFFFFFFF )
    return soId

def splitPath( path ):
    '''Splits the given path into the directory path, the base file name and an array of extensions'''
    
    parts = os.path.basename( path ).split('.')
    baseName = parts[0]
    exts = []
    for i in range( 1, len( parts ) ):
        exts.append( parts[i] )
    
    return ( os.path.dirname( path ), baseName, exts )

def bitUnpack( value, mask, bitOffset):
    '''Unpacks the specified bits from the value'''
    return ( value >> bitOffset ) & mask 

def bitPack( value, mask, bitOffset, index):
    '''Packs the specified bits into the value'''
    return ( value & ~( mask << bitOffset ) ) | ( index & mask ) << bitOffset

def iterModelIndexBuffer( model, primitive, indexReadStream ):
    '''
    fix index buffer for drawing by subtracting the vertex start index from the indices
    '''
    indexStart = ( primitive.indexBufferOffset + primitive.indexStartIndex ) * 2
    indexEnd = indexStart + ( primitive.indexCount * 2 )
    indexReadStream.seek( indexStart )
    badIdx = -1
    for i in range(primitive.indexCount):
        idx = indexReadStream.readUShort()
        fixedIdx = idx - primitive.vertexStartIndex
        assert( idx >= 0 )
        if (fixedIdx < 0):
            badIdx = i
        yield fixedIdx
    if badIdx != -1: print("Bad indices at " + str(badIdx) + " indexStart: " + str(indexStart) + " vertexStartIndex: " + str(primitive.vertexStartIndex))
    
def getLibDir():
    '''Gets the path to the library directory'''
    
    return os.path.dirname(os.path.realpath(__file__))

def getResourceDir():
    '''Gets the path to the resource directory'''
    
    return getLibDir() + '/res'

def getExtractedResourceFilePath( basePath, hash, ext ):
    '''Finds an existing path to a resource file with or without the hash suffix'''
    
    oldPath = basePath + '.' + hash + '.' + ext
    newPath = basePath + '.' + ext
    if os.path.exists( oldPath ):
        return ( oldPath, False )
    elif os.path.exists( newPath ):
        return ( newPath, True )
    else:
        return ( None, None )
    
def isResourceFilePathWithHash( path ):
    return re.match(r"\w+\.([0-9]|[a-f]|[A-F])+\.\w{3}", path)

class ResourcePath:
    def __init__( self, fullPath, rootPath=None ):
        self.fullPath = os.path.abspath( fullPath ).replace("/", "\\")
        self.basePath, self.fullName = os.path.split(fullPath)
        self.basePath = self.basePath.replace("/", "\\")
        
        nameParts = self.fullName.split('.')
        self.baseName = nameParts[0]
        self.hash = None
        if len(nameParts) == 2:
            self.ext = nameParts[1]
        elif len(nameParts) == 3:
            self.hash = nameParts[1]
            self.ext = nameParts[2]
        else:
            raise Exception("Invalid path: " + fullPath)
        
        self.fullPathNoExt = self.basePath + '\\' + self.baseName
        
        self.relPath = None
        self.relBasePath = None
        self.relPathNoExt = None
        
        if rootPath != None:
            rootPath = os.path.abspath( rootPath ).replace("/", "\\")
            pathRootIndex = self.fullPath.find( rootPath )
            if pathRootIndex == 0 and self.fullPath[len(rootPath)] == '\\':
                # root folder found in path
                self.relPath = self.fullPath[len(rootPath)+1:]
                self.relBasePath = self.basePath[len(rootPath)+1:]
                self.relPathNoExt = self.fullPathNoExt[len(rootPath)+1:]
            else:
                # no root folder found in path
                pass

    
def resolveTexturePath( basePath, texturePath ):
    # load TEX and convert to DDS before loading the model
    
    # normalize texture path
    texturePathNrm = texturePath.replace( '\\', '/' )
    
    # find the root of the texture path relative to the current model directory
    texturePathParts = texturePathNrm.split( '/' )
    relTexturePathRoot = ''
    for i in range( 1, len( texturePathParts )):
        relTexturePathRoot += '../'
    fullRelTexturePathRoot = os.path.join( basePath, relTexturePathRoot ) 
    texturePathRoot = os.path.realpath( fullRelTexturePathRoot )
    
    # find the real texture path
    realTexturePath = os.path.join( texturePathRoot, texturePath )
    textureTEXPath, _ = getExtractedResourceFilePath( realTexturePath, '241f5deb', 'tex' )
    if textureTEXPath == None:
        # failsafe: try to look for the tex files in the current model directory in case we don't find it 
        # won't work for all textures
        textureTEXPath, _ = getExtractedResourceFilePath( basePath + '/' + os.path.basename( texturePath ), '241f5deb', 'tex' )
        textureDDSPath =  os.path.join( basePath, os.path.basename( texturePath ) + ".dds" ) # failsafe
        if textureTEXPath == None:
            print( 'WARNING: TEX file not found: {}'.format( texturePath ) )  
    else:
        textureDDSPath = os.path.splitext( textureTEXPath )[0] + '.dds'
        
    return ( textureTEXPath, textureDDSPath )

Y_TO_Z_UP_MATRIX = nclCreateMat44((NclVec4((1,  0,  0, 0)),  # x=x
                                   NclVec4((0,  0,  1, 0)),  # y=z
                                   NclVec4((0, -1,  0, 0)),  # z=-y
                                   NclVec4((0,  0,  0, 1))))

Z_TO_Y_UP_MATRIX = nclCreateMat44((NclVec4((1,  0,  0, 0)),  # x=x
                                   NclVec4((0,  0, -1, 0)),  # y=-z
                                   NclVec4((0,  1,  0, 0)),  # z=y
                                   NclVec4((0,  0,  0, 1))))

def transformMatrixToZUp( mtx ):
    return mtx * Y_TO_Z_UP_MATRIX
    
def transformMatrixToYUp( mtx ):
    return mtx * Z_TO_Y_UP_MATRIX
    
def isValidByteIndex( idx ):
    return idx not in [255, -1]

if __name__ == '__main__':
    test = ResourcePath("X:\\game\\platform\\pc\\Ultimate Marvel vs. Capcom 3\\nativePCx64\\chr\\archive\\0045_00 - falcon\\chr\\Nova\\model\\1p\\Nova.58a15856.mod")
    pass