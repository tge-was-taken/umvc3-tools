# TODO: substitute this when moving to Blender/Max
try:
    from inc_noesis import *
except:
    raise Exception("Blender/Max support not yet implemented")

def writeVec3( stream, value ):
    stream.writeFloat( value[0] )
    stream.writeFloat( value[1] )
    stream.writeFloat( value[2] )
    
def writeVec4( stream, value ):
    stream.writeFloat( value[0] )
    stream.writeFloat( value[1] )
    stream.writeFloat( value[2] )
    stream.writeFloat( value[3] )
    
def writeMat44( stream, value ):
    stream.writeBytes( value.toBytes() )
    
def NoeFileStream_getSize( stream ):
    return stream.fileSize

NoeBitStream.writeVec3 = writeVec3
NoeBitStream.writeVec4 = writeVec4
NoeBitStream.writeMat44 = writeMat44
NoeFileStream.writeVec3 = writeVec3
NoeFileStream.writeVec4 = writeVec4
NoeFileStream.writeMat44 = writeMat44
NoeFileStream.getSize = NoeFileStream_getSize


        
class rModelJointMaterialLodId:
    '''rModel joint packed joint, material and lod indices'''
    SIZE = 0x04
    
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
        
class rModelHeader:
    '''rModel (MOD) file header structure v221'''
    SIZE = 0xA4
    MAGIC = 0x444F4D
    VERSION = 211
    
    def __init__( self ):
        self.magic = rModelHeader.MAGIC
        self.version = rModelHeader.VERSION
        self.jointCount = 0
        self.primitiveCount = 0
        self.materialCount = 0
        self.vertexCount = 0
        self.indexCount = 0
        self.polygonCount = 0
        self.vertexBufferSize = 0
        self.vertexBuffer2Size = 0
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
        self.field9c = 0
        self.primitiveJointLinkCount = 0
        
    def read( self, stream ):
        self.magic = stream.readInt()
        self.version = stream.readShort()
        self.jointCount = stream.readShort()
        self.primitiveCount = stream.readShort()
        self.materialCount = stream.readShort()
        self.vertexCount = stream.readInt()
        self.indexCount = stream.readInt()
        self.polygonCount = stream.readInt()
        self.vertexBufferSize = stream.readInt()
        self.vertexBuffer2Size = stream.readInt()
        self.groupCount = stream.readInt64()
        self.jointOffset = stream.readInt64()
        self.groupOffset = stream.readInt64()
        self.materialOffset = stream.readInt64()
        self.primitiveOffset = stream.readInt64()
        self.vertexBufferOffset = stream.readInt64()
        self.indexBufferOffset = stream.readInt64()
        self.exDataOffset = stream.readInt64()
        self.boundingSphere = stream.readVec4()
        self.min = stream.readVec4()
        self.max = stream.readVec4()
        self.field90 = stream.readInt()
        self.field94 = stream.readInt()
        self.field98 = stream.readInt()
        self.field9c = stream.readInt()
        self.primitiveJointLinkCount = stream.readInt()
        
    def write( self, stream ):
        stream.writeInt( self.magic )
        stream.writeShort( self.version )
        stream.writeShort( self.jointCount )
        stream.writeShort( self.primitiveCount )
        stream.writeShort( self.materialCount )
        stream.writeInt( self.vertexCount )
        stream.writeInt( self.indexCount )
        stream.writeInt( self.polygonCount )
        stream.writeInt( self.vertexBufferSize )
        stream.writeInt( self.vertexBuffer2Size )
        stream.writeInt64( self.groupCount )
        stream.writeInt64( self.jointOffset )
        stream.writeInt64( self.groupOffset )
        stream.writeInt64( self.materialOffset )
        stream.writeInt64( self.primitiveOffset )
        stream.writeInt64( self.vertexBufferOffset )
        stream.writeInt64( self.indexBufferOffset )
        stream.writeInt64( self.exDataOffset )
        stream.writeVec4( self.boundingSphere )
        stream.writeVec4( self.min )
        stream.writeVec4( self.max )
        stream.writeInt( self.field90 )
        stream.writeInt( self.field94 )
        stream.writeInt( self.field98 )
        stream.writeInt( self.field9c )
        stream.writeInt( self.primitiveJointLinkCount )
        
