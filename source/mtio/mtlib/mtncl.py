''' 
Noesis compatibility lib.
Wraps types in an interface mirroring that of Noesis' types.
'''

import struct
import math
import mttarget

class NclVec2:
    def __init__( self, vec2 = (0,0) ):
        self.vec2 = vec2
        
    def __getitem__( self, key ):
        return self.vec2[key]
        
    def __setitem__( self, key, value ):
        self.vec2 = nclEnsureList( self.vec2 )
        self.vec2[key] = value
        
    def __repr__( self ):
        return str( self.vec2 )
    
if mttarget.noesis:
    from inc_noesis import *
    
    # map aliases
    NclBitStream = NoeBitStream
    NclVec3 = NoeVec3
    NclVec4 = NoeVec4
    NclMat44 = NoeMat44
    NclMat43 = NoeMat43
    
    print("ncl: noesis")
else:
    def nclTupleToList( tup ):
        return [item for item in tup]

    def nclEnsureList( val ):
        if isinstance( val, tuple ):
            return nclTupleToList( val )
        return val

    class NclVec3:
        def __init__( self, vec3 = (0,0,0) ):
            self.vec3 = vec3
            
        def __getitem__( self, key ):
            return self.vec3[key]
            
        def __setitem__( self, key, value ):
            self.vec3 = nclEnsureList( self.vec3 )
            self.vec3[key] = value
            
        def __repr__( self ):
            return str( self.vec3 )
        
        def toVec4( self, w = 1 ):
            return NclVec4( ( self[0], self[1], self[2], w ) )
        
        def toList( self ):
            return nclEnsureList( self.vec3 )
            
    class NclVec4:
        def __init__( self, vec4 = (0,0,0,0) ):
            self.vec4 = vec4
            
        def __getitem__( self, key ):
            return self.vec4[key]
            
        def __setitem__( self, key, value ):
            self.vec4 = nclEnsureList( self.vec4 )
            self.vec4[key] = value
            
        def __repr__( self ):
            return str( self.vec4 )
        
        def toVec3( self ):
            return NclVec3( ( self[0], self[1], self[2] ) )
        
        def toList( self ):
            return nclEnsureList( self.vec4 )
        
    identityMat43Tuple = ( NclVec3((1.0, 0.0, 0.0)),        NclVec3((0.0, 1.0, 0.0)),       NclVec3((0.0, 0.0, 1.0)),       NclVec3((0.0, 0.0, 0.0)) )
    identityMat44Tuple = ( NclVec4((1.0, 0.0, 0.0, 0.0)),   NclVec4((0.0, 1.0, 0.0, 0.0)),  NclVec4((0.0, 0.0, 1.0, 0.0)),  NclVec4((0.0, 0.0, 0.0, 1.0)) )
        
    class NclMat43:
        def __init__( self, mat43 = identityMat43Tuple ):
            self.mat43 = mat43
            
        def __getitem__( self, key ):
            return self.mat43[key]
            
        def __setitem__( self, key, value ):
            self.mat43[key] = value
            
        def __repr__( self ):
            return str( self.mat43 )
        
        def __rmul__( self, other ):
            return self.__mul__( other )
        
        def __mul__( self, other ):
            if isinstance( other, NclMat43 ):
                # 1 0 0 0
                # 0 1 0 0
                # 0 0 1 0
                # 0 0 0 1
                
                m11 = self[0][0] * other[0][0] + self[0][1] * other[1][0] + self[0][2] * other[2][0]
                m12 = self[0][0] * other[0][1] + self[0][1] * other[1][1] + self[0][2] * other[2][1]
                m13 = self[0][0] * other[0][2] + self[0][1] * other[1][2] + self[0][2] * other[2][2]
                
                m21 = self[1][0] * other[0][0] + self[1][1] * other[1][0] + self[1][2] * other[2][0]
                m22 = self[1][0] * other[0][1] + self[1][1] * other[1][1] + self[1][2] * other[2][1]
                m23 = self[1][0] * other[0][2] + self[1][1] * other[1][2] + self[1][2] * other[2][2]
                
                m31 = self[2][0] * other[0][0] + self[2][1] * other[1][0] + self[2][2] * other[2][0]
                m32 = self[2][0] * other[0][1] + self[2][1] * other[1][1] + self[2][2] * other[2][1]
                m33 = self[2][0] * other[0][2] + self[2][1] * other[1][2] + self[2][2] * other[2][2]
                
                m41 = self[3][0] * other[0][0] + self[3][1] * other[1][0] + self[3][2] * other[2][0] + other[3][0]
                m42 = self[3][0] * other[0][1] + self[3][1] * other[1][1] + self[3][2] * other[2][1] + other[3][1]
                m43 = self[3][0] * other[0][2] + self[3][1] * other[1][2] + self[3][2] * other[2][2] + other[3][2]
                
                return NclMat43( ( NclVec3( ( m11, m12, m13 ) ), 
                                   NclVec3( ( m21, m22, m23 ) ),
                                   NclVec3( ( m31, m32, m33 ) ), 
                                   NclVec3( ( m41, m42, m43 ) ) ) )
            elif isinstance( other, NclMat44 ):
                return self.toMat44() * other
            else:
                return NotImplemented
            
        def toMat44( self ):
            return NclMat44( ( self[0].toVec4( 0 ), self[1].toVec4( 0 ), self[2].toVec4( 0 ), self[3].toVec4( 1 ) ) )
        
        @staticmethod
        def createScale( scale ):
            mtx = NclMat43()
            mtx[0][0] = scale # s 0 0
            mtx[1][1] = scale # 0 s 0
            mtx[2][2] = scale # 0 0 s
                              # 0 0 0
            return mtx
            
    class NclMat44:
        def __init__( self, mat44 = identityMat44Tuple ):
            self.mat44 = mat44
            
        def __getitem__( self, key ):
            return self.mat44[key]
            
        def __setitem__( self, key, value ):
            self.mat44[key] = value
            
        def __repr__( self ):
            return str( self.mat44 )
        
        def __mul__( self, other ):
            if isinstance( other, NclMat44 ):
                m11 = self[0][0] * other[0][0] + self[0][1] * other[1][0] + self[0][2] * other[2][0] + self[0][3] * other[3][0]
                m12 = self[0][0] * other[0][1] + self[0][1] * other[1][1] + self[0][2] * other[2][1] + self[0][3] * other[3][1]
                m13 = self[0][0] * other[0][2] + self[0][1] * other[1][2] + self[0][2] * other[2][2] + self[0][3] * other[3][2]
                m14 = self[0][0] * other[0][3] + self[0][1] * other[1][3] + self[0][2] * other[2][3] + self[0][3] * other[3][3]
                
                m21 = self[1][0] * other[0][0] + self[1][1] * other[1][0] + self[1][2] * other[2][0] + self[1][3] * other[3][0]
                m22 = self[1][0] * other[0][1] + self[1][1] * other[1][1] + self[1][2] * other[2][1] + self[1][3] * other[3][1]
                m23 = self[1][0] * other[0][2] + self[1][1] * other[1][2] + self[1][2] * other[2][2] + self[1][3] * other[3][2]
                m24 = self[1][0] * other[0][3] + self[1][1] * other[1][3] + self[1][2] * other[2][3] + self[1][3] * other[3][3]
                
                m31 = self[2][0] * other[0][0] + self[2][1] * other[1][0] + self[2][2] * other[2][0] + self[2][3] * other[3][0]
                m32 = self[2][0] * other[0][1] + self[2][1] * other[1][1] + self[2][2] * other[2][1] + self[2][3] * other[3][1]
                m33 = self[2][0] * other[0][2] + self[2][1] * other[1][2] + self[2][2] * other[2][2] + self[2][3] * other[3][2]
                m34 = self[2][0] * other[0][3] + self[2][1] * other[1][3] + self[2][2] * other[2][3] + self[2][3] * other[3][3]
                
                m41 = self[3][0] * other[0][0] + self[3][1] * other[1][0] + self[3][2] * other[2][0] + self[3][3] * other[3][0]
                m42 = self[3][0] * other[0][1] + self[3][1] * other[1][1] + self[3][2] * other[2][1] + self[3][3] * other[3][1]
                m43 = self[3][0] * other[0][2] + self[3][1] * other[1][2] + self[3][2] * other[2][2] + self[3][3] * other[3][2]
                m44 = self[3][0] * other[0][3] + self[3][1] * other[1][3] + self[3][2] * other[2][3] + self[3][3] * other[3][3]        
                
                return NclMat44( ( NclVec4( ( m11, m12, m13, m14 ) ), 
                                   NclVec4( ( m21, m22, m23, m24 ) ),
                                   NclVec4( ( m31, m32, m33, m34 ) ), 
                                   NclVec4( ( m41, m42, m43, m44 ) ) ) )
            elif isinstance( other, NclMat43 ):
                return self * other.toMat44()
            else:
                return NotImplemented
        
        def toMat43( self ):
            return NclMat43( ( self[0].toVec3(), self[1].toVec3(), self[2].toVec3(), self[3].toVec3() ) )
        
        @staticmethod
        def createScale( scale ):
            mtx = NclMat44()
            mtx[0][0] = scale # s 0 0 0
            mtx[1][1] = scale # 0 s 0 0
            mtx[2][2] = scale # 0 0 s 0
                              # 0 0 0 1
            return mtx

    class Endian:
        LITTLE = 0
        BIG = 1
        STRUCT_FORMAT = ['<', '>']

    class NclBitStream:
        def __init__( self, buffer = None, endian = Endian.LITTLE ):
            self.buffer = buffer
            self.size = 0
            self.offset = 0
            self.capacity = 0
            self.setEndian( endian )

            if self.buffer != None:
                self.size = len( self.buffer )
                self.capacity = self.size
            else:
                self.buffer = bytearray( 1024 * 1024 )
                self.size = 0
                self.capacity = len( self.buffer )
                
        def _ensureCapacity( self, size ):
            while self.offset + size > self.capacity:
                oldCapacity = self.capacity
                self.capacity *= 2
                self.buffer.extend([0] * ( self.capacity - oldCapacity ) )
            
        def _writeArray( self, size, fmt, *data ):
            self._ensureCapacity( size )
            struct.pack_into( self.endianFmt + fmt, self.buffer, self.offset, *data )
            self.offset += size
            self.size = max( self.size, self.offset )
            
        def _write( self, size, fmt, data ):
            self._ensureCapacity( size )
            struct.pack_into( self.endianFmt + fmt, self.buffer, self.offset, data )
            self.offset += size
            self.size = max( self.size, self.offset )
            
        def _read( self, size, fmt ):
            data = struct.unpack_from( self.endianFmt + fmt, self.buffer, self.offset )
            self.offset += size
            return data
                
        def getBuffer( self ):
            if self.capacity > self.size:
                return self.buffer[0:self.size]
            else:
                return self.buffer
        
        def getSize( self ):
            return self.size
        
        def getOffset( self ):
            return self.offset
        
        def setOffset( self, offset ):
            self.offset = offset
        
        def setEndian( self, endian ):
            self.endian = endian
            self.endianFmt = Endian.STRUCT_FORMAT[ self.endian ]
            
        def checkEOF( self ):
            return self.getOffset() >= self.getSize()
        
        def writeBytes( self, data ):
            self._writeArray( len(data), "B" * len(data), *data )
                
        def writeByte( self, data ):
            self._ensureCapacity( 1 )
            self.buffer[ self.offset ] = data & 0xFF
            self.offset += 1
            
        def writeBool( self, data ):
            self.writeByte( data )
            
        def writeUByte( self, data ):
            self.writeByte( data )
            
        def writeShort( self, data ):
            self._write( 2, "h", data )
            
        def writeUShort( self, data ):
            self._write( 2, "H", data & 0xFFFF )
            
        def writeInt( self, data ):
            self._write( 4, "i", data )
            
        def writeUInt( self, data ):
            self._write( 4, "I", data & 0xFFFFFFFF  )
            
        def writeInt64( self, data ):
            self._write( 8, "q", data )
            
        def writeUInt64( self, data ):
            self._write( 8, "Q", data & 0xFFFFFFFFFFFFFFFF )
            
        def writeFloat( self, data ):
            self._write( 4, "f", data )
            
        def writeDouble( self, data ):
            self._write( 8, "d", data )
            
        def readBytes( self, count ):
            return bytes( self._read( count, "B" * count ) )
            
        def readBool( self ):
            return self._read( 1, "B" )[0] != 0
        
        def readByte( self ):
            return self._read( 1, "b" )[0]
        
        def readUByte( self ):
            return self._read( 1, "B" )[0]
        
        def readShort( self ):
            return self._read( 2, "h" )[0]
        
        def readUShort( self ):
            return self._read( 2, "H" )[0]
        
        def readInt( self ):
            return self._read( 4, "i" )[0]
        
        def readUInt( self ):
            return self._read( 4, "I" )[0]
        
        def readFloat( self ):
            return self._read( 4, "f" )[0]
        
        def readDouble( self ):
            return self._read( 4, "d" )[0]
        
        def readInt64( self ):
            return self._read( 8, "q" )[0]
        
        def readUInt64( self ):
            return self._read( 8, "Q" )[0]
        
        def readString( self ):
            buffer = bytearray()
            b = self.readByte()
            s = ""
            while b != 0:
                buffer.append( b )
                b = self.readByte()
                
            return buffer.decode( "ascii" )
        
