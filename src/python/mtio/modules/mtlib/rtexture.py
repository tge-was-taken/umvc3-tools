'''
Binary texture (.TEX) serialization module. 
'''

import util
from ncl import *
from dds import *

class rTextureHeaderDesc(object):
    def __init__( self, value=0 ):
        self.value = value
        
    @staticmethod
    def create( dimensions=2, shift=0, field2=0, typeVal=0xA09D ):
        desc = rTextureHeaderDesc()
        desc.setType( typeVal )
        desc.setField2( field2 )
        desc.setShift( shift )
        desc.setDimensions( dimensions )
        return desc
        
    def getType( self ):
        return util.bitUnpack( self.value, 0xFFFF, 0 )
    
    def setType( self, value ):
        self.value = util.bitPack( self.value, 0xFFFF, 0, value )
        
    def getField2( self ):
        return util.bitUnpack( self.value, 0xFF, 16 )
    
    def setField2( self, value ):
        self.value = util.bitPack( self.value, 0xFF, 16, value )
        
    def getShift( self ):
        return util.bitUnpack( self.value, 0xF, 24 )
    
    def setShift( self, value ):
        self.value = util.bitPack( self.value, 0xF, 24, value )
        
    def getDimensions( self ):
        return util.bitUnpack( self.value, 0xF, 28 )
    
    def setDimensions( self, value ):
        self.value = util.bitPack( self.value, 0xF, 28, value )   
        
    def getValue( self ):
        return self.value
    
    def setValue( self, value ):
        self.value = value  
        
    type = property( getType, setType )
    field2 = property( getField2, setField2 )
    shift = property( getShift, setShift )
    dimensions = property( getDimensions, setDimensions )

class rTextureHeaderDim(object):
    def __init__( self, value=0 ):
        self.value = value
        
    @staticmethod
    def create( width, height, mipCount ):
        dim = rTextureHeaderDim()
        dim.setWidth( width )
        dim.setHeight( height )
        dim.setMipCount( mipCount )
        return dim
        
    def getMipCount( self ):
        return util.bitUnpack( self.value, 0x3F, 0 )
    
    def setMipCount( self, value ):
        self.value = util.bitPack( self.value, 0x3F, 0, value )
        
    def getWidth( self ):
        return util.bitUnpack( self.value, 0x1FFF, 6 )
    
    def setWidth( self, value ):
        self.value = util.bitPack( self.value, 0x1FFF, 6, value )
        
    def getHeight( self ):
        return util.bitUnpack( self.value, 0x1FFF, 19 )
    
    def setHeight( self, value ):
        self.value = util.bitPack( self.value, 0x1FFF, 19, value )
        
    def getValue( self ):
        return self.value
    
    def setValue( self, value ):
        self.value = value    
        
    mipCount = property( getMipCount, setMipCount )
    height = property( getHeight, setHeight )
    width = property( getWidth, setWidth )