class rModelPrimitive:
    SIZE = 0x38
    
    def __init__(self):
        self.type = 0
        self.vertexCount = 0
        self.indices = rModelJointMaterialLodId()
        self.category1 = 0
        self.category2 = 0
        self.vertexStride = 0
        self.renderMode = 0
        self.vertexStartIndex = 0
        self.vertexBufferOffset = 0
        self.vertexShader = ShaderObjectId()
        self.indexBufferOffset = 0
        self.indexCount = 0
        self.indexStartIndex = 0
        self.boneIdStart = 0
        self.primitiveJointLinkCount = 0
        self.index = 0
        self.minVertexIndex = 0
        self.maxVertexIndex = 0
        self.field2c = 0
        self.primitiveJointLinkPtr = 0
        
    def read(self, stream):
        self.type = stream.readShort()
        self.vertexCount = stream.readShort()
        self.indices = rModelJointMaterialLodId(stream.readUInt())
        self.category1 = stream.readByte()
        self.category2 = stream.readByte()
        self.vertexStride = stream.readByte()
        self.renderMode = stream.readByte()
        self.vertexStartIndex = stream.readInt()
        self.vertexBufferOffset = stream.readInt()
        self.vertexShader = ShaderObjectId(stream.readUInt())
        self.indexBufferOffset = stream.readInt()
        self.indexCount = stream.readInt()
        self.indexStartIndex = stream.readInt()
        self.boneIdStart = stream.readByte()
        self.primitiveJointLinkCount = stream.readByte()
        self.index = stream.readShort()
        self.minVertexIndex = stream.readShort()
        self.maxVertexIndex = stream.readShort()
        self.field2c = stream.readInt()
        self.primitiveJointLinkPtr = stream.readInt64()
        
    def write( self, stream ):
        stream.writeShort( self.type )
        stream.writeShort( self.vertexCount )
        stream.writeUInt( self.indices.getValue() )
        stream.writeByte( self.category1 )
        stream.writeByte( self.category2 )
        stream.writeByte( self.vertexStride )
        stream.writeByte( self.renderMode )
        stream.writeInt( self.vertexStartIndex )
        stream.writeInt( self.vertexBufferOffset )
        stream.writeUInt( self.vertexShader.getValue() )
        stream.writeInt( self.indexBufferOffset )
        stream.writeInt( self.indexCount )
        stream.writeInt( self.indexStartIndex )
        stream.writeByte( self.boneIdStart )
        stream.writeByte( self.primitiveJointLinkCount )
        stream.writeShort( self.index )
        stream.writeShort( self.minVertexIndex )
        stream.writeShort( self.maxVertexIndex )
        stream.writeInt( self.field2c )
        stream.writeInt64( self.primitiveJointLinkPtr )
        
class rModelGroup:
    SIZE = 0x20
    
    def __init__(self):
        self.field00 = 0
        self.field04 = 0
        self.field08 = 0
        self.field0c = 0
        self.field10 = 0
        self.field14 = 0
        self.field18 = 0
        self.field1c = 0
        
    def read(self, stream):
        self.field00 = stream.readInt()
        self.field04 = stream.readInt()
        self.field08 = stream.readInt()
        self.field0c = stream.readInt()
        self.field10 = stream.readFloat()
        self.field14 = stream.readFloat()
        self.field18 = stream.readFloat()
        self.field1c = stream.readFloat()
        
    def write( self, stream ):
        stream.writeInt( self.field00 )
        stream.writeInt( self.field04 )
        stream.writeInt( self.field08 )
        stream.writeInt( self.field0c )
        stream.writeFloat( self.field10 )
        stream.writeFloat( self.field14 )
        stream.writeFloat( self.field18 )
        stream.writeFloat( self.field1c )
        
class rModelJoint:
    SIZE = 0x18
    
    def __init__(self):
        self.no = 0
        self.parent = 0
        self.symmetry = 0
        self.field03 = 0
        self.field04 = 0
        self.length = 0 
        self.offset = NoeVec3()
        
    def read(self, stream):
        self.no = stream.readUByte()
        self.parent = stream.readUByte()
        self.symmetry = stream.readUByte()
        self.field03 = stream.readByte()
        self.field04 = stream.readFloat()
        self.length = stream.readFloat()
        self.offset = stream.readVec3()
        
    def write( self, stream ):
        stream.writeUByte( self.no )
        stream.writeUByte( self.parent )
        stream.writeUByte( self.symmetry )
        stream.writeByte( self.field03 )
        stream.writeFloat( self.field04 )
        stream.writeFloat( self.length )
        stream.writeVec3( self.offset )

