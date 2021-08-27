from mtrshader import rShaderObjectId
from mtncl import *
import mtutil

class rModelConstants:
    MATERIAL_NAME_LENGTH = 128

class rModelPrimitiveIndices:
    '''rModel joint packed joint, material and lod indices'''
    SIZE = 0x04
    
    def __init__(self, value=0):
        self.value = value
        
    def _unpack(self, mask, bitOffset):
        return (self.value & (mask << bitOffset)) >> bitOffset
    
    def _pack(self, mask, bitOffset, index):
        self.value = (self.value & ~(mask << bitOffset)) | (index & mask) << bitOffset
        
    def getGroupId(self):
        return self._unpack(0x00000FFF, 0)
    
    def setGroupId(self, index):
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
        self.vertexBuffer2Size = 0 # not used
        self.groupCount = 0
        self.jointOffset = 0
        self.groupOffset = 0
        self.materialOffset = 0
        self.primitiveOffset = 0
        self.vertexBufferOffset = 0
        self.indexBufferOffset = 0
        self.exDataOffset = 0 # set but not used (data is empty)
        self.center = NclVec3()
        self.radius = 0
        self.min = NclVec4()
        self.max = NclVec4()
        self.field90 = 1000 # constant
        self.field94 = 3000 # constant
        self.field98 = 1 # rarely 0, 4
        self.field9c = 0 # constant
        self.primitiveJointLinkCount = 0
        
    def read( self, stream ):
        self.magic = stream.readUInt()
        self.version = stream.readUShort()
        self.jointCount = stream.readUShort()
        self.primitiveCount = stream.readUShort()
        self.materialCount = stream.readUShort()
        self.vertexCount = stream.readUInt()
        self.indexCount = stream.readUInt()
        self.polygonCount = stream.readUInt()
        self.vertexBufferSize = stream.readUInt()
        self.vertexBuffer2Size = stream.readUInt()
        self.groupCount = stream.readUInt64()
        self.jointOffset = stream.readUInt64()
        self.groupOffset = stream.readUInt64()
        self.materialOffset = stream.readUInt64()
        self.primitiveOffset = stream.readUInt64()
        self.vertexBufferOffset = stream.readUInt64()
        self.indexBufferOffset = stream.readUInt64()
        self.exDataOffset = stream.readUInt64()
        self.center = stream.readVec3()
        self.radius = stream.readFloat()
        self.min = stream.readVec4()
        self.max = stream.readVec4()
        self.field90 = stream.readUInt()
        self.field94 = stream.readUInt()
        self.field98 = stream.readUInt()
        self.field9c = stream.readUInt()
        self.primitiveJointLinkCount = stream.readUInt()
        
    def write( self, stream ):
        stream.writeUInt( self.magic )
        stream.writeUShort( self.version )
        stream.writeUShort( self.jointCount )
        stream.writeUShort( self.primitiveCount )
        stream.writeUShort( self.materialCount )
        stream.writeUInt( self.vertexCount )
        stream.writeUInt( self.indexCount )
        stream.writeUInt( self.polygonCount )
        stream.writeUInt( self.vertexBufferSize )
        stream.writeUInt( self.vertexBuffer2Size )
        stream.writeUInt64( self.groupCount )
        stream.writeUInt64( self.jointOffset )
        stream.writeUInt64( self.groupOffset )
        stream.writeUInt64( self.materialOffset )
        stream.writeUInt64( self.primitiveOffset )
        stream.writeUInt64( self.vertexBufferOffset )
        stream.writeUInt64( self.indexBufferOffset )
        stream.writeUInt64( self.exDataOffset )
        stream.writeVec3( self.center )
        stream.writeFloat( self.radius )
        stream.writeVec4( self.min )
        stream.writeVec4( self.max )
        stream.writeUInt( self.field90 )
        stream.writeUInt( self.field94 )
        stream.writeUInt( self.field98 )
        stream.writeUInt( self.field9c )
        stream.writeUInt( self.primitiveJointLinkCount )
        
