import os
import sys
import datetime

class DefaultLogger:
    def _log( self, level, msg, *args ):
        formattedMsg = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S:%f') + ' [' + level + ']: ' + str(msg)
        print( formattedMsg, *args )
    
    def debug( self, msg, *args ):
        self._log( 'DEBUG', msg, *args )
    
    def info( self, msg, *args ):
        self._log( 'INFO', msg, *args )
    
    def warn( self, msg, *args ):
        self._log( 'WARNING', msg, *args )
    
    def error( self, msg, *args ):
        self._log( 'ERROR', msg, *args )
    
_impl = DefaultLogger()

def setLogger( logger ):
    _impl = logger
    
def getLogger():
    return _impl
    
def debug( msg, *args ):
    _impl.debug( msg, *args )
        
def info( msg, *args ):
    _impl.info( msg, *args )
    
def warn( msg, *args ):
    _impl.warn( msg, *args )
    
def error( msg, *args ):
    _impl.error( msg, *args )