class rTextureSurfaceFmt:
    # OPA: opaque
    # XLU: translucent
    BM_OPA   = 19 # DXT1
    DXT1_20  = 20 # DXT1, not used in mvc3
    DXT5_21  = 21 # DXT5, not used in mvc3
    DXT5_22  = 22 # DXT5, not used in mvc3
    BM_XLU   = 23 # DXT5
    DXT5_24  = 24 # DXT5, not used in mvc3
    MM_OPA   = 25 # DXT1
    DXT1_26  = 26 # DXT1, not used in mvc3
    DXT5_27  = 27 # DXT5, not used in mvc3
    DXT1_30  = 30 # DXT1, not used in mvc3
    NM       = 31 # DXT5
    DXT5_32  = 32 # DXT5, not used in mvc3
    DXT5_33  = 33 # DXT5, not used in mvc3
    DXT5_35  = 35 # DXT5, not used in mvc3
    DXT5_36  = 36 # DXT5, not used in mvc3
    DXT5_37  = 37 # DXT5, not used in mvc3
    LIN      = 39 # RGBA, used for linear textures/ramps
    DXT1_41  = 41 # DXT1, not used in mvc3
    BM_HQ    = 42 # DXT5    
    DXT5_43  = 43 # DXT5, not used in mvc3
    DXT5_47  = 47 # DXT5, not used in mvc3
    
    @staticmethod
    def getDDSFormat( fmt ):
        if fmt in [rTextureSurfaceFmt.BM_OPA, rTextureSurfaceFmt.DXT1_20, 
                   rTextureSurfaceFmt.MM_OPA, rTextureSurfaceFmt.DXT1_26, 
                   rTextureSurfaceFmt.DXT1_30, rTextureSurfaceFmt.DXT1_41]: 
            return DDS_FOURCC_DXT1
        elif fmt in [rTextureSurfaceFmt.DXT5_21, rTextureSurfaceFmt.DXT5_22,
                     rTextureSurfaceFmt.BM_XLU, rTextureSurfaceFmt.DXT5_24,
                     rTextureSurfaceFmt.DXT5_27, rTextureSurfaceFmt.NM,
                     rTextureSurfaceFmt.DXT5_32, rTextureSurfaceFmt.DXT5_33,
                     rTextureSurfaceFmt.DXT5_35, rTextureSurfaceFmt.DXT5_36,
                     rTextureSurfaceFmt.DXT5_37, rTextureSurfaceFmt.BM_HQ,
                     rTextureSurfaceFmt.DXT5_43, rTextureSurfaceFmt.DXT5_47]:
            return DDS_FOURCC_DXT5
        elif fmt in[rTextureSurfaceFmt.LIN]:
            return DDS_FOURCC_NONE # RGBA
        
    _specialTextureNames = {
        'DEAmoji00_MM': DXT5_21,
        'yari_MM': LIN,
        'Wesker_nuno_DM': DXT1_30,
        'DefaultCube_CM': DXT5_32,
        'ZERmoyou02': LIN,
        'ZERmoyoured02': LIN,
        'ZERmoyouyellow02': LIN,
    }
        
    @staticmethod
    def getFormatFromTextureName( name, alpha ):
        if name in rTextureSurfaceFmt._specialTextureNames:
            return rTextureSurfaceFmt._specialTextureNames[ name ]
        elif '_BM' in name:
            if 'toon' in name:
                return rTextureSurfaceFmt.LIN
            elif '_HQ' in name:
                return rTextureSurfaceFmt.BM_HQ
            elif alpha:
                return rTextureSurfaceFmt.BM_XLU
            else:
                return rTextureSurfaceFmt.BM_OPA
        elif '_LM' in name or \
             '_CM' in name or \
             '_NUKI' in name:
            return rTextureSurfaceFmt.BM_OPA
        elif '_AM' in name or \
             '_MM' in name:
            return rTextureSurfaceFmt.MM_OPA
        elif '_DM' in name or \
             '_NM' in name:
            return rTextureSurfaceFmt.NM
        elif '_LIN' in name:
            return rTextureSurfaceFmt.LIN

