import os
import sys
sys.path.append( os.path.dirname( sys.path[0] ) )

from shaderinfo import *

def fixName( name ):
    shaderVarName = name
    if shaderVarName == "":
        shaderVarName = "_EMPTY_"
    shaderVarName = shaderVarName.replace("$", "_DOLLAR_")
    return shaderVarName
    
def fixHash( hash ):
    return hash & 0xFFFFF

def main():
    db = ShaderObjectInfoDb()
    db.loadCsv("X:/work/umvc3_model/resources/shaderhashes.csv", "X:/work/umvc3_model/resources/shaderinputs.csv")
    
    with open("umvc3pcshaderdb.py", "w") as f:
        f.write("# Generated file. Any changes made will be lost.\n")
        f.write("from shaderinfo import *\n")
        f.write("shaderObjects = []\n")
        f.write("shaderObjectsByName = {}\n")
        f.write("shaderObjectsByHash = {}\n")
        
        f.write("def _add( shaderObject ):\n")
        f.write("\tshaderObjects.append( shaderObject )\n")
        f.write("\tshaderObjectsByName[ shader.name ] = shader\n")
        f.write("\tshaderObjectsByHash[ shader.hash ] = shader\n")
        f.write("")
        
        for shaderInfo in db.shaders:
            inputStr = ""
            for inputInfo in shaderInfo.inputs:
                inputStr += "ShaderInputInfo( {}, {}, '{}', {} ), ".format( inputInfo.offset, inputInfo.type, inputInfo.name, inputInfo.componentCount)
            
            shaderHash = fixHash( shaderInfo.hash )
            shaderVarName = fixName( shaderInfo.name )
            
            f.write("{} = ShaderObjectInfo( {}, '{}', {}, [{}] )\n".format(shaderVarName, shaderInfo.index, shaderInfo.name, hex(shaderHash), inputStr))
        
        for shaderInfo in db.shaders:
            shaderVarName = fixName( shaderInfo.name )
            f.write("_add( {} )\n".format(shaderVarName))
            
        
        

if __name__ == "__main__":
    main() 