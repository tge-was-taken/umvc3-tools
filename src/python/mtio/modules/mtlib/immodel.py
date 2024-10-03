'''
Intermediate (im) model representation to simplify model conversion from foreign data structures
'''

from dataclasses import dataclass
from ncl import *
from rmodel import *
import vertexcodec
import modelutil
from immaterial import *
import re
from copy import copy, deepcopy
import sys

def _isValidBoundingSphere( bs ):
    '''Returns if the bounding sphere is not None or identity'''
    return bs != None and (bs[0] != 0 and bs[1] != 0 and bs[2] != 0 and bs[3] != 0)
        
class imVertexWeight:
    def __init__( self ):
        self.weights = []
        self.indices = []

class imEnvelope:
    def __init__( self, name=None, joint=None, field04=0, field08=0, field0c=0, 
        boundingSphere=None, min=None, max=None, localMtx=None, field80=None, index=sys.maxsize ):
        self.name = name
        self.joint = joint
        self.field04 = field04
        self.field08 = field08
        self.field0c = field0c
        self.boundingSphere = deepcopy(boundingSphere) if boundingSphere is not None else None
        self.min = deepcopy(min) if min is not None else None
        self.max = deepcopy(max) if max is not None else None
        self.localMtx = deepcopy(localMtx) if localMtx is not None else None
        self.field80 = deepcopy(field80) if field80 is not None else None
        self.index = index if index != None else sys.maxsize
        
