import os
import sys
import datetime
from abc import ABC, abstractmethod
import traceback

class LoggerBase(ABC):
    def __init__(self) -> None:
        super().__init__()
        self._categoryStack = []
        self._indentLevel = 0
        self._hasError = False

    def formatMessage( self, level, msg ):
        formattedMsg = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S:%f') + ' [' + level + ']: ' + (self._indentLevel * ' ') + str(msg)
        return formattedMsg

    @abstractmethod
    def log( self, level, msg, *args ):
        pass

    def clear( self ):
        self._categoryStack = []
        self._indentLevel = 0
        self._hasError = False

    def debug( self, msg, *args ):
        self.log( 'DEBUG', msg, *args )
    
    def info( self, msg, *args ):
        self.log( 'INFO', msg, *args )
    
    def warn( self, msg, *args ):
        self.log( 'WARNING', msg, *args )
    
    def error( self, msg, *args ):
        self._hasError = True
        self.log( 'ERROR', msg, *args )

    def exception( self, e ):
        self.error( ''.join(traceback.format_exception( None, e, e.__traceback__ ) ) )

    def push( self, cat = None ):
        self._categoryStack.append( cat )
        self._indentLevel += 1

    def pop( self ):
        self._categoryStack.pop()
        self._indentLevel -= 1

    def hasError( self ):
        return self._hasError

class ConsoleLogger(LoggerBase):
    def log( self, level, msg, *args ):
        print( self.formatMessage( level, msg ), *args )
    
_impl = ConsoleLogger()

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