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
        
class ShaderObjectId:
    SIZE = 0x04
    
    def __init__(self, value=0):
        self.value = value
        
    def getIndex(self):
        return (self.value & 0x00000FFF)
    
    def setIndex(self, index):
        self.value = (self.value & ~0x00000FFF) | (index & 0x00000FFF) 
        
    def getHash(self):
        return (self.value & 0xFFFFF000) >> 12
    
    def setHash(self, hashVal):
        self.value = (self.value & ~0xFFFFF000) | (hashVal & 0xFFFFF000) << 12
        
    def getValue(self):
        return self.value
        
    def setValue(self, value):
        self.value = value
        
    def nameEquals(self, cache, name):
        if cache != None:
            return cache.getShaderByHash(self.getHash()).name == name
        else:
            return False