class rModelPrimitiveJointLink:
    SIZE = 0x90
    
    def __init__( self ):
        self.jointIdx = 0
        self.field04 = 0
        self.field08 = 0
        self.field0c = 0
        self.boundingSphere = NoeVec4()
        self.min = NoeVec4()
        self.max = NoeVec4()
        self.localMtx = NoeMat44()
        self.field80 = NoeVec4()
        
    def read( self, stream ):
        self.jointIdx = stream.readInt()
        self.field04 = stream.readInt()
        self.field08 = stream.readInt()
        self.field0c = stream.readInt()
        self.boundingSphere = stream.readVec4()
        self.min = stream.readVec4()
        self.max = stream.readVec4()
        self.localMtx = stream.readMat44()
        self.field80 = stream.readVec4()
        
    def write( self, stream ):
        stream.writeInt( self.jointIdx )
        stream.writeInt( self.field04 )
        stream.writeInt( self.field08 )
        stream.writeInt( self.field0c )
        stream.writeVec4( self.boundingSphere )
        stream.writeVec4( self.min )
        stream.writeVec4( self.max )
        stream.writeMat44( self.localMtx )
        stream.writeVec4( self.field80 )
        
class rModelExData:
    '''Optional animation related extra data extension for rModel'''
    
    def __init__( self ):
        self.count1 = 0
        self.count2 = 0
        self.primValues = []
        self.vertexBufferSize = 0
        self.vertexBuffer = bytes()
        self.vertexBuffer2Size = 0
        self.vertexBuffer2 = bytes()
        
    def read( self, primitiveCount, stream ):
        self.count1 = stream.readShort()
        self.count2 = stream.readShort()
        for i in range( primitiveCount ):
            self.primValues.append( stream.readInt() )
        self.vertexBufferSize = stream.readInt()
        self.vertexBuffer = stream.readBytes( self.exVertexBufferSize )
        self.vertexBuffer2Size = stream.readInt()
        self.vertexBuffer2 = stream.readBytes( self.exVertexBuffer2Size )
    
    def write( self, stream ):
        stream.writeShort( self.count1 )
        stream.writeShort( self.count2 )
        for value in self.primValues:
            stream.writeInt( value )
        stream.writeInt( self.vertexBufferSize )
        stream.writeBytes( self.vertexBuffer )
        stream.writeInt( self.vertexBuffer2Size )
        stream.writeBytes( self.vertexBuffer2 )
        
