'''
Binary shader serialization module.
'''

class rShaderObjectId:
    SIZE = 0x04
    
    def __init__(self, value=0):
        self.value = value
        
    def getIndex(self):
        return (self.value & 0x00000FFF)
    
    def setIndex(self, index):
        self.value = ((self.value & ~0x00000FFF) | (index & 0x00000FFF)) & 0xFFFFFFFF
        
    def getHash(self):
        return (self.value & 0xFFFFF000) >> 12
    
    def setHash(self, hashVal):
        self.value = ((self.value & ~0xFFFFF000) | (hashVal & 0xFFFFF) << 12) & 0xFFFFFFFF
        
    def getValue(self):
        return self.value
        
    def setValue(self, value):
        self.value = value
        
    def nameEquals(self, cache, name):
        if cache != None:
            return cache.getShaderByHash(self.getHash()).name == name
        else:
            return False