class rModelPrimitive:
    '''Represents a model resource primitive; each primitive specifies the data needed for a drawcall'''
    
    SIZE = 0x38
    
    def __init__(self):
        self.flags = 0xFFFF
        self.vertexCount = 0
        self.indices = rModelPrimitiveIndices()
        self.indices.setLodIndex( 255 ) # lods arent used for characters
        self.vertexFlags = 9 # 3, 17, 25, ..
        self.vertexStride = 0
        self.renderFlags = 195 # 67, 3
        self.vertexStartIndex = 0
        self.vertexBufferOffset = 0
        # 4 vertex weights per bone
        self.vertexShader = mtutil.getShaderObjectIdFromName( 'IASkinTB4wt' )
        self.indexBufferOffset = 0
        self.indexCount = 0
        self.indexStartIndex = 0
        self.boneIdStart = 0
        self.primitiveJointLinkCount = 0
        self.id = 0
        self.minVertexIndex = 0
        self.maxVertexIndex = 0
        self.field2c = 0 # always 0
        self.primitiveJointLinkPtr = 0 # init at runtime
        
    def read(self, stream):
        self.flags = stream.readUShort()
        self.vertexCount = stream.readUShort()
        self.indices = rModelPrimitiveIndices(stream.readUInt())
        self.vertexFlags = stream.readUShort()
        self.vertexStride = stream.readUByte()
        self.renderFlags = stream.readUByte()
        self.vertexStartIndex = stream.readUInt()
        self.vertexBufferOffset = stream.readUInt()
        self.vertexShader = rShaderObjectId(stream.readUInt())
        self.indexBufferOffset = stream.readUInt()
        self.indexCount = stream.readUInt()
        self.indexStartIndex = stream.readUInt()
        self.boneIdStart = stream.readUByte()
        self.primitiveJointLinkCount = stream.readUByte()
        self.id = stream.readUShort()
        self.minVertexIndex = stream.readUShort()
        self.maxVertexIndex = stream.readUShort()
        self.field2c = stream.readUInt()
        self.primitiveJointLinkPtr = stream.readUInt64()
        
    def write( self, stream ):
        stream.writeUShort( self.flags )
        stream.writeUShort( self.vertexCount )
        stream.writeUInt( self.indices.getValue() )
        stream.writeUShort( self.vertexFlags )
        stream.writeUByte( self.vertexStride )
        stream.writeUByte( self.renderFlags )
        stream.writeUInt( self.vertexStartIndex )
        stream.writeUInt( self.vertexBufferOffset )
        stream.writeUInt( self.vertexShader.getValue() )
        stream.writeUInt( self.indexBufferOffset )
        stream.writeUInt( self.indexCount )
        stream.writeUInt( self.indexStartIndex )
        stream.writeUByte( self.boneIdStart )
        stream.writeUByte( self.primitiveJointLinkCount )
        stream.writeUShort( self.id )
        stream.writeUShort( self.minVertexIndex )
        stream.writeUShort( self.maxVertexIndex )
        stream.writeUInt( self.field2c )
        stream.writeUInt64( self.primitiveJointLinkPtr )
        
class rModelGroup:
    '''Group of model primitives that form an object'''
    
    SIZE = 0x20
    
    def __init__(self):
        self.id = 0 
        self.field04 = 0  # always 0
        self.field08 = 0  # always 0
        self.field0c = 0  # always 0
        self.boundingSphere = NclVec4()
        
    def read(self, stream):
        self.id = stream.readUInt()
        self.field04 = stream.readUInt()
        self.field08 = stream.readUInt()
        self.field0c = stream.readUInt() 
        self.boundingSphere = stream.readVec4()
        
    def write( self, stream ):
        stream.writeUInt( self.id )
        stream.writeUInt( self.field04 )
        stream.writeUInt( self.field08 )
        stream.writeUInt( self.field0c )
        stream.writeVec4( self.boundingSphere )
        
class rModelJoint:
    '''Represents a model resource joint's properties and relations'''
    
    SIZE = 0x18
    
    def __init__(self):
        self.id = 0 # original name is 'no'
        self.parentIndex = 0
        self.symmetryIndex = 0
        self.field03 = 0 # always 0
        self.field04 = 0 # varies a lot, similar to length?
        self.length = 0  
        self.offset = NclVec3()
        
    def read(self, stream):
        self.id = stream.readUByte()
        self.parentIndex = stream.readUByte()
        self.symmetryIndex = stream.readUByte()
        self.field03 = stream.readUByte()
        self.field04 = stream.readFloat()
        self.length = stream.readFloat()
        self.offset = stream.readVec3()
        
    def write( self, stream ):
        stream.writeUByte( self.id )
        stream.writeUByte( self.parentIndex )
        stream.writeByte( self.symmetryIndex )
        stream.writeUByte( self.field03 )
        stream.writeFloat( self.field04 )
        stream.writeFloat( self.length )
        stream.writeVec3( self.offset )

