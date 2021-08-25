import struct
import binascii

from mtncl import *
 
import mttarget

if mttarget.noesis:
    # Noesis implementation
    import noesis
    
    # type 2
    def encodeF16( val ):
        return noesis.encodeFloat16( val )
    
    # type 2
    def decodeF16( val ):
        return noesis.getFloat16( val )
# elif mttarget.numpy:
#     # Numpy implementation
#     import numpy

#     def encodeF16( val ):
#         return struct.unpack( "H", numpy.float16( val ).tobytes() )[0]
    
#     def decodeF16( val ):
#         buffer = struct.pack( "H", val ) 
#         return numpy.frombuffer( buffer, dtype=numpy.float16 )[0]
else:
    def encodeF16( float32 ):
        return float( struct.unpack( 'H', struct.pack( 'e', float32 ) )[0] )
    
    def decodeF16( float16 ):
        return float( struct.unpack( 'e', struct.pack( 'H', float16 ) )[0] )
    
    # Python implementation
    # https://davidejones.com/blog/python-precision-floating-point/
    # def encodeF16( float32 ):
    #     F16_EXPONENT_BITS = 0x1F
    #     F16_EXPONENT_SHIFT = 10
    #     F16_EXPONENT_BIAS = 15
    #     F16_MANTISSA_BITS = 0x3ff
    #     F16_MANTISSA_SHIFT =  (23 - F16_EXPONENT_SHIFT)
    #     F16_MAX_EXPONENT =  (F16_EXPONENT_BITS << F16_EXPONENT_SHIFT)

    #     a = struct.pack('>f',float32)
    #     b = binascii.hexlify(a)

    #     f32 = int(b,16)
    #     f16 = 0
    #     sign = (f32 >> 16) & 0x8000
    #     exponent = ((f32 >> 23) & 0xff) - 127
    #     mantissa = f32 & 0x007fffff
                
    #     if exponent == 128:
    #         f16 = sign | F16_MAX_EXPONENT
    #         if mantissa:
    #             f16 |= (mantissa & F16_MANTISSA_BITS)
    #     elif exponent > 15:
    #         f16 = sign | F16_MAX_EXPONENT
    #     elif exponent > -15:
    #         exponent += F16_EXPONENT_BIAS
    #         mantissa >>= F16_MANTISSA_SHIFT
    #         f16 = sign | exponent << F16_EXPONENT_SHIFT | mantissa
    #     else:
    #         f16 = sign
    #     return f16
    
    # def decodeF16( float16 ):
    #     s = int((float16 >> 15) & 0x00000001)    # sign
    #     e = int((float16 >> 10) & 0x0000001f)    # exponent
    #     f = int(float16 & 0x000003ff)            # fraction

    #     if e == 0:
    #         if f == 0:
    #             return int(s << 31)
    #         else:
    #             while not (f & 0x00000400):
    #                 f = f << 1
    #                 e -= 1
    #             e += 1
    #             f &= ~0x00000400
    #             #print(s,e,f)
    #     elif e == 31:
    #         if f == 0:
    #             return int((s << 31) | 0x7f800000)
    #         else:
    #             return int((s << 31) | 0x7f800000 | (f << 13))

    #     e = e + (127 -15)
    #     f = f << 13
    #     float32 = int((s << 31) | (e << 23) | f)
    #     return struct.unpack( '>f', struct.pack( '>L', float32 ) )[0]
    
def isNormalizedFloat( v ):
    return v >= -1 and v <= 1

def isNormalized( v ):
    if isinstance( v, float ): 
        return isNormalizedFloat( v )
    if isinstance( v, NclVec2 ): 
        return isNormalizedFloat( v[0] ) and isNormalizedFloat( v[1] )
    if isinstance( v, NclVec3 ):
        return isNormalizedFloat( v[0] ) and isNormalizedFloat( v[1] ) and isNormalizedFloat( v[2] )
    if isinstance( v, NclVec4 ):
        return isNormalizedFloat( v[0] ) and isNormalizedFloat( v[1] ) and isNormalizedFloat( v[2] ) and isNormalizedFloat( v[3] )
    raise Exception( "Unsupported value type" )

