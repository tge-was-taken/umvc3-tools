import yaml
from collections import namedtuple

import mtutil
from mtrshader import rShaderObjectId
import mvc3shaderdb
import mvc3types

class rMaterialTextureInfo: 
    SIZE = 0x28
    MAX_NAME_LENGTH = 64
    
    def __init__( self ):
        self.typeHash = 0
        self.field04 = 0
        self.field08 = 0
        self.field0c = 0
        self.field10 = 0
        self.field14 = 0
        self.path = ""
        
    def read( self, stream ):
        self.typeHash = stream.readInt()
        self.field04 = stream.readInt()
        self.field08 = stream.readInt()
        self.field0c = stream.readInt()
        self.field10 = stream.readInt()
        self.field14 = stream.readInt()
        self.path = mtutil.readCStringBuffer( stream, rMaterialTextureInfo.MAX_NAME_LENGTH )
        
    def write( self, stream ):
        stream.writeUInt( self.typeHash )
        stream.writeUInt( self.field04 )
        stream.writeUInt( self.field08 )
        stream.writeUInt( self.field0c )
        stream.writeUInt( self.field10 )
        stream.writeUInt( self.field14 )
        mtutil.writeCStringBuffer( stream, self.path, rMaterialTextureInfo.MAX_NAME_LENGTH )
        
class rMaterialCmdListInfo:
    def __init__(self, value=0):
        self.value = value
        
    def _unpack(self, mask, bitOffset):
        return mtutil.bitUnpack( self.value, mask, bitOffset )
    
    def _pack(self, mask, bitOffset, index):
        self.value = mtutil.bitPack( self.value, mask, bitOffset, index )
        
    def getCount(self):
        return self._unpack(0x00000FFF, 0)
    
    def setCount(self, index):
        self._pack(0x00000FFF, 0, index)
        
    def getFlags( self ):
        return self._unpack( 0x000FFFFF, 12 )
    
    def setFlags( self, value ):
        self._pack( 0x000FFFFF, 12, value )
        
    def getValue(self):
        return self.value
        
    def setValue(self, value):
        self.value = value
        
class rMaterialCmdType:
    SetFlag = 0
    SetConstantBuffer = 1
    SetSamplerState = 2
    SetTexture = 3
    
class rMaterialCmdInfo:
    def __init__( self, value = 0 ):
        self.value = value
        
    def _unpack(self, mask, bitOffset):
        return mtutil.bitUnpack( self.value, mask, bitOffset )
    
    def _pack(self, mask, bitOffset, index):
        self.value = mtutil.bitPack( self.value, mask, bitOffset, index )
        
    def getType( self ):
        return self._unpack( 0x0000000F, 0 )
    
    def setType( self, cmdType ):
        self._pack( 0x0000000F, 0, cmdType )
        
    def getUnknown( self ):
        return self._unpack( 0x0000FFFF, 4 )
    
    def setUnknown( self, val ):
        self._pack( 0x0000FFFF, 4, val )
        
    def getShaderObjectIndex( self ):
        return self._unpack( 0x00000FFF, 20 )
    
    def setShaderObjectIndex( self, index ):
        self._pack( 0x00000FFF, 20, index )
        
    def getValue( self ):
        return self.value
    
    def setValue( self, val ):
        self.value = val
        
