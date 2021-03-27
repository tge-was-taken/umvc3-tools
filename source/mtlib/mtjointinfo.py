import mtutil

class JointInfo:
    def __init__( self, jointId, jointName, opposite ):
        self.id = jointId
        self.name = jointName
        self.opposite = opposite

class JointInfoDb:
    DEFAULT_NAME_PREFIX = "joint_"
    LEFT_SUFFIX = "_l"
    RIGHT_SUFFIX = "_r"
    
    def __init__( self ):
        self.joints = []
        self.lookupById = {}
        self.lookupByName = {}
        
    def loadCsv( self, path ):
        self.joints = []
        self.lookupById = {}
        self.lookupByName = {}
        
        with open( path ) as f:       
            line = f.readline()  # header
            line = f.readline().rstrip()
            while line != "":
                # skip commented lines
                if line[0] == '#' or line[0] == '/':
                    line = f.readline().rstrip()
                    continue
                
                cols = line.split( ',' )
                jointId = int( cols[0] )
                jointName = cols[1]
                jointInfo = JointInfo( jointId, jointName, None )
                if jointInfo.id in self.lookupById: raise Exception( "Duplicate id in joint info csv: " + str(jointInfo.id) )
                if jointInfo.name in self.lookupByName: raise Exception( "Duplicate name in joint info csv: " + str( jointInfo.name ) )
                
                self.joints.append( jointInfo )
                self.lookupById[ jointId ] = jointInfo
                self.lookupByName[ jointName ] = jointInfo
                line = f.readline().rstrip()
        self._determineOpposites()
                
    def getDefaultJointName( self, jointId ):
        return self.DEFAULT_NAME_PREFIX + str( jointId )
                
    def _determineOpposites( self ):
        for jointInfo in self.joints:
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