# type 1
def decodeF32( val ):
    return float( val )

# type 3
def decodeU16( val ):
    return float( val )

# type 4
def decodeS16( val ):
    return float( val )
        
# type 5
def decodeFS16( val ):
    '''
    65534 - 32767 =  32767 / 32767 = 1
    0     - 32767 = -32767 / 32767 = -1
    '''
    '''
    65534 / 32767 = 2
    '''
    assert( val >= 0 )

    # unsigned version
    #return float( ( val - 32767 ) / 32767 )

    # assumes val is signed
    return float( val / 32767 )

# type 7
def decodeS8( val ):
    return float( val )

# type 8
def decodeU8( val ):
    return float( val )

# type 9
def decodeFS8( val ):
    # assumes val is unsigned
    return float( ( val - 127 ) / 127 )

# type 10
def decodeFU8( val ):
    '''
    254 - 127 =  127 / 127 =  1
    0   - 127 = -127 / 127 = -1
    '''
    return float( ( val - 127 ) / 127 )

# type 11
def decompressNormals32_10_10_10_2(bits):
    x = (bits & 0x3FF)
    y = (bits >> 10) & 0x3FF
    z = (bits >> 20) & 0x3FF
    w = (bits >> 30) & 0xFF
    return (float( (x - 511) / 512 ), float( (y - 511) / 512 ), float( (z - 511) / 512 ), float( w / 3 ))

def decompressNormalsU32_11_11_10(bits):
    x = ( ( bits       ) & 0x7FF ) / 0x7FF
    y = ( ( bits >> 11 ) & 0x7FF ) / 0x7FF
    z = ( ( bits >> 22 ) & 0x3FF ) / 0x3FF
    return [ float( x ), float( y ), float( z ) ]

def decompressNormalsS32_11_11_10(bits):
    x = ( ( ( bits       ) & 0x7FF ) - 0x3FF ) / ( 0x3FF + 1 )
    y = ( ( ( bits >> 11 ) & 0x7FF ) - 0x3FF ) / ( 0x3FF + 1 )
    z = ( ( ( bits >> 22 ) & 0x3FF ) - 0x1FF ) / ( 0x1FF + 1 )
    return [ float( x ), float( y ), float( z ) ]

# type 13

# type 14


# type 1
def encodeF32( val ):
    return float( val )

# type 3
def encodeU16( val ):
    return int( val ) & 0xFFFF
        
# type 5
def encodeFS16( val ):
    '''
     1  * 32767 =  32767 + 32767 = 65534
    -1  * 32767 = -32767 + 32767 = 0
    '''
    assert( isNormalizedFloat( val ) )
    return int( val * 32767 ) & 0xFFFF
    #return int( ( val * 32767 ) + 32767 ) & 0xFFFF

# type 7
def encodeS8( val ):
    return int( val ) & 0xFF

# type 8
def encodeU8( val ):
    return int( val ) & 0xFF

# type 9
def encodeFU8( val ):
    assert( isNormalizedFloat( val ) )
    return int( val * 0xFF ) & 0xFF

# type 10
def encodeFS8( val ):
    '''
    1  * 127 =  127 + 127 = 254
    -1 * 127 = -127 + 127 = 0
    '''
    assert( isNormalizedFloat( val ) )
    return int( ( val * 127 ) + 127 ) & 0xFF

# type 11
def decompressNormals32_10_10_10_2(bits):
    x = (bits & 0x3FF)
    y = (bits >> 10) & 0x3FF
    z = (bits >> 20) & 0x3FF
    w = (bits >> 30) & 0xFF
    return ( float( (x - 511) / 512 ), float( (y - 511) / 512 ), float( (z - 511) / 512 ), float( w / 3 ))

def decompressNormalsU32_11_11_10(bits):
    x = ( ( bits       ) & 0x7FF ) / 0x7FF
    y = ( ( bits >> 11 ) & 0x7FF ) / 0x7FF
    z = ( ( bits >> 22 ) & 0x3FF ) / 0x3FF
    vec = [ float( x ), float( y ), float( z ) ]
    return vec