class rMaterialCBMaterial:
    def __init__( self ):
        self.field00 = 0.3471069931983948
        self.field04 = 0.3471069931983948
        self.field08 = 0.3471069931983948
        self.field0c = 1.0
        
        self.field10 = 1.0
        self.field14 = 1.0
        self.field18 = 1.0
        self.field1c = 10.0
        
        self.field20 = 1.0
        self.field24 = -0.0
        self.field28 = 0.0
        self.field2c = 5.0
        
        self.field30 = 0.0
        self.field34 = 1.0
        self.field38 = 0.0
        self.field3c = 0.0
        
        self.field40 = 1.0
        self.field44 = 0.0
        self.field48 = 0.0
        self.field4c = 0.0
        
        self.field50 = 0.0
        self.field54 = 1.0
        self.field58 = 0.0
        self.field5c = 0.0
        
        self.field60 = 1.0
        self.field64 = 0.0
        self.field68 = 0.0
        self.field6c = 0.0
        
        self.field70 = 0.0
        self.field74 = 1.0
        self.field78 = 0.0
        self.field7c = 0.0
        
    def read( self, stream ):
        self.field00 = stream.readFloat()
        self.field04 = stream.readFloat()
        self.field08 = stream.readFloat()
        self.field0c = stream.readFloat()
        
        self.field10 = stream.readFloat()
        self.field14 = stream.readFloat()
        self.field18 = stream.readFloat()
        self.field1c = stream.readFloat()
        
        self.field20 = stream.readFloat()
        self.field24 = stream.readFloat()
        self.field28 = stream.readFloat()
        self.field2c = stream.readFloat()
        
        self.field30 = stream.readFloat()
        self.field34 = stream.readFloat()
        self.field38 = stream.readFloat()
        self.field3c = stream.readFloat()
        
        self.field40 = stream.readFloat()
        self.field44 = stream.readFloat()
        self.field48 = stream.readFloat()
        self.field4c = stream.readFloat()
        
        self.field50 = stream.readFloat()
        self.field54 = stream.readFloat()
        self.field58 = stream.readFloat()
        self.field5c = stream.readFloat()
        
        self.field60 = stream.readFloat()
        self.field64 = stream.readFloat()
        self.field68 = stream.readFloat()
        self.field6c = stream.readFloat()
        
        self.field70 = stream.readFloat()
        self.field74 = stream.readFloat()
        self.field78 = stream.readFloat()
        self.field7c = stream.readFloat()
        
    def write( self, stream ):
        stream.writeFloat( self.field00 )
        stream.writeFloat( self.field04 )
        stream.writeFloat( self.field08 )
        stream.writeFloat( self.field0c )
        
        stream.writeFloat( self.field10 )
        stream.writeFloat( self.field14 )
        stream.writeFloat( self.field18 )
        stream.writeFloat( self.field1c )
        
        stream.writeFloat( self.field20 )
        stream.writeFloat( self.field24 )
        stream.writeFloat( self.field28 )
        stream.writeFloat( self.field2c )
        
        stream.writeFloat( self.field30 )
        stream.writeFloat( self.field34 )
        stream.writeFloat( self.field38 )
        stream.writeFloat( self.field3c )
        
        stream.writeFloat( self.field40 )
        stream.writeFloat( self.field44 )
        stream.writeFloat( self.field48 )
        stream.writeFloat( self.field4c )
        
        stream.writeFloat( self.field50 )
        stream.writeFloat( self.field54 )
        stream.writeFloat( self.field58 )
        stream.writeFloat( self.field5c )
        
        stream.writeFloat( self.field60 )
        stream.writeFloat( self.field64 )
        stream.writeFloat( self.field68 )
        stream.writeFloat( self.field6c )
        
        stream.writeFloat( self.field70 )
        stream.writeFloat( self.field74 )
        stream.writeFloat( self.field78 )
        stream.writeFloat( self.field7c )
    
# union
class rMaterialCmdData:
    def __init__( self, value = 0 ):
        self.value = value
        
    def getConstantBufferDataOffset( self ):
        return self.value
    
    def getShaderObjectId( self ):
        return rShaderObjectId( self.value )
    
    def getTextureIndex( self ):
        return self.value
    
    def setConstantDataBufferOffset( self, offset ):
        self.value = offset
        
    def setShaderObjectId( self, idVal ):
        self.value = idVal.getValue()
        
    def setTextureIndex( self, index ):
        self.value = index
        
    def getValue( self ):
        return self.value
    
    def setValue( self, value ):
        self.value = value
        
class rMaterialCmd:
    SIZE = 0x18
    
    def __init__( self ):
        self.info = rMaterialCmdInfo()
        self.field04 = 0
        self.data = rMaterialCmdData()
        self.shaderObjectId = rShaderObjectId()
        self.field14 = 0
        
    def read( self, stream ):
        self.info = rMaterialCmdInfo( stream.readInt() )
        self.field04 = stream.readInt()
        self.data = rMaterialCmdData( stream.readInt64() )
        self.shaderObjectId = rShaderObjectId( stream.readInt() )
        self.field14 = stream.readInt()
        
    def write( self, stream ):
        stream.writeUInt( self.info.getValue() )
        stream.writeUInt( self.field04 )
        stream.writeUInt64( self.data.getValue() )
        stream.writeUInt( self.shaderObjectId.getValue() )
        stream.writeUInt( self.field14 )
        