class rModelStreamBase:
    def __init__( self, stream ):
        self.stream = stream
        self.header = rModelHeader()
        self.headerPos = 0
        
    # properties
    def getHeader( self ):
        return self.header
    
    def getHeaderPos( self ):
        return self.headerPos
    
    def getJointPos( self, i = 0 ):
        return self.headerPos + self.header.jointOffset + ( i * rModelJoint.SIZE )
    
    def hasJoints( self ):
        return self.header.jointOffset != 0 and self.header.jointCount > 0
    
    def getJointLocalMtxPos( self, i = 0 ):
        return self.getJointPos( self.header.jointCount ) + ( i * (4*4*4) )
    
    def getJointWorldMtxPos( self, i = 0 ):
        return self.getJointLocalMtxPos( self.header.jointCount ) + ( i * (4*4*4) )
    
    def getJointMapPos( self, i = 0 ):
        return self.getJointWorldMtxPos( self.header.jointCount ) + i
    
    def hasGroups( self ):
        return self.header.groupOffset > 0 and self.header.groupCount > 0
    
    def getGroupPos( self, i = 0 ):
        return self.headerPos + self.header.groupOffset + ( i * rModelGroup.SIZE )
    
    def hasMaterials( self ):
        return self.header.materialOffset > 0 and self.header.materialCount > 0
    
    def getMaterialPos( self, i = 0 ):
        return self.headerPos + self.header.materialOffset + ( i * rModel.MATERIAL_NAME_LENGTH )
    
    def hasPrimitives( self ):
        return self.header.primitiveOffset > 0 and self.header.primitiveCount > 0
    
    def getPrimitivePos( self, i = 0 ):
        return self.headerPos + self.header.primitiveOffset + ( i * rModelPrimitive.SIZE )
    
    def getPrimitiveLinkPos( self, i = 0 ):
        return self.getPrimitivePos() + ( self.header.primitiveCount * rModelPrimitive.SIZE ) + ( i * rModelPrimitiveJointLink.SIZE )
    
    def hasPrimitiveJointLinks( self ):
        return self.hasPrimitives() and self.header.primitiveJointLinkCount > 0
    
    def hasVertexBuffer( self ):
        return self.header.vertexBufferOffset > 0 and self.header.vertexBufferSize > 0
    
    def getVertexBufferPos( self ):
        return self.headerPos + self.header.vertexBufferOffset
    
    def getVertexBuffer2Pos( self ):
        return getVertexBufferPos() + self.header.vertexBufferSize
    
    def hasVertexBuffer2( self ):
        return self.header.vertexBuffer2Size > 0
    
    def hasIndexBuffer( self ):
        return self.header.indexBufferOffset > 0 and self.header.indexCount > 0
    
    def getIndexBufferPos( self ):
        return self.headerPos + self.header.indexBufferOffset
    
    def getIndexBufferSize( self ):
        return self.header.indexCount * 2
    
    def getExDataPos( self ):
        return self.headerPos + self.header.exDataOffset
    
    def isValid( self ):
        return self.header.magic == rModelHeader.MAGIC and self.hasMaterials() and self.hasPrimitives() \
            and self.hasVertexBuffer() and self.hasIndexBuffer()
        
class rModelStreamReader(rModelStreamBase):
    '''Model resource file reader'''
    
    def __init__( self, stream ):
        super(rModelStreamReader, self).__init__( stream )
        self.beginFile()
        
    # methods
    def beginFile( self ):
        self.headerPos = self.stream.tell()
        self.header.read( self.stream )
        pass
    
    def endFile( self ):
        pass
    
    def _iterInstanceReadFn( self, offset, count, type ):
        if offset == 0 or count == 0: return
        for i in range( count ):
            self.stream.seek( offset )
            value = type()
            value.read( self.stream )
            offset = self.stream.tell()
            yield value
            
    def _iterStreamReadFn( self, offset, count, func ):
        if offset == 0 or count == 0: return
        for i in range( count ):
            self.stream.seek( offset )
            value = func()
            offset = self.stream.tell()
            yield value
    
    def iterJoints( self ):
        return self._iterInstanceReadFn( self.getJointPos(), self.header.jointCount, rModelJoint )
            
    def iterJointLocalMtx( self ):
        return self._iterStreamReadFn( self.getJointLocalMtxPos(), self.header.jointCount, self.stream.readMat44 )
    
    def iterJointWorldMtx( self ):
        return self._iterStreamReadFn( self.getJointWorldMtxPos(), self.header.jointCount, self.stream.readMat44 )
    
    def iterBoneMap( self ):
        return self._iterStreamReadFn( self.getJointMapPos(), 256, self.stream.readByte )
            
    def iterGroups( self ):
        return self._iterInstanceReadFn( self.getGroupPos(), self.header.groupCount, rModelGroup )
            
    def iterMaterials( self ):
        offset = self.getMaterialPos()
        for i in range( self.header.materialCount ):
            self.stream.seek( offset )
            name = self.stream.readBytes( rModel.MATERIAL_NAME_LENGTH ).decode( "ASCII" ).rstrip( '\0' )
            offset = self.stream.tell()
            yield name
            
    def iterPrimitives( self ):
        return self._iterInstanceReadFn( self.getPrimitivePos(), self.header.primitiveCount, rModelPrimitive )
    
    def iterPrimitiveJointLinks( self ):
        return self._iterInstanceReadFn( self.getPrimitiveLinkPos(), self.header.primitiveJointLinkCount, rModelPrimitiveJointLink )

    def getVertexBuffer( self ):
        self.stream.seek( self.getVertexBufferPos() )
        return self.stream.readBytes( self.header.vertexBufferSize )
    
    def getVertexBuffer2( self ):
        if not self.hasVertexBuffer2(): 
            return None
        
        self.stream.seek( self.getVertexBuffer2Pos() )
        return self.stream.readBytes( self.header.vertexBuffer2Size )
    
    def getIndexBuffer( self ):
        self.stream.seek( self.getIndexBufferPos() )
        return self.stream.readBytes( self.header.indexCount * 2 )
    
    def getExData( self ):
        self.stream.seek( self.getExDataPos() )
        hasExData = self.stream.readInt() == 1
        if not hasExData:
            return None
        exData = rModelExData()
        exData.read( self.header.primitiveCount, self.stream )
        return exData
    
