''' 
Joint info/metadata classes.
Used for retrieving additional info about model joints like names.
'''
import os
from mtrmodel import *
import mtutil
from mtncl import *
import yaml
import ruamel.yaml

def setYamlFlowStyle(x):
    retval = ruamel.yaml.comments.CommentedSeq(x)
    retval.fa.set_flow_style()  # fa -> format attribute
    return retval

class JointMetadata:
    DEFAULT_NAME_PREFIX = "jnt_"
    LEFT_SUFFIX = "_l"
    RIGHT_SUFFIX = "_r"
    
    def __init__( self ):
        self.id = int()
        self.name = str()
        self.parent = None 
        self.symmetry = None 
        self.field03 = int()
        self.field04 = float()
        self.length = float()
        self.offset = NclVec3()
        
    @staticmethod
    def getDefaultName( id ):
        return JointMetadata.DEFAULT_NAME_PREFIX + str( id )
    
    @staticmethod
    def isDefaultName( name ):
        return name.startswith( JointMetadata.DEFAULT_NAME_PREFIX )
    
    @staticmethod
    def getIdFromName( name ):
        return int(name[len( JointMetadata.DEFAULT_NAME_PREFIX ):])
        
class GroupMetadata:
    DEFAULT_NAME_PREFIX = 'grp_'
    
    def __init__( self ):
        self.id = int()
        self.name = str()
        self.field04 = int()
        self.field08 = int()
        self.field0c = int()
        self.boundingSphere = NclVec4()
        
    @staticmethod
    def getDefaultName( id ):
        return GroupMetadata.DEFAULT_NAME_PREFIX + str( id )
    
    @staticmethod
    def isDefaultName( name ):
        return name.startswith( GroupMetadata.DEFAULT_NAME_PREFIX )
    
    @staticmethod
    def getIdFromName( name ):
        return int(name[len( GroupMetadata.DEFAULT_NAME_PREFIX ):])
        
class PrimitiveJointLinkMetadata:
    def __init__( self ):
        self.jointId = int()
        self.field04 = int()
        self.field08 = int()
        self.field0c = int()
        self.boundingSphere = NclVec4()
        self.min = NclVec4()
        self.max = NclVec4()
        self.localMtx = NclMat44()
        self.field80 = NclVec4()
        
class PrimitiveMetadata:
    DEFAULT_NAME_PREFIX = 'prm_'
    
    def __init__( self ):
        self.id = int()
        self.name = str()
        self.links = []
        
    @staticmethod
    def getDefaultName( id ):
        return PrimitiveMetadata.DEFAULT_NAME_PREFIX + str( id )
    
    @staticmethod
    def isDefaultName( name ):
        return name.startswith( PrimitiveMetadata.DEFAULT_NAME_PREFIX )
    
    @staticmethod
    def getIdFromName( name ):
        return int(name[len( PrimitiveMetadata.DEFAULT_NAME_PREFIX ):])

