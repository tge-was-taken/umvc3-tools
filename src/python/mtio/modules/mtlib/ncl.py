''' 
Noesis compatibility lib.
Wraps types in an interface mirroring that of Noesis' types.
'''
import struct
import math
import libtarget

def nclTupleToList( tup ):
    return [item for item in tup]

def nclEnsureList( val ):
    if isinstance( val, tuple ):
        return nclTupleToList( val )
    return val

class Endian:
    LITTLE = 0
    BIG = 1
    STRUCT_FORMAT = ['<', '>']

if not libtarget.noesis:
    import glm
    
    NclVec2 = glm.vec2
    NclVec3 = glm.vec3
    NclVec4 = glm.vec4
    NclMat43 = glm.mat4x3
    NclMat44 = glm.mat4x4
    
    def nclCreateVec4( *args ):
        if len( args ) == 1 and isinstance( args[0], glm.vec3 ):
            return glm.vec4( args[0][0], args[0][1], args[0][2], 1 )
        else:
            return glm.vec4( *args )
    
    def nclCreateMat43( *args ):
        if len( args ) == 1 and len( args[0] ) == 4 and isinstance( args[0][0], NclVec3 ):
            rows = args[0]
            return glm.mat4x3(  rows[0][0], rows[0][1], rows[0][2],
                                rows[1][0], rows[1][1], rows[1][2],
                                rows[2][0], rows[2][1], rows[2][2],
                                rows[3][0], rows[3][1], rows[3][2])
            # return glm.mat4x3(  rows[0][0], rows[1][0], rows[2][0], rows[3][0],
            #                     rows[0][1], rows[1][1], rows[2][1], rows[3][1],
            #                     rows[0][2], rows[1][2], rows[2][2], rows[3][2],
            #                     )
        elif len( args ) == 0:
            return glm.mat4x3( 1 )
        else:
            return glm.mat4x3( *args )
    
    def nclCreateMat44( *args ):
        if len( args ) == 1 and len( args[0] ) == 4 and isinstance( args[0][0], glm.vec4 ):
            rows = args[0]
            return glm.mat4x4(  rows[0][0], rows[0][1], rows[0][2], rows[0][3],
                                rows[1][0], rows[1][1], rows[1][2], rows[1][3],
                                rows[2][0], rows[2][1], rows[2][2], rows[2][3],
                                rows[3][0], rows[3][1], rows[3][2], rows[3][3])
            # return glm.mat4x4(  rows[0][0], rows[1][0], rows[2][0], rows[3][0],
            #                     rows[0][1], rows[1][1], rows[2][1], rows[3][1],
            #                     rows[0][2], rows[1][2], rows[2][2], rows[3][2],
            #                     rows[0][3], rows[1][3], rows[2][3], rows[3][3])
        # elif len( args ) == 1 and len( args[0] ) == 4 and isinstance( args[0][0], glm.vec3 ):
        #     rows = args[0]
        #     return glm.mat4x4(  rows[0][0], rows[0][1], rows[0][2], 0,
        #                         rows[1][0], rows[1][1], rows[1][2], 0,
        #                         rows[2][0], rows[2][1], rows[2][2], 0,
        #                         rows[3][0], rows[3][1], rows[3][2], 1)
        elif len( args ) == 1 and isinstance( args[0], glm.mat4x3 ):
            rows = args[0]
            return glm.mat4x4(  rows[0][0], rows[0][1], rows[0][2], 0,
                                rows[1][0], rows[1][1], rows[1][2], 0,
                                rows[2][0], rows[2][1], rows[2][2], 0,
                                rows[3][0], rows[3][1], rows[3][2], 1)
            # return glm.mat4x4(  rows[0][0], rows[1][0], rows[2][0], rows[3][0],
            #                     rows[0][1], rows[1][1], rows[2][1], rows[3][1],
            #                     rows[0][2], rows[1][2], rows[2][2], rows[3][2],
            #                     0,          0,          0,          1)
        elif len( args ) == 0:
            return glm.mat4x4( 1 )
        else:
            return glm.mat4x4( *args )
    
    def nclNormalize( vec ):
        return glm.normalize( vec )
    
    def nclLength( vec ):
        return glm.length( vec )
    
    def nclLengthSq( vec ):
        return glm.length2( vec )
    
    def nclDot( left, right ):
        return glm.dot( left, right )
    
    def nclCross( left, right ):
        return glm.cross( left, right )
    
    def nclInverse( mtx ):
        return glm.inverse( mtx )
    
    def nclTranspose( mtx ):
        return glm.transpose( mtx )
    
    def nclScale( scalar ):
        temp = glm.mat4()
        return glm.scale( temp, glm.vec3( scalar, scalar, scalar ) )
    
    def nclTranslation( vec ):
        return glm.translation( vec )
    
    def nclTransform( vec, mtx ):
        if isinstance( vec, glm.vec3 ):
            res = mtx * glm.vec4( vec[0], vec[1], vec[2], 1 )
            return glm.vec3( res[0], res[1], res[2] )
        else:
            return mtx * vec
        
    def nclMultiply( mtxL, mtxR ):
        return mtxR * mtxL
        
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
                
