''' 
Joint info/metadata classes.
Used for retrieving additional info about model joints like names.
'''

import mtutil

class JointInfo:
    def __init__( self, jointId, jointName, opposite ):
        self.id = jointId
        self.name = jointName
        self.opposite = opposite

class JointInfoDb:
    DEFAULT_NAME_PREFIX = "jnt_"
    LEFT_SUFFIX = "_l"
    RIGHT_SUFFIX = "_r"
    
    def __init__( self ):
        self.joints = []
        self.lookupById = {}
        self.lookupByName = {}
     
    @staticmethod   
    def getDefaultCsvPath( name ):
        '''Gets the default CSV path for the given name'''
        return mtutil.getResourceDir() + '/jointinfo/' + name + '.csv'
        
    def loadCsvFromFile( self, path ):
        '''Loads a joint info CSV from the given file path'''
        
        self.joints = []
        self.lookupById = {}
        self.lookupByName = {}
        
        jointSymmetryIds = []
        with open( path ) as f:       
            line = f.readline()  # header
            line = f.readline().rstrip()
            while line != "":
                # skip commented lines
                if line[0] == '#' or line[0] == '/':
                    line = f.readline().rstrip()
                    continue
                
                # parse columns
                cols = line.split( '\t' )
                jointId = int( cols[0] )
                jointName = cols[1]
                jointSymmetryId = int( cols[2] ) if len( cols ) > 2 else None
                
                # validate data
                jointInfo = JointInfo( jointId, jointName, None )
                if jointInfo.id in self.lookupById: raise Exception( "Duplicate id in joint info csv {}: {}".format( path, str(jointInfo.id) ) )
                if jointInfo.name in self.lookupByName: raise Exception( "Duplicate name in joint info csv {}: {}".format( path, jointInfo.name ) )
                
                # populate lookups
                self.joints.append( jointInfo )
                self.lookupById[ jointId ] = jointInfo
                self.lookupByName[ jointName ] = jointInfo
                jointSymmetryIds.append( jointSymmetryId )
                
                line = f.readline().rstrip()
                
        self._determineOpposites( jointSymmetryIds )
                                
    def _determineOpposites( self, jointSymmetryIds ):
        for i, jointInfo in enumerate( self.joints ):
            if jointSymmetryIds[i] != None:
                # opposite was specified in csv by id
                jointInfo.opposite = self.getJointInfoById( jointSymmetryIds[i] )
            else: 
                # opposite was not specified in the csv    
                # find opposite from the name format
                if jointInfo.name.endswith( self.LEFT_SUFFIX ):
                    jointInfo.opposite = self.getJointInfoByName( mtutil.replaceSuffix( jointInfo.name, self.LEFT_SUFFIX, self.RIGHT_SUFFIX ) )
                elif jointInfo.name.endswith( self.RIGHT_SUFFIX ):
                    jointInfo.opposite = self.getJointInfoByName( mtutil.replaceSuffix( jointInfo.name, self.RIGHT_SUFFIX, self.LEFT_SUFFIX ) )       
        
    def getJointInfoById( self, jointId ):
        if not jointId in self.lookupById:
            return None
        else:
            return self.lookupById[ jointId ]
        
    def getJointInfoByName( self, jointName ):
        if not jointName in self.lookupByName:
            if jointName.startswith( self.DEFAULT_NAME_PREFIX ):
                jointId = int(jointName[len( self.DEFAULT_NAME_PREFIX ):])
                return self.getJointInfoById( jointId )
            else:
                return None
        else:
            return self.lookupByName[ jointName ]
      
    @staticmethod  
    def getDefaultJointName( jointId ):
        return JointInfoDb.DEFAULT_NAME_PREFIX + str( jointId )