class rModelStreamWriter( rModelStreamBase ):
    def __init__( self, stream ):
        super( rModelStreamWriter, self ).__init__( stream )
        self.jointLocalMtx = None 
        self.jointInvBindMtx = None
        self.boneMap = None
        self.init()
        
    def seek( self, pos ):
        diff = pos - self.stream.getSize()
        if diff > 0:
            self.stream.seek( self.stream.getSize() )
            for i in range( diff ):
                self.stream.writeByte( 0 )
        self.stream.seek( pos )
        
    def align( self, alignment ):
        while ( self.stream.tell() - self.headerPos ) % alignment != 0:
            self.stream.writeByte( 0 )
        
    def init( self ):
        self.headerPos = self.stream.tell()
        self.header = rModelHeader()
        self.seek( rModelHeader.SIZE )
        self.jointLocalMtx = []
        self.jointInvBindMtx = []
        self.boneMap = []
        for i in range(256):
            self.boneMap.append(-1)
        
    def flush( self ):        
        if ( self.header.exDataOffset == 0 ):
            # needs to be filled in even if missing
            self.setExData( None )
            
        # write header with all populated values
        endPos = self.stream.tell()        
        self.seek( self.headerPos )
        self.header.write( self.stream )
        self.seek( endPos )
        
    def setVersion( self, version ):
        self.header.version = version
        
    def setVertexCount( self, value ):
        self.header.vertexCount = value
        
    def setPolygonCount( self, value ):
        self.header.polygonCount = value
        
    def setBoundingSphere( self, value ):
        self.header.boundingSphere = value
        
    def setMin( self, value ):
        self.header.min = value
        
    def setMax( self, value ):
        self.header.max = value
        
    def calcBounds( self ):
        raise Exception("Not implemented")
    
    def setField90( self, value ):
        self.header.feld90 = value
        
    def setField94( self, value ):
        self.header.field94 = value
    
    def setField98( self, value ):
        self.header.field98 = value
        
    def setField9c( self, value ):
        self.header.field9c = value
    
    def beginJointList( self ):
        self.header.jointOffset = self.stream.tell() - self.headerPos
        
    def addJoint( self, joint, localMtx, invBindMtx ): 
        index = self.header.jointCount
        self.header.jointCount += 1
        joint.write( self.stream )
        self.jointLocalMtx.append( localMtx )
        self.jointInvBindMtx.append( invBindMtx )
        
    def setJointMap( self, map ):
        assert(len(map) == 256)
        self.boneMap = map
        
    def endJointList( self ):
        # write joint matrices & bonemap
        for mtx in self.jointLocalMtx:
            self.stream.writeMat44( mtx )
        self.jointLocalMtx = None
        
        for mtx in self.jointInvBindMtx:
            self.stream.writeMat44( mtx )
        self.jointInvBindMtx = None
        
        for val in self.boneMap:
            self.stream.writeByte( val )
        self.bneMap = None
        pass
        
    def beginGroupList( self ):
        self.header.groupOffset = self.stream.tell() - self.headerPos 
        
    def addGroup( self, group ):
        index = self.header.groupCount
        self.header.groupCount += 1  
        #self.seek( self.getGroupPos( index ) )
        group.write( self.stream )    
    
    def endGroupList( self ):
        pass
    
    def beginMaterialList( self ):
        self.header.materialOffset = self.stream.tell() - self.headerPos
        
    def addMaterial( self, name ):
        index = self.header.materialCount
        self.header.materialCount += 1
        start = self.stream.tell()
        self.stream.writeBytes( name.encode("ASCII") )
        end = self.stream.tell()
        paddingBytes = rModel.MATERIAL_NAME_LENGTH - ( end - start )
        for i in range( paddingBytes ):
            self.stream.writeByte( 0 )
        
    def endMaterialList( self ):
        pass
    
    def beginPrimitiveList( self ):
        self.header.primitiveOffset = self.stream.tell() - self.headerPos
        
    def addPrimitive( self, prim ):
        index = self.header.primitiveCount
        self.header.primitiveCount += 1
        #self.seek( self.getPrimitivePos( index ) )
        prim.write( self.stream )
        
    def endPrimitiveList( self ):
        pass
    
    def beginPrimitiveJointLinkList( self ):
        pass
    
    def addPrimitiveJointLink( self, primJointLink ):
        self.header.primitiveJointLinkCount += 1
        primJointLink.write( self.stream )     
    
    def endPrimitiveJointLinkList( self ):
        pass
    
    def beginVertexBuffer( self ):
        self.header.vertexBufferOffset = self.stream.tell() - self.headerPos
        
    def endVertexBuffer( self ):
        self.header.vertexBufferSize = self.stream.tell() - self.getVertexBufferPos()
        pass
    
    def setVertexBuffer( self, vertexBuffer ):
        self.beginVertexBuffer()
        self.stream.writeBytes( vertexBuffer )
        self.endVertexBuffer()
        
    def beginVertexBuffer2( self ):
        pass
    
    def endVertexBuffer2( self ):
        self.header.vertexBuffer2Size = self.stream.tell() - self.getVertexBuffer2Pos()
    
    def setVertexBuffer2( self, buffer ):
        self.beginVertexBuffer2()
        self.stream.writeBytes( buffer )
        self.endVertexBuffer2()
        
    def beginIndexBuffer( self ):
        self.header.indexBufferOffset = self.stream.tell() - self.headerPos
        
    def endIndexBuffer( self ):
        self.header.indexCount = int( ( self.stream.tell() - self.getIndexBufferPos() ) / 2 )
        self.align( 4 )
    
    def setIndexBuffer( self, buffer ):
        self.beginIndexBuffer()
        self.stream.writeBytes( buffer )
        self.endIndexBuffer()   
        
    def beginExData( self ):
        self.header.exDataOffset = self.stream.tell() - self.headerPos
        
    def endExData( self ):
        pass
        
    def setExData( self, exData ):
        self.beginExData()
        if exData != None:
            self.stream.writeInt( 1 )
            exData.write( self.stream )
        else:
            self.stream.writeInt( 0 )
        self.endExData() 

