# wrapper script to launch the plugin
import sys
import os 
import glob

_defaultModules = None

def _getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

def _isDebugEnv():
    return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )

def _getDefaultModules():
    global _defaultModules
    if _defaultModules is None:
        with open( os.path.join( os.path.dirname( __file__ ), './src/_default_modules.txt' ) ) as f:
            _defaultModules = []
            line = f.readline().strip()
            while line != '':
                _defaultModules.append(line)
                line = f.readline().strip()
    return _defaultModules

def _attachDebugger():
    try:
        import ptvsd
        print( ptvsd.enable_attach() )
    except:
        pass
    
def _deleteModule(filename):
    modules = list(sys.modules.keys())
    if filename in modules:
        print(f'bootstrapper: deleting module {filename}')
        del sys.modules[filename]

def _bootstrap():
    try:
        from pymxs import runtime as rt
        rt.clearListener()
    except:
        pass
    
    # fix import paths to allow loading modules and packages from directories above the current
    curDir = os.path.dirname( __file__ )
    rootDir = os.path.realpath( os.path.join( curDir, '../../' ) )
    modulesDir = os.path.realpath( os.path.join( rootDir, 'modules' ) )
    srcDir = os.path.realpath( os.path.join( curDir, './src' ) )
    dirs = [rootDir, modulesDir, curDir, srcDir]
    for dir in dirs:
        if not dir in sys.path: sys.path.append( dir )
            
    print(f'bootstrapper: load directories: {dirs}')

    # force reload modules by deleting any loaded instance of a module or package
    for file in glob.iglob(modulesDir + "/**/*", recursive=True):
        fileName, _ = os.path.splitext(os.path.basename(file))
        qualName = f'{os.path.basename(os.path.dirname(file))}.{fileName}'
        
        _deleteModule(fileName)
        _deleteModule(qualName)

    if _isDebugEnv():
        _attachDebugger()
        
    try:
        loadedModules = [x for x in list(sys.modules.keys()) if not x in _getDefaultModules()]
        print(f'bootstrapper: loaded modules: {loadedModules}')
    except:
        pass
    
def _installMenu():
    from pymxs import runtime as rt
    rt.MtMaxEntrypointFilePath = os.path.realpath(__file__)
    rt.fileIn( _getScriptDir() + '/src/maxscript/menu.ms' )
    
if __name__ == '__main__':
    _bootstrap()
    _installMenu()
    from src import *
    main()