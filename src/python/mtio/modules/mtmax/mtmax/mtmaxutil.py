import os
import sys
from pymxs import runtime as rt

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))
    
lastWindowUpdateTime = rt.timestamp()
def lazyUpdateUI():
    global lastWindowUpdateTime
    if rt.timestamp() - lastWindowUpdateTime > 1000:
        rt.windows.processPostedMessages()
        lastWindowUpdateTime = rt.timestamp()

def isDebugEnv():
    return True
    
def clearLog():
    rt.clearListener()
    try:
        rt.mtLogRollout.edtLog.text = ''
    except:
        pass
    
def logDebug( msg, *args ):
    if isDebugEnv():
        print( msg, *args )
        
def logInfo( msg, *args ):
    print( msg, *args )
    try:
        rt.mtLogRollout.edtLog.text += msg + '\n'
    except:
        pass
    
def selectOpenFile( category, ext ):
    return rt.getOpenFileName(
        caption=("Open " + category + " file"),
        types=( category + " (*." + ext + ")|*." + ext ),
        historyCategory=( category + " Object Presets" ) )
    
def runMaxScript( name ):
    rt.fileIn( getScriptDir() + '/maxscript/' + name  )