class rMaterialAnimEntryHeaderInfo:
    SIZE = 4
    
    def __init__( self, value = 0 ):
        self.value = value
        
    def getUnknown1( self ):
        return mtutil.bitUnpack( self.value, 0x3, 0 )
    
    def setUnknown1( self, value ):
        self.value = mtutil.bitPack( self.value, 0x3, 0, value )
        
    def getEntry2Count( self ):
        return mtutil.bitUnpack( self.value, 0xFFFF, 2 )
    
    def setEntry2Count( self, value ):
        self.value = mtutil.bitPack( self.value, 0xFFFF, 2, value )
        
    def getEntryCount( self ):
        return mtutil.bitUnpack( self.value, 0x3FFF, 18 )
    
    def setEntryCount( self, value ):
        self.value = mtutil.bitPack( self.value, 0x3FFF, 18, value )
        
    def setValue( self, value ):
        self.value = value
        
    def getValue( self ):
        return self.value
        
        
class rMaterialAnimSubEntry1:
    SIZE = 4
    
    def __init__( self ):
        self.shaderObjectId = rShaderObjectId()
        
    def read( self, stream ):
        self.shaderObjectId = rShaderObjectId( stream.readUInt() )
    
    def write( self, stream ):
        stream.writeUInt( self.shaderObjectId.getValue() )
        
class rMaterialAnimSubEntry2HeaderInfo:
    SIZE = 4
    
    def __init__( self, value = 0 ):
        self.value = value
        
    def getType( self ):
        return mtutil.bitUnpack( self.value, 0x0000000F, 0 )
    
    def setType( self, value ):
        self.value = mtutil.bitPack( self.value, 0x0000000F, 0, value )
        
    def getUnknown1( self ):
        return mtutil.bitUnpack( self.value, 0xF, 4 )
    
    def setUnknown1( self, value ):
        self.value = mtutil.bitPack( self.value, 0xF, 4, value )
        
    def getEntryCount( self ):
        return mtutil.bitUnpack( self.value, 0xFFFFFF, 8 )
    
    def setEntryCount( self, value ):
        self.value = mtutil.bitPack( self.value, 0xFFFFFF, 8, value )
        
    def setValue( self, value ):
        self.value = value
        
    def getValue( self ):
        return self.value
        
# rMaterialAnimSubEntry2TypeHeaderSizes   = [ 12, 32, 12, 24, 92, 8, 36, 36 ]
# rMaterialAnimSubEntry2TypeEntrySizes    = [ 8,  20, 8,  16, 80, 8, 24, 24 ] 
# rMaterialAnimSubEntry2TypeEntryCountMod = [ 0,  -1, 0,  -1, -1, 0, -1, -1 ]

rMaterialAnimSubEntry2TypeHeaderSizes   = [ 12, 32, 12, 24, 92, 8, 36, 36 ]
rMaterialAnimSubEntry2TypeEntrySizes    = [ 8,  20, 8,  16, 80, 8, 24, 24 ] 
rMaterialAnimSubEntry2TypeEntryCountMod = [ 0,  -1, 0,  -1, -1, 0, -1, -1 ]
        
class rMaterialAnimSubEntry2Header:
    SIZE = 0x10
    
    def __init__( self ):
        self.shaderObjectId = rShaderObjectId()
        self.info = rMaterialAnimSubEntry2HeaderInfo()
        self.field08 = 0
        self.field0c = 0
        
    def read( self, stream ):
        self.shaderObjectId = rShaderObjectId( stream.readUInt() )
        self.info = rMaterialAnimSubEntry2HeaderInfo( stream.readUInt() )
        self.field08 = stream.readUInt()
        self.field0c = stream.readUInt()
        
    def write( self, stream ):
        stream.writeUInt( self.shaderObjectId.getValue() )
        stream.writeUInt( self.info.getValue() )
        stream.writeUInt( self.field08 )
        stream.writeUInt( self.field0c )
   
class rMaterialAnimEntryHeader:
    SIZE = 32
    
    def __init__( self ):
        self.field00 = 0
        self.info = rMaterialAnimEntryHeaderInfo()
        self.entryList1Offset = 0
        self.hash = 0
        self.field14 = 0
        self.entryList2Offset = 0
        
    def read( self, stream ):
        self.field00 = stream.readUInt()
        self.info = rMaterialAnimEntryHeaderInfo( stream.readUInt() )
        self.entryList1Offset = stream.readUInt64()
        self.hash = stream.readUInt()
        self.field14 = stream.readUInt()
        self.entryList2Offset = stream.readUInt64()
        
    def write( self, stream ):
        stream.writeUInt( self.field00 )
        stream.writeUInt( self.info.getValue() )
        stream.writeUInt64( self.entryList1Offset )
        stream.writeUInt( self.hash )
        stream.writeUInt( self.field14 )
        stream.writeUInt64( self.entryList2Offset )
        