class ModelMetadata:
    CURRENT_VERSION = 1
    
    def __init__( self ):
        self.version = ModelMetadata.CURRENT_VERSION
        self.name = ''
        self.joints = []
        self.groups = []
        self.primitives = []
        self.primitiveJointLinks = []
        self.jointLookupById = dict()
        self.jointLookupByName = dict()
        self.groupLookupById = dict()
        self.groupLookupByName = dict()
        self.primLookupById = dict()
        self.primLookupByName = dict()
        
    @staticmethod   
    def getDefaultFilePath( name ):
        '''Gets the default YML path for the given name'''
        return mtutil.getResourceDir() + '/metadata/' + name + '.yml'
    
    @staticmethod
    def _copyValuesExcept( obj, yObj, excluded ):
        for key in yObj:
            if key not in excluded:
                setattr( obj, key, yObj[ key ] )
    @staticmethod              
    def _copyAttributesExcept( obj, yObj, excluded ):
        for key in obj.__dict__:
            if key not in excluded:
                yObj[key] = getattr( obj, key )
    
    @staticmethod            
    def _iterComplexMappings( obj ):
        if len( obj ) == 0:
            return
        
        header = list(obj.keys())[0]
        keys = [x.strip() for x in header.split(',')]
        for values in obj[header]:
            yield dict( zip( keys,values ) )
            
    @staticmethod
    def _createComplexMapping( objs ):
        if len( objs ) == 0:
            return dict()
        
        keys = list( objs[0].keys() )
        header = keys[0]
        for i in range( 1, len( keys ) ):
            header += ', ' + keys[i]
            
        values = list()
        for obj in objs:
            values.append( setYamlFlowStyle( list( obj.values() ) ) )
            
        result = dict()
        result[header] = values
        return result
            
    def _determineJointOpposites( self, jointSymmetryIds ):
        for i, jointMeta in enumerate( self.joints ):
            if jointSymmetryIds[i] not in [None, '', -1]:
                # opposite was specified in csv by id
                jointMeta.symmetry = self.getJointById( jointSymmetryIds[i] )
            else: 
                # opposite was not specified in the csv    
                # find opposite from the name format
                if jointMeta.name.endswith( self.LEFT_SUFFIX ):
                    jointMeta.symmetry = self.getJointByName( mtutil.replaceSuffix( jointMeta.name, self.LEFT_SUFFIX, self.RIGHT_SUFFIX ) )
                elif jointMeta.name.endswith( self.RIGHT_SUFFIX ):
                    jointMeta.symmetry = self.getJointByName( mtutil.replaceSuffix( jointMeta.name, self.RIGHT_SUFFIX, self.LEFT_SUFFIX ) ) 
                else:
                    jointMeta.symmetry = None 
                    
    def _getObjectById( self, lookup, id ):
        if not id in lookup:
            return None
        else:
            return lookup[ id ]
        
    def _getObjectByName( self, type, lookupName, lookupId, name ):
        if not name in lookupName:
            if type.isDefaultName( name ):
                id = type.getIdFromName( name )
                if id in lookupId:
                    return lookupId[ id ]
                else:
                    return None
            else:
                return None
        else:
            return lookupName[ name ]
        
    def _getObjectName( self, type, lookupId, id ):
        if not id in lookupId:
            return type.getDefaultName( id )
        else:
            return lookupId[ id ].name
        
    def _sort( self ):
        self.joints = list( sorted( self.joints, key=lambda x: x.id ) )
        self.groups = list( sorted( self.groups, key=lambda x: x.id ) )
        self.primitives = list( sorted( self.primitives, key=lambda x: x.id ) )
        
    @staticmethod
    def generateInitialMetadata( path ):
        refMetadata = ModelMetadata()
        refMetadata.loadFile( ModelMetadata.getDefaultFilePath( '_ref' ) )
        
        with os.scandir( path ) as it:
            for entry in it:
                if entry.name.endswith(".mod") and entry.is_file():
                    basePath, baseName, exts = mtutil.splitPath( entry.name )
                    modBuffer = mtutil.loadIntoByteArray( entry.path )
                    mod = rModelData()
                    mod.read( NclBitStream( modBuffer ) )
                    
                    metadata = ModelMetadata()
                    metadata.initFromBinary( baseName, mod, refMetadata )
                    metadata.saveFile( ModelMetadata.getDefaultFilePath( baseName ) )
        
    def initFromBinary( self, name, modelData, refMetadata ):
        self.name = name
        
        # create id mappings for lookups
        for mJoint in modelData.joints:
            if not mJoint.id in self.jointLookupById:
                self.jointLookupById[mJoint.id] = JointMetadata()
                
        for mGroup in modelData.groups:
            if not mGroup.id in self.groupLookupById:
                self.groupLookupById[mGroup.id] = GroupMetadata()
                
        for mPrim in modelData.primitives:
            if not mPrim.id in self.primLookupById:
                self.primLookupById[mPrim.id] = PrimitiveMetadata()
        
        # create joint metadata
        for mJoint in modelData.joints:
            joint = self.jointLookupById[mJoint.id]
            joint.id = mJoint.id
            isDefaultName = False
            if joint.name in [None, '']:
                joint.name = JointMetadata.getDefaultName( joint.id )
                isDefaultName = True
            joint.parent = None
            if mJoint.parentIndex != 255:
                joint.parent = self.getJointById( modelData.joints[ mJoint.parentIndex].id )
            joint.symmetry = None
            if mJoint.symmetryIndex != 255:
                joint.symmetry = self.getJointById( modelData.joints[ mJoint.symmetryIndex ].id )
            joint.field03 = mJoint.field03
            joint.field04 = mJoint.field04
            joint.length = mJoint.length
            joint.offset = mJoint.offset
            
            if isDefaultName and refMetadata != None:
                refJoint = refMetadata.getJointById( joint.id )
                
                # try to look for a suitable name in the reference joint db
                # not perfect, but a close approximation in a lot of cases
                if refJoint != None:
                    joint.name = refJoint.name
            
            self.joints.append( joint )
            self.jointLookupByName[ joint.name ] = joint
         
        # create group metadata   
        for mGroup in modelData.groups:
            group = GroupMetadata()
            group.id = mGroup.id
            isDefaultName = False
            if group.name in [None, '']:
                group.name = GroupMetadata.getDefaultName( group.id )
                isDefaultName = True
            group.field04 = mGroup.field04 
            group.field08 = mGroup.field08
            group.field0c = mGroup.field0c
            group.boundingSphere = mGroup.boundingSphere
            
            if isDefaultName and refMetadata != None and \
                ( group.id >= 70 or refMetadata.name == self.name ):
                refGroup = refMetadata.getGroupById( group.id )
                if refGroup != None:
                    group.name = refGroup.name
            
            self.groups.append( group )
            self.groupLookupById[ group.id ] = group.id
            self.groupLookupByName[ group.name ] = group.name
        
        # create primitive metadata
        primJointLinkIndex = 0
        for mPrim in modelData.primitives:
            prim = PrimitiveMetadata()
            prim.id = mPrim.id
            isDefaultName = False
            if prim.name in [None, '']:
                prim.name = PrimitiveMetadata.getDefaultName( prim.id )
                isDefaultName = True
            
            prim.links = []
            if isDefaultName and refMetadata != None and refMetadata.name == self.name:
                refPrim = refMetadata.getPrimitiveById( prim.id )
                if refPrim != None:
                    prim.name = refPrim.name
            
            self.primitives.append( prim )
            self.primLookupById[ prim.id ] = prim
            self.primLookupByName[ prim.name ] = prim
            primJointLinkIndex += mPrim.primitiveJointLinkCount
            
        self._sort()
        
    def loadFile( self, path ):
        yamlText = ''
        with open( path, 'r' ) as f:
            yamlText = f.read()
        
        yamlObj = yaml.safe_load( yamlText )
        if yamlObj['version'] > ModelMetadata.CURRENT_VERSION:
            raise Exception('Unsupported model metadata version')
        
        self.name = yamlObj['name']
        
        # populate id lookups first for resolving later
        for yJoint in self._iterComplexMappings( yamlObj['joints'] ):
            joint = JointMetadata()
            self.jointLookupById[yJoint['id']] = joint
        
        # populate values
        for yJoint in self._iterComplexMappings( yamlObj['joints'] ):
            joint = self.jointLookupById[yJoint['id']]
            self._copyValuesExcept( joint, yJoint, ['parentId', 'symmetryId', 'offset'] )
            joint.parent = self.getJointById( yJoint['parentId'] )
            joint.symmetry = self.getJointById( yJoint['symmetryId'] )
            joint.offset = NclVec3(yJoint['offset'])
            self.jointLookupByName[joint.name] = joint
            self.joints.append( joint )
        
        for yGroup in self._iterComplexMappings( yamlObj['groups'] ):
            group = GroupMetadata()
            self._copyValuesExcept( group, yGroup, ['boundingSphere'])
            group.boundingSphere = NclVec4( yGroup['boundingSphere'] )
            self.groupLookupById[group.id] = group
            self.groupLookupByName[group.name] = group
            self.groups.append( group )
        
        for yPrim in self._iterComplexMappings( yamlObj['primitives'] ):
            prim = PrimitiveMetadata()
            self._copyValuesExcept( prim, yPrim, [])  
            self.primLookupById[ prim.id ] = prim
            self.primLookupByName[ prim.name ] = prim 
            self.primitives.append( prim ) 
    
    def saveFile( self, path ):
        # turn classes into dicts
        joints = []
        for joint in self.joints:
            yJoint = dict()
            self._copyAttributesExcept( joint, yJoint, ['parent', 'symmetry', 'offset'] )
            yJoint['parentId'] = joint.parent.id if joint.parent != None else -1
            yJoint['symmetryId'] = joint.symmetry.id if joint.symmetry != None else -1
            yJoint['offset'] = joint.offset.toList()
            joints.append( yJoint )
            
        groups = []
        for group in self.groups:
            yGroup = dict()
            self._copyAttributesExcept( group, yGroup, 'boundingSphere' )
            yGroup['boundingSphere'] = group.boundingSphere.toList()
            groups.append( yGroup )
            
        primitives = []
        for prim in self.primitives:
            yPrim = dict()
            self._copyAttributesExcept( prim, yPrim, [] )
            primitives.append( yPrim )
        
        with open( path, 'w' ) as f:
            yamlObj = dict()
            yamlObj['version'] = self.CURRENT_VERSION
            yamlObj['name'] = self.name
            yamlObj['joints'] = self._createComplexMapping( joints )
            yamlObj['groups'] = self._createComplexMapping( groups )
            yamlObj['primitives'] = self._createComplexMapping( primitives )
            yaml = ruamel.yaml.YAML()
            yaml.width = 1024
            yaml.dump( yamlObj, f )
        
    def getJointById( self, jointId ):
        return self._getObjectById( self.jointLookupById, jointId )
        
    def getJointByName( self, jointName ):
        return self._getObjectByName( JointMetadata, self.jointLookupByName, self.jointLookupById, jointName )
       
    def getJointName( self, id ):
        return self._getObjectName( JointMetadata, self.jointLookupById, id )
        
    def getGroupById( self, groupId ):
        return self._getObjectById( self.groupLookupById, groupId )
        
    def getGroupByName( self, groupName ):
        return self._getObjectByName( GroupMetadata, self.groupLookupByName, self.groupLookupById, groupName )
        
    def getGroupName( self, id ):
        return self._getObjectName( GroupMetadata, self.groupLookupById, id )
        
    def getPrimitiveById( self, primitiveId ):
        return self._getObjectById( self.primLookupById, primitiveId )
        
    def getPrimitiveByName( self, primitiveName ):
        return self._getObjectByName( PrimitiveMetadata, self.primLookupByName, self.primLookupById, primitiveName )
    
    def getPrimitiveName( self, id ):
        return self._getObjectName( PrimitiveMetadata, self.primLookupById, id )
    
if __name__ == '__main__':
    m = ModelMetadata()
    m.loadFile( ModelMetadata.getDefaultFilePath('_ref') )
    j = m.getJointByName('pelvis')
    j2 = m.getJointById(2)
    assert( j.id == j2.id )
    g = m.getGroupByName('grp_body')
    g2 = m.getGroupById( 3 )
    assert( g.id == g2.id )
    p = m.getPrimitiveByName( 'prm_headband' )
    p2 = m.getPrimitiveById( 3 )
    assert( p.id == p2.id )
    
    m.saveFile( ModelMetadata.getDefaultFilePath('test') )
    
    ModelMetadata.generateInitialMetadata('X:\\work\\umvc3_model\\samples\\test')
    
    pass
    