class rTextureHeaderFmt:
    def __init__( self, value=0 ):
        self.value = value
        
    @staticmethod
    def create( field4=0, field3=1, surfaceFmt=rTextureSurfaceFmt.BM_XLU, surfaceCount=1 ):
        dim = rTextureHeaderFmt()
        dim.setField4( field4 )
        dim.setField3( field3 )
        dim.setSurfaceFmt( surfaceFmt )
        dim.setSurfaceCount( surfaceCount )
        return dim
        
    def getSurfaceCount( self ):
        return util.bitUnpack( self.value, 0xFF, 0 )
    
    def setSurfaceCount( self, value ):
        self.value = util.bitPack( self.value, 0xFF, 0, value )
        
    def getSurfaceFmt( self ):
        return util.bitUnpack( self.value, 0xFF, 8 )
    
    def setSurfaceFmt( self, value ):
        self.value = util.bitPack( self.value, 0xFF, 8, value )
        
    def getField3( self ):
        return util.bitUnpack( self.value, 0x1FFF, 16 )
    
    def setField3( self, value ):
        self.value = util.bitPack( self.value, 0x1FFF, 16, value )
        
    def getField4( self ):
        return util.bitUnpack( self.value, 0x3, 29 )
    
    def setField4( self, value ):
        self.value = util.bitPack( self.value, 0x3, 29, value )   
        
    def getValue( self ):
        return self.value
    
    def setValue( self, value ):
        self.value = value  
        
    surfaceCount = property( getSurfaceCount, setSurfaceCount )
    surfaceFmt = property( getSurfaceFmt, setSurfaceFmt )
    field3 = property( getField3, setField3 )
    field4 = property( getField4, setField4 )

class rTextureHeader:
    def __init__( self ):
        self.magic = 0x00584554
        self.desc = rTextureHeaderDesc.create()
        self.dim = rTextureHeaderDim.create( 0, 0, 0 )
        self.fmt = rTextureHeaderFmt.create()
        
    def read( self, stream ):
        self.magic = stream.readUInt()
        self.desc = rTextureHeaderDesc( stream.readUInt() )
        self.dim = rTextureHeaderDim( stream.readUInt() )
        self.fmt = rTextureHeaderFmt( stream.readUInt() )
        
    def write( self, stream ):
        stream.writeUInt( self.magic )
        stream.writeUInt( self.desc.getValue() )
        stream.writeUInt( self.dim.getValue() )
        stream.writeUInt( self.fmt.getValue() )
        
class rTextureFace:
    def __init__( self ):
        self.field00 = 0
        self.negative = NclVec3()
        self.positive = NclVec3()
        self.uv = NclVec3()
        
    def read( self, stream ):
        self.field00 = stream.readFloat()
        self.negative = stream.readVec3()
        self.positive = stream.readVec3()
        self.uv = stream.readVec2()
        
    def write( self, stream ):
        stream.writeFloat( self.field00 )
        stream.writeVec3( self.negative )
        stream.writeVec3( self.positive )
        stream.writeVec2( self.uv )
    
class rTextureSurfaceData:
    def __init__( self ):
        self.mips = []
        