class rMaterialAnimHeader:
    SIZE = 0x8
    
    def __init__( self ):
        self.entryCount = 0
        self.field04 = 0
        
    def read( self, stream ):
        base = stream.getOffset()
        self.entryCount = stream.readUInt()
        self.field04 = stream.readUInt()
        
    def write( self, stream ):
        stream.writeUInt( self.entryCount )
        stream.writeUInt( self.field04 )
        
class rMaterialInfo:
    SIZE = 0x48
    
    def __init__( self ):
        self.typeHash = 0
        self.field04 = 0
        self.nameHash = 0
        self.cmdBufferSize = 0
        self.blendState = rShaderObjectId()
        self.depthStencilState = rShaderObjectId()
        self.rasterizerState = rShaderObjectId()
        self.cmdListInfo = rMaterialCmdListInfo()
        self.flags = 0
        self.field24 = 0
        self.field28 = 0
        self.field2c = 0
        self.field30 = 0
        self.animDataSize = 0
        self.cmdListOffset = 0
        self.animDataOffset = 0
        
    def read( self, stream ):
        self.typeHash = stream.readUInt()
        self.field04 = stream.readUInt()
        self.nameHash = stream.readUInt()
        self.cmdBufferSize = stream.readUInt()
        self.blendState = rShaderObjectId( stream.readUInt() )
        self.depthStencilState = rShaderObjectId( stream.readUInt() )
        self.rasterizerState = rShaderObjectId( stream.readUInt() )
        self.cmdListInfo = rMaterialCmdListInfo( stream.readUInt() )
        self.flags = stream.readUInt()
        self.field24 = stream.readUInt()
        self.field28 = stream.readUInt()
        self.field2c = stream.readUInt()
        self.field30 = stream.readUInt()
        self.animDataSize = stream.readUInt()
        self.cmdListOffset = stream.readUInt64()
        self.animDataOffset = stream.readUInt64()
    
    def write( self, stream ):
        stream.writeUInt( self.typeHash )
        stream.writeUInt( self.field04 )
        stream.writeUInt( self.nameHash )
        stream.writeUInt( self.cmdBufferSize )
        stream.writeUInt( self.blendState.getValue() )
        stream.writeUInt( self.depthStencilState.getValue() )
        stream.writeUInt( self.rasterizerState.getValue() )
        stream.writeUInt( self.cmdListInfo.getValue() )
        stream.writeUInt( self.flags )
        stream.writeUInt( self.field24 )
        stream.writeUInt( self.field28 )
        stream.writeUInt( self.field2c )
        stream.writeUInt( self.field30 )
        stream.writeUInt( self.animDataSize )
        stream.writeUInt64( self.cmdListOffset )
        stream.writeUInt64( self.animDataOffset )
    
class rMaterialHeader:
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
        stream.writeUInt64( self.magic )
        stream.writeUInt( self.materialCount )
        stream.writeUInt( self.textureCount )
        stream.writeUInt( self.hash )
        stream.writeUInt( self.field14 )
        stream.writeUInt64( self.textureOffset )
        stream.writeUInt64( self.materialOffset )
       
# data holders 
class rMaterialAnimSubEntry2Data:
    def __init__( self ):
        self.header = rMaterialAnimSubEntry2Header()
        self.entryListHeader = None
        self.entries = []
    
class rMaterialAnimEntryData:
    def __init__( self ):
        self.header = rMaterialAnimEntryHeader()
        self.entryList1 = []
        self.entryList2 = []
        
class rMaterialAnimData:
    def __init__( self ):
        self.header = rMaterialAnimHeader()
        self.entries = []
    
class rMaterialInfoData:
    def __init__( self ):
        self.info = rMaterialInfo()
        self.cmds = []
        self.animData = None
     
# writing code   
class MaterialInfoWriteContext:
    def __init__( self ):
        #start data cmds animDataHeader 
        self.start = 0
        self.data = None
        self.cmds = []
        self.animData = None
           
