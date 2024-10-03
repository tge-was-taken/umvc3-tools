'''
DDS utility library for reading and writing DDS files.
'''

from ncl import *
import util

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
DDS_FOURCC_NONE = 0
DDS_FOURCC_DXT1 = FOURCC( 'D', 'X', 'T', '1' )
DDS_FOURCC_DXT2 = FOURCC( 'D', 'X', 'T', '2' )
DDS_FOURCC_DXT3 = FOURCC( 'D', 'X', 'T', '3' )
DDS_FOURCC_DXT4 = FOURCC( 'D', 'X', 'T', '4' )
DDS_FOURCC_DXT5 = FOURCC( 'D', 'X', 'T', '5' )
DDS_FOURCC_DXT10 = FOURCC( 'D', 'X', '1', '0' )

DDS_FOURCC = DDPF_FOURCC
DDS_RGB = DDPF_RGB
DDS_RGBA = DDPF_RGB | DDPF_ALPHAPIXELS
DDS_LUMINANCE = DDPF_LUMINANCE
DDS_LUMINANCEA = DDPF_LUMINANCE | DDPF_ALPHAPIXELS
DDS_ALPHA = DDPF_ALPHA

DXGI_FORMAT_UNKNOWN = 0
DXGI_FORMAT_R32G32B32A32_TYPELESS = 1
DXGI_FORMAT_R32G32B32A32_FLOAT = 2
DXGI_FORMAT_R32G32B32A32_UINT = 3
DXGI_FORMAT_R32G32B32A32_SINT = 4
DXGI_FORMAT_R32G32B32_TYPELESS = 5
DXGI_FORMAT_R32G32B32_FLOAT = 6
DXGI_FORMAT_R32G32B32_UINT = 7
DXGI_FORMAT_R32G32B32_SINT = 8
DXGI_FORMAT_R16G16B16A16_TYPELESS = 9
DXGI_FORMAT_R16G16B16A16_FLOAT = 10
DXGI_FORMAT_R16G16B16A16_UNORM = 11
DXGI_FORMAT_R16G16B16A16_UINT = 12
DXGI_FORMAT_R16G16B16A16_SNORM = 13
DXGI_FORMAT_R16G16B16A16_SINT = 14
DXGI_FORMAT_R32G32_TYPELESS = 15
DXGI_FORMAT_R32G32_FLOAT = 16
DXGI_FORMAT_R32G32_UINT = 17
DXGI_FORMAT_R32G32_SINT = 18
DXGI_FORMAT_R32G8X24_TYPELESS = 19
DXGI_FORMAT_D32_FLOAT_S8X24_UINT = 20
DXGI_FORMAT_R32_FLOAT_X8X24_TYPELESS = 21
DXGI_FORMAT_X32_TYPELESS_G8X24_UINT = 22
DXGI_FORMAT_R10G10B10A2_TYPELESS = 23
DXGI_FORMAT_R10G10B10A2_UNORM = 24
DXGI_FORMAT_R10G10B10A2_UINT = 25
DXGI_FORMAT_R11G11B10_FLOAT = 26
DXGI_FORMAT_R8G8B8A8_TYPELESS = 27
DXGI_FORMAT_R8G8B8A8_UNORM = 28
DXGI_FORMAT_R8G8B8A8_UNORM_SRGB = 29
DXGI_FORMAT_R8G8B8A8_UINT = 30
DXGI_FORMAT_R8G8B8A8_SNORM = 31
DXGI_FORMAT_R8G8B8A8_SINT = 32
DXGI_FORMAT_R16G16_TYPELESS = 33
DXGI_FORMAT_R16G16_FLOAT = 34
DXGI_FORMAT_R16G16_UNORM = 35
DXGI_FORMAT_R16G16_UINT = 36
DXGI_FORMAT_R16G16_SNORM = 37
DXGI_FORMAT_R16G16_SINT = 38
DXGI_FORMAT_R32_TYPELESS = 39
DXGI_FORMAT_D32_FLOAT = 40
DXGI_FORMAT_R32_FLOAT = 41
DXGI_FORMAT_R32_UINT = 42
DXGI_FORMAT_R32_SINT = 43
DXGI_FORMAT_R24G8_TYPELESS = 44
DXGI_FORMAT_D24_UNORM_S8_UINT = 45
DXGI_FORMAT_R24_UNORM_X8_TYPELESS = 46
DXGI_FORMAT_X24_TYPELESS_G8_UINT = 47
DXGI_FORMAT_R8G8_TYPELESS = 48
DXGI_FORMAT_R8G8_UNORM = 49
DXGI_FORMAT_R8G8_UINT = 50
DXGI_FORMAT_R8G8_SNORM = 51
DXGI_FORMAT_R8G8_SINT = 52
DXGI_FORMAT_R16_TYPELESS = 53
DXGI_FORMAT_R16_FLOAT = 54
DXGI_FORMAT_D16_UNORM = 55
DXGI_FORMAT_R16_UNORM = 56
DXGI_FORMAT_R16_UINT = 57
DXGI_FORMAT_R16_SNORM = 58
DXGI_FORMAT_R16_SINT = 59
DXGI_FORMAT_R8_TYPELESS = 60
DXGI_FORMAT_R8_UNORM = 61
DXGI_FORMAT_R8_UINT = 62
DXGI_FORMAT_R8_SNORM = 63
DXGI_FORMAT_R8_SINT = 64
DXGI_FORMAT_A8_UNORM = 65
DXGI_FORMAT_R1_UNORM = 66
DXGI_FORMAT_R9G9B9E5_SHAREDEXP = 67
DXGI_FORMAT_R8G8_B8G8_UNORM = 68
DXGI_FORMAT_G8R8_G8B8_UNORM = 69
DXGI_FORMAT_BC1_TYPELESS = 70
DXGI_FORMAT_BC1_UNORM = 71
DXGI_FORMAT_BC1_UNORM_SRGB = 72
DXGI_FORMAT_BC2_TYPELESS = 73
DXGI_FORMAT_BC2_UNORM = 74
DXGI_FORMAT_BC2_UNORM_SRGB = 75
DXGI_FORMAT_BC3_TYPELESS = 76
DXGI_FORMAT_BC3_UNORM = 77
DXGI_FORMAT_BC3_UNORM_SRGB = 78
DXGI_FORMAT_BC4_TYPELESS = 79
DXGI_FORMAT_BC4_UNORM = 80
DXGI_FORMAT_BC4_SNORM = 81
DXGI_FORMAT_BC5_TYPELESS = 82
DXGI_FORMAT_BC5_UNORM = 83
DXGI_FORMAT_BC5_SNORM = 84
DXGI_FORMAT_B5G6R5_UNORM = 85
DXGI_FORMAT_B5G5R5A1_UNORM = 86
DXGI_FORMAT_B8G8R8A8_UNORM = 87
DXGI_FORMAT_B8G8R8X8_UNORM = 88
DXGI_FORMAT_R10G10B10_XR_BIAS_A2_UNORM = 89
DXGI_FORMAT_B8G8R8A8_TYPELESS = 90
DXGI_FORMAT_B8G8R8A8_UNORM_SRGB = 91
DXGI_FORMAT_B8G8R8X8_TYPELESS = 92
DXGI_FORMAT_B8G8R8X8_UNORM_SRGB = 93
DXGI_FORMAT_BC6H_TYPELESS = 94
DXGI_FORMAT_BC6H_UF16 = 95
DXGI_FORMAT_BC6H_SF16 = 96
DXGI_FORMAT_BC7_TYPELESS = 97
DXGI_FORMAT_BC7_UNORM = 98
DXGI_FORMAT_BC7_UNORM_SRGB = 99
DXGI_FORMAT_AYUV = 100
DXGI_FORMAT_Y410 = 101
DXGI_FORMAT_Y416 = 102
DXGI_FORMAT_NV12 = 103
DXGI_FORMAT_P010 = 104
DXGI_FORMAT_P016 = 105
DXGI_FORMAT_420_OPAQUE = 106
DXGI_FORMAT_YUY2 = 107
DXGI_FORMAT_Y210 = 108
DXGI_FORMAT_Y216 = 109
DXGI_FORMAT_NV11 = 110
DXGI_FORMAT_AI44 = 111
DXGI_FORMAT_IA44 = 112
DXGI_FORMAT_P8 = 113
DXGI_FORMAT_A8P8 = 114
DXGI_FORMAT_B4G4R4A4_UNORM = 115
DXGI_FORMAT_P208 = 130
DXGI_FORMAT_V208 = 131
DXGI_FORMAT_V408 = 132
DXGI_FORMAT_SAMPLER_FEEDBACK_MIN_MIP_OPAQUE = 133
DXGI_FORMAT_SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE = 134
DXGI_FORMAT_FORCE_UINT = 0xffffffff