class rTextureData:
    def __init__( self ):
        self.header = rTextureHeader()
        self.faces = []
        self.surfaces = []
        
    def read( self, stream ):
        self.header.read( stream )
        
        if self.header.desc.getDimensions() == 6:
            for i in range( 3 ):
                face = rTextureFace()
                face.read( stream )
                self.faces.append( face )
        
        mipOffsets = []
        for i in range( self.header.fmt.getSurfaceCount() * self.header.dim.getMipCount() ):
            mipOffsets.append( stream.readUInt64() )
        
        for i in range( self.header.fmt.getSurfaceCount() ):
            surface = rTextureSurfaceData()
             
            for j in range( self.header.dim.getMipCount() ):
                off = mipOffsets[ i * self.header.dim.getMipCount() + j ]
                
                # determine mip size
                nextOff = None
                nextMipOffsetIdx = i * self.header.dim.getMipCount() + j + 1
                if nextMipOffsetIdx < len( mipOffsets ):
                    nextOff = mipOffsets[ nextMipOffsetIdx ]
                else:
                    nextOff = stream.getSize()
                        
                # read mip data
                size = nextOff - off
                stream.setOffset( off )
                mip = stream.readBytes( size )
                surface.mips.append( mip )
                
            self.surfaces.append( surface )
                
    def write( self, stream ):
        self.header.write( stream )
        
        for face in self.faces:
            face.write( stream )
        
        offPos = stream.getOffset()
        off = offPos + ( 8 * self.header.fmt.getSurfaceCount() * self.header.dim.getMipCount() )
        for surface in self.surfaces:
            for mip in surface.mips:
                # write offset
                stream.setOffset( offPos )
                stream.writeUInt64( off )
                offPos = stream.getOffset()
                
                # write data
                stream.setOffset( off )
                stream.writeBytes( mip )
                off += len( mip )
                
    def loadBinaryFile( self, path ):
        self.read( NclBitStream( util.loadIntoByteArray( path ) ) )
        
    def saveBinaryFile( self, path ):
        stream = NclBitStream()
        self.write( stream )
        util.saveByteArrayToFile( path, stream.getBuffer() )
        
    def toDDS( self ):
        hasMips = self.header.dim.mipCount > 1
        isCubeMap = self.header.fmt.surfaceCount > 1
        
        dds = DDSFile()
        dds.header.dwFlags |= DDSD_LINEARSIZE
        if hasMips:
            dds.header.dwFlags |= DDSD_MIPMAPCOUNT
            dds.header.dwCaps |= DDSCAPS_MIPMAP
        if isCubeMap:
            dds.header.dwCaps |= DDSCAPS_COMPLEX
            dds.header.dwCaps2 |= DDS_CUBEMAP_ALLFACES
                   
        dds.header.dwHeight = self.header.dim.getHeight()
        dds.header.dwWidth = self.header.dim.getWidth()
        dds.header.dwMipMapCount = self.header.dim.getMipCount()   
        dds.buffer = bytearray()
        for surface in self.surfaces:
            for mip in surface.mips:
                dds.buffer += mip

        fourCC = rTextureSurfaceFmt.getDDSFormat( self.header.fmt.getSurfaceFmt() )
        if fourCC != DDS_FOURCC_NONE:
            blockSize = 16
            if fourCC == DDS_FOURCC_DXT1:
                blockSize = 8
            
            pitch = ddsCalcLinearSizeBlockCompressed( self.header.dim.getWidth(), self.header.dim.getHeight(), blockSize )
            dds.header.dwPitchOrLinearSize = pitch
            dds.header.ddspf.dwFlags |= DDPF_FOURCC
            dds.header.ddspf.dwFourCC = fourCC
        else:
            # TODO RGBA is assumed here
            dds.header.ddspf.dwFlags |= DDS_RGBA
            dds.header.ddspf.dwRGBBitCount = 32
            dds.header.ddspf.dwRBitMask = 0xff
            dds.header.ddspf.dwGBitMask = 0xff00
            dds.header.ddspf.dwBBitMask = 0xff0000
            dds.header.ddspf.dwABitMask = 0xff000000
            dds.header.dwPitchOrLinearSize = ddsCalcPitchBpp( dds.header.dwWidth, dds.header.ddspf.dwRGBBitCount )

        return dds
    
    def setDefaultCubeMapFaces( self ):
        self.faces.clear()
        
        face = rTextureFace()
        face.field00 = 0.4837379
        face.negative[0] = -0.05054046
        face.negative[1] = 0.04008521
        face.negative[2] = 0.01001853
        face.positive[0] = 0.005333615
        face.positive[1] = -0.03039154
        face.positive[2] = 0.1364427
        face.uv[0] = 0.01015308
        face.uv[1] = 0.02520043
        self.faces.append( face )
        
        face = rTextureFace()
        face.field00 = 1.357952
        face.negative[0] = 0.009200307
        face.negative[1] = -0.04620323
        face.negative[2] = 0.02067803
        face.positive[0] = 0.0100703
        face.positive[1] = -0.09296682
        face.positive[2] = 0.2509833
        face.uv[0] = 0.02939349
        face.uv[1] = -0.03288069
        self.faces.append( face )
        
        face = rTextureFace()
        face.field00 = 1.029677
        face.negative[0] = -0.04863077
        face.negative[1] = 0.01793304
        face.negative[2] = 0.02242514
        face.positive[0] = 0.009546677
        face.positive[1] = -0.02904901
        face.positive[2] = 0.221782
        face.uv[0] = 0.03200468
        face.uv[1] = -0.06776269
        self.faces.append( face )
    
    @staticmethod
    def fromDDS( dds: DDSFile ):
        tex = rTextureData()
        isCubeMap = dds.header.dwCaps2 & DDSCAPS2_CUBEMAP
        
        surfaceCount = 1
        if isCubeMap:
            surfaceCount = 6
        
        off = 0
        for i in range( surfaceCount ):
            surface = rTextureSurfaceData()
            fmt = None
            if dds.header.ddspf.dwFlags & DDPF_FOURCC:
                blockSize = 8
                fmt = rTextureSurfaceFmt.BM_OPA
                if dds.header.ddspf.dwFourCC != DDS_FOURCC_DXT1:
                    fmt = rTextureSurfaceFmt.BM_XLU
                    blockSize = 16
                
                width = dds.header.dwWidth 
                height = dds.header.dwHeight
                for i in range( dds.header.dwMipMapCount ):
                    size = ddsCalcLinearSizeBlockCompressed( width, height, blockSize )
                    mip = dds.buffer[off:off+size]
                    assert(len(mip) == size)
                    off += size
                    width //= 2
                    height //= 2
                    surface.mips.append( mip )
            else:
                # TODO LIN assumed here
                fmt = rTextureSurfaceFmt.LIN
                width = dds.header.dwWidth 
                height = dds.header.dwHeight
                for i in range( dds.header.dwMipMapCount ):
                    size = ddsCalcLinearSizeBpp( width, height, dds.header.ddspf.dwRGBBitCount )
                    mip = dds.buffer[off:off+size]
                    assert(len(mip) == size)
                    off += size
                    width = max( 1, width // 2 )
                    height = max( 1, height // 2 )
                    surface.mips.append( mip )

            tex.surfaces.append( surface )

        tex.header.dim.setMipCount( dds.header.dwMipMapCount )
        tex.header.dim.setHeight( dds.header.dwHeight )
        tex.header.dim.setWidth( dds.header.dwWidth )
        tex.header.fmt.setSurfaceFmt( fmt )        
        tex.header.fmt.setField3( 1 )
        tex.header.fmt.setField4( 0 )
        tex.header.fmt.setSurfaceCount( len( tex.surfaces ) )
        if isCubeMap:
            tex.header.desc.setDimensions( 6 )
            tex.setDefaultCubeMapFaces()
        
        return tex
        
def _test():
    # tex = rTextureData()
    # tex.loadBinaryFile( "X:/work/umvc3_model/samples/UMVC3ModelSamples/Ryu/Ryu_tex1_BM.241f5deb.tex" )
    # tex.saveBinaryFile( "test.tex" )
    # tex.toDDS().saveFile( "test.dds" )
    # newTex = rTextureData.fromDDS( DDSFile.fromFile( 'test.dds' ) )
    # newTex.saveBinaryFile( "testnew.tex" )
    tex = rTextureData()
    tex.loadBinaryFile( "X:\\game\\platform\\pc\\Ultimate Marvel vs. Capcom 3\\nativePCx64\\UserShader\\toon_Black_BM_HQ.tex" )
    tex.toDDS().saveFile( "X:\\game\\platform\\pc\\Ultimate Marvel vs. Capcom 3\\nativePCx64\\UserShader\\toon_Black_BM_HQ.dds" )
    newTex = rTextureData.fromDDS( DDSFile.fromFile("X:\\game\\platform\\pc\\Ultimate Marvel vs. Capcom 3\\nativePCx64\\UserShader\\toon_Black_BM_HQ.dds" ))
    newTex.saveBinaryFile( "X:\\game\\platform\\pc\\Ultimate Marvel vs. Capcom 3\\nativePCx64\\UserShader\\toon_Black_BM_HQ_new.tex" )
        
if __name__ == '__main__':
    _test()