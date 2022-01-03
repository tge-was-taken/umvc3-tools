import os
import sys
import subprocess
from zipfile import ZipFile
import ctypes

DEPENDENCIES = ['--upgrade pip', 'pyyaml', 'ruamel.yaml', 'numpy', 'pyglm']
MIN_SUPPORTED_VER = 2021

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def parseMaxVersion( name ):
    if name.startswith( '3ds Max ' ):
        verStr = name.replace( '3ds Max ', "" )
        ver = None
        try:
            ver = int( verStr )
        except:
            print( f'warning: unable to determine 3ds Max installation version for {dir.path}')
            return None
        
        if ver < MIN_SUPPORTED_VER:
            # no python 3 support
            print( f"notice: skipping incompatible 3ds Max installation (version: {ver}, {MIN_SUPPORTED_VER} or up required)" )
            return None
        
        return ver

def findSupportedMaxInstallDirs():
    autodeskDir = os.path.join( os.environ['ProgramFiles'], 'Autodesk' )
    installDirs = []
    for dir in os.scandir( autodeskDir ):
        if not dir.is_dir():
            continue
        
        ver = parseMaxVersion( dir.name )
        if ver != None:
            installDirs.append((dir.path, ver))
                
    return installDirs

def findPython3Dir( installDir ):
    for dir in os.scandir( installDir ):
        if dir.is_dir() and dir.name.startswith( 'Python3' ):
            return dir.path

def execPython( pythonDir, args ):
    pythonExePath = os.path.join( pythonDir, "python.exe")
    print( f'executing: {pythonExePath} {args}')
    subprocess.run( [ pythonExePath, *args.split(' ') ], stdout=sys.stdout)
    
def pipInstall( pythonDir, args ):
    execPython( pythonDir, f'-m pip install --user {args}' )
    
def selectMaxInstallDir():
    print( 'locating compatible 3ds Max installations...' )
    installDirs = findSupportedMaxInstallDirs()
    curInstallDir = ''
    curInstallVer = 0
    curPythonDir = ''
    
    if len( installDirs ) == 0:
        print( 'no supported 3ds Max installations were found (min supported version is 2021)' )
        path = input( "please enter the path to your 3ds Max installation or press enter to exit\n" )
        if path.strip() == '':
            sys.exit( 1 )
        
        ver = parseMaxVersion( os.path.basename( path ) )
        if ver == None:
            print( 'the specified installation directory does not contain a compatible 3ds Max installation' )
            sys.exit( 1 )
        
        if ver < MIN_SUPPORTED_VER:
            print( f"the specified 3ds Max installation version is not supported (version: {ver}, {MIN_SUPPORTED_VER} or up required)" )
            sys.exit( 1 )
            
        installDirs.append( (path, ver) )
        
    if len( installDirs ) > 1:
        print( 'multiple compatible 3ds Max installations were detected' )
        for installDir, ver in installDirs:
            print( f'version {ver}\t{installDir}')
        selectedVerStr = input( 'enter which version (number) to use: ' )
        selectedVer = None
        try:
            selectedVer = int( selectedVerStr )
        except:
            print( 'invalid version selected, expected a version number' )
            sys.exit( 1 )
        
        for installDir, ver in installDirs:
            if ver == selectedVer:
                curInstallDir = installDir
                curInstallVer = ver
                break
        if curInstallDir == '':
            print( f'invalid version selected: {selectedVer}'  )
            sys.exit( 1 )
    else:
        curInstallDir, curInstallVer = installDirs[0]
        
    curPythonDir = findPython3Dir( curInstallDir )
    return (curInstallDir, curInstallVer, curPythonDir)
    
def main():
    # select install dir
    installDir, installVer, pythonDir = selectMaxInstallDir()
    
    # ensure pip is installed
    pythonLibDir = os.path.join( pythonDir, 'Lib' )
    ensurePipPath = os.path.join( pythonLibDir, 'ensurepip' )
    if not os.path.exists( ensurePipPath ):
        # 3ds Max 2021 introduced this in a later update
        # so copy it to the installation directory
        if not isAdmin():
            print( 'additional files need to be copied to the installation directory, for which admin priveleges are required' )
            print( 'the script will now restart with admin priveleges' )
            input( 'press any key to continue' )
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit( 0 )
        zipFile = ZipFile( getScriptDir() + '/ensurepip.zip' )
        zipFile.extractall( pythonLibDir )
        
    
    execPython( pythonDir, '-m ensurepip --upgrade --user' )
    
    # install packages
    for package in DEPENDENCIES:
        pipInstall( pythonDir, package )
        
    print( 'setup finished successfully' )
    input( 'press any key to exit' )
    

        
if __name__ == '__main__':
    main()
        