class rModelPrimitiveJointLink:
    SIZE = 0x90
    
    def __init__( self ):
        self.jointIndex = 0
        self.field04 = 0 # always 0
        self.field08 = 0 # always 0
        self.field0c = 0 # always 0
        self.boundingSphere = NclVec4()
        self.min = NclVec4()
        self.max = NclVec4()
        self.localMtx = nclCreateMat44()
        self.field80 = NclVec4()
        
    def read( self, stream ):
        self.jointIndex = stream.readUInt()
        self.field04 = stream.readUInt()
        self.field08 = stream.readUInt()
        self.field0c = stream.readUInt()
        self.boundingSphere = stream.readVec4()
        self.min = stream.readVec4()
        self.max = stream.readVec4()
        self.localMtx = stream.readMat44()
        self.field80 = stream.readVec4()
        
    def write( self, stream ):
        stream.writeUInt( self.jointIndex )
        stream.writeUInt( self.field04 )
        stream.writeUInt( self.field08 )
        stream.writeUInt( self.field0c )
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
        self.count1 = stream.readUShort()
        self.count2 = stream.readUShort()
        for i in range( primitiveCount ):
            self.primValues.append( stream.readUInt() )
        self.vertexBufferSize = stream.readUInt()
        self.vertexBuffer = stream.readBytes( self.exVertexBufferSize )
        self.vertexBuffer2Size = stream.readUInt()
        self.vertexBuffer2 = stream.readBytes( self.exVertexBuffer2Size )
    
    def write( self, stream ):
        stream.writeUShort( self.count1 )
        stream.writeUShort( self.count2 )
        for value in self.primValues:
            stream.writeUInt( value )
        stream.writeUInt( self.vertexBufferSize )
        stream.writeBytes( self.vertexBuffer )
        stream.writeUInt( self.vertexBuffer2Size )
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
        return self.headerPos + self.header.materialOffset + ( i * rModelConstants.MATERIAL_NAME_LENGTH )
    
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
        return self.getVertexBufferPos() + self.header.vertexBufferSize
    
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
        self.headerPos = self.stream.getOffset()
        self.header.read( self.stream )
        pass
    
    def endFile( self ):
        pass
    
    def _iterInstanceReadFn( self, offset, count, type ):
        if offset == 0 or count == 0: return
        for i in range( count ):
            self.stream.setOffset( offset )
            value = type()
            value.read( self.stream )
            offset = self.stream.getOffset()
            yield value
            
    def _iterStreamReadFn( self, offset, count, func ):
        if offset == 0 or count == 0: return
        for i in range( count ):
            self.stream.setOffset( offset )
            value = func()
            offset = self.stream.getOffset()
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
            self.stream.setOffset( offset )
            name = self.stream.readBytes( rModelConstants.MATERIAL_NAME_LENGTH ).decode( "ASCII" ).rstrip( '\0' )
            offset = self.stream.getOffset()
            yield name
            
    def iterPrimitives( self ):
        return self._iterInstanceReadFn( self.getPrimitivePos(), self.header.primitiveCount, rModelPrimitive )
    
    def iterPrimitiveJointLinks( self ):
        return self._iterInstanceReadFn( self.getPrimitiveLinkPos(), self.header.primitiveJointLinkCount, rModelPrimitiveJointLink )

    def getVertexBuffer( self ):
        self.stream.setOffset( self.getVertexBufferPos() )
        return self.stream.readBytes( self.header.vertexBufferSize )
    
    def getVertexBuffer2( self ):
        if not self.hasVertexBuffer2(): 
            return None
        
        self.stream.setOffset( self.getVertexBuffer2Pos() )
        return self.stream.readBytes( self.header.vertexBuffer2Size )
    
    def getIndexBuffer( self ):
        self.stream.setOffset( self.getIndexBufferPos() )
        return self.stream.readBytes( self.header.indexCount * 2 )
    
    def getExData( self ):
        self.stream.setOffset( self.getExDataPos() )
        hasExData = self.stream.readUInt() == 1
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
            self.stream.setOffset( self.stream.getSize() )
            for i in range( diff ):
                self.stream.writeByte( 0 )
        self.stream.setOffset( pos )
        
    def align( self, alignment ):
        while ( self.stream.getOffset() - self.headerPos ) % alignment != 0:
            self.stream.writeByte( 0 )
        
    def init( self ):
        self.headerPos = self.stream.getOffset()
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
        endPos = self.stream.getOffset()        
        self.seek( self.headerPos )
        self.header.write( self.stream )
        self.seek( endPos )
        
    def setVersion( self, version ):
        self.header.version = version
        
    def setVertexCount( self, value ):
        self.header.vertexCount = value
        
    def setPolygonCount( self, value ):
        self.header.polygonCount = value
        
    def setCenter( self, value ):
        self.header.center = value
        
    def setRadius( self, value ):
        self.header.radius = value
        
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
        self.header.jointOffset = self.stream.getOffset() - self.headerPos
        
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
        self.header.groupOffset = self.stream.getOffset() - self.headerPos 
        
    def addGroup( self, group ):
        index = self.header.groupCount
        self.header.groupCount += 1  
        #self.seek( self.getGroupPos( index ) )
        group.write( self.stream )    
    
    def endGroupList( self ):
        pass
    
    def beginMaterialList( self ):
        self.header.materialOffset = self.stream.getOffset() - self.headerPos
        
    def addMaterial( self, name ):
        index = self.header.materialCount
        self.header.materialCount += 1
        start = self.stream.getOffset()
        self.stream.writeBytes( name.encode("ASCII") )
        end = self.stream.getOffset()
        paddingBytes = rModelConstants.MATERIAL_NAME_LENGTH - ( end - start )
        for i in range( paddingBytes ):
            self.stream.writeByte( 0 )
        
    def endMaterialList( self ):
        pass
    
    def beginPrimitiveList( self ):
        self.header.primitiveOffset = self.stream.getOffset() - self.headerPos
        
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
        self.header.vertexBufferOffset = self.stream.getOffset() - self.headerPos
        
    def endVertexBuffer( self ):
        self.header.vertexBufferSize = self.stream.getOffset() - self.getVertexBufferPos()
        pass
    
    def setVertexBuffer( self, vertexBuffer ):
        self.beginVertexBuffer()
        self.stream.writeBytes( vertexBuffer )
        self.endVertexBuffer()
        
    def beginVertexBuffer2( self ):
        pass
    
    def endVertexBuffer2( self ):
        self.header.vertexBuffer2Size = self.stream.getOffset() - self.getVertexBuffer2Pos()
    
    def setVertexBuffer2( self, buffer ):
        self.beginVertexBuffer2()
        self.stream.writeBytes( buffer )
        self.endVertexBuffer2()
        
    def beginIndexBuffer( self ):
        self.header.indexBufferOffset = self.stream.getOffset() - self.headerPos
        
    def endIndexBuffer( self ):
        self.header.indexCount = int( ( self.stream.getOffset() - self.getIndexBufferPos() ) / 2 )
        self.align( 4 )
    
    def setIndexBuffer( self, buffer ):
        self.beginIndexBuffer()
        self.stream.writeBytes( buffer )
        self.endIndexBuffer()   
        
    def beginExData( self ):
        self.header.exDataOffset = self.stream.getOffset() - self.headerPos
        
    def endExData( self ):
        pass
        
    def setExData( self, exData ):
        self.beginExData()
        if exData != None:
            self.stream.writeUInt( 1 )
            exData.write( self.stream )
        else:
            self.stream.writeUInt( 0 )
        self.endExData() 

class rModelData:
    '''Represents all of the data in an rModel resource'''
        
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
        writer.setCenter( self.header.center )
        writer.setRadius( self.header.radius )
        writer.setMax( self.header.max )
        writer.setMin( self.header.min )
        
        if len(self.joints) > 0:
            writer.beginJointList()
            for i in range(len(self.joints)):
                writer.addJoint( self.joints[i], self.jointLocalMtx[i], self.jointInvBindMtx[i] )
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
        
    def calcModelMtx( self ):
        modelMtx = nclCreateMat44()
        if len( self.joints ) > 0:
            modelMtx = nclMultiply( self.jointInvBindMtx[0], self.jointLocalMtx[0] )
        return modelMtx
        