class rMaterialStreamWriter:
    def __init__(self, stream):
        self.stream = stream
        self.header = rMaterialHeader()
        self.headerStart = self.stream.getOffset()
        self.seek( self.headerStart + rMaterialHeader.SIZE )
        self.matInfoCtxs = []
        self.matInfoCtx = None
        
    def seek( self, pos ):
        diff = pos - self.stream.getSize()
        if diff > 0:
            self.stream.setOffset( self.stream.getSize() )
            for i in range( diff ):
                self.stream.writeByte( 0 )
        self.stream.setOffset( pos )
        
    def align( self, alignment ):
        while ( self.stream.getOffset() - self.headerStart ) % alignment != 0:
            self.stream.writeByte( 0 )
        
    def setHash( self, val ):
        self.header.hash = val
    
    def setField14( self, val ):
        self.header.field14 = val
        
    def flush( self ):
        endPos = self.stream.getOffset()
        self.stream.setOffset( self.headerStart )
        # write fixed up header
        self.header.write( self.stream )
        self.stream.setOffset( endPos )
        
    def beginTextureInfoList( self ):
        self.header.textureOffset = self.stream.getOffset() - self.headerStart
        pass
    
    def addTextureInfo( self, textureInfo ):
        textureInfo.write( self.stream )
        self.header.textureCount += 1
        pass
    
    def endTextureInfoList( self ):
        pass
    
    def beginMaterialInfoList( self ):
        self.header.materialOffset = self.stream.getOffset() - self.headerStart
        pass
    
    def beginMaterialInfo( self, materialInfo ):
        # reserve space for material info, write later
        self.matInfoCtx = MaterialInfoWriteContext()
        self.matInfoCtx.start = self.stream.getOffset()
        self.matInfoCtx.data = materialInfo
        self.seek( self.matInfoCtx.start + rMaterialInfo.SIZE )
        
        # clear procedural data
        self.matInfoCtx.data.cmdBufferSize = 0
        self.matInfoCtx.data.cmdListInfo.setCount( 0 )
        self.matInfoCtx.data.cmdListOffset = 0
        self.matInfoCtx.data.offset40 = 0
        self.matInfoCtxs.append( self.matInfoCtx )
        
    def endMaterialInfo( self ):
        self.header.materialCount += 1
        pass
        
    def addMaterialCmd( self, cmd, bufferData ):
        # commands are written after the material infos, so queue them for now
        self.matInfoCtx.cmds.append( ( cmd, bufferData ) )
        
    def beginMaterialAnimData( self, header ):
        self.matInfoCtx.animData = rMaterialAnimData()
        self.matInfoCtx.animData.header = header
        self.matInfoCtx.animData.header.entryCount = 0
        
    def endMaterialAnimData( self ):
        pass
        
    def beginMaterialAnimEntry( self, header ):
        self.matInfoCtx.animDataEntry = rMaterialAnimEntryData()
        self.matInfoCtx.animDataEntry.header = header
        
    def addMaterialAnimSubEntry1( self, entry ):
        self.matInfoCtx.animDataEntry.entryList1.append( entry )
        self.matInfoCtx.animDataEntry.header.info.setEntryCount( len( self.matInfoCtx.animDataEntry.entryList1 ) )
        
    def addMaterialAnimSubEntry2( self, header, dataHeader, dataEntries ):
        entry2 = rMaterialAnimSubEntry2Data()
        entry2.header = header
        entry2.entryListHeader = dataHeader
        entry2.entries = dataEntries
        self.matInfoCtx.animDataEntry.entryList2.append( entry2 )
        self.matInfoCtx.animDataEntry.header.info.setEntry2Count( 
            len( self.matInfoCtx.animDataEntry.entryList2 ) )
        
        
    def endMaterialAnimEntry( self ):
        self.matInfoCtx.animData.entries.append( self.matInfoCtx.animDataEntry )
        self.matInfoCtx.animData.header.entryCount += 1
        pass
    
    def _getAligned( self, val, alignment ):
        while val % alignment != 0:
            val += 1
        return val
    
    def endMaterialInfoList( self ):
        # material info list has ended
        # after this come the material commands + constant buffer data for each material

        # write command data
        self.align( 16 )
        for ctx in self.matInfoCtxs:
            # fill in command list fields
            materialCmdPos = self.stream.getOffset()
            ctx.data.cmdListOffset = materialCmdPos - self.headerStart
            ctx.data.cmdListInfo.setCount( len( ctx.cmds ) )
            
            # reserve space for cmd info
            self.seek( self.stream.getOffset() + rMaterialCmd.SIZE * len( ctx.cmds ) )
                
            # write command constant buffers so we can fix up command buffer offsets
            self.align( 16 ) 
            for cmd, cmdData in ctx.cmds:
                if cmd.info.getType() == rMaterialCmdType.SetConstantBuffer:
                    cmd.data.setConstantDataBufferOffset( self.stream.getOffset() - ctx.data.cmdListOffset )
                    assert( isinstance( cmdData, list ) )
                    assert( len( cmdData ) > 0 )
                    assert( isinstance( cmdData[0], float ) )
                    for v in cmdData:
                        self.stream.writeFloat( v )
                # the rest are stored inside the comand header
                elif cmd.info.getType() in [rMaterialCmdType.SetFlag, rMaterialCmdType.SetSamplerState]:
                    cmd.data.setShaderObjectId( cmdData )
                elif cmd.info.getType() == rMaterialCmdType.SetTexture:
                    cmd.data.setTextureIndex( cmdData )
            
            # calculate cmd buffer size     
            self.align( 16 ) 
            cmdBufferEndPos = self.stream.getOffset()
            ctx.data.cmdBufferSize = cmdBufferEndPos - materialCmdPos
            
            # write command info now that they're all fixed up
            self.seek( materialCmdPos )
            for cmd, cmdData in ctx.cmds:
                cmd.write( self.stream )
                
            # done
            self.seek( cmdBufferEndPos )
            
        # now we write the animation data
        for ctx in self.matInfoCtxs:
            if ctx.animData != None:
                # write header
                animDataHeaderPos = self.stream.getOffset()
                ctx.animData.header.write( self.stream )
                
                # write entries
                nextOffsetPos = self.stream.getOffset()
                nextDataPos = self._getAligned( nextOffsetPos + ctx.animData.header.entryCount * 8, 16 )
                
                for entry in ctx.animData.entries: 
                    # reserve space for the entry header        
                    dataPos = nextDataPos
                    self.seek( nextDataPos + rMaterialAnimEntryHeader.SIZE )
                    
                    # write sub entries
                    entryList1Pos = self.stream.getOffset()
                    for entry1 in entry.entryList1:
                        entry1.write( self.stream )
                        
                    entryList2Pos = self.stream.getOffset()
                    for entry2 in entry.entryList2:
                        entry2.header.write( self.stream )
                        self.stream.writeBytes( entry2.entryListHeader )
                        for subEntry in entry2.entries:
                            self.stream.writeBytes( subEntry )
                            
                    nextDataPos = self.stream.getOffset()
                    
                    # write entry after populating offsets
                    self.seek( dataPos )
                    entry.header.entryList1Offset = entryList1Pos - animDataHeaderPos
                    entry.header.entryList2Offset = entryList2Pos - animDataHeaderPos
                    entry.header.write( self.stream )
                    
                    # write entry offset
                    self.seek( nextOffsetPos )
                    self.stream.writeUInt64( dataPos - animDataHeaderPos )
                    nextOffsetPos = self.stream.getOffset()
                    
                ctx.data.animDataOffset = animDataHeaderPos
                ctx.data.animDataSize = nextDataPos - nextOffsetPos
                self.seek( nextDataPos )
                
                
        
        materialCmdEndPos = self.stream.getOffset()
        
        # go back and actually write the material info now that we know where
        # the data is in the file
        self.seek( self.headerStart + self.header.materialOffset )
        for ctx in self.matInfoCtxs:
            ctx.data.write( self.stream )
            
        # and that's all folks
        self.seek( materialCmdEndPos )
                