D3D11_RESOURCE_DIMENSION_UNKNOWN = 0
D3D11_RESOURCE_DIMENSION_BUFFER = 1
D3D11_RESOURCE_DIMENSION_TEXTURE1D = 2
D3D11_RESOURCE_DIMENSION_TEXTURE2D = 3
D3D11_RESOURCE_DIMENSION_TEXTURE3D = 4

D3D11_RESOURCE_MISC_GENERATE_MIPS = 0x1
D3D11_RESOURCE_MISC_SHARED = 0x2
D3D11_RESOURCE_MISC_TEXTURECUBE = 0x4
D3D11_RESOURCE_MISC_DRAWINDIRECT_ARGS = 0x10
D3D11_RESOURCE_MISC_BUFFER_ALLOW_RAW_VIEWS = 0x20
D3D11_RESOURCE_MISC_BUFFER_STRUCTURED = 0x40
D3D11_RESOURCE_MISC_RESOURCE_CLAMP = 0x80
D3D11_RESOURCE_MISC_SHARED_KEYEDMUTEX = 0x100
D3D11_RESOURCE_MISC_GDI_COMPATIBLE = 0x200
D3D11_RESOURCE_MISC_SHARED_NTHANDLE = 0x800
D3D11_RESOURCE_MISC_RESTRICTED_CONTENT = 0x1000
D3D11_RESOURCE_MISC_RESTRICT_SHARED_RESOURCE = 0x2000
D3D11_RESOURCE_MISC_RESTRICT_SHARED_RESOURCE_DRIVER = 0x4000
D3D11_RESOURCE_MISC_GUARDED = 0x8000
D3D11_RESOURCE_MISC_TILE_POOL = 0x20000
D3D11_RESOURCE_MISC_TILED = 0x40000
D3D11_RESOURCE_MISC_HW_PROTECTED = 0x80000
D3D11_RESOURCE_MISC_SHARED_DISPLAYABLE = 0x80001
D3D11_RESOURCE_MISC_SHARED_EXCLUSIVE_WRITER = 0x80002

