
from dataclasses import dataclass
import os
from typing import Any, Dict, Iterable, List
from immaterial import imMaterialInfo, imMaterialLib
import util
import numpy as np

@dataclass
class MaterialTemplateCommand(object):
    type: str = None
    name: str = None
    data: Any = None

@dataclass
class MaterialTemplate(object):
    baseName: str = None
    type: str = None
    blendState: str = None
    depthStencilState: str = None
    rasterizerState: str = None
    cmdListFlags: int = None
    matFlags: int = None
    cmds: List[MaterialTemplateCommand] = None
    
    def __post_init__( self ):
        self.cmds = [] if self.cmds is None else self.cmds

def generateIndex():
    with open(util.getLibDir() + '\\mvc3materialtemplatedb_generated.py', 'w') as f:
        f.write("templates = [\n")
        for root, dirs, files in os.walk( util.getResourceDir() + '\\material_templates' ):
            for file in files:
                lib = imMaterialLib()
                lib.loadYamlFile( os.path.join( root, file ) )
                mat = lib.materials[0]
                
                f.write( ' MaterialTemplate(\n')
                f.write(f'  baseName="{os.path.basename( file )}",\n')
                f.write(f'  type="{mat.type}",\n')
                f.write(f'  blendState="{mat.blendState}",\n')
                f.write(f'  depthStencilState="{mat.depthStencilState}",\n')
                f.write(f'  rasterizerState="{mat.rasterizerState}",\n')
                f.write(f'  cmdListFlags={hex(mat.cmdListFlags)},\n')
                f.write(f'  matFlags={hex(mat.matFlags)},\n')
                f.write(f'  cmds=[\n')
                for cmd in mat.cmds:
                    data = f'"{cmd.data}"' if isinstance(cmd.data, str) else str(cmd.data)
                    f.write(f'   MaterialTemplateCommand("{cmd.type}", "{cmd.name}", {data}),\n')
                f.write(f'  ]\n')
                f.write(' ),\n')         
        f.write(']\n')
        
# def generateIndexNumpy():
    
#     allFiles = []
#     for root, dirs, files in os.walk( util.getResourceDir() + '\\material_templates' ):
#         allFiles += [os.path.join( root, x ) for x in files]
    
    
#     arr = np.empty((len(allFiles)), dtype=str)
#     for i, file in enumerate( allFiles ):
#         lib = imMaterialLib()
#         lib.loadYamlFile( file )
#         mat = lib.materials[0]
        
#         arr2 = np.empty(8, dtype=str)
#         j = 0
#         arr2[j+0] = os.path.basename(file)
#         arr2[j+1] = mat.type
#         arr2[j+2] = mat.blendState
#         arr2[j+3] = mat.depthStencilState
#         arr2[j+4] = mat.rasterizerState
#         arr2[j+5] = mat.cmdListFlags
#         arr2[j+6] = mat.matFlags
#         #arr2[j+7] = mat.cmds    
#         arr[i] = arr2
        
    

def query( filter: MaterialTemplate ) -> Iterable[imMaterialInfo]:
    try:
        from mvc3materialtemplatedb_generated import templates
    except Exception as e:
        pass
    
    for template in templates:
        mat = template
        if filter.baseName is not None and os.path.basename(file) != filter.baseName: continue
        if filter.type is not None and mat.type != filter.type: continue 
        if filter.blendState is not None and mat.blendState != filter.blendState: continue
        if filter.depthStencilState is not None and mat.depthStencilState != filter.depthStencilState: continue
        if filter.rasterizerState is not None and mat.rasterizerState != filter.rasterizerState: continue
        if filter.cmdListFlags is not None and mat.cmdListFlags != filter.cmdListFlags: continue
        if filter.matFlags is not None and mat.matFlags != filter.blendState: continue
        
        
        matchedAllCommandFilters = True
        matchedAny = False
        for cmdFilter in filter.cmds:
            match = False
            
            for cmd in mat.cmds:
                if cmdFilter.type is not None:
                    # if filtering on type...
                    if cmd.type == cmdFilter.type:
                        if cmdFilter.name is not None:
                            # if filtering on name....
                            if cmd.name == cmdFilter.name:
                                if cmdFilter.data is not None:
                                    # if filtering on data..
                                    match = cmd.data == cmdFilter.data
                                else:
                                    # not filtering on data, so accept the previous match
                                    match = True
                            else:
                                # command does not match filter
                                match = False
                        else:
                            # not filtering on name, so accept the previous match
                            match = True
                    else:  
                        # command does not match filter
                        match = False
                        
                if match:
                    matchedAny = True
                    break
               
            matchedAllCommandFilters = matchedAllCommandFilters and match   
              
        if matchedAllCommandFilters and matchedAny:
            yield mat
                
if __name__ == '__main__':
    #generateIndex()
    #generateIndexNumpy()
    results = list(query(MaterialTemplate(
        cmds = [
            MaterialTemplateCommand(
                type='texture',
                name='tLightingMap')
        ]
    )))
    print(results)
            
            
             