class imCacheVertex:
    '''Trivially hash-able container for optimizing the vertex cache'''
    def __init__( self ):
        self.position = ()
        self.normal = ()
        self.tangent = ()
        self.uvPrimary = ()
        self.uvSecondary = ()
        self.uvUnique = ()
        self.uvExtend = ()
        self.weights = ()
        self.weightIndices = ()
        
    def __eq__(self, o: object) -> bool:
        if isinstance( o, imCacheVertex ):
            return self.position == o.position and \
                   self.normal == o.normal and \
                   self.tangent == o.tangent and \
                   self.uvPrimary == o.uvPrimary and \
                   self.uvSecondary == o.uvSecondary and \
                   self.uvUnique == o.uvUnique and \
                   self.uvExtend == o.uvExtend and \
                   self.weights == o.weights and \
                   self.weightIndices == o.weightIndices
                   
    def __hash__( self ):
        return hash((self.position, self.normal, self.tangent, self.uvPrimary, self.uvSecondary, self.uvUnique, self.uvExtend, self.weights, self.weightIndices))
    
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); fs16 Position[3];
 FSeek( p + 6 ); fs16 Weight[1];
 FSeek( p + 8 ); fs8 Normal[3];
 FSeek( p + 11 ); fs8 Occlusion[1];
 FSeek( p + 12 ); fs8 Tangent[4];
 FSeek( p + 16 ); u8 Joint[4];
 FSeek( p + 20 ); f16 TexCoord[2];
 FSeek( p + 24 ); f16 Weight_2[2];
 FSeek( p + 20 ); f16 UV_Primary[2];
 FSeek( p + 20 ); f16 UV_Secondary[2];
 FSeek( p + 20 ); f16 UV_Unique[2];
 FSeek( p + 20 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IASkinTB4wt;
'''    

class imVertex(object):
    STRIDE = None
    SHADER = None
    MAX_WEIGHT_COUNT = None
    COMPRESSED = None
    
    def __init__( self ):
        self.position = NclVec3()
        self.normal = NclVec3()
        self.tangent = NclVec4()
        self.occlusion = 0
        self.weights = [0,0,0,0]
        self.jointIds = [0,0,0,0]
        self.uvPrimary = NclVec2()
        self.uvSecondary = NclVec2()
        self.uvUnique = NclVec2()
        self.uvExtend = NclVec2()
        
    def getFlags( self ):
        raise NotImplementedError()
        
    def write( self, stream ):
        raise NotImplementedError()
        
class imVertexIASkinTB4wt(imVertex):
    STRIDE = 28
    SHADER = 'IASkinTB4wt'
    MAX_WEIGHT_COUNT = 4
    COMPRESSED = True
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod  
    def getFlags():
        return target.current.vertexFlags_IASkinTB4wt
    
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[0] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[1] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[2] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[3] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.weights[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.weights[2] ) )
        
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); fs16 Position[3];
 FSeek( p + 6 ); fs16 Weight[1];
 FSeek( p + 8 ); fu8 Normal[3];
 FSeek( p + 11 ); fu8 Occlusion[1];
 FSeek( p + 12 ); fu8 Tangent[4];
 FSeek( p + 16 ); f16 TexCoord[2];
 FSeek( p + 20 ); f16 Joint[2];
 FSeek( p + 16 ); f16 UV_Primary[2];
 FSeek( p + 16 ); f16 UV_Secondary[2];
 FSeek( p + 16 ); f16 UV_Unique[2];
 FSeek( p + 16 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IASkinTB2wt;
'''        

class imVertexIASkinTB2wt(imVertex):
    STRIDE = 24
    SHADER = 'IASkinTB2wt'
    MAX_WEIGHT_COUNT = 2
    COMPRESSED = True
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod
    def getFlags():
        return target.current.vertexFlags_IASkinTB2wt

    def write( self, stream: NclBitStream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.jointIds[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.jointIds[1] ) )
        
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); fs16 Position[3];
 FSeek( p + 6 ); u16 Joint[1];
 FSeek( p + 8 ); fu8 Normal[3];
 FSeek( p + 11 ); fu8 Occlusion[1];
 FSeek( p + 12 ); fu8 Tangent[4];
 FSeek( p + 16 ); f16 TexCoord[2];
 FSeek( p + 16 ); f16 UV_Primary[2];
 FSeek( p + 16 ); f16 UV_Secondary[2];
 FSeek( p + 16 ); f16 UV_Unique[2];
 FSeek( p + 16 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IASkinTB1wt;
'''
        
class imVertexIASkinTB1wt(imVertex):
    STRIDE = 20
    SHADER = 'IASkinTB1wt'
    MAX_WEIGHT_COUNT = 1
    COMPRESSED = True
    
    def __init__( self ):
        super().__init__()
     
    @staticmethod   
    def getFlags():
        return target.current.vertexFlags_IASkinTB1wt
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeU16( self.jointId ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
        
'''
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); f32 Position[3];
 FSeek( p + 12 ); fu8 Normal[3];
 FSeek( p + 15 ); fs8 Occlusion[1];
 FSeek( p + 16 ); fu8 Tangent[4];
 FSeek( p + 20 ); f16 TexCoord[2];
 FSeek( p + 20 ); f16 UV_Primary[2];
 FSeek( p + 20 ); f16 UV_Secondary[2];
 FSeek( p + 20 ); f16 UV_Unique[2];
 FSeek( p + 20 ); f16 UV_Extend[2];
} rVertexShaderInputLayout_IANonSkinTB;
'''
class imVertexIANonSkinTB(imVertex):
    STRIDE = 24
    SHADER = 'IANonSkinTB'
    MAX_WEIGHT_COUNT = 0
    COMPRESSED = False
    
    def __init__( self ):
        super().__init__()
    
    @staticmethod    
    def getFlags():
        return 0x01
        
    def write( self, stream ):
        stream.writeFloat( vertexcodec.encodeF32( self.position[0] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[1] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
        
'''
/* size = 24 */
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); /* 1 */ f32 Position[3];
 FSeek( p + 12 ); /* 11 */ vec432 Normal[1];
 FSeek( p + 16 ); /* 2 */ f16 TexCoord[2];
 FSeek( p + 20 ); /* 2 */ f16 TexCoord_2[2];
 FSeek( p + 16 ); /* 2 */ f16 UV_Primary[2]; /* alias of TexCoord */ 
 FSeek( p + 16 ); /* 2 */ f16 UV_Secondary[2]; /* alias of TexCoord */ 
 FSeek( p + 20 ); /* 2 */ f16 UV_Unique[2]; /* alias of TexCoord_2 */ 
 FSeek( p + 16 ); /* 2 */ f16 UV_Extend[2]; /* alias of TexCoord */ 
 FSeek( p + 24 );
} rVertexShaderInputLayout_IANonSkinBL;
'''

class imVertexIANonSkinBL(imVertex):
    STRIDE = 24
    SHADER = 'IANonSkinBL'
    MAX_WEIGHT_COUNT = 0
    COMPRESSED = False
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod    
    def getFlags():
        return 0x101
        
    def write( self, stream ):
        stream.writeFloat( vertexcodec.encodeF32( self.position[0] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[1] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[2] ) )
        stream.writeUInt( vertexcodec.encodeX8Y8Z8W8( self.normal ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvUnique[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvUnique[1] ) )
        
'''
/* size = 36 */
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); /* 1 */ f32 Position[3];
 FSeek( p + 12 ); /* 9 */ fs8 Normal[3];
 FSeek( p + 15 ); /* 10 */ fu8 Occlusion[1];
 FSeek( p + 16 ); /* 9 */ fs8 Tangent[4];
 FSeek( p + 20 ); /* 2 */ f16 TexCoord[2];
 FSeek( p + 24 ); /* 2 */ f16 TexCoord_2[2];
 FSeek( p + 28 ); /* 2 */ f16 TexCoord_3[2];
 FSeek( p + 32 ); /* 2 */ f16 TexCoord_4[2];
 FSeek( p + 20 ); /* 2 */ f16 UV_Primary[2]; /* alias of TexCoord */ 
 FSeek( p + 28 ); /* 2 */ f16 UV_Secondary[2]; /* alias of TexCoord_3 */ 
 FSeek( p + 32 ); /* 2 */ f16 UV_Unique[2]; /* alias of TexCoord_4 */ 
 FSeek( p + 24 ); /* 2 */ f16 UV_Extend[2]; /* alias of TexCoord_2 */ 
 FSeek( p + 36 );
} rVertexShaderInputLayout_IANonSkinTBNLA;
'''

class imVertexIANonSkinTBNLA(imVertex):
    STRIDE = 36
    SHADER = 'IANonSkinTBNLA'
    MAX_WEIGHT_COUNT = 0
    COMPRESSED = False
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod    
    def getFlags():
        return 0x201
        
    def write( self, stream ):
        stream.writeFloat( vertexcodec.encodeF32( self.position[0] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[1] ) )
        stream.writeFloat( vertexcodec.encodeF32( self.position[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFU8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3] ) )     
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvExtend[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvExtend[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvSecondary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvSecondary[1] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvUnique[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvUnique[1] ) )
        
'''
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeU16( self.jointId ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.normal[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.occlusion ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[0] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[1] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[2] ) )
        stream.writeUByte( vertexcodec.encodeFS8( self.tangent[3]) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[0] ) )
        stream.writeUShort( vertexcodec.encodeF16( self.uvPrimary[1] ) )