class rModel:
    '''Represents all of the data in an rModel resource'''
    
    MATERIAL_NAME_LENGTH = 128
        
    def __init__( self ):
        self.header = rModelHeader()
        self.joints = []
        self.jointLocalMtx = []
        self.jointInvBindMtx = []
        self.boneMap = []
        self.groups = []
        self.materials = []
        self.primitives = []
        self.primitiveJointLinks = []
        self.vertexBuffer = []
        self.vertexBuffer2 = None
        self.indexBuffer = []
        self.exData = None
        
    def read( self, stream ):
        reader = rModelStreamReader( stream )
        self.header = reader.getHeader()
        
        for joint in reader.iterJoints():
            self.joints.append( joint )
            
        for mtx in reader.iterJointLocalMtx():
            self.jointLocalMtx.append( mtx )
            
        for mtx in reader.iterJointWorldMtx():
            self.jointInvBindMtx.append( mtx )
            
        for boneMapIdx in reader.iterBoneMap():
            self.boneMap.append( boneMapIdx )
        
        for grp in reader.iterGroups():
            self.groups.append( grp )
            
        for mat in reader.iterMaterials():
            self.materials.append( mat )
            
        for prim in reader.iterPrimitives():
            self.primitives.append( prim )
            
        for primJointLink in reader.iterPrimitiveJointLinks():
            self.primitiveJointLinks.append( primJointLink )
            
        self.vertexBuffer = reader.getVertexBuffer()
        self.vertexBuffer2 = reader.getVertexBuffer2()
        self.indexBuffer = reader.getIndexBuffer()
        self.exData = reader.getExData()
        
    def write( self, stream ):
        writer = rModelStreamWriter( stream )
        writer.setVersion( self.header.version )
        writer.setVertexCount( self.header.vertexCount )
        writer.setPolygonCount( self.header.polygonCount )
        writer.setField90( self.header.field90 )
        writer.setField94( self.header.field94 )
        writer.setField98( self.header.field98 )
        writer.setField9c( self.header.field9c )
        writer.setBoundingSphere( self.header.boundingSphere )
        writer.setMax( self.header.max )
        writer.setMin( self.header.min )
        
        if len(self.joints) > 0:
            writer.beginJointList()
            i = 0
            for joint in self.joints:
                writer.addJoint( joint, self.jointLocalMtx[i], self.jointInvBindMtx[i])
                i += 1
            writer.setJointMap( self.boneMap )
            writer.endJointList()
            
        if len( self.groups ) > 0:
            writer.beginGroupList()
            for grp in self.groups:
                writer.addGroup( grp )
            writer.endGroupList()
        
        if len( self.materials ) > 0:
            writer.beginMaterialList()
            for mat in self.materials:
                writer.addMaterial( mat )
            writer.endMaterialList()
            
        if len( self.primitives ) > 0:
            writer.beginPrimitiveList()
            for prim in self.primitives:
                writer.addPrimitive( prim )
            writer.endPrimitiveList()
            
        if len( self.primitiveJointLinks ):
            writer.beginPrimitiveJointLinkList()
            for primJointLink in self.primitiveJointLinks:
                writer.addPrimitiveJointLink( primJointLink )
            writer.endPrimitiveJointLinkList()
            
        writer.setVertexBuffer( self.vertexBuffer )
        writer.setIndexBuffer( self.indexBuffer )
        writer.setExData( self.exData )
        writer.flush()

