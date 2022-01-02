import os
import sys
from pymxs import runtime as rt
import mtmaxutil
import datetime
import traceback


def _getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

_categoryStack = []
_indentLevel = 0
_logFilePath = os.path.join( _getScriptDir(), 'log.txt' )
if os.path.exists( _logFilePath ):
    os.remove( _logFilePath )

def _log( level, msg, *args ):
    global _indentLevel
    formattedMsg = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' [' + level + ']: ' + (_indentLevel * ' ') + msg
    print( formattedMsg, *args )
    with open( _logFilePath, 'a' ) as f:
        f.write( formattedMsg + '\n' )
    
    # too slow
    # if level != 'DBG ':
    #     try:
    #         rt.mtLogRollout.edtLog.text += msg + '\n'
    #     except:
    #         pass

def clear():
    rt.clearListener()
    try:
        rt.mtLogRollout.edtLog.text = ''
    except:
        pass
    
    _categoryStack = []
    _indentLevel = 0
    
def debug( msg, *args ):
    if mtmaxutil.isDebugEnv():
        _log( 'DEBUG', msg, *args )
        
def info( msg, *args ):
    _log( 'INFO', msg, *args )
    
def warn( msg, *args ):
    _log( 'WARNING', msg, *args )
    
def error( msg, *args ):
    _log( 'ERROR', msg, *args )
    
def exception( e ):
    error( ''.join(traceback.format_exception( None, e, e.__traceback__ ) ) )
    
def push( cat = None ):
    global _categoryStack
    global _indentLevel
    
    _categoryStack.append( cat )
    _indentLevel += 1
    
def pop():
    global _categoryStack
    global _indentLevel
    
    _categoryStack.pop()
    _indentLevel -= 1