class rMaterialStreamReader:
    def __init__( self, stream ):
        self.stream = stream
        self.startPos = stream.getOffset()
        self.header = rMaterialHeader()
        self.header.read( self.stream )
        self.objectToOffset = dict()
        
    def _readStructAtOffset( self, structType, offset ):
        p = self.stream.getOffset()
        self.stream.setOffset( offset )
        value = structType()
        value.read( self.stream )
        self.stream.setOffset( p )
        return value
    
    def _iterStructArray( self, structType, offset, count ):
        nextOffset = offset
        for i in range( count ):
            self.stream.setOffset( nextOffset )
            val = structType()
            self.objectToOffset[ val ] = self.stream.getOffset()
            val.read( self.stream )
            offset = nextOffset
            nextOffset = self.stream.getOffset()
            yield val
            
    def _iterStructPtrArray( self, structType, offset, count, base ):
        ptrOffset = offset
        for i in range( count ):
            # read offset (tr)
            self.stream.setOffset( ptrOffset )
            offset = self.stream.readUInt64()
            ptrOffset = self.stream.getOffset()
            
            # read struct at offset
            self.stream.setOffset( base + offset )
            value = structType()
            self.objectToOffset[ value ] = self.stream.getOffset()
            value.read( self.stream )
            yield value
    
    def getHeader( self ):
        return self.header
    
    def getMaterialAnimHeader( self, materialInfo ):
        if materialInfo.animDataSize <= 0:
            return None
        return self._readStructAtOffset( rMaterialAnimHeader, materialInfo.animDataOffset )
    
    def iterTextureInfo( self ):
        return self._iterStructArray( rMaterialTextureInfo, self.header.textureOffset, self.header.textureCount )
            
    def iterMaterialInfo( self ):
        return self._iterStructArray( rMaterialInfo, self.header.materialOffset, self.header.materialCount )
            
    def iterMaterialCmd( self, materialInfo ):
        return self._iterStructArray( rMaterialCmd, materialInfo.cmdListOffset, materialInfo.cmdListInfo.getCount() )
            
    def iterMaterialAnimEntry( self, materialInfo, animHeader ):
        if animHeader == None: return
        return self._iterStructPtrArray( rMaterialAnimEntryHeader, 
                                        materialInfo.animDataOffset + rMaterialAnimHeader.SIZE, 
                                        animHeader.entryCount, 
                                        materialInfo.animDataOffset )
            
    def iterMaterialAnimSubEntry1( self, materialInfo, animEntry ):
        return self._iterStructArray( rMaterialAnimSubEntry1, 
                                     materialInfo.animDataOffset + animEntry.entryList1Offset, 
                                     animEntry.info.getEntryCount() )
            
    def iterMaterialAnimSubEntry2( self, materialInfo, animEntry ):
        return self._iterStructArray( rMaterialAnimSubEntry2Header, 
                                     materialInfo.animDataOffset + animEntry.entryList2Offset, 
                                     animEntry.info.getEntry2Count() )
                 
    def getMaterialAnimSubEntry2TypeHeader( self, subEntry2 ):
        offset = self.objectToOffset[ subEntry2 ]
        dataOffset = offset + rMaterialAnimSubEntry2Header.SIZE
        dataType = subEntry2.info.getType()
        headerSize = rMaterialAnimSubEntry2TypeHeaderSizes[ dataType ]
        realEntryCount = subEntry2.info.getEntryCount() + rMaterialAnimSubEntry2TypeEntryCountMod[ dataType ]
        entrySize = rMaterialAnimSubEntry2TypeEntrySizes[ dataType ]
        
        self.stream.setOffset( dataOffset )
        return self.stream.readBytes( headerSize )
        
                
    def iterMaterialAnimSubEntry2Entries( self, subEntry2 ):
        offset = self.objectToOffset[ subEntry2 ]
        dataType = subEntry2.info.getType()
        headerSize = rMaterialAnimSubEntry2TypeHeaderSizes[ dataType ]
        realEntryCount = subEntry2.info.getEntryCount() + rMaterialAnimSubEntry2TypeEntryCountMod[ dataType ]
        entrySize = rMaterialAnimSubEntry2TypeEntrySizes[ dataType ]
        
        dataOffset = offset + rMaterialAnimSubEntry2Header.SIZE + headerSize
        for i in range( realEntryCount ):
            self.stream.setOffset( dataOffset )
            entry = self.stream.readBytes( entrySize )
            dataOffset = self.stream.getOffset()
            yield entry
        
            
    '''Gets the data associated with the material command'''
    def getMaterialCmdData( self, materialInfo, materialCmd ):
        cmdType = materialCmd.info.getType()
        
        if ( cmdType == rMaterialCmdType.SetFlag ):
            return materialCmd.data.getShaderObjectId()
        elif ( cmdType == rMaterialCmdType.SetConstantBuffer ):
            temp = self.stream.getOffset()
            self.stream.setOffset( materialInfo.cmdListOffset + materialCmd.data.getConstantBufferDataOffset() )
            data = None
            shaderObjectHash = materialCmd.shaderObjectId.getHash() 
            if ( shaderObjectHash == mvc3shaderdb.CBMaterial.hash ):
                data = mtutil.readFloatBuffer( self.stream, 32 )
            elif ( shaderObjectHash == mvc3shaderdb._DOLLAR_Globals.hash ):
                data = mtutil.readFloatBuffer( self.stream, 76 )
            elif ( shaderObjectHash == mvc3shaderdb.CBDiffuseColorCorect.hash ):
                data = mtutil.readFloatBuffer( self.stream, 4 )
            elif ( shaderObjectHash == mvc3shaderdb.CBHalfLambert.hash ):
                data = mtutil.readFloatBuffer( self.stream, 4 )
            elif ( shaderObjectHash == mvc3shaderdb.CBToon2.hash ):
                data = mtutil.readFloatBuffer( self.stream, 4 )
            else:
                raise Exception( "Unhandled constant buffer: {}".format( hex( shaderObjectHash ) ) )
                
            self.stream.setOffset( temp )
            return data
        elif ( cmdType == rMaterialCmdType.SetSamplerState ):
            return materialCmd.data.getShaderObjectId()
        elif ( materialCmd.info.getType() == rMaterialCmdType.SetTexture ):
            return materialCmd.data.getTextureIndex()
        else:
            return materialCmd.data.getValue()
            
