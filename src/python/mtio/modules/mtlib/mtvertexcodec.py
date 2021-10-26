'''
Vertex component encoding & decoding module.
'''

import struct
import binascii
import math

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
else:
    def encodeF16( float32 ):
        return int( struct.unpack( 'H', struct.pack( 'e', float32 ) )[0] )
    
    def decodeF16( float16 ):
        return float( struct.unpack( 'e', struct.pack( 'H', float16 ) )[0] )
    
def isNormalizedFloat( v ):
    return True
    #return v >= -1 and v <= 1

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
    #assert( val < 0x8000 )
    # sign = -1 if val & 0x8000 else 1
    # imm = val & ~0x8000
    # return float( ( imm / (0x8000-1) ) * sign )
    return float( val / 32767 )

# type 7
def decodeS8( val ):
    return float( val )

# type 8
def decodeU8( val ):
    return float( val )

# type 9
def decodeFS8( val ):
    return float( ( val - 127 ) / 127 )

# type 10
def decodeFU8( val ):
    return float( val / 255 )

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
    assert( isNormalizedFloat( val ) )
    if val < 0:
        return int( ~int( abs( val ) * -0x8000 ) + 1 ) & 0xFFFF
    else:
        return int( abs( val ) * 0x7FFF ) & 0xFFFF

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
    assert( isNormalizedFloat( val ) )
    val = 0 if math.isnan( val ) else val
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

    table = [
        1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0,
        -0.0, -0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9, -1.0
    ]
    
    
if __name__ == '__main__':
    test()