DDS_ALPHA_MODE_UNKNOWN = 0
DDS_ALPHA_MODE_STRAIGHT = 1
DDS_ALPHA_MODE_PREMULTIPLIED = 2
DDS_ALPHA_MODE_OPAQUE = 3
DDS_ALPHA_MODE_CUSTOM = 4

class DDS_HEADER_DXT10:
    def __init__( self ):
        self.dxgiFormat = DXGI_FORMAT_UNKNOWN
        self.resourceDimension = D3D11_RESOURCE_DIMENSION_UNKNOWN
        self.miscFlag = 0
        self.arraySize = 1
        self.miscFlags2 = 0
        
    def read( self, stream ):
        self.dxgiFormat = stream.readUInt()
        self.resourceDimension = stream.readUInt()
        self.miscFlag = stream.readUInt()
        self.arraySize = stream.readUInt()
        self.miscFlags2 = stream.readUInt()
        
    def write( self, stream ):
        stream.writeUInt( self.dxgiFormat )
        stream.writeUInt( self.resourceDimension )
        stream.writeUInt( self.miscFlag )
        stream.writeUInt( self.arraySize )
        stream.writeUInt( self.miscFlags2 )

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
    
def ddsCalcPitchBlockCompressed( width, blockSize ):
    return int(max( 1, ((width+3)//4) ) * blockSize)

def ddsCalcPitchRgb( width ):
    return ((width+1) >> 1) * 4

def ddsCalcPitchBpp( width, bpp ):
    return ( width * bpp + 7 ) // 8

def ddsAlign4( val ):
    return int(max(1, ( (val + 3) // 4 ) ))

def ddsCalcLinearSizeBlockCompressed( width, height, blockSize ):
    return int( ( ddsAlign4( width ) * ddsAlign4( height ) ) * blockSize )

def ddsCalcLinearSizeBpp( width, height, bpp ):
    return int( ( width * height ) * (bpp / 8) )
        
class DDSFile:
    def __init__( self ):
        self.header = DDS_HEADER()
        self.dxt10Header = DDS_HEADER_DXT10()
        self.buffer = bytearray()
        
    def read( self, stream ):
        if stream.readUInt() != DDS_MAGIC:
            raise Exception( "Invalid DDS file" )
        
        self.header.read( stream )
        if self.header.ddspf.dwFourCC == DDS_FOURCC_DXT10:
            self.dxt10Header.read( stream )
        self.buffer = stream.readBytes( stream.getSize() - stream.getOffset() )
        
    def write( self, stream ):
        stream.writeUInt( DDS_MAGIC )
        self.header.write( stream )
        if self.header.ddspf.dwFourCC == DDS_FOURCC_DXT10:
            self.dxt10Header.write( stream )
        stream.writeBytes( self.buffer )
        
    def calcPitch( self ):
        pitch = 0
        if self.header.ddspf.dwFlags & DDPF_FOURCC:
            blockSize = 16
            if self.header.ddspf.dwFourCC == DDS_FOURCC_DXT1:
                blockSize = 8
            pitch = ddsCalcPitchBlockCompressed( self.header.dwWidth, blockSize )
        else:
            pitch = ddsCalcPitchBpp( self.header.dwWidth, self.header.ddspf.dwRGBBitCount )
        return pitch
    
    def loadFile( self, path ):
        self.read( NclBitStream( util.loadIntoByteArray( path ) ) )
        
    def saveFile( self, path ):
        stream = NclBitStream()
        self.write( stream )
        util.saveByteArrayToFile( path, stream.getBuffer() )
        
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
        