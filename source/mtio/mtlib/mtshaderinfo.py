
class ShaderInputInfo:
    '''Describes a shader input variable'''
    def __init__(self, off, typeVal, name, componentCount):
        self.offset = off
        self.type = typeVal
        self.name = name
        self.componentCount = componentCount

class ShaderObjectInfo:
    '''Describes a shader object'''
    def __init__(self, index, name, hashValue, inputs=[]):
        self.index = index
        self.name = name
        self.hash = hashValue
        self.inputs = []
        self.inputsByName = {}
        if len(inputs) > 0:
            for inputInfo in inputs:
                self.addInput( inputInfo )
        
    def addInput( self, inputInfo ):
        self.inputs.append( inputInfo )
        if not self.hasInput( inputInfo.name ):
            self.inputsByName[ inputInfo.name ] = [ inputInfo ]
        else:
            self.inputsByName[ inputInfo.name ].append( inputInfo )
        
    def getInput( self, name ):
        return self.inputsByName[ name ]
    
    def hasInput( self, name ):
        return name in self.inputsByName
    
class ShaderObjectInfoDb:
    '''Represents a database containing info about all shader object used in the game''' 
    def __init__( self ):
        self.shaders = []
        self.shaderByHash = {}
        self.shaderByName = {}
        
    def loadCsv( self, shaderHashesPath, shaderInputsPath ):
        # read shader hash -> name mapping
        with open(shaderHashesPath) as f:
            f.readline() # header
            line = f.readline()
            while line != "":
                tokens = line.split(",")
                idx = int(tokens[0])
                name = tokens[1]
                hashVal = int(tokens[2], 16) if name != "" else 0
                entry = ShaderObjectInfo(idx, name, hashVal)
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
                shader = self.getShaderObjectInfoByName(shaderName)
                shader.addInput( ShaderInputInfo( inputOffset, inputType, inputName, inputCmpCount ) )
                line = f.readline()
                
    def addShaderObjectInfo( self, info ):
        self.shaders.append(info)
        self.shaderByHash[info.hash] = info 
        self.shaderByName[info.name] = info
                
    def getShaderObjectInfoByHash(self, hashVal):
        return self.shaderByHash[hashVal]
    
    def getShaderObjectInfoByName(self, name):
        return self.shaderByName[name]