# bind extension methods after binding type names
def writeVec2( self, value ):
    self.writeFloat( value[0] )
    self.writeFloat( value[1] )

def writeVec3( self, value ):
    self.writeFloat( value[0] )
    self.writeFloat( value[1] )
    self.writeFloat( value[2] )
    
def writeVec4( self, value ):
    self.writeFloat( value[0] )
    self.writeFloat( value[1] )
    self.writeFloat( value[2] )
    self.writeFloat( value[3] )
    
def writeMat44( self, value ):
    self.writeVec4( value[0] )
    self.writeVec4( value[1] )
    self.writeVec4( value[2] )
    self.writeVec4( value[3] )
    
def writeMat43( self, value ):
    self.writeVec3( value[0] )
    self.writeVec3( value[1] )
    self.writeVec3( value[2] )
    self.writeVec3( value[3] )

def readVec2( self ):
    return NclVec3( ( self.readFloat(), self.readFloat() ) )

def readVec3( self ):
    return NclVec3( ( self.readFloat(), self.readFloat(), self.readFloat() ) )

def readVec4( self ):
    return NclVec4( ( self.readFloat(), self.readFloat(), self.readFloat(), self.readFloat() ) )

def readMat44( self ):
    return NclMat44( ( self.readVec4(), self.readVec4(), self.readVec4(), self.readVec4() ) )

def readMat43( self ):
    return NclMat43( ( self.readVec3(), self.readVec3(), self.readVec3(), self.readVec3() ) )

# bind extensions
NclBitStream.writeVec2 = writeVec2
NclBitStream.writeVec3 = writeVec3
NclBitStream.writeVec4 = writeVec4
NclBitStream.writeMat44 = writeMat44
NclBitStream.writeMat43 = writeMat43
NclBitStream.readVec2 = readVec2
NclBitStream.readVec3 = readVec3
NclBitStream.readVec4 = readVec4
NclBitStream.readMat44 = readMat44
NclBitStream.readMat43 = readMat43

if mttarget.noesis:
    # bind extensions to NoeBitStream as well
    NoeBitStream.writeVec2 = writeVec2
    NoeBitStream.writeVec3 = writeVec3
    NoeBitStream.writeVec4 = writeVec4
    NoeBitStream.writeMat44 = writeMat44
    NoeBitStream.writeMat43 = writeMat43
    NoeBitStream.readVec2 = readVec2
    NoeBitStream.readVec3 = readVec3
    NoeBitStream.readVec4 = readVec4
    NoeBitStream.readMat44 = readMat44
    NoeBitStream.readMat43 = readMat43