else:
    from inc_noesis import *
    
    NclBitStream = NoeBitStream
    
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
        
        def __eq__( self, other ):
            if isinstance( other, NclVec2 ):  
                return self.vec2 == other.vec2
            else:
                return False
    
    NclVec3 = NoeVec3
    NclVec4 = NoeVec4
    nclCreateMat44 = NoeMat44
    NclMat43 = NoeMat43
    
    def nclNormalize( vec ):
        return vec.normalize()
    
    def nclLength( vec ):
        return vec.length()
    
    def nclLengthSq( vec ):
        return vec.lengthSq()
    
    def nclDot( left, right ):
        return left.dot( right )
    
    def nclCross( left, right ):
        return left.cross( right )
    
    def nclInverse( mtx ):
        return mtx.inverse()
    
    def nclTranspose( mtx ):
        return mtx.transpose()
    
    def nclScale( scale ):
        mtx = NoeMat43()
        mtx[0][0] = scale # s 0 0 0
        mtx[1][1] = scale # 0 s 0 0
        mtx[2][2] = scale # 0 0 s 0
        #mtx[3][3] = scale # 0 0 0 s
        return mtx
    
    def nclTranslation( vec ):
        mtx = NoeMat43()
        mtx[3] = vec
        return mtx
    
    def nclCreateVec4( *args ):
        if len( args ) == 1 and isinstance( args[0], NoeVec3 ):
            return NoeVec4( ( args[0][0], args[0][1], args[0][2], 1 ) )
        else:
            return NoeVec4( *args )
    
    def nclCreateMat44( *args ):
        if len( args ) == 1 and isinstance( args[0], tuple ):
            return NoeMat44( *args )
        elif len( args ) == 1 and isinstance( args[0], NoeMat43 ):
            return args[0].toMat44()
        elif len( args ) == 1 and isinstance( args[0], NoeMat44 ):
            return args[0]
        elif len( args ) == 0:
            return NoeMat44()
        else:
            return NoeMat44( *args )
    
    def nclCreateMat43( *args ):
        if len( args ) == 1 and isinstance( args[0], tuple ):
            return NoeMat43( *args )
        elif len( args ) == 1 and isinstance( args[0], NoeMat43 ):
            return args[0]
        elif len( args ) == 1 and isinstance( args[0], NoeMat44 ):
            return args[0].toMat43()
        elif len( args ) == 0:
            return NoeMat43()
        else:
            return NoeMat43( *args )
    
    def nclTransform( vec, mtx ):
        if isinstance( mtx, NoeMat44 ) and isinstance( vec, NoeVec3 ):
            vec4 = NoeVec4((vec[0], vec[1], vec[2], 1))
            res = (mtx * vec4)
            return NoeVec3((res[0], res[1], res[2]))
        else:
            return mtx * vec
        
    def nclMultiply( mtxL, mtxR ):
        return mtxL * mtxR

# doesn't work
# NclVec2.x = lambda x : x[0]
# NclVec2.y = lambda x : x[1]
# NclVec3.x = lambda x : x[0]
# NclVec3.y = lambda x : x[1]
# NclVec3.z = lambda x : x[2]
# NclVec4.x = lambda x : x[0]
# NclVec4.y = lambda x : x[1]
# NclVec4.z = lambda x : x[2]
# NclVec4.w = lambda x : x[3]

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
    return nclCreateMat44( ( self.readVec4(), self.readVec4(), self.readVec4(), self.readVec4() ) )

def readMat43( self ):
    return nclCreateMat43( ( self.readVec3(), self.readVec3(), self.readVec3(), self.readVec3() ) )

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

if libtarget.noesis:
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
    
# TESTING
def _testNoesis():
    #(matrix3 [0.0267394,0.225189,-0.321831] [0.0083079,-0.322828,-0.225196] [-0.392704,0.00850355,-0.0266778] [1.51196,7.70545,58.7118])
    # m = _NclMat43( ( ( 0.0267394,0.225189,-0.321831), ( 0.0083079,-0.322828,-0.225196 ), ( -0.392704,0.00850355,-0.0266778 ), ( 1.51196,7.70545,58.7118 ) ) )
    # p = _NclVec3( ( 8.768, 10.554, 11.735 ))
    # s = 2
    
    m2 = NoeMat43( ( ( 0.0267394,0.225189,-0.321831 ), ( 0.0083079,-0.322828,-0.225196 ), ( -0.392704,0.00850355,-0.0266778 ), ( 1.51196,7.70545,58.7118 ) ) )
    p2 = NoeVec3( ( 8.768, 10.554, 11.735 ) )
    s2 = 2
    
    print( 'mul', m2 * m2 )
    print( 'inv',  m2.inverse() )
    print( 'tra  ', m2.transpose() )
    
def _testGlm():
    print('hello glm')
    vec2 = glm.vec2((0, 1))
    print( vec2 )
    print( vec2[1] == 1 )
    
    import inspect
    for m in inspect.getmembers(NclMat43):
        if not m[0].startswith('__'):
            print(m)
    
    # m2 = NclMat43( ( ( 0.0267394,0.225189,-0.321831 ), ( 0.0083079,-0.322828,-0.225196 ), ( -0.392704,0.00850355,-0.0266778 ), ( 1.51196,7.70545,58.7118 ) ) )
    # p2 = NclVec3( ( 8.768, 10.554, 11.735 ) )
    # s2 = 2
    
    # print( 'mul', m2 * m2 )
    # print( 'inv',  m2.inverse() )
    # print( 'tra  ', m2.transpose() )
    
if libtarget.noesis:
    _testNoesis() 
    
if __name__ == '__main__':
    _testGlm()