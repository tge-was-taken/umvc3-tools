'''
DDS utility library for reading and writing DDS files.
'''

from mtncl import *
import mtutil

'''
struct DDS_PIXELFORMAT {
  DWORD dwSize;
  DWORD dwFlags;
  DWORD dwFourCC;
  DWORD dwRGBBitCount;
  DWORD dwRBitMask;
  DWORD dwGBitMask;
  DWORD dwBBitMask;
  DWORD dwABitMask;
};
'''
'''Texture contains alpha data; dwRGBAlphaBitMask contains valid data.'''
DDPF_ALPHAPIXELS = 0x1
'''Used in some older DDS files for alpha channel only uncompressed data (dwRGBBitCount contains the alpha channel bitcount; dwABitMask contains valid data)'''
DDPF_ALPHA = 0x2
'''Texture contains compressed RGB data; dwFourCC contains valid data.'''
DDPF_FOURCC = 0x4
'''Texture contains uncompressed RGB data; dwRGBBitCount and the RGB masks (dwRBitMask, dwGBitMask, dwBBitMask) contain valid data.'''
DDPF_RGB = 0x40
'''Used in some older DDS files for YUV uncompressed data (dwRGBBitCount contains the YUV bit count; dwRBitMask contains the Y mask, dwGBitMask contains the U mask, dwBBitMask contains the V mask)'''
DDPF_YUV = 0x200
'''Used in some older DDS files for single channel color uncompressed data (dwRGBBitCount contains the luminance channel bit count; dwRBitMask contains the channel mask). Can be combined with DDPF_ALPHAPIXELS for a two channel DDS file.'''
DDPF_LUMINANCE = 0x2000

class DDS_PIXELFORMAT:
    def __init__( self ):
        self.dwSize = 32
        self.dwFlags = 0
        self.dwFourCC = 0
        self.dwRGBBitCount = 0
        self.dwRBitMask = 0
        self.dwGBitMask = 0
        self.dwBBitMask = 0
        self.dwABitMask = 0
        
    def read( self, stream ):
        self.dwSize = stream.readUInt()
        self.dwFlags = stream.readUInt()
        self.dwFourCC = stream.readUInt()
        self.dwRGBBitCount = stream.readUInt()
        self.dwRBitMask = stream.readUInt()
        self.dwGBitMask = stream.readUInt()
        self.dwBBitMask = stream.readUInt()
        self.dwABitMask = stream.readUInt()
        
    def write( self, stream ):
        stream.writeUInt( self.dwSize )
        stream.writeUInt( self.dwFlags )
        stream.writeUInt( self.dwFourCC )
        stream.writeUInt( self.dwRGBBitCount )
        stream.writeUInt( self.dwRBitMask )
        stream.writeUInt( self.dwGBitMask )
        stream.writeUInt( self.dwBBitMask )
        stream.writeUInt( self.dwABitMask )

'''
typedef struct {
  DWORD           dwSize;
  DWORD           dwFlags;
  DWORD           dwHeight;
  DWORD           dwWidth;
  DWORD           dwPitchOrLinearSize;
  DWORD           dwDepth;
  DWORD           dwMipMapCount;
  DWORD           dwReserved1[11];
  DDS_PIXELFORMAT ddspf;
  DWORD           dwCaps;
  DWORD           dwCaps2;
  DWORD           dwCaps3;
  DWORD           dwCaps4;
  DWORD           dwReserved2;
} DDS_HEADER;
'''
'''Required in every .dds file.'''
DDSD_CAPS = 0x1
'''Required in every .dds file.'''
DDSD_HEIGHT = 0x2
'''Required in every .dds file.'''
DDSD_WIDTH = 0x4
'''Required when pitch is provided for an uncompressed texture.'''
DDSD_PITCH = 0x8
'''Required in every .dds file.'''
DDSD_PIXELFORMAT = 0x1000
'''Required in a mipmapped texture.'''
DDSD_MIPMAPCOUNT = 0x20000
'''Required when pitch is provided for a compressed texture.'''
DDSD_LINEARSIZE = 0x80000
'''Required in a depth texture.'''
DDSD_DEPTH = 0x800000

