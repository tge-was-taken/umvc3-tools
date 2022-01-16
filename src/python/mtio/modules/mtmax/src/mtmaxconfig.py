import sys
import yaml
import os
import importlib
import mtmaxutil
import maxlog

# general
flipUpAxis = True
debug = False
showLogOnError = True

# import settings
importWeights = True
importFilePath = ''
importConvertTexturesToDDS = True
importMetadataPath = ''
importNormals = True
importGroups = True
importSkeleton = True
importPrimitives = True
importSaveMrlYml = True
importCreateLayer = True
importScale = 1
importBakeScale = True

# export settings
exportWeights = True
exportFilePath = ''
exportTexturesToTex = True
exportMetadataPath = ''
exportNormals = True
exportGroups = True
exportSkeleton = True
exportPrimitives = True
exportPjl = True
exportExistingMrlYml = False
exportRefPath = ''
exportMrlYmlPath = ''
exportUseRefJoints = True
exportUseRefPjl = True
exportUseRefBounds = True
exportUseRefGroups = True
exportGenerateMrl = True
exportRoot = ''
exportOverwriteTextures = False
exportScale = 1
exportBakeScale = True
exportGroupPerMesh = False
exportGeneratePjl = True
exportMaterialPreset = 'nDraw::MaterialChar'

# debug settings
debugForcePhysicalMaterial = False
debugImportPrimitiveIdFilter = []
debugDisableLog = False
debugExportForceShader = ''

def _getModule():
    if not __name__ in sys.modules:
        importlib.import_module(__name__)
    return sys.modules[__name__]

def _getSavePath():
    return os.path.join(mtmaxutil.getAppDataDir(), 'config.yml')

def _getVariables():
    mod = _getModule()
    variables = dict([(item, getattr(mod, item)) for item in dir(mod) if \
        not item.startswith('__') and 
        (
        isinstance(getattr(mod, item), int) or 
        isinstance(getattr(mod, item), bool) or
        isinstance(getattr(mod, item), float) or
        isinstance(getattr(mod, item), str)
        )])
    return variables

def save():
    with open(_getSavePath(), 'w') as f:
        yaml.dump(_getVariables(), f)

def load():
    if os.path.exists(_getSavePath()):
        with open(_getSavePath(), 'r') as f:
            temp = yaml.load(f, Loader=yaml.FullLoader)
            if temp != None:
                for key in temp:
                    if hasattr(_getModule(), key):
                        setattr(_getModule(), key, temp[key])
                        
    # fixup mutually exclusive options
    global exportGenerateMrl
    if exportExistingMrlYml and exportGenerateMrl:
        exportGenerateMrl = False
        
def dump():
    s = "config:\n"
    for key in _getVariables():
        val = getattr(_getModule(), key)
        s += f"{key} = {val}\n"
    maxlog.debug(s)
        

if __name__ == '__main__':
    save()
    load()

