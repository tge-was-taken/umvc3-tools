import os
import sys
from typing import Iterable
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
        return True
    return False

def isDebugEnv():
    return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )
    
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
    import mtmaxconfig
    if mtmaxconfig.showLogOnError:
        msg = \
        f'''
        {brief}
        
        {details}
        
        See the log or the MaxScript listener for more details.
        The log file will now be opened in your default text editor.
        Please upload the entire log file whenever you file a bug report.
        
        Script version: {mtmaxver.version}
        '''
        
        showMessageBox( msg )
    else:
        msg = \
        f'''
        {brief}
        
        {details}
        
        See the log or the MaxScript listener for more details.
        The log file can be found at {getLogFilePath()}
        Script version: {mtmaxver.version}
        '''
        
        showMessageBox( msg )
    
def showExceptionMessageBox( brief, e ):
    msg = ''
    if hasattr(e, 'args') and len(e.args) > 0:
        msg = e.args[0]
    showErrorMessageBox( brief, msg )
    
def openListener():
    rt.actionMan.executeAction( 0, "40472" )
    
def openLogFile():
    os.system( getLogFilePath() )

def toMaxArray( it: Iterable, converter=lambda x: x ):
    arr = rt.Array()
    for i in it:
        rt.append( arr, converter( i ) )
    return arr