def decompressNormalsS32_11_11_10(bits):
    x = ( ( ( bits       ) & 0x7FF ) - 0x3FF ) / ( 0x3FF + 1 )
    y = ( ( ( bits >> 11 ) & 0x7FF ) - 0x3FF ) / ( 0x3FF + 1 )
    z = ( ( ( bits >> 22 ) & 0x3FF ) - 0x1FF ) / ( 0x1FF + 1 )
    return [ float( x ), float( y ), float( z ) ]

# type 13

# type 14
# def decodeVertexComponent( compType, stream ):
#     if   compType == 1: return [stream.readFloat()]
#     elif compType == 2: return [stream.readHalfFloat()]
#     elif compType == 3: return [stream.readUShort()]
#     elif compType == 4: return [stream.readHalfFloat()] # half float?
#     elif compType == 5: return [decodeFS16(stream.readShort())]
#     elif compType == 8: return [stream.readUByte()]
#     elif compType == 9: return [decodeFS8(stream.readUByte())]
#     elif compType == 10: return [stream.readByte()]
#     elif compType == 11: return decompressNormalsU32_11_11_10( stream.readUInt() )
#     else: raise Exception( "Unhandled vertex component type: " + str( compType ) )


def decodeVertexComponent( compType, stream ):
    if   compType == 1: return [decodeF32(stream.readFloat())]
    elif compType == 2: return [decodeF16(stream.readUShort())]
    elif compType == 3: return [decodeU16(stream.readUShort())]
    elif compType == 4: return [decodeF16(stream.readUShort())]
    elif compType == 5: return [decodeFS16(stream.readUShort())]
    elif compType == 8: return [decodeU8(stream.readUByte())]
    elif compType == 9: return [decodeFS8(stream.readUByte())]
    elif compType == 10: return [decodeFU8(stream.readUByte())]
    elif compType == 11: return decompressNormalsU32_11_11_10( stream.readUInt() )
    else: raise Exception( "Unhandled vertex component type: " + str( compType ) )
    
def decodeVertexInputLayout( inputInfo, reader, writer, p ):
    '''
    Returns new component count
    '''
    start = writer.tell()
    reader.seek( p + inputInfo.offset )
    for i in range( inputInfo.componentCount ):
        for v in decodeVertexComponent( inputInfo.type, reader ):
            writer.writeFloat( v )
    end = writer.tell()
    size = end - start
    newComponentCount = int(size / 4)
    return newComponentCount

def decodeVertexBuffer( shaderInfo, vertexBuffer, vertexCount, stride ):
    '''
    Returns (buffer, newStride, newInputs)
    '''
    reader = NclBitStream( vertexBuffer )
    writer = NclBitStream()
    newInputs = []
    newStride = 0
    
    if vertexCount > 0:
        for key, value in shaderInfo.inputsByName.items():
            newOffset = writer.tell()
            newComponentCount = 0
            for inputInfo in value:
                newComponentCount += decodeVertexInputLayout( inputInfo, reader, writer, 0 )
            newInputs.append( ( key, newOffset, newComponentCount ) )
            
        newStride = writer.tell()
        
        for i in range(1, vertexCount):
            p = i * stride
            for key, value in shaderInfo.inputsByName.items():
                for inputInfo in value:
                    decodeVertexInputLayout( inputInfo, reader, writer, p )
    
    return (writer.getBuffer(), newStride, newInputs)
    
def test():
    encFS16Val = 14691
    decFS16Val = decodeFS16( encFS16Val )
    encFS16Val2 = encodeFS16( decFS16Val )
    assert( encFS16Val2 == encFS16Val )
    
    encFS8Val = 186
    decFS8Val = decodeFS8( encFS8Val )
    decFS8Val2 = encodeFS8( decFS8Val )
    assert( decFS8Val2 == encFS8Val )
    
    encF16Val = 0x3B3B
    decF16Val = decodeF16( encF16Val )
    decF16Val2 = encodeF16( decF16Val )
    assert( decF16Val2 == encF16Val )
    
    
if __name__ == '__main__':
    test()