DDS_HEADER_FLAGS_TEXTURE = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
DDS_HEADER_FLAGS_MIPMAP = DDSD_MIPMAPCOUNT
DDS_HEADER_FLAGS_VOLUME = DDSD_DEPTH
DDS_HEADER_FLAGS_PITCH = DDSD_PITCH
DDS_HEADER_FLAGS_LINEARSIZE = DDSD_LINEARSIZE

'''Optional; must be used on any file that contains more than one surface (a mipmap, a cubic environment map, or mipmapped volume texture).'''
DDSCAPS_COMPLEX = 0x8
'''Optional; should be used for a mipmap.'''
DDSCAPS_MIPMAP = 0x400000
'''Required'''
DDSCAPS_TEXTURE = 0x1000

DDS_SURFACE_FLAGS_MIPMAP = DDSCAPS_COMPLEX | DDSCAPS_MIPMAP
DDS_SURFACE_FLAGS_TEXTURE = DDSCAPS_TEXTURE
DDS_SURFACE_FLAGS_CUBEMAP = DDSCAPS_COMPLEX

'''Required for a cube map.'''
DDSCAPS2_CUBEMAP = 0x200
'''Required when these surfaces are stored in a cube map.'''
DDSCAPS2_CUBEMAP_POSITIVEX = 0x400
'''Required when these surfaces are stored in a cube map.'''
DDSCAPS2_CUBEMAP_NEGATIVEX = 0x800
'''Required when these surfaces are stored in a cube map.'''
DDSCAPS2_CUBEMAP_POSITIVEY = 0x1000
'''Required when these surfaces are stored in a cube map.'''
DDSCAPS2_CUBEMAP_NEGATIVEY = 0x2000
'''Required when these surfaces are stored in a cube map.'''
DDSCAPS2_CUBEMAP_POSITIVEZ = 0x4000
'''Required when these surfaces are stored in a cube map.'''
DDSCAPS2_CUBEMAP_NEGATIVEZ = 0x8000
'''Required for a volume texture.'''
DDSCAPS2_VOLUME = 0x200000

DDS_CUBEMAP_POSITIVEX = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEX
DDS_CUBEMAP_POSITIVEY = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEY
DDS_CUBEMAP_POSITIVEZ = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_POSITIVEZ
DDS_CUBEMAP_NEGATIVEX = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_NEGATIVEX
DDS_CUBEMAP_NEGATIVEY = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_NEGATIVEY
DDS_CUBEMAP_NEGATIVEZ = DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_NEGATIVEZ
DDS_CUBEMAP_ALLFACES  = DDS_CUBEMAP_POSITIVEX | DDS_CUBEMAP_POSITIVEY | DDS_CUBEMAP_POSITIVEZ | DDS_CUBEMAP_NEGATIVEX | DDS_CUBEMAP_NEGATIVEY | DDS_CUBEMAP_NEGATIVEZ

def FOURCC(a,b,c,d):
    return ( (ord(a) & 0xFF) << 0 | (ord(b) & 0xFF) << 8 | (ord(c) & 0xFF) << 16 | (ord(d) & 0xFF) << 24 ) & 0xFFFFFFFF

DDS_MAGIC = FOURCC( 'D', 'D', 'S', ' ' )
DDS_FOURCC_DXT1 = FOURCC( 'D', 'X', 'T', '1' )
DDS_FOURCC_DXT2 = FOURCC( 'D', 'X', 'T', '2' )
DDS_FOURCC_DXT3 = FOURCC( 'D', 'X', 'T', '3' )
DDS_FOURCC_DXT4 = FOURCC( 'D', 'X', 'T', '4' )
DDS_FOURCC_DXT5 = FOURCC( 'D', 'X', 'T', '5' )

