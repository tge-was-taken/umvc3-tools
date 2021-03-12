# MT framework model loader
import yaml
from zlib import crc32
import io

NCL_SEEK_ABS = 0
NCL_SEEK_REL = 1
NCL_BIGENDIAN = 1
NCL_LITTLEENDIAN = 0

class NclBitStream:    
    def __init__(self, buffer):
        self.position = 0
        self.buffer = buffer
        self.size = len(buffer)
        self.offsetStack = []
        self.setEndian(NCL_LITTLEENDIAN)
        
    def getBuffer(self, startOfs = None, endOfs = None):
        if startOfs is not None and endOfs is not None:
            return self.buffer[startOfs:endOfs]
        else:
            return self.buffer
        
    def getSize(self):
        return self.size
    
    def setOffset(self, ofs):
        pass
    
    def getOffset(self):
        pass
    
    def setBitOffset(self, ofs):
        pass
    
    def getBitOffset(self):
        pass
    
    def pushOffset(self):
        self.offsetStack.append((self.getOffset(), self.getBitOffset()))
        
    def popOffset(self):
        byteOffset, bitOffset = self.offsetStack.pop()
        self.setOffset(byteOffset)
        self.setBitOffset(bitOffset)
  
    def setEndian(self, bigEndian = NCL_LITTLEENDIAN):
        self.endian = bigEndian
        
    def setByteEndianForBits(self, bigEndian = NCL_LITTLEENDIAN):
        pass
    
    def checkEOF(self):
        return self.getOffset() >= self.getSize()
    
    def writeBytes(self, data):
        pass

    def writeBits(self, val, numBits):
        pass
    
    def writeBool(self, val):
        pass

    def writeByte(self, val):
        pass

    def writeUByte(self, val):
        pass

    def writeShort(self, val):
        pass

    def writeUShort(self, val):
        pass

    def writeInt(self, val):
        pass

    def writeUInt(self, val):
        pass

    def writeFloat(self, val):
        pass

    def writeDouble(self, val):
        pass

    def writeInt64(self, val):
        pass

    def writeUInt64(self, val):
        pass

    def writeHalfFloat(self, val):
        pass

    def writeString(self, str, writeTerminator = 1):
        pass

    def readBytes(self, numBytes):
        value = self.buffer[self.position:self.position+numBytes]
        self.position += numBytes
        value

    def readBits(self, numBits):
        pass

    def readRevBits(self, numBits):
        pass

    def readBool(self):
        return self.readByte() == 1

    def readByte(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<b", self.buffer, self.position)
        else:
            value = struct.unpack_from(">b", self.buffer, self.position)
        
        self.position += 1
        return value
    
    def readUByte(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<B", self.buffer, self.position)
        else:
            value = struct.unpack_from(">B", self.buffer, self.position)
        
        self.position += 1
        return value
    
    def readShort(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<h", self.buffer, self.position)
        else:
            value = struct.unpack_from(">h", self.buffer, self.position)
        
        self.position += 2
        return value
    
    def readUShort(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<H", self.buffer, self.position)
        else:
            value = struct.unpack_from(">H", self.buffer, self.position)
        
        self.position += 2
        return value
    
    def readInt(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<l", self.buffer, self.position)
        else:
            value = struct.unpack_from(">l", self.buffer, self.position)
        
        self.position += 4
        return value
    
    def readUInt(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<L", self.buffer, self.position)
        else:
            value = struct.unpack_from(">L", self.buffer, self.position)
        
        self.position += 4
        return value
    
    def readFloat(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<f", self.buffer, self.position)
        else:
            value = struct.unpack_from(">f", self.buffer, self.position)
        
        self.position += 4
        return value
    
    def readDouble(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<d", self.buffer, self.position)
        else:
            value = struct.unpack_from(">d", self.buffer, self.position)
        
        self.position += 8
        return value
    
    def readInt64(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<q", self.buffer, self.position)
        else:
            value = struct.unpack_from(">q", self.buffer, self.position)
        
        self.position += 8
        return value
    
    def readUInt64(self):
        if (self.endianness == NCL_LITTLEENDIAN):
            value = struct.unpack_from("<Q", self.buffer, self.position)
        else:
            value = struct.unpack_from(">Q", self.buffer, self.position)
        
        self.position += 8
        return value
    
    def readUInt24(self):
        pass 

    def readHalfFloat(self):
        pass

    def readString(self):
        pass

    def seek(self, addr, isRelative = NCL_SEEK_ABS):
        if isRelative == NCL_SEEK_REL:
            self.position += addr
        else:
            self.position = addr
  
    def tell(self):
        return self.position

    def checkEOF(self):
        return self.tell() >= self.getSize()

class NclVec3:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        
    def read(self, bs):
        self.x = bs.readFloat()
        self.y = bs.readFloat()
        self.z = bs.readFloat()
        
class NclVec4:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.w = 0
        
    def read(self, bs):
        self.x = bs.readFloat()
        self.y = bs.readFloat()
        self.z = bs.readFloat()
        self.w = bs.readFloat()
        
class NclMat44:
    def __init__(self):
        self.rows = [NclVec4(), NclVec4(), NclVec4(), NclVec4()]
        
    def read(self, bs):
        self.rows[0].read(bs)
        self.rows[1].read(bs)
        self.rows[2].read(bs)
        self.rows[3].read(bs)  
        
# contains a dump of the shader cache, containing name + key (hash)
class ShaderInputInfo:
    def __init__(self, off, typeVal, name, componentCount):
        self.offset = off
        self.type = typeVal
        self.name = name
        self.componentCount = componentCount

class ShaderInfo:
    def __init__(self, idx, name, hashValue):
        self.index = idx
        self.name = name
        self.hash = hashValue
        self.inputs = []
        self.inputsByName = {}
        
    def addInput( self, input ):
        self.inputs.append( input )
        if not self.hasInput( input.name ):
            self.inputsByName[ input.name ] = [ input ]
        else:
            self.inputsByName[ input.name ].append( input )
        
    def getInput( self, name ):
        return self.inputsByName[ name ]
    
    def hasInput( self, name ):
        return name in self.inputsByName

# modeled after sMvc3ShaderCache
class ShaderCache:
    def __init__(self, shaderHashesPath, shaderInputsPath):
        self.shaders = []
        self.shaderByHash = {}
        self.shaderByName = {}
        
        # read shader hash -> name mapping
        with open(shaderHashesPath) as f:
            f.readline() # header
            line = f.readline()
            while line != "":
                tokens = line.split(",")
                idx = int(tokens[0])
                name = tokens[1]
                hashVal = int(tokens[2], 16) if name != "" else 0
                entry = ShaderInfo(idx, name, hashVal)
                self.shaders.append(entry)
                self.shaderByHash[hashVal] = entry 
                self.shaderByName[name] = entry
                line = f.readline()
                
        # read shader inputs
        with open(shaderInputsPath) as f:
            f.readline() # header
            line = f.readline()
            while line != "":
                # shader,offset,type,name,componentcount
                tokens = line.split(",")
                shaderName = tokens[0]
                inputOffset = int(tokens[1])
                inputType = int(tokens[2])
                inputName = tokens[3]
                inputCmpCount = int(tokens[4])
                shader = self.getShaderByName(shaderName)
                shader.addInput( ShaderInputInfo( inputOffset, inputType, inputName, inputCmpCount ) )
                line = f.readline()
                
    def getShaderByHash(self, hashVal):
        return self.shaderByHash[hashVal]
    
    def getShaderByName(self, name):
        return self.shaderByName[name]
        
class rModelVertexShaderRef:
    def __init__(self, value=0):
        self.value = value
        
    @staticmethod
    def fromName(name, index=0):
        self = rModelVertexShaderRef()
        self.setHash(crc32(name.decode(), 0xFFFFFFFF))
        
    def getIndex(self):
        return (self.value & 0x00000FFF)
    
    def setIndex(self, index):
        self.value = (self.value & ~0x00000FFF) | (index & 0x00000FFF) 
        
    def getHash(self):
        return (self.value & 0xFFFFF000) >> 12
    
    def setHash(self, hash):
        self.value = (self.value & ~0xFFFFF000) | (hash & 0xFFFFF000) << 12
        
    def getValue(self):
        return self.value
        
    def setValue(self, value):
        self.value = value
        
    def nameEquals(self, cache, name):
        if cache != None:
            return cache.getShaderByHash(self.getHash()).name == name
        else:
            return False
        
class rModelMaterialIndices:
    def __init__(self, value=0):
        self.value = value
        
    def _unpack(self, mask, bitOffset):
        return (self.value & (mask << bitOffset)) >> bitOffset
    
    def _pack(self, mask, bitOffset, index):
        self.value = (self.value & ~(mask << bitOffset)) | (index & mask) << bitOffset
        
    def getJointIndex(self):
        return self._unpack(0x00000FFF, 0)
    
    def setJointIndex(self, index):
        self._pack(0x00000FFF, 0, index)
        
    def getMaterialIndex(self):
        return self._unpack(0x00000FFF, 12)
    
    def setMaterialIndex(self, index):
        self._pack(0x00000FFF, 12, index)
        
    def getLodIndex(self):
        return self._unpack(0x000000FF, 24)
    
    def setLodIndex(self, index):
        self._pack(0x000000FF, 24, index)
        
    def getValue(self):
        return self.value
        
    def setValue(self, value):
        self.value = value
        
class rModelPrimitive:
    def __init__(self):
        self.type = 0
        self.vertexCount = 0
        self.indices = rModelMaterialIndices()
        self.category1 = 0
        self.category2 = 0
        self.vertexStride = 0
        self.renderMode = 0
        self.vertexStartIndex = 0
        self.vertexBufferOffset = 0
        self.vertexShader = rModelVertexShaderRef()
        self.indexBufferOffset = 0
        self.indexCount = 0
        self.indexStartIndex = 0
        self.boneIdStart = 0
        self.primitiveJointLinkIndex = 0
        self.index = 0
        self.minVertexIndex = 0
        self.maxVertexIndex = 0
        self.field2C = 0
        self.primitiveJointLinkPtr = 0
        self.field34 = 0
        
    def read(self, bs):
        self.type = bs.readShort()
        self.vertexCount = bs.readShort()
        self.indices = rModelMaterialIndices(bs.readUInt())
        self.category1 = bs.readByte()
        self.category2 = bs.readByte()
        self.vertexStride = bs.readByte()
        self.renderMode = bs.readByte()
        self.vertexStartIndex = bs.readInt()
        self.vertexBufferOffset = bs.readInt()
        self.vertexShader = rModelVertexShaderRef(bs.readUInt())
        self.indexBufferOffset = bs.readInt()
        self.indexCount = bs.readInt()
        self.indexStartIndex = bs.readInt()
        self.boneIdStart = bs.readByte()
        self.primitiveJointLinkIndex = bs.readByte()
        self.index = bs.readShort()
        self.minVertexIndex = bs.readShort()
        self.maxVertexIndex = bs.readShort()
        self.field2C = bs.readInt()
        self.primitiveJointLinkPtr = bs.readInt()
        self.field34 = bs.readInt()
        
class rModelGroup:
    def __init__(self):
        self.field00 = 0
        self.field04 = 0
        self.field08 = 0
        self.field0C = 0
        self.field10 = 0
        self.field14 = 0
        self.field18 = 0
        self.field1C = 0
        
    def read(self, bs):
        self.field00 = bs.readInt()
        self.field04 = bs.readInt()
        self.field08 = bs.readInt()
        self.field0C = bs.readInt()
        self.field10 = bs.readFloat()
        self.field14 = bs.readFloat()
        self.field18 = bs.readFloat()
        self.field1C = bs.readFloat()
        
class rModelJoint:
    def __init__(self):
        self.no = 0
        self.parent = 0
        self.symmetry = 0
        self.field03 = 0
        self.field04 = 0
        self.length = 0 
        self.offset = NoeVec3()
        
    def read(self, bs):
        self.no = bs.readUByte()
        self.parent = bs.readUByte()
        self.symmetry = bs.readUByte()
        self.field03 = bs.readByte()
        self.field04 = bs.readFloat()
        self.length = bs.readFloat()
        self.offset = bs.readVec3()

class rModelPrimitiveJointLink:
    def __init__(self):
        self.jointIdx = 0
        self.field04 = 0
        self.field08 = 0
        self.field0C = 0
        self.boundingSphere = NoeVec4()
        self.min = NoeVec4()
        self.max = NoeVec4()
        self.localMtx = NoeMat44()
        self.field80 = NoeVec4()
        
    def read(self, bs):
        self.jointIdx = bs.readInt()
        self.field04 = bs.readInt()
        self.field08 = bs.readInt()
        self.field0C = bs.readInt()
        self.boundingSphere = bs.readVec4()
        self.min = bs.readVec4()
        self.max = bs.readVec4()
        self.localMtx = bs.readMat44()
        self.field80 = bs.readVec4()

class rModelHeader:
    MAGIC = 0x444F4D
    VERSION = 211
    
    def __init__(self):
        self.magic = rModelHeader.MAGIC
        self.version = rModelHeader.VERSION
        self.jointCount = 0
        self.primitiveCount = 0
        self.materialCount = 0
        self.vertexCount = 0
        self.polygonCount = 0
        self.vertexBufferSize = 0
        self.secondBufferSize = 0
        self.groupCount = 0
        self.jointOffset = 0
        self.groupOffset = 0
        self.materialOffset = 0
        self.primitiveOffset = 0
        self.vertexBufferOffset = 0
        self.indexBufferOffset = 0
        self.exDataOffset = 0
        self.boundingSphere = NoeVec4()
        self.min = NoeVec4()
        self.max = NoeVec4()
        self.field90 = 1000
        self.field94 = 3000
        self.field98 = 1
        self.field9C = 0
        self.primitiveJointLinkCount = 0
        
    @staticmethod
    def isValidStream(bs):
        return bs.readInt() == rModelHeader.MAGIC
        
    def read(self, bs):
        self.magic = bs.readInt()
        self.version = bs.readShort()
        self.jointCount = bs.readShort()
        self.primitiveCount = bs.readShort()
        self.materialCount = bs.readShort()
        self.vertexCount = bs.readInt()
        self.indexCount = bs.readInt()
        self.polygonCount = bs.readInt()
        self.vertexBufferSize = bs.readInt()
        self.secondBufferSize = bs.readInt()
        self.groupCount = bs.readInt64()
        self.jointOffset = bs.readInt64()
        self.groupOffset = bs.readInt64()
        self.materialOffset = bs.readInt64()
        self.primitiveOffset = bs.readInt64()
        self.vertexBufferOffset = bs.readInt64()
        self.indexBufferOffset = bs.readInt64()
        self.exDataOffset = bs.readInt64()
        self.boundingSphere = bs.readVec4()
        self.min = bs.readVec4()
        self.max = bs.readVec4()
        self.field90 = bs.readInt()
        self.field94 = bs.readInt()
        self.field98 = bs.readInt()
        self.field9C = bs.readInt()
        self.primitiveJointLinkCount = bs.readInt()

class rModel:
    def __init__(self):
        self.header = rModelHeader()
        self.joints = []
        self.jointLocalMtx = []
        self.jointInvBindMtx = []
        self.jointMap = []
        self.groups = []
        self.materials = []
        self.primitives = []
        self.primitiveJointLinks = []
        self.vertexBuffer = []
        self.indexBuffer = []
        self.hasExData = False
        self.exCount1 = 0
        self.exCount2 = 0
        self.exPrimValues = []
        self.exVertexBufferSize = 0
        self.exVertexBuffer = []
        self.exVertexBuffer2Size = 0
        self.exVertexBuffer2 = []
        
    def read(self, bs):
        p = bs.tell()
        
        self.header.read(bs)
        
        # read joints
        bs.seek( p + self.header.jointOffset )
        for i in range( self.header.jointCount ):
            joint = rModelJoint()
            joint.read(bs)
            self.joints.append(joint)
        
        for i in range( self.header.jointCount ):
            mtx = bs.readMat44()
            self.jointLocalMtx.append(mtx)
            
        for i in range( self.header.jointCount ):
            mtx = bs.readMat44()
            self.jointInvBindMtx.append(mtx)
            
        self.jointMap = []
        for i in range(256):
            self.jointMap.append( bs.readUByte() )
        
        # read groups
        bs.seek( p + self.header.groupOffset )
        for i in range( self.header.groupCount ):
            grp = rModelGroup()
            grp.read(bs)
            self.groups.append(grp)
         
        # read materials   
        bs.seek( p + self.header.materialOffset )
        for i in range( self.header.materialCount ):
            mat = bs.readBytes(128).decode("ASCII").rstrip("\0")
            self.materials.append(mat)
          
        # read primitives  
        bs.seek( p + self.header.primitiveOffset )
        for i in range( self.header.primitiveCount ):
            prim = rModelPrimitive()
            prim.read(bs)
            self.primitives.append(prim)
        
        # read primitive joint links    
        for i in range( self.header.primitiveJointLinkCount ):
            pjl = rModelPrimitiveJointLink()
            pjl.read(bs)
            self.primitiveJointLinks.append(pjl)
            
        # read vertex buffer
        self.vertexBuffer = bs.readBytes( self.header.vertexBufferSize )
        
        # read index buffer
        self.indexBuffer = bs.readBytes( self.header.indexCount * 2 )
        
        # read ex data
        self.hasExData = bs.readInt() == 1
        if ( self.hasExData ):
            self.exCount1 = bs.readShort()
            self.exCount2 = bs.readShort()
            for i in range( self.header.primitiveCount ):
                self.exPrimValues.append(bs.readInt())
            self.exVertexBufferSize = bs.readInt()
            self.exVertexBuffer = bs.readBytes( self.exVertexBufferSize )
            self.exVertexBuffer2Size = bs.readInt()
            self.exVertexBuffer2 = bs.readBytes( self.exVertexBuffer2Size )

class MrlTextureInfo: 
    def __init__(self):
        self.hash = 0
        self.field04 = 0
        self.field08 = 0
        self.field0c = 0
        self.field10 = 0
        self.field14 = 0
        self.path = ""
        
    def read(self, bs):
        self.hash = bs.readInt()
        self.field04 = bs.readInt()
        self.field08 = bs.readInt()
        self.field0c = bs.readInt()
        self.field10 = bs.readInt()
        self.field14 = bs.readInt()
        self.path = bs.readBytes(64).decode("ASCII").rstrip("\0")

class MrlHeader:
    MAGIC = 0x22004C524D
    
    def __init__(self):
        self.magic = 0x22004C524D
        self.materialCount = 0
        self.textureCount = 0
        self.hash = 0
        self.field14 = 0
        self.textureOffset = 0
        self.field20 = 0   
        
    def read(self, bs):
        self.magic = bs.readInt64()
        self.materialCount = bs.readInt()
        self.textureCount = bs.readInt()
        self.hash = bs.readInt()
        self.field14 = bs.readInt()
        self.textureOffset = bs.readInt64()
        self.field20 = bs.readInt64()

class MrlFile:
    def __init__(self):
        self.header = MrlHeader()
        self.textures = []
        
    def read(self, bs):
        self.header.read(bs)
        
        bs.seek( self.header.textureOffset )
        for i in range(0, self.header.textureCount):
            tex = MrlTextureInfo()
            tex.read(bs)
            print(tex.path)
            self.textures.append(tex)

def debugDumpObj(obj):
    print(yaml.dump(obj))
    
def hexdump( src, length=16, sep='.' ):
    '''
    @brief Return {src} in hex dump.
    @param[in] length	{Int} Nb Bytes by row.
    @param[in] sep		{Char} For the text part, {sep} will be used for non ASCII char.
    @return {Str} The hexdump
    @note Full support for python2 and python3 !
    '''
    result = [];

    # Python3 support
    try:
        xrange(0,1);
    except NameError:
        xrange = range;

    for i in xrange(0, len(src), length):
        subSrc = src[i:i+length];
        hexa = '';
        isMiddle = False;
        for h in xrange(0,len(subSrc)):
            if h == length/2:
                hexa += ' ';
            h = subSrc[h];
            if not isinstance(h, int):
                h = ord(h);
            h = hex(h).replace('0x','');
            if len(h) == 1:
                h = '0'+h;
            hexa += h+' ';
        hexa = hexa.strip(' ');
        text = '';
        for c in subSrc:
            if not isinstance(c, int):
                c = ord(c);
            if 0x20 <= c < 0x7F:
                text += chr(c);
            else:
                text += sep;
        result.append(('%08X:  %-'+str(length*(2+1)+1)+'s  |%s|') % (i, hexa, text));

    return '\n'.join(result)

# noesis specific
from inc_noesis import *

def readVec3(self):
    return NoeVec3((self.readFloat(), self.readFloat(), self.readFloat()))
def readVec4(self):
    return NoeVec4((self.readFloat(), self.readFloat(), self.readFloat(), self.readFloat()))
def readMat44(self):
    return NoeMat44((readVec4(self), readVec4(self), readVec4(self), readVec4(self)))
def readMat43(self):
    return NoeMat43((readVec4(self), readVec4(self), readVec4(self)))
                    
NoeBitStream.readVec3 = readVec3
NoeBitStream.readVec4 = readVec4
NoeBitStream.readMat44 = readMat44
NoeBitStream.readMat43 = readMat43

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
    handle = noesis.register("MT Framework Model", ".mod")
    noesis.setHandlerTypeCheck(handle, modCheckType)
    noesis.setHandlerLoadModel(handle, modLoadModel)
    #noesis.logPopup()
    return 1


def modCheckType(data):
    return rModelHeader.isValidStream(NoeBitStream(data))

# typedef enum<u32>
# {
#     rShaderInputLayoutElementType_F32 = 1, // 32 bit single precision float
#     rShaderInputLayoutElementType_F16 = 2, // 16 bit half precision float
#     rShaderInputLayoutElementType_IU16 = 3, // guess, 16 bit integer (joint index)
#     rShaderInputLayoutElementType_IS16 = 4, // guess, 16 bit integer (joint index)
#     rShaderInputLayoutElementType_FS16 = 5, // guess, 16 bit normalized compressed float, divisor = 1 << 15 - 1
#     rShaderInputLayoutElementType_IS8 = 7, // guess
#     rShaderInputLayoutElementType_IU8 = 8, // guess, 8 bit unsigned joint index
#     rShaderInputLayoutElementType_FU8  = 9, // guess, 8 bit normalized compressed float, divisor = 255
#     rShaderInputLayoutElementType_FS8 = 10, // guess,  8 bit normalized compressed float, divisor = 127
#     rShaderInputLayoutElementType_11_11_11_10 = 11, // guess, 4 bytes, used for normals
#     rShaderInputLayoutElementType_RGB = 13, // guess, 1 byte, used for colors without alpha
#     rShaderInputLayoutElementType_RGBA = 14, // guess
# } rShaderInputLayoutElementType;

def convertInputTypeToRPGEODATA( t ):
    if t == 1: return noesis.RPGEODATA_FLOAT
    if t == 2: return noesis.RPGEODATA_HALFFLOAT
    if t == 3: return noesis.RPGEODATA_USHORT
    if t == 4: return noesis.RPGEODATA_HALFFLOAT
    if t == 5: return noesis.RPGEODATA_SHORT
    if t == 7: return noesis.RPGEODATA_BYTE
    if t == 8: return noesis.RPGEODATA_UBYTE
    if t == 9: return noesis.RPGEODATA_UBYTE
    if t == 10: return noesis.RPGEODATA_BYTE
    if t == 11: return noesis.RPGEODATA_UBYTE # 11_11_11_10
    if t == 13: return noesis.RPGEODATA_BYTE
    if t == 14: return noesis.RPGEODATA_BYTE
    raise Exception("Unknown input type: " + str(t))

        # public Vec4 U32toVec4(UInt32 U32)
        # {
        #     Int16 X = Convert.ToInt16(U32 & 0x3ff);
        #     Int16 Y = Convert.ToInt16((U32 >> 10) & 0x3ff);
        #     Int16 Z = Convert.ToInt16((U32 >> 20) & 0x3ff);
        #     byte W = Convert.ToByte((U32) >> 30);
        #     return new Vec4((X - 512) / 512f, (Y - 512) / 512f, (Z - 512) / 512f, W/3f);
        # }

def decompressNormals32_10_10_10_2(bits):
    x = (bits & 0x3FF)
    y = (bits >> 10) & 0x3FF
    z = (bits >> 20) & 0x3FF
    w = (bits >> 30) & 0xFF
    return ((x - 511) / 512, (y - 511) / 512, (z - 511) / 512, w / 3)

def decompressNormalsU32_11_11_10(bits):
    x = ( ( bits       ) & 0x7FF ) / 0x7FF
    y = ( ( bits >> 11 ) & 0x7FF ) / 0x7FF
    z = ( ( bits >> 22 ) & 0x3FF ) / 0x3FF
    return (x, y, z, 1)

def decompressNormalsS32_11_11_10(bits):
    x = ( ( ( bits       ) & 0x7FF ) - 0x3FF ) / ( 0x3FF + 1 )
    y = ( ( ( bits >> 11 ) & 0x7FF ) - 0x3FF ) / ( 0x3FF + 1 )
    z = ( ( ( bits >> 22 ) & 0x3FF ) - 0x1FF ) / ( 0x1FF + 1 )
    return (x, y, z, 1)

def decompressFS16( bits ):
    return ( bits / 32767 )

def compressFS16( val ):
    return ( val * 32767 )
    
def decompressFU8( bits ):
    return ( bits - 127 ) / 128

def compressFU8( val ):
    return ( val * 128 ) + 127

def decompressVertexShaderInput( inputInfo, reader, writer, p ):
    start = writer.tell()
    reader.seek( p + inputInfo.offset )
    for i in range(inputInfo.componentCount):
        if   inputInfo.type == 1: writer.writeFloat(reader.readFloat())
        elif inputInfo.type == 2: writer.writeFloat(reader.readHalfFloat())
        elif inputInfo.type == 3: writer.writeFloat(reader.readUShort())
        elif inputInfo.type == 4: writer.writeFloat(reader.readHalfFloat())
        elif inputInfo.type == 5: writer.writeFloat(decompressFS16(reader.readShort()))
        elif inputInfo.type == 7: writer.writeFloat(reader.readByte())
        elif inputInfo.type == 8: writer.writeFloat(reader.readUByte())
        elif inputInfo.type == 9: writer.writeFloat(decompressFU8(reader.readUByte()))
        elif inputInfo.type == 10: writer.writeFloat(reader.readByte())
        elif inputInfo.type == 11: 
            x, y, z, w = decompressNormalsS32_11_11_10(reader.readUInt())
            writer.writeFloat(x)
            writer.writeFloat(y)
            writer.writeFloat(z)
            writer.writeFloat(w)
        elif inputInfo.type == 13: writer.writeFloat(reader.readByte())
        elif inputInfo.type == 14: writer.writeFloat(reader.readByte())
        else:         raise Exception("Unknown input type: " + str(inputInfo.type))
    end = writer.tell()
    size = end - start
    newComponentCount = int(size / 4)
    return newComponentCount

def decompressVertexBuffer( shaderInfo, vertexBuffer, vertexCount, stride ):
    reader = NoeBitStream( vertexBuffer )
    writer = NoeBitStream()
    newInputs = []
    newStride = 0
    
    if vertexCount > 0:
        for key, value in shaderInfo.inputsByName.items():
            newOffset = writer.tell()
            newComponentCount = 0
            for inputInfo in value:
                newComponentCount += decompressVertexShaderInput( inputInfo, reader, writer, 0 )
            newInputs.append( ( key, newOffset, newComponentCount ) )
            
        newStride = writer.tell()
        
        for i in range(1, vertexCount):
            p = i * stride
            for key, value in shaderInfo.inputsByName.items():
                for inputInfo in value:
                    decompressVertexShaderInput( inputInfo, reader, writer, p )
    
    return (writer.getBuffer(), newStride, newInputs)
        

def tryBindShaderInput( shaderInfo, name, func, vertexBuffer, stride, useCount = False ):
    if shaderInfo.hasInput(name):
        inputInfos = shaderInfo.getInput( name )
        for inputInfo in inputInfos:
            print( "input name: " + inputInfo.name )
            print( "input type: " + str( inputInfo.type ) )
            if not useCount: func( vertexBuffer, convertInputTypeToRPGEODATA( inputInfo.type ), stride, inputInfo.offset )
            else:            func( vertexBuffer, convertInputTypeToRPGEODATA( inputInfo.type ), stride, inputInfo.offset, inputInfo.componentCount )

def loadTextureFromPath(texName):
    folderName = rapi.getDirForFilePath(rapi.getInputName())
    folderName = folderName.replace('\\', '/')
    if (rapi.checkFileExists(folderName + texName)):
        texData = rapi.loadIntoByteArray(folderName + texName)
        texture = rapi.loadTexByHandler(texData, ".dds")
        texture.name = rapi.getExtensionlessName(rapi.getLocalFileName(texName))
        return texture
    return None

def modLoadModel(data, mdlList):
    
    shaderNamePath = "X:/work/umvc3_model/resources/shaderhashes.csv"
    shaderInputsPath = "X:/work/umvc3_model/resources/shaderinputs.csv"
    shaderCache = ShaderCache(shaderNamePath, shaderInputsPath)
    
    model = rModel()
    model.read(NoeBitStream(data))
    
    mrl = MrlFile()
    mrl.read(NoeBitStream(rapi.loadPairedFileOptional("material file", ".mrl")))
    
    ctx = rapi.rpgCreateContext()
    
    #rapi.rpgSetBoneMap( model.jointMap[1:] )
    
    # set model transform
    # restore bind pose (undo world transform & reapply local transform)
    modelMtx = model.jointInvBindMtx[0].toMat43() * model.jointLocalMtx[0].toMat43()
    rapi.rpgSetTransform( modelMtx )
    
    # build model meshes
    indexBs = NoeBitStream(model.indexBuffer)
    matList = []    
    texList = []
    for i in range(len(model.primitives)):
        primitive = model.primitives[i]
        jointLink = model.primitiveJointLinks[primitive.primitiveJointLinkIndex]
        shaderInfo = shaderCache.getShaderByHash( primitive.vertexShader.getHash() )
        print("shader name: " + shaderInfo.name)
        #if shaderInfo.name != "IASkinBridge1wt":
        #    continue
        
        for inputInfo in shaderInfo.inputs:
            print("  input name: " + inputInfo.name )
            print("  input type: " + str(inputInfo.type) )
            print("  input cmpc: " + str(inputInfo.componentCount))
        
        meshName = "primitive_{}_shader_{}".format(i, shaderInfo.name)
        rapi.rpgSetName( meshName )
        
        # create material
        materialName = model.materials[primitive.indices.getMaterialIndex()]
        textureName = mrl.textures[primitive.indices.getMaterialIndex() % mrl.header.textureCount].path + format(mrl.header.hash, "x") + ".dds"
        print(textureName)
        material = NoeMaterial(materialName , "")
        material.setTexture(textureName)
        matList.append(material)
        texList.append(loadTextureFromPath(textureName)) # or loaded texture // path to texfile etc whichever works
        
        rapi.rpgSetMaterial( material.name )

        # set bone map 
        boneMap = model.jointMap[primitive.primitiveJointLinkIndex:len(model.jointMap)]
        #rapi.rpgSetBoneMap( boneMap )

        # decode vertex buffer
        vertexStart = primitive.vertexBufferOffset + (primitive.vertexStartIndex * primitive.vertexStride)
        vertexEnd = vertexStart + (primitive.vertexCount * primitive.vertexStride)
        vertexBuffer = model.vertexBuffer[vertexStart:vertexEnd]
        decVertexBuffer, decStride, decInputs = decompressVertexBuffer( shaderInfo, vertexBuffer, primitive.vertexCount, primitive.vertexStride )       
        for inputName, inputOffset, inputComponentCount in decInputs:
            print(inputName, inputOffset, inputComponentCount)
            if   inputName == "Position":   rapi.rpgBindPositionBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )
            elif inputName == "Normal":     rapi.rpgBindNormalBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )  
            elif inputName == "Joint":      rapi.rpgBindBoneIndexBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset, inputComponentCount )  
            elif inputName == "Weight":     rapi.rpgBindBoneWeightBufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset, inputComponentCount )
            elif inputName == "UV_Primary": rapi.rpgBindUV1BufferOfs( decVertexBuffer, noesis.RPGEODATA_FLOAT, decStride, inputOffset )
        #tryBindShaderInput( shaderInfo, "Position", rapi.rpgBindPositionBufferOfs, vertexBuffer, primitive.vertexStride )
        #tryBindShaderInput( shaderInfo, "Normal", rapi.rpgBindNormalBufferOfs, vertexBuffer, primitive.vertexStride )
        #tryBindShaderInput( shaderInfo, "Joint", rapi.rpgBindBoneIndexBufferOfs, vertexBuffer, primitive.vertexStride, True )
        #tryBindShaderInput( shaderInfo, "Weight", rapi.rpgBindBoneWeightBufferOfs, vertexBuffer, primitive.vertexStride, True )
        #tryBindShaderInput( shaderInfo, "UV_Primary", rapi.rpgBindUV1BufferOfs, vertexBuffer, primitive.vertexStride )
            
        #if shaderInfo.hasInput("Joint"):
        
        # print("{:02X}".format(primitive.vertexShader.getHash()))
        # if ( primitive.vertexShader.nameEquals( cache, "IASkinBridge1wt" ) ):
        #     rapi.rpgBindPositionBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0 )
        #     rapi.rpgBindBoneIndexBufferOfs( vertexBuffer, noesis.RPGEODATA_HALFFLOAT, primitive.vertexStride, 6, 1 )
        #     rapi.rpgBindNormalBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 8 )
        # elif ( primitive.vertexShader.nameEquals( cache, "IASkinBridge2wt" ) ):
        #     rapi.rpgBindPositionBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0 )
        #     rapi.rpgBindBoneWeightBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 6, 1 )
        #     rapi.rpgBindNormalBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 8 )
        #     rapi.rpgBindBoneIndexBufferOfs( vertexBuffer, noesis.RPGEODATA_HALFFLOAT, primitive.vertexStride, 12, 2 )
        # elif ( primitive.vertexShader.nameEquals( cache, "IASkinBridge4wt" ) ):
        #     rapi.rpgBindPositionBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0 )
        #     rapi.rpgBindNormalBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 8 )
        #     #rapi.rpgBindBoneWeightBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 12, 4 )
        #     #rapi.rpgBindBoneIndexBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 16, 4 )
        # elif ( primitive.vertexShader.nameEquals( cache, "IASkinTB1wt" ) ):
        #     rapi.rpgBindPositionBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0 )
        #     rapi.rpgBindNormalBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 8 )
        #     #rapi.rpgBindBoneWeightBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 12, 4 )
        #     #rapi.rpgBindBoneIndexBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 16, 4 )
        # elif ( primitive.vertexShader.nameEquals( cache, "IASkinTB2wt" ) ):
        #     # MODVertexBufferc31f201d | ( 1C | C31F2h ) | IASkinTB2wt | SkinnedCharacter021[U1NS]
        #     rapi.rpgBindPositionBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0 )
        #     rapi.rpgBindBoneWeightBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 6, 1 )
        #     rapi.rpgBindNormalBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 8 )
        #     rapi.rpgBindTangentBufferOfs( vertexBuffer, noesis.RPGEODATA_BYTE, primitive.vertexStride, 12 )
        #     rapi.rpgBindUV1BufferOfs( vertexBuffer, noesis.RPGEODATA_HALFFLOAT, primitive.vertexStride, 16 )
        #     rapi.rpgBindBoneIndexBufferOfs( vertexBuffer, noesis.RPGEODATA_HALFFLOAT, primitive.vertexStride, 20, 2 )
        # elif ( primitive.vertexShader.nameEquals( cache, "IASkinTB4wt" ) ):
        #     rapi.rpgBindPositionBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0 )
        #     rapi.rpgBindBoneWeightBufferOfs( vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 6, 1 )
        #     rapi.rpgBindNormalBufferOfs( vertexBuffer, noesis.RPGEODATA_UBYTE, primitive.vertexStride, 8 )
        #     rapi.rpgBindTangentBufferOfs( vertexBuffer, noesis.RPGEODATA_BYTE, primitive.vertexStride, 12 )
        #     rapi.rpgBindUV1BufferOfs( vertexBuffer, noesis.RPGEODATA_HALFFLOAT, primitive.vertexStride, 16 )
        #     rapi.rpgBindBoneIndexBufferOfs( vertexBuffer, noesis.RPGEODATA_HALFFLOAT, primitive.vertexStride, 20, 4 )
        # else:
        #     print("unhandled")
        #     rapi.rpgBindPositionBufferOfs(vertexBuffer, noesis.RPGEODATA_SHORT, primitive.vertexStride, 0)
        
        # fix index buffer for drawing by subtracting the vertex start index from the indices
        indexStart = ( primitive.indexBufferOffset + primitive.indexStartIndex ) * 2
        indexEnd = indexStart + ( primitive.indexCount * 2 )
        indexBuffer = []
        indexBs.seek( indexStart )
        for i in range(model.header.indexCount):
            indexBuffer.append( indexBs.readShort() - primitive.vertexStartIndex )
        indexBufferBytes = struct.pack("<" + 'h'*len(indexBuffer), *indexBuffer)
            
        rapi.rpgCommitTriangles( indexBufferBytes, noesis.RPGEODATA_SHORT, primitive.indexCount, noesis.RPGEO_TRIANGLE, 1 )
        #rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, primitive.vertexCount, noesis.RPGEO_POINTS, 1)
        rapi.rpgClearBufferBinds()
        #break

    mdl = rapi.rpgConstructModel()                                                          
    
    # build bones
    noeBones = []
    for i in range(len(model.joints)):
        joint = model.joints[i]
        name = "joint_{}".format(joint.no)
        matrix = model.jointLocalMtx[i].toMat43()
        
        parent = -1
        if ( joint.parent != 255 ):
            parent = joint.parent
            matrix *= noeBones[parent].getMatrix()
        
        noeBone = NoeBone(i, name, matrix, None, parent)
        noeBones.append(noeBone)
    mdl.setBones(noeBones)
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    
    mdlList.append(mdl)
    rapi.rpgClearBufferBinds()
    return 1