'''
        
'''
/* size = 12 */
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); /* 5 */ fs16 Position[3];
 FSeek( p + 6 ); /* 3 */ s16 Joint[1];
 FSeek( p + 8 ); /* 11 */ vec432 Normal[1];
 FSeek( p + 12 );
} rVertexShaderInputLayout_IASkinBridge1wt;
'''
class imVertexIASkinBridge1wt(imVertex):
    STRIDE = 12
    SHADER = 'IASkinBridge1wt'
    MAX_WEIGHT_COUNT = 1
    COMPRESSED = True
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod    
    def getFlags():
        return 0x09
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeShort( vertexcodec.encodeS16( self.jointIds[0] ) )
        stream.writeUInt( vertexcodec.encodeX8Y8Z8W8( self.normal ) )

'''
/* size = 16 */
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); /* 5 */ fs16 Position[3];
 FSeek( p + 6 ); /* 5 */ fs16 Weight[1];
 FSeek( p + 8 ); /* 11 */ vec432 Normal[1];
 FSeek( p + 12 ); /* 4 */ u16 Joint[2];
 FSeek( p + 16 );
} rVertexShaderInputLayout_IASkinBridge2wt;
'''
class imVertexIASkinBridge2wt(imVertex):
    STRIDE = 16
    SHADER = 'IASkinBridge2wt'
    MAX_WEIGHT_COUNT = 2
    COMPRESSED = True
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod    
    def getFlags():
        return 0x11
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.weights[0] ) )
        stream.writeUInt( vertexcodec.encodeX8Y8Z8W8( self.normal ) )
        stream.writeShort( vertexcodec.encodeS16( self.jointIds[0] ) )
        stream.writeShort( vertexcodec.encodeS16( self.jointIds[1] ) )

'''
/* size = 20 */
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); /* 5 */ fs16 Position[3];
 FSeek( p + 8 ); /* 8 */ u8 Joint[4];
 FSeek( p + 12 ); /* 10 */ fu8 Weight[4];
 FSeek( p + 16 ); /* 11 */ vec432 Normal[1];
 FSeek( p + 20 );
} rVertexShaderInputLayout_IASkinBridge4wt;
'''
class imVertexIASkinBridge4wt(imVertex):
    STRIDE = 20
    SHADER = 'IASkinBridge4wt'
    MAX_WEIGHT_COUNT = 4
    COMPRESSED = True
    
    def __init__( self ):
        super().__init__()
        
    @staticmethod    
    def getFlags():
        return 0x21
        
    def write( self, stream ):
        stream.writeUShort( vertexcodec.encodeFS16( self.position[0] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[1] ) )
        stream.writeUShort( vertexcodec.encodeFS16( self.position[2] ) )
        stream.writeUShort( 0 ) # padding
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[0] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[1] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[2] ) )
        stream.writeUByte( vertexcodec.encodeU8( self.jointIds[3] ) )
        stream.writeUByte( vertexcodec.encodeFU8( self.weights[0] ) )
        stream.writeUByte( vertexcodec.encodeFU8( self.weights[1] ) )
        stream.writeUByte( vertexcodec.encodeFU8( self.weights[2] ) )
        stream.writeUByte( vertexcodec.encodeFU8( self.weights[3] ) )
        stream.writeUInt( vertexcodec.encodeX8Y8Z8W8( self.normal ) )

'''
/* size = 28 */
typedef struct {
 local int64 p = FTell();
 FSeek( p + 0 ); /* 5 */ fs16 Position[3];
 FSeek( p + 8 ); /* 8 */ u8 Joint[8];
 FSeek( p + 16 ); /* 10 */ fu8 Weight[8];
 FSeek( p + 24 ); /* 11 */ vec432 Normal[1];
 FSeek( p + 28 );
} rVertexShaderInputLayout_IASkinBridge8wt;
'''
        
@dataclass()
class imVertexFormat(object):
    vertexType: imVertex = None
    
    def __init__( self, vertexType=None ):
        self.vertexType = vertexType
    
    @staticmethod
    def createFromShader( shader ):
        if shader == imVertexIASkinTB4wt.SHADER: return imVertexFormat( imVertexIASkinTB4wt )
        elif shader == imVertexIASkinBridge4wt.SHADER: return imVertexFormat( imVertexIASkinBridge4wt )
        elif shader == imVertexIASkinTB2wt.SHADER: return imVertexFormat( imVertexIASkinTB2wt )
        elif shader == imVertexIASkinBridge2wt.SHADER: return imVertexFormat( imVertexIASkinBridge2wt )
        elif shader == imVertexIASkinTB1wt.SHADER: return imVertexFormat( imVertexIASkinTB1wt )
        elif shader == imVertexIASkinBridge1wt.SHADER: return imVertexFormat( imVertexIASkinBridge1wt )
        elif shader == imVertexIANonSkinTB.SHADER: return imVertexFormat( imVertexIANonSkinTB )
        elif shader == imVertexIANonSkinBL.SHADER: return imVertexFormat( imVertexIANonSkinBL )
        elif shader == imVertexIANonSkinTBNLA.SHADER: return imVertexFormat( imVertexIANonSkinTBNLA )
        else: return None
        
    def fixVertexFormat( self, model, prim ):
        maxUsedBoneCount = prim.getMaxUsedBoneCount()

        if self.vertexType.MAX_WEIGHT_COUNT < maxUsedBoneCount:
            # the specified vertex format does not support sufficient weights
            # so select a more suitable one instead
            if maxUsedBoneCount > 2 and maxUsedBoneCount <= 4:
                self.vertexType = imVertexIASkinTB4wt
            elif maxUsedBoneCount == 2:
                self.vertexType = imVertexIASkinTB2wt
            else:
                self.vertexType = imVertexIASkinTB1wt
        else:
            if len( model.joints ) > 0 and not self.vertexType.COMPRESSED:
                # if the specified vertex type is uncompressed, but we're exporting a character model,
                # that's not going to work, so rectify it
                self.vertexType = imVertexIASkinTB1wt
    
    @staticmethod
    def determineBestVertexFormat( model, prim ):
        '''
        Determine the best vertex format according to the data contained in the primitive.
        '''
   
        fmt = imVertexFormat()
        maxUsedBoneCount = prim.getMaxUsedBoneCount()

        if maxUsedBoneCount > 2 and maxUsedBoneCount <= 4:
            if prim.hasUvs():      
                fmt.vertexType = imVertexIASkinTB4wt
            else:
                fmt.vertexType = imVertexIASkinBridge4wt
        elif maxUsedBoneCount == 2:
            if prim.hasUvs():
                fmt.vertexType = imVertexIASkinTB2wt
            else:
                fmt.vertexType = imVertexIASkinBridge2wt
        elif maxUsedBoneCount == 1:
            if prim.hasUvs():
                fmt.vertexType = imVertexIASkinTB1wt
            else:
                fmt.vertexType = imVertexIASkinBridge4wt
        else:
            if len( model.joints ) > 0:
                # assume that when the model has joints, it's a character model
                # that uses compressed vertices
                fmt.vertexType = imVertexIASkinTB1wt
            else:
                fmt.vertexType = imVertexIANonSkinTBNLA
             
        return fmt

class imPrimitive(object):
    '''
    Intermediate primitive data container intended to be used for generating optimized data for export
    '''
    
    def __init__( self, name, materialName, flags=0xFFFF, group=None, 
            lodIndex=0xFF, vertexFlags=None, vertexStride=None, renderFlags=67, 
            vertexShader=None, id=None, field2c=0, 
            positions=None, tangents=None, normals=None, uvPrimary=None, uvSecondary=None, uvUnique=None, uvExtend=None, weights=None, indices=None, 
            envelopes=None, index=sys.maxsize ):
        self.name = name
        self.materialName = materialName
        self.flags = flags
        self.group = group
        self.lodIndex = lodIndex
        self.renderFlags = renderFlags
        self.id = id
        self.field2c = field2c
        self.positions = positions if positions != None else []
        self.tangents = tangents if tangents != None else []
        self.normals = normals if normals != None else []
        self.uvPrimary = uvPrimary if uvPrimary != None else []
        self.uvSecondary = uvSecondary if uvSecondary != None else []
        self.uvUnique = uvUnique if uvUnique != None else []
        self.uvExtend = uvExtend if uvExtend != None else []
        self.weights = weights if weights != None else []
        self.indices = indices if indices != None else []
        self.vertexFormat = imVertexFormat( vertexShader )
        self.envelopes = envelopes if envelopes != None else []
        # use maxsize here to ensure new entries come after those who have explicit ordering
        self.index = index if index != None else sys.maxsize

    def getMaxUsedBoneCount( self ):
        '''
        Get the max. number of used bones in the primitive
        '''
        totalMaxUsedBoneCount = 0
        if self.isSkinned():
            for w in self.weights:
                usedBoneCount = 0
                for j in range( 0, len( w.weights ) ):
                    weight = w.weights[ j ]
                    if weight > 0.001:
                        usedBoneCount += 1            
                totalMaxUsedBoneCount = max( usedBoneCount, totalMaxUsedBoneCount )
        return totalMaxUsedBoneCount

    def reduceWeights( self, maxWeightsPerVertex ):
        '''
        Reduce the weights in the primitive to be less or equal to the given max weights per vertex.
        The most influential weights are kept, and the remainder is equally distributed.
        '''
        
        # pick 4 most influential weights and remove the others
        if self.isSkinned():
            for k, w in enumerate( self.weights ):
                weightIndex = []
                for k in range( 0, len(w.weights) ):
                    weightIndex.append((w.weights[k], w.indices[k]))
                weightIndex = sorted(weightIndex, key=lambda x: x[0])

                weightTotal = 0
                w.weights = []
                w.indices = []
                for k in range( 0, min(len(weightIndex), maxWeightsPerVertex) ):
                    weight, index = weightIndex[k]
                    weightTotal += weight
                    w.weights.append( weight )
                    w.indices.append( index )

                # average out the weights
                weightRemainder = 1 - weightTotal
                weightAvgStep = weightRemainder / len(w.weights)
                for k in range( 0, len(w.weights) ):
                    w.weights[k] += weightAvgStep
                    
    def updateVertexFormat( self, model ):
        if self.vertexFormat != None and self.vertexFormat.vertexType != None:
            # if we have a vertex format assigned already (eg through import),
            # fix up any inconsistencies between the data the vertex format expects
            # and what's actually in the mesh
            self.vertexFormat.fixVertexFormat( model, self )
        else:
            # determine best vertex format based on mesh specifics
            self.vertexFormat = imVertexFormat.determineBestVertexFormat( model, self )

    def isIndexed( self ):
        return self.indices is not None and len( self.indices ) > 0
    
    def isSkinned( self ):
        return self.weights is not None and len( self.weights ) > 0
    
    def hasUvs( self ):
        return self.uvPrimary is not None and len( self.uvPrimary ) > 0
    
    def makeDirect( self ):
        '''
        Removes the need for the index buffer by duplicating all the vertex data according to it.
        '''
        if not self.isIndexed():
            return
        else:
            raise NotImplementedError()
        
    def removeUnusedUvs( self, progressCb = None ):
        def _trim( progressCb, list ):
            used = False
            for i, uv in enumerate( list ):
                if progressCb is not None: progressCb( 'Trimming uvs', i, len( list ) )
                
                if uv[0] != 0 or uv[1] != 0:
                    used = True
                    break
            if not used:
                return []
            else:
                return list
            
        self.uvPrimary = _trim( progressCb, self.uvPrimary )
        self.uvSecondary = _trim( progressCb, self.uvSecondary )
        self.uvUnique = _trim( progressCb, self.uvUnique )
        self.uvExtend = _trim( progressCb, self.uvExtend )
    
    def makeIndexed( self, progressCb = None ):
        '''
        Makes the model indexed by removing all duplicate vertex data and generating an index buffer that refers to each vertex component by index.
        '''
        self.makeDirect()
        
        # copy vertex data
        positions = self.positions
        normals = self.normals
        uvPrimary = self.uvPrimary
        uvSecondary = self.uvSecondary
        uvUnique = self.uvUnique
        uvExtend = self.uvExtend
        weights = self.weights
        tangents = self.tangents
        isSkinned = self.isSkinned()
        hasUvs = self.hasUvs()
        
        # clear vertex data
        self.positions = []
        self.normals = []
        self.uvPrimary = []
        self.uvSecondary = [] 
        self.uvUnique = []
        self.uvExtend = []
        self.weights = []
        self.tangents = []
        self.indices = []
        
        # optimize vertex buffer
        vertexIdxLookup = dict()
        nextVertexIdx = 0
        for i in range( 0, len( positions ) ):
            if progressCb != None: progressCb( 'Optimizing vertices', i, len(positions) )
            
            cv = imCacheVertex()
            cv.position = (positions[i][0], positions[i][1], positions[i][2])
            cv.normal = (normals[i][0], normals[i][1], normals[i][2])
            
            if hasUvs:
                cv.uvPrimary = (uvPrimary[i][0], uvPrimary[i][1])
                cv.uvSecondary = (uvSecondary[i][0], uvSecondary[i][1]) if uvSecondary != None and len(uvSecondary) != 0 else None
                cv.uvUnique = (uvUnique[i][0], uvUnique[i][1]) if uvUnique != None and len(uvUnique) != 0 else None
                cv.uvExtend = (uvExtend[i][0], uvExtend[i][1]) if uvExtend != None and len(uvExtend) != 0 else None    
                cv.tangent = (tangents[i][0], tangents[i][1], tangents[i][2], tangents[i][3]) if tangents != None else None

            if isSkinned:
                cv.weights = tuple(weights[i].weights)
                cv.weightIndices = tuple(weights[i].indices)

            if cv not in vertexIdxLookup:
                idx = nextVertexIdx
                nextVertexIdx += 1
                vertexIdxLookup[cv] = idx

                self.positions.append( NclVec3( cv.position ) )
                self.normals.append( NclVec3( cv.normal ) )
                
                if hasUvs:
                    self.uvPrimary.append( NclVec2( cv.uvPrimary ) )        
                    if cv.uvSecondary != None: self.uvSecondary.append( NclVec2( cv.uvSecondary ) )
                    if cv.uvUnique != None: self.uvUnique.append( NclVec2( cv.uvUnique ) )
                    if cv.uvExtend != None: self.uvExtend.append( NclVec2( cv.uvExtend ) )
                    if cv.tangent != None: self.tangents.append( NclVec4( cv.tangent ) )
                
                if isSkinned:
                    vtxWeight = imVertexWeight()
                    vtxWeight.indices = cv.weightIndices
                    vtxWeight.weights = cv.weights
                    self.weights.append( vtxWeight )
            else:
                idx = vertexIdxLookup.get(cv)

            self.indices.append(idx)
           
    def generateTriStrips( self, progressCb=None ):
        # generate fake strips by creating strips containing only 1 triangle
        tempIndices = list(self.indices)
        self.indices=[]
        for i in range( 0, len( tempIndices ) ):
            if progressCb != None: progressCb( 'Generating triangle strips', i, len( tempIndices ) )
            
            if i != 0 and i % 3 == 0:
                self.indices.append( 0xFFFF )
            
            self.indices.append( tempIndices[i] )
            
    def generateTangents( self, progressCb=None ):
        tangents = [NclVec3()] * len(self.positions)
        bitangents = [NclVec3()] * len(self.positions)
        self.tangents = []
        count = len( self.indices ) if self.isIndexed() else len( self.positions )

        for i in range( 0, count, 3 ):
            if progressCb != None: progressCb( 'Calculating tangent and binormal', i, count )
            triangleA = self.indices[i] if self.isIndexed() else i
            triangleB = self.indices[i+1] if self.isIndexed() else i+1
            triangleC = self.indices[i+2] if self.isIndexed() else i+2
            positionA = self.positions[ triangleC ] - self.positions[ triangleA ]
            positionB = self.positions[ triangleB ] - self.positions[ triangleA ]

            texCoordA = self.uvPrimary[ triangleC ] - self.uvPrimary[ triangleA ]
            texCoordB = self.uvPrimary[ triangleB ] - self.uvPrimary[ triangleA ]

            direction = texCoordA[0] * texCoordB[1] - texCoordA[1] * (1.0 if texCoordB[0] > 0.0 else -1.0)
            #EDIT
            direction *= -1

            tangent = ( positionA * texCoordB[1] - positionB * texCoordA[1] ) * direction
            bitangent = ( positionB * texCoordA[0] - positionA * texCoordB[0] ) * direction

            tangents[ triangleA ] += tangent
            tangents[ triangleB ] += tangent
            tangents[ triangleC ] += tangent

            bitangents[ triangleA ] += bitangent
            bitangents[ triangleB ] += bitangent
            bitangents[ triangleC ] += bitangent
            
        for i in range( 0, len( tangents ) ):
            if progressCb != None: progressCb( 'Averaging tangents', i, len( tangents ) )
            normal = self.normals[ i ]

            tangent = nclNormalize( tangents[ i ] )
            bitangent = nclNormalize( bitangents[ i ] )

            tangent = nclNormalize( tangent - normal * nclDot( tangent, normal ) )
            bitangent = nclNormalize( bitangent - normal * nclDot( bitangent, normal ) )

            directionCheck = nclDot( nclNormalize( nclCross( normal, tangent ) ), bitangent )
            self.tangents.append( NclVec4( ( tangent[0], tangent[1], tangent[2], (1.0 if directionCheck > 0.0 else -1.0 ) ) ) )

        # Look for NaNs
        for i in range( 0, len( self.positions ) ):
            if progressCb != None: progressCb( 'Resolving NaNs', i, len( self.positions ) )
            position = self.positions[ i ]
            tangent = self.tangents[ i ]

            if not math.isnan( tangent[0] ) and not math.isnan( tangent[1] ) and not math.isnan( tangent[2] ):
                continue

            nearestVertexIndex = -1
            currentDistance = float("+inf")

            for j in range( 0, len( self.positions ) ):
                positionToCompare = self.positions[ j ]
                tangentToCompare = self.tangents[ j ]

                if i == j or math.isnan( tangentToCompare[0] ) or math.isnan( tangentToCompare[1] ) or math.isnan( tangentToCompare[2] ):
                    continue

                #distance = nclDistanceSq( position, positionToCompare );
                temp = position - positionToCompare
                distance = nclDot(temp, temp)

                if distance > currentDistance: 
                    continue

                nearestVertexIndex = j
                currentDistance = distance

            if nearestVertexIndex != -1:
                self.tangents[ i ] = self.tangents[ nearestVertexIndex ]
                
@dataclass
class imPrimitiveWorkingSet:
    current: imPrimitive
    primitives: List[imPrimitive]
        
class imJoint:
    def __init__( self, name='', id=None, localMtx=None, worldMtx=None, 
        invBindMtx=None, parent=None, symmetry=None, field03=0, 
        field04=0, offset=None, length=None, index=sys.maxsize ):

        assert localMtx is None or isinstance(localMtx, NclMat44)
        assert worldMtx is None or isinstance(worldMtx, NclMat44)
        assert invBindMtx is None or isinstance(invBindMtx, NclMat44)

        self.name = name
        self.invBindMtx = deepcopy(invBindMtx)
        self.id = 0 if id is None else id
        self.symmetry = symmetry
        self.field03 = 0 if field03 is None else field03
        self.field04 = 0 if field04 is None else field04
         # use maxsize here to ensure new entries come after those who have explicit ordering
        self.index = index if index != None else sys.maxsize

        self.localMtx = deepcopy(localMtx)
        self.worldMtx = deepcopy(worldMtx)
        self.parent = parent
        if self.localMtx is None:
            assert self.worldMtx != None
            self.updateLocalFromWorld()
        elif self.worldMtx is None:
            assert self.localMtx != None
            self.updateWorldFromLocal()

        self.offset = deepcopy(offset)
        if self.offset is None:
            self.updateOffsetFromLocal()

        self.length = length
        if self.length is None:
            self.updateLength()
        
        assert self.worldMtx != None
        assert self.localMtx != None
        assert self.id != None
        assert self.length != None
        assert self.offset != None

    def setParent( self, parent ):
        self.parent = parent
        self.worldMtx = None
        assert self.localMtx != None
        self.updateWorldFromLocal()


    def getWorldMtx( self ):
        if self.worldMtx is None:
            self.updateWorldFromLocal()
    
        return self.worldMtx

    def updateWorldFromLocal( self ):
        self.worldMtx = deepcopy(self.localMtx)
        if self.parent != None:
            self.worldMtx = self.parent.getWorldMtx() * self.worldMtx

    def updateLocalFromWorld( self ):
        # calculate local matrix if only world matrix is given
        self.localMtx = deepcopy(self.getWorldMtx())
        parentWorldMtx = nclCreateMat44()
        if self.parent != None:
            parentWorldMtx = self.parent.getWorldMtx()
            # localMtx = worldMtx * nclInverse( parentWorldMtx )
            self.localMtx = nclInverse( parentWorldMtx ) * self.localMtx
        return self.localMtx

    def updateOffsetFromLocal( self ):
        # take translation component of local matrix as offset
        self.offset = deepcopy(self.localMtx[3])

    def updateLength( self ):
        # calculate length
        self.length = nclLength( self.offset ) if not ( self.offset[0] == 0 and  self.offset[1] == 0 and  self.offset[2] == 0) else 0

class imGroup:
    def __init__( self, name, id, field04 = 0, field08 = 0, field0c = 0, boundingSphere = None, index = sys.maxsize ):
        assert id != None
        
        self.name = name
        self.id = id
        self.field04 = 0 if field04 is None else field04
        self.field08 = 0 if field08 is None else field08
        self.field0c = 0 if field0c is None else field0c
        self.boundingSphere = deepcopy(boundingSphere) if boundingSphere != None else None # can be zero, in which case it is calculated later
         # use maxsize here to ensure new entries come after those who have explicit ordering
        self.index = index if index != None else sys.maxsize
        
class imTag:
    PATTERN = re.compile(r"""@(.+?)(?!=\()\((.+?(?!=\)))\)""")
    
    def iterTags( name ):
        for tag, value in re.findall(imTag.PATTERN, name):
            yield tag, value
        
class imModel:
    '''Intermediate model data'''

    def __init__( self, primitives=None, joints=None, materials=None, groups=None,
        center=None, radius=None, min=None, max=None, 
        field90=1000, field94=3000, field98=1, field9c=0 ):
        self.primitives: List[imPrimitive] = primitives if primitives != None else []
        self.joints = joints if joints != None else []
        self.materials = materials if materials != None else []
        self.groups = groups if groups != None else []
        self.center = deepcopy(center)
        self.radius = radius
        self.min = deepcopy(min)
        self.max = deepcopy(max)
        self.field90 = field90
        self.field94 = field94
        self.field98 = field98
        self.field9c = field9c

    def getGroupById( self, id ):
        for group in self.groups:
            if group.id == id:
                return group
        return None

    def getJointById( self, id ):
        for joint in self.joints:
            if joint.id == id:
                return joint
        return None
        
    def fromBinaryModel( self, mod ):
        pass
        
    def toBinaryModel( self, progressCb=None ):
        mod = rModelData()
        
        for i in range(0, 256):
            mod.boneMap.append(-1)
            
        # create id -> index map
        # order joints by index, or at the end of not specified
        self.joints = sorted( self.joints, key=lambda x: x.index )
        if len( self.joints ) > 255:
            raise RuntimeError( f"Too many bones. (max 256, got {len(self.joints)})" )
        
        for i, joint in enumerate( self.joints ):
            mod.boneMap[ joint.id ] = i
        
        # convert joints
        for i, joint in enumerate( self.joints ): 
            if progressCb != None: progressCb( 'Converting joints', i, len( self.joints ) )
                              
            modJoint = rModelJoint()
            modJoint.id = joint.id
            modJoint.parentIndex = self.joints.index( joint.parent ) if joint.parent != None else -1
            modJoint.symmetryIndex = self.joints.index( joint.symmetry ) if joint.symmetry != None else -1 # improper index causes animation glitches
            modJoint.field03 = joint.field03
            modJoint.field04 = joint.field04
            modJoint.offset = joint.offset
            modJoint.length = joint.length
            mod.joints.append( modJoint )
            mod.jointLocalMtx.append( joint.localMtx )

            if joint.invBindMtx != None:
                # TODO: can this possibly be made to work?
                # mod.jointInvBindMtx.append( joint.invBindMtx )
                pass
            else:
                # inverse bind matrix is calculated after processing vertices because it includes the model matrix
                pass

        # convert groups
        # order groups by index, or at the end of not specified
        self.groups = sorted( self.groups, key=lambda x: x.index )
        for i, group in enumerate( self.groups ):
            if progressCb != None: progressCb( 'Converting groups', i, len( self.groups ) )
            
            modGroup = rModelGroup()
            
            if _isValidBoundingSphere(group.boundingSphere):
                modGroup.boundingSphere = group.boundingSphere
            else:
                # calc group bounds
                groupVerts = []
                for prim in self.primitives:
                    if prim.group == group:
                        groupVerts += prim.positions
                
                bounds = modelutil.calcBounds( groupVerts )
                modGroup.boundingSphere = NclVec4( bounds.center[0], bounds.center[1], bounds.center[2], bounds.radius )
            
            modGroup.field04 = group.field04
            modGroup.field08 = group.field08
            modGroup.field0c = group.field0c
            modGroup.id = group.id
            mod.groups.append( modGroup )
        
        nextVertexOffset = 0
        nextTriangleIndex = 0
        vertices = []
        indices = []
        
        # sort by index to keep order
        self.primitives = sorted( self.primitives, key=lambda x: x.index )
        for meshIndex, mesh in enumerate( self.primitives ):
            if progressCb != None: progressCb( 'Converting primitives', meshIndex, len( self.primitives ) )
            
            mesh: imPrimitive
            
            # convert envelope
            mesh.envelopes = sorted( mesh.envelopes, key=lambda x: x.index )
            for i, envelope in enumerate( mesh.envelopes ):
                modEnvelope = rModelEnvelope()
                modEnvelope.jointIndex = self.joints.index( envelope.joint ) if envelope.joint is not None else 255
                modEnvelope.field04 = envelope.field04
                modEnvelope.field08 = envelope.field08
                modEnvelope.field0c = envelope.field0c
                if _isValidBoundingSphere(envelope.boundingSphere) and envelope.min != None and envelope.max != None:
                    # copy bounds from model
                    modEnvelope.boundingSphere = envelope.boundingSphere
                    modEnvelope.min = envelope.min
                    modEnvelope.max = envelope.max
                else:
                    # calc bounds
                    bounds = modelutil.calcBounds( mesh.positions )
                    modEnvelope.boundingSphere = NclVec4( bounds.center[0], bounds.center[1], bounds.center[2], bounds.radius )
                    modEnvelope.min = NclVec4((bounds.vmin[0], bounds.vmin[1], bounds.vmin[2], 0))
                    modEnvelope.max = NclVec4((bounds.vmax[0], bounds.vmax[1], bounds.vmax[2], 0))
                    assert( modEnvelope.boundingSphere != None )

                if envelope.localMtx != None:
                    # copy it over
                    modEnvelope.localMtx = envelope.localMtx
                else:
                    # TODO find a more proper way to do this
                    # approximate it based on the primitive center
                    modEnvelope.localMtx = nclCreateMat44()
                    modEnvelope.localMtx[3] = NclVec4( modEnvelope.boundingSphere[0], modEnvelope.boundingSphere[1], modEnvelope.boundingSphere[2], 1 )
                    
                # TODO fix this hack, may end up causing culling issues
                modEnvelope.field80 = envelope.field80 if envelope.field80 != None else \
                    NclVec4((999999,999999,999999,0))
                    #NclVec4((951.5436,95.71989,33.6127,0))
                mod.envelopes.append(modEnvelope)
            
            # find material
            meshMatIndex = -1
            for matIndex, mat in enumerate( mod.materials ):
                if mat == mesh.materialName:
                    meshMatIndex = matIndex
                    break
                
            if meshMatIndex == -1:
                # add material
                meshMatIndex = len( mod.materials )
                mod.materials.append( mesh.materialName )
                
            if mesh.getMaxUsedBoneCount() > 4:
                mesh.reduceWeights( 4 )

            # determine vertex format 
            mesh.updateVertexFormat( self )
            
            # convert vertices
            for i in range(0, len(mesh.positions)):
                if progressCb != None: progressCb( 'Converting vertices', i, len( mesh.positions ) )
                
                vtx: imVertex = mesh.vertexFormat.vertexType()                
                vtx.position = mesh.positions[i]
                vtx.normal = mesh.normals[i]  
                vtx.occlusion = 1
                
                if mesh.hasUvs():
                    vtx.tangent = mesh.tangents[i]  
                    vtx.uvPrimary = mesh.uvPrimary[i]
                    
                    # assign other uv channels to primary if they're not assigned
                    vtx.uvSecondary = mesh.uvSecondary[i] if mesh.uvSecondary is not None and len(mesh.uvSecondary) > i else vtx.uvPrimary
                    vtx.uvUnique = mesh.uvUnique[i] if mesh.uvUnique is not None and len(mesh.uvUnique) > i else vtx.uvPrimary
                    vtx.uvExtend = mesh.uvExtend[i] if mesh.uvExtend is not None and len(mesh.uvExtend) > i else vtx.uvPrimary
                
                if vtx.MAX_WEIGHT_COUNT == 0:
                    pass
                elif vtx.MAX_WEIGHT_COUNT == 1:
                    # HACK assume that when the vertex has no indices but is assigned a vertex format with 1 weight, that it's an unrigged mesh
                    # for a skeleton mesh model
                    if not mesh.isSkinned() or len( mesh.weights[i].indices ) == 0:
                        jointIndex = 0
                    else:
                        jointIndex = mesh.weights[ i ].indices[ 0 ]

                    vtx.jointId = jointIndex
                else:            
                    lastJointId = 0
                    weightSum = 0
                    usedBoneCount = 0
                    for j in range( 0, vtx.MAX_WEIGHT_COUNT ):
                        if j >= len( mesh.weights[ i ].weights ):
                            # vanilla models repeat the last joint id with a weight of 0
                            vtx.jointIds[ j ] = lastJointId
                            vtx.weights[ j ] = 0
                            continue
                        
                        weight = mesh.weights[ i ].weights[ j ]
                        if weight < 0.001:
                            # remove very small weights
                            weight = 0
                        
                        jointIndex = mesh.weights[ i ].indices[ j ]
                        joint = mod.joints[ jointIndex ]
                        boneId = jointIndex
                        
                        vtx.weights[ j ] = weight
                        weightSum += weight
                        
                        vtx.jointIds[ j ] = boneId
                        lastJointId = boneId
                        
                        if weight > 0.001:
                            usedBoneCount += 1
                        
                    assert usedBoneCount > 0, 'mesh {} has unrigged vertex at index {}'.format(mesh.name, i)

                    # adjust for floating point error by averaging out the weights
                    weightError = 1 - weightSum
                    weightAvgStep = weightError / usedBoneCount
                    for j in range( usedBoneCount ):
                        vtx.weights[ j ] += weightAvgStep
                
                vertices.append( vtx )
                
            # convert indices
            for i in range(0, len( mesh.indices ) ):
                if progressCb != None: progressCb( 'Converting face indices', i, len( mesh.indices ) )
                indices.append( mesh.indices[ i ] )
                
            # create primitive
            prim = rModelPrimitive()
            prim.flags = mesh.flags # no obvious effect
            prim.vertexCount = len( mesh.positions )
            prim.indices.setGroupId( mesh.group.id if mesh.group != None else 0 )
            prim.indices.setLodIndex( mesh.lodIndex )
            prim.indices.setMaterialIndex( meshMatIndex )

            # set vertex flags based on bone count
            prim.vertexFlags = mesh.vertexFormat.vertexType.getFlags()
            prim.vertexStride = mesh.vertexFormat.vertexType.STRIDE
            prim.renderFlags = mesh.renderFlags
            prim.vertexStartIndex = 0
            prim.vertexBufferOffset = nextVertexOffset
            prim.vertexShader = mvc3shaderdb.getShaderObjectIdFromName( mesh.vertexFormat.vertexType.SHADER )
            prim.indexBufferOffset = nextTriangleIndex
            prim.indexCount = len( mesh.indices )
            prim.indexStartIndex = 0
            prim.boneIdStart = 0
            prim.envelopeCount = len(mesh.envelopes)
            prim.id = meshIndex + 1 if mesh.id is None else mesh.id # ids start with 1
            prim.minVertexIndex = 0
            prim.maxVertexIndex = prim.minVertexIndex + prim.vertexCount
            prim.field2c = 0
            prim.envelopePtr = 0
            mod.primitives.append( prim )
            
            nextVertexOffset += prim.vertexCount * prim.vertexStride
            nextTriangleIndex += prim.indexCount 
        
        bounds = modelutil.calcBounds( x.position for x in vertices )
        
        if len( self.joints ) > 0:
            # compress vertices
            
            if len(mod.jointInvBindMtx) == 0:
                # calculate distance between 2 furthest points
                # will be used as the vertex scale
                vscale = -bounds.vminpoint + bounds.vmaxpoint
                vbias = bounds.vmin * -1
                
                # set up model matrix
                modelMtx = nclCreateMat43()
                modelMtx[3] = vbias
                modelMtx *= (1/vscale)
                modelMtx = nclCreateMat44(modelMtx)
                
                # calculate joint inverse bind matrices
                for i, joint in enumerate( self.joints ):
                    if progressCb != None: progressCb( 'Calculating inverse bind matrices', i, len( self.joints ) )   
                    # apply model matrix to world transform of each joint
                    invBindMtx = nclInverse( nclMultiply( joint.getWorldMtx(), modelMtx ) )
                    finalInvBindMtx = nclCreateMat44( invBindMtx )
                    mod.jointInvBindMtx.append( finalInvBindMtx )
            else:
                # extract the model matrix from the inverse bind matrix of the root bone
                modelMtx = nclInverse( mod.jointInvBindMtx[0] )
            
            # normalize vertices
            modelMtxNormal = nclTranspose( nclInverse( modelMtx ) )
            
            for i, v in enumerate( vertices ):
                if progressCb != None: progressCb( 'Compressing vertices', i, len( vertices ) )
                v.position = nclTransform( v.position, modelMtx )
                v.normal = nclNormalize( nclTransform( v.normal, modelMtxNormal ) )
        
        # create buffers
        vertexBufferStream = NclBitStream()
        for i, v in enumerate( vertices ):
            if progressCb != None: progressCb( 'Writing vertices', i, len( vertices ) )
            start = vertexBufferStream.getOffset()
            v.write( vertexBufferStream )
            realStride = vertexBufferStream.getOffset() - start
            assert( realStride == v.STRIDE )
        mod.vertexBuffer = vertexBufferStream.getBuffer()
            
        indexBufferStream = NclBitStream()
        for i in indices:
            if progressCb != None: progressCb( 'Writing indices', i, len( indices ) )
            indexBufferStream.writeUShort( i )
        mod.indexBuffer = indexBufferStream.getBuffer()
            
        # fill out header
        mod.header.jointCount = len( mod.joints )
        mod.header.primitiveCount = len( mod.primitives )
        mod.header.materialCount = len( mod.materials )
        mod.header.vertexCount = len( vertices )
        mod.header.indexCount = len( indices )
        mod.header.polygonCount = mod.header.indexCount // 3
        mod.header.vertexBufferSize = len( mod.vertexBuffer )
        mod.header.vertexBuffer2Size = 0
        mod.header.groupCount = len( mod.groups )
        mod.header.center = bounds.center if self.center is None else self.center
        mod.header.radius = bounds.radius if self.radius is None else self.radius
        mod.header.min = nclCreateVec4( bounds.vmin ) if self.min is None else self.min
        mod.header.max = nclCreateVec4( bounds.vmax ) if self.max is None else self.max
        mod.header.field90 = self.field90
        mod.header.field94 = self.field94
        mod.header.field98 = self.field98
        mod.header.field9c = self.field9c
        mod.header.envelopeCount = len( mod.envelopes )
        return mod
        
    def saveBinaryStream( self, stream ):
        mod = self.toBinaryModel()
        mod.write( stream )