class DDS_HEADER:
    def __init__( self ):
        self.dwSize = 124
        self.dwFlags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
        self.dwHeight = 0
        self.dwWidth = 0
        self.dwPitchOrLinearSize = 0
        self.dwDepth = 0
        self.dwMipMapCount = 0
        self.dwReserved1 = [0] * 11
        self.ddspf = DDS_PIXELFORMAT()
        self.dwCaps = DDSCAPS_TEXTURE
        self.dwCaps2 = 0
        self.dwCaps3 = 0
        self.dwCaps4 = 0
        self.dwReserved2 = 0
        
    def read( self, stream ):
        self.dwSize = stream.readUInt()
        self.dwFlags = stream.readUInt()
        self.dwHeight = stream.readUInt()
        self.dwWidth = stream.readUInt()
        self.dwPitchOrLinearSize = stream.readUInt()
        self.dwDepth = stream.readUInt()
        self.dwMipMapCount = stream.readUInt()
        for i in range( 11 ):
            self.dwReserved1[ i ] = stream.readUInt()
        self.ddspf.read( stream )
        self.dwCaps = stream.readUInt()
        self.dwCaps2 = stream.readUInt()
        self.dwCaps3 = stream.readUInt()
        self.dwCaps4 = stream.readUInt()
        self.dwReserved2 = stream.readUInt()
        
    def write( self, stream ):
        stream.writeUInt( self.dwSize )
        stream.writeUInt( self.dwFlags )
        stream.writeUInt( self.dwHeight )
        stream.writeUInt( self.dwWidth )
        stream.writeUInt( self.dwPitchOrLinearSize )
        stream.writeUInt( self.dwDepth )
        stream.writeUInt( self.dwMipMapCount )
        for i in range( 11 ):
            stream.writeUInt( self.dwReserved1[i] )
        self.ddspf.write( stream )
        stream.writeUInt( self.dwCaps )
        stream.writeUInt( self.dwCaps2 )
        stream.writeUInt( self.dwCaps3 )
        stream.writeUInt( self.dwCaps4 )
        stream.writeUInt( self.dwReserved2 )
    
def ddsCalcPitchCompressed( width, blockSize ):
    return int(max( 1, ((width+3)//4) ) * blockSize)

def ddsCalcPitchRgb( width ):
    return ((width+1) >> 1) * 4

def ddsCalcPitchGeneric( width, bpp ):
    return ( width * bpp + 7 ) // 8

def ddsAlign4( val ):
    return int(max(1, ( (val + 3) // 4 ) ))

def ddsCalcLinearSizeCompressed( width, height, blockSize ):
    return int( ( ddsAlign4( width ) * ddsAlign4( height ) ) * blockSize )
        
class DDSFile:
    def __init__( self ):
        self.header = DDS_HEADER()
        self.buffer = bytearray()
        
    def read( self, stream ):
        if stream.readUInt() != DDS_MAGIC:
            raise Exception( "Invalid DDS file" )
        
        self.header.read( stream )
        self.buffer = stream.readBytes( stream.getSize() - stream.getOffset() )
        
    def write( self, stream ):
        stream.writeUInt( DDS_MAGIC )
        self.header.write( stream )
        stream.writeBytes( self.buffer )
        
    def calcPitch( self ):
        pitch = 0
        if self.header.ddspf.dwFlags & DDPF_FOURCC:
            blockSize = 16
            if self.header.ddspf.dwFourCC == DDS_FOURCC_DXT1:
                blockSize = 8
            pitch = ddsCalcPitchCompressed( self.header.dwWidth, blockSize )
        else:
            pitch = ddsCalcPitchGeneric( self.header.dwWidth, self.header.ddspf.dwRGBBitCount )
        return pitch
    
    def loadFile( self, path ):
        self.read( NclBitStream( mtutil.loadIntoByteArray( path ) ) )
        
    def saveFile( self, path ):
        stream = NclBitStream()
        self.write( stream )
        mtutil.saveByteArrayToFile( path, stream.getBuffer() )
        
    @staticmethod
    def fromFile( path ):
        dds = DDSFile()
        dds.loadFile( path )
        return dds
        
def _test():
    dds = DDSFile()
    dds.loadFile( "X:/work/umvc3_model/samples/UMVC3ModelSamples/Ryu/Ryu_tex1_BM.241f5deb.dds" )
    dds.saveFile( "test.dds" )
    pass
        
if __name__ == '__main__':
    _test()
        