class MrlTextureInfo: 
    def __init__(self):
        self.hash = 0
        self.field04 = 0
        self.field08 = 0
        self.field0c = 0
        self.field10 = 0
        self.field14 = 0
        self.path = ""
        
    def read(self, stream):
        self.hash = stream.readInt()
        self.field04 = stream.readInt()
        self.field08 = stream.readInt()
        self.field0c = stream.readInt()
        self.field10 = stream.readInt()
        self.field14 = stream.readInt()
        self.path = stream.readBytes( rModel.MATERIAL_NAME_LENGTH ).decode( "ASCII" ).rstrip( "\0" )
        
    def write(self, stream):
        stream.writeInt( self.hash )
        stream.writeInt( self.field04 )
        stream.writeInt( self.field08 )
        stream.writeInt( self.field0c )
        stream.writeInt( self.field10 )
        stream.writeInt( self.field14 )
        stream.writeString( self.path )
    
class MrlHeader:
    MAGIC = 0x22004C524D
    SIZE = 0x28
    
    def __init__(self):
        self.magic = 0x22004C524D
        self.materialCount = 0
        self.textureCount = 0
        self.hash = 0
        self.field14 = 0
        self.textureOffset = 0
        self.materialOffset = 0   
        
    def read(self, stream):
        self.magic = stream.readInt64()
        self.materialCount = stream.readInt()
        self.textureCount = stream.readInt()
        self.hash = stream.readInt()
        self.field14 = stream.readInt()
        self.textureOffset = stream.readInt64()
        self.materialOffset = stream.readInt64()
        
    def write( self, stream ):
        self.writeInt64( self.magic )
        self.writeInt( self.materialCount )
        self.writeInt( self.textureCount )
        self.writeInt( self.hash )
        self.writeInt( self.field14 )
        self.writeInt( self.textureOffset )
        self.writeInt( self.materialOffset )
        
class MrlWriter:
    def __init__(self, stream):
        self.stream = stream
        self.header = MrlHeader()
        self.headerStart = 0
    
    def beginFile( self, hashVal, field14 ):
        # rewrite header as we go
        self.headerStart = self.stream.tell()
        self.header.hash = hashVal
        self.header.field14 = field14        
        self.stream.seek( self.headerStart + MrlHeader.SIZE )
        
    def endFile( self ):
        endPos = self.stream.tell()
        self.stream.seek( self.headerStart )
        # write fixed up header
        self.header.write( self.stream )
        self.stream.seek( endPos )
        
    def beginTextureInfoList( self ):
        self.header.textureOffset = stream.tell() - self.headerStart
        pass
    
    def writeTextureInfo( self, textureInfo ):
        textureInfo.write( self.stream )
        self.header.textureCount += 1
        pass
    
    def endTextureInfoList( self ):
        pass
    
    def beginMaterialInfoList( self ):
        self.header.materialOffset = stream.tell() - self.headerStart
        pass
    
    def writeMaterialInfo( self, materialInfo ):
        materialInfo.write( self.stream )
        self.header.materialCount += 1
        pass
    
    def endMaterialInfoList( self ):
        pass
    
