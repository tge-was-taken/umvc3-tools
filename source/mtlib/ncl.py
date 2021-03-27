# NCL - Noesis compatibility library

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