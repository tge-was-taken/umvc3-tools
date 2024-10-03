import os
import sys
import subprocess
from zipfile import ZipFile
import ctypes

DEPENDENCIES = ['pyyaml', 'ruamel.yaml', 'numpy', 'pyglm', 'ptvsd', 'Pillow']
MIN_SUPPORTED_VER = (3,4)

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

def isAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def parseBlenderVersion( name ):
    def parseVersionString( verStr ):
        ver = None
        try:
            verParts =  verStr.split('.')
            ver = (int( verParts[0] ), int( verParts[1] ))
        except:
            print( f'warning: unable to determine Blender installation version for {name}')
            return None
        
        if ver[0] < MIN_SUPPORTED_VER[0] or ver[1] < MIN_SUPPORTED_VER[1]:
            # no python 3 support
            print( f"notice: skipping incompatible Blender installation (version: {ver}, {MIN_SUPPORTED_VER} or up required)" )
            return None

        return ver

    if name.startswith( 'Blender ' ):
        verStr = name.replace( 'Blender ', "" ).strip()
        return parseVersionString( verStr )
    elif name.startswith( 'blender-' ):
        verStr = name.split('-')[1]
        return parseVersionString( verStr )

def findSupportedBlenderInstallDirs():
    blenderFoundationDir = os.path.join( os.environ['ProgramFiles'], 'Blender Foundation' )
    installDirs = []
    for dir in os.scandir( blenderFoundationDir ):
        if not dir.is_dir():
            continue
        
        ver = parseBlenderVersion( dir.name )
        if ver != None:
            installDirs.append((dir.path, ver))
                
    return installDirs

def findPython3Dir( installDir, installVer ):
    return installDir + '/' + str(installVer[0]) + '.' + str(installVer[1]) + '/python' 

def execPython( pythonDir, args ):
    pythonExePath = pythonDir + '/bin/python.exe'
    print( f'executing: {pythonExePath} {args}')
    subprocess.run( [ pythonExePath, *args ], stdout=sys.stdout)
    
def selectBlenderInstallDir():
    print( 'locating compatible Blender installations...' )
    installDirs = findSupportedBlenderInstallDirs()
    curInstallDir = ''
    curInstallVer = 0
    curPythonDir = ''
    
    if len( installDirs ) == 0:
        print( f'no supported Blender installations were found (min supported version is {MIN_SUPPORTED_VER})' )
        path = input( "please enter the path to your Blender installation or press enter to exit\n" )
        if path.strip() == '':
            sys.exit( 1 )
        
        ver = parseBlenderVersion( os.path.basename( path ) )
        if ver == None:
            print( 'the specified installation directory does not contain a compatible Blender installation' )
            sys.exit( 1 )
        
        if ver < MIN_SUPPORTED_VER:
            print( f"the specified Blender installation version is not supported (version: {ver}, {MIN_SUPPORTED_VER} or up required)" )
            sys.exit( 1 )
            
        installDirs.append( (path, ver) )
        
    if len( installDirs ) > 1:
        print( 'multiple compatible Blender installations were detected' )
        for installDir, ver in installDirs:
            print( f'version {ver}\t{installDir}')
        selectedVerStr = input( 'enter which version (number) to use: ' )
        selectedVer = None
        try:
            selectedVerParts = selectedVerStr.strip().split('.')
            selectedVer = (int( selectedVerParts[0] ), int( selectedVerParts[1] ))
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
        
    curPythonDir = findPython3Dir( curInstallDir, curInstallVer )
    return (curInstallDir, curInstallVer, curPythonDir)
    
def main():
    if len(sys.argv) == 1:
        # select install dir
        installDir, installVer, pythonDir = selectBlenderInstallDir()
    else:
        # override install dir with the user specified one
        installDir = sys.argv[1]
        installVer = parseBlenderVersion( os.path.basename( installDir ) )
        pythonDir = findPython3Dir( installDir, installVer )

    # ensure pip is installed
    pythonLibDir = os.path.join( pythonDir, 'lib' )
    pythonSitePackagesDir = os.path.join( pythonLibDir, 'site-packages' )
    ensurePipPath = os.path.join( pythonLibDir, 'ensurepip' )
    if not os.path.exists( ensurePipPath ):
        if not isAdmin():
            print( 'additional files need to be copied to the installation directory, for which admin priveleges are required' )
            print( 'the script will now restart with admin priveleges' )
            input( 'press any key to continue' )
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit( 0 )
        zipFile = ZipFile( getScriptDir() + '/ensurepip.zip' )
        zipFile.extractall( pythonLibDir )
        
    execPython( pythonDir, ['-m', 'ensurepip', '--upgrade', '--root', pythonSitePackagesDir] )
    
    # install packages
    for package in DEPENDENCIES:
        execPython( pythonDir, ['-m', 'pip', 'install', '--upgrade', '--target', pythonSitePackagesDir, package] )
        
    print( 'setup finished successfully' )
    input( 'press any key to exit' )
    

        
if __name__ == '__main__':
    main()
        
