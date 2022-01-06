import os
import sys
from pymxs import runtime as rt
import mtmaxver

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))
    
lastWindowUpdateTime = rt.timestamp()
def updateUI():
    global lastWindowUpdateTime
    if rt.timestamp() - lastWindowUpdateTime > 3000:
        print('UI update triggered')
        rt.windows.processPostedMessages()
        lastWindowUpdateTime = rt.timestamp()

def isDebugEnv():
    return True
    
def selectOpenFile( category, ext ):
    return rt.getOpenFileName(
        caption=("Open " + category + " file"),
        types=( category + " (*." + ext + ")|*." + ext ),
        historyCategory=( category + " Object Presets" ) )

def selectSaveFile( category, ext ):
    return rt.getSaveFileName(
        caption=("Save " + category + " file"),
        types=( category + " (*." + ext + ")|*." + ext ),
        historyCategory=( category + " Object Presets" ) )
    
def showMessageBox( msg, title="Notice" ):
    rt.messageBox( msg, title=title, beep=True )
    
def runMaxScript( name ):
    rt.fileIn( getScriptDir() + '/maxscript/' + name  )
    
def getAppDataDir():
    path = os.path.expandvars( '%APPDATA%\\MtMax' )
    os.makedirs( path, exist_ok=True )
    return path

def getLogFilePath():
    return os.path.join( getAppDataDir(), 'log.txt' )

def showErrorMessageBox( brief, details = '' ):
    showMessageBox( f"{brief}\n\n{details}\n\nSee the log or the MaxScript listener for more details.\nThe log file can be found at {getLogFilePath()}\nScript version: {mtmaxver.version}" )
    
def showExceptionMessageBox( brief, e ):
    showErrorMessageBox( brief, e.args[0] if len(e.args) > 0 else "" )