class rMaterialData:
    '''Represents all data stored in an rMaterial resource'''
    
    def __init__( self ):
        self.header = rMaterialHeader()
        self.textures = []
        self.materials = []
        
    def read( self, stream ):
        reader = rMaterialStreamReader( stream )
        self.header = reader.getHeader()
        
        for texInfo in reader.iterTextureInfo():
            self.textures.append(texInfo)
            
        for matInfo in reader.iterMaterialInfo():
            mat = rMaterialInfoData()
            mat.info = matInfo
            for matCmd in reader.iterMaterialCmd( matInfo ):
                matCmdData = reader.getMaterialCmdData( matInfo, matCmd )
                mat.cmds.append((matCmd, matCmdData))
                
            animHeader = reader.getMaterialAnimHeader( mat.info )
            if animHeader != None:
                mat.animData = rMaterialAnimData()
                mat.animData.header = animHeader
                for animEntryHeader in reader.iterMaterialAnimEntry( mat.info, animHeader ):
                    animEntryData = rMaterialAnimEntryData()
                    animEntryData.header = animEntryHeader
                    
                    for se1 in reader.iterMaterialAnimSubEntry1( mat.info, animEntryData.header ):
                        animEntryData.entryList1.append( se1 )
                    
                    for se2Header in reader.iterMaterialAnimSubEntry2( mat.info, animEntryData.header ):
                        se2 = rMaterialAnimSubEntry2Data()
                        se2.header = se2Header
                        se2.entryListHeader = reader.getMaterialAnimSubEntry2TypeHeader( se2.header )
                        #for se2entry in reader.iterMaterialAnimSubEntry2Entries( se2.header ):
                        #    se2.entries.append( se2entry )
                        animEntryData.entryList2.append( se2 )
 
                    mat.animData.entries.append( animEntryData )
                
            self.materials.append( mat )
            
    def write( self, stream ):
        writer = rMaterialStreamWriter( stream )
        writer.setHash( self.header.hash )
        writer.setField14( self.header.field14 )
        
        writer.beginTextureInfoList()
        for texInfo in self.textures:
            writer.addTextureInfo( texInfo )
        writer.endTextureInfoList()
        
        writer.beginMaterialInfoList()
        for mat in self.materials:
            writer.beginMaterialInfo( mat.info )
            for cmd, cmdData in mat.cmds:
                writer.addMaterialCmd( cmd, cmdData )
            if mat.animData != None:
                writer.beginMaterialAnimData( mat.animData.header )
                for entry in mat.animData.entries:
                    writer.beginMaterialAnimEntry( entry.header )
                    
                    for entry1 in entry.entryList1:
                        writer.addMaterialAnimSubEntry1( entry1 )
                        
                    for entry2 in entry.entryList2:
                        writer.addMaterialAnimSubEntry2( entry2.header, entry2.entryListHeader, entry2.entries )
                        
                    writer.endMaterialAnimEntry()
                writer.endMaterialAnimData()
                
            writer.endMaterialInfo()
        writer.endMaterialInfoList()
        
        writer.flush()