class MrlMaterialInfo:
    def __init__( self ):
        self.typeHash = 0
        self.field04 = 0
        self.hash08 = 0
        self.offset0c = 0
        self.blendSource = ShaderObjectId()
        self.depthStencil = ShaderObjectId()
        self.renderSetting = ShaderObjectId()
        self.cmdListInfo = 0
        self.flags20 = 0
        self.field24 = 0
        self.field28 = 0
        self.field2c = 0
        self.field30 = 0
        self.field34 = 0
        self.cmdListOffset = 0
        self.offset40 = 0
        
    def read( self, stream ):
        self.typeHash = stream.readInt()
        self.field04 = stream.readInt()
        self.hash08 = stream.readInt()
        self.offset0c = stream.readInt()
        self.blendSource.read( stream )
        self.depthStencil.read( stream )
        self.renderSetting.read( stream )
        self.cmdListInfo.read( stream )
        self.flags20 = stream.readInt()
        self.field24 = stream.readInt()
        self.field28 = stream.readInt()
        self.field2c = stream.readInt()
        self.field30 = stream.readInt()
        self.field34 = stream.readInt()
        self.cmdListOffset = stream.readInt64()
        self.offset40 = stream.readInt64()
    
    
class MrlFileReader:
    def __init__( self, stream ):
        self.stream = stream
        self.startPos = stream.tell()
        self.header = MrlHeader()
        
    def beginFile( self ):
        self.header.read( self.stream )
    
    def endFile( self ):
        pass
    
    def getHeader( self ):
        return self.header
    
    def iterTextureInfo( self ):
        offset = self.header.materialOffset
        for i in range( self.header.textureCount ):
            self.reader.seek( offset )
            textureInfo = MrlTextureInfo()
            textureInfo.read( self.stream )
            offset = stream.tell()
            yield textureInfo
            
    def iterMaterialInfo( self ):
        offset = self.header.materialOffset
        for i in range( self.header.materialCount ):
            self.reader.seek( offset )
            materialInfo = MrlMaterialInfo()
            materialInfo.read( stream ) 
            offset = stream.tell()
            yield materialInfo
            
    def iterMaterialCmd( self, materialInfo ):
        offset = materialInfo.cmdListOffset
        for i in range( materialInfo.cmdListInfo.count ):
            self.reader.seek( offset )
            cmd = MrlMaterialCmd()
            cmd.read( self.stream ) 
            offset = self.stream.tell()
            yield cmd 
            

class MrlFile:
    def __init__(self):
        self.header = MrlHeader()
        self.textures = []
        self.materials = []
        
    def read(self, stream):
        self.header.read(stream)
        
        stream.seek( self.header.textureOffset )
        for i in range(0, self.header.textureCount):
            tex = MrlTextureInfo()
            tex.read(stream)
            print(tex.path)
            self.textures.append(tex)
            
    def write( self, stream ):
        writer = MrlWriter( stream )
        
        # write file
        writer.beginFile( self.header.hash, self.header.field14 )
        
        # write textures
        writer.beginTextureInfoList()
        for textureInfo in self.textures:
            writer.writeTextureInfo( textureInfo )
        writer.endTextureInfoList()
        
        # write materials
        writer.beginMaterialInfoList()
        for materialInfo in self.materials:
            writer.writeMaterialInfo( materialInfo )
        writer.endMaterialInfoList()
        
        writer.endFile()
        
# high-level model representation to simplify processing        
class Material:
    def __init__( self ):
        self.name = "defaultMaterial"
        self.type = 0 # todo
        self.blendState = 0
        self.depthStencilState = 0
        self.rasterizerState = 0
        self.flags20
        # etc

class Model:
    def __init__( self ):
        self.materials = []
        
    def _loadMrl( stream ):
        reader = MrlFileReader( stream )
        reader.beginFile()
        
        textures = []
        for textureInfo in reader.iterTextureInfo():
            textures.append( textureInfo )
            
        reader.endFile()