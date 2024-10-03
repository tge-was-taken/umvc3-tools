'''
Vertex component encoding & decoding module.
'''

import struct
import binascii
import math
import target
import util

from ncl import *
 
import libtarget

if libtarget.noesis:
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
    return (v >= -1 and v <= 1) or v == float('nan')

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

# type 6
def decodeFU16( val ):
    return float( val / 65535 )

# type 7
def decodeS8( val ):
    return float( val )

# type 8
def decodeU8( val ):
    return float( val )

# type 9
def decodeFS8( val ):
    if target.current.name in ['aa-pc']:
        return float( util.s8( val ) / 127 )
    else:
        # mvc3-pc
        return float( ( val - 127 ) / 127 )

# type 10
def decodeFU8( val ):
    return float( val / 255 )

# type 11
def decodeX8Y8Z8W8( val ):
    return [decodeFS8( ( val & 0x000000FF ) >> 0 ), 
            decodeFS8( ( val & 0x0000FF00 ) >> 8 ), 
            decodeFS8( ( val & 0x00FF0000 ) >> 16 ), 
            decodeFS8( ( val & 0xFF000000 ) >> 24 )]

# type 13

# type 14
def decodeR8G8B8A8( val ):
    return [( val & 0x000000FF ) >> 0,
            ( val & 0x0000FF00 ) >> 8,
            ( val & 0x00FF0000 ) >> 16,
            ( val & 0xFF000000 ) >> 24 ]

# type 1
def encodeF32( val ):
    return float( val )

# type 3
def encodeU16( val ):
    return int( val ) & 0xFFFF

# type 4
def encodeS16( val ):
    return int( val )
        
# type 5
def encodeFS16( val ):
    #assert( isNormalizedFloat( val ) )
    if val < 0:
        return int( ~int( abs( val ) * -0x8000 ) + 1 ) & 0xFFFF
    else:
        return int( abs( val ) * 0x7FFF ) & 0xFFFF
    
# type 6
def encodeFU16( val ):
    return ( val * 0xFFFF ) & 0xFFFF

# type 7
def encodeS8( val ):
    return int( val ) & 0xFF

# type 8
def encodeU8( val ):
    return int( val ) & 0xFF

# type 9
def encodeFU8( val ):
    #assert( isNormalizedFloat( val ) )
    return int( val * 0xFF ) & 0xFF

# type 10
def encodeFS8( val ):
    val = 0 if math.isnan( val ) else val
    if target.current.name in ['aa-pc']:
        return int( val * 127 ) & 0xFF
    else:
        # mvc3-pc
        return int( ( val * 127 ) + 127 ) & 0xFF

# type 11
def encodeX8Y8Z8W8( val ):
    x = val[0]
    y = val[1]
    z = val[2]
    w = val[3] if len(val) > 3 else 1
    
    enc = (encodeFS8( x ) << 0  ) & 0x000000FF | \
          (encodeFS8( y ) << 8  ) & 0x0000FF00 | \
          (encodeFS8( z ) << 16 ) & 0x00FF0000 | \
          (encodeFS8( w ) << 24 ) & 0xFF000000
    return enc & 0xFFFFFFFF

# type 13

# type 14
def encodeR8G8B8A8( val ):
    enc = (val[0] << 0  ) & 0x000000FF | \
          (val[0] << 8  ) & 0x0000FF00 | \
          (val[0] << 16 ) & 0x00FF0000 | \
          (val[0] << 24 ) & 0xFF000000
    return enc & 0xFFFFFFFF


def decodeVertexComponent( compType, stream ):
    if   compType == 1: return [decodeF32(stream.readFloat())]
    elif compType == 2: return [decodeF16(stream.readUShort())]
    elif compType == 3: return [decodeU16(stream.readUShort())]
    elif compType == 4: return [decodeS16(stream.readShort())]
    elif compType == 5: return [decodeFS16(stream.readUShort())]
    elif compType == 6: return [decodeFU16(stream.readUShort())]
    elif compType == 7: return [decodeS8(stream.readUByte())]
    elif compType == 8: return [decodeU8(stream.readUByte())]
    elif compType == 9: return [decodeFS8(stream.readUByte())]
    elif compType == 10: return [decodeFU8(stream.readUByte())]
    elif compType == 11: return decodeX8Y8Z8W8( stream.readUInt() )
    # elif compType == 12: 
    elif compType == 13: return [decodeU8( stream.readUByte() )]
    elif compType == 14: return decodeR8G8B8A8( stream.readUInt() )
    else: raise Exception( "Unhandled vertex component type: " + str( compType ) )
    
def encodeVertexComponent( compType, val ):
    if   compType == 1:  return encodeF32( val )
    elif compType == 2:  return encodeF16( val )
    elif compType == 3:  return encodeU16( val )
    elif compType == 4:  return encodeS16( val )
    elif compType == 5:  return encodeFS16( val )
    elif compType == 6:  return encodeFU16( val )
    elif compType == 7:  return encodeS8( val )
    elif compType == 8:  return encodeU8( val )
    elif compType == 9:  return encodeFS8( val )
    elif compType == 10: return encodeFU8( val )
    elif compType == 11: return encodeX8Y8Z8W8( val )
    # elif compType == 12: 
    elif compType == 13: return encodeU8( val )
    elif compType == 14: return encodeR8G8B8A8( val )
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