# wrapper script to launch the plugin
import sys
import os 

# fix import paths
def _fixImports():
    curDir = os.path.dirname( __file__ ) 
    if not curDir in sys.path: sys.path.append( curDir )
    packageDir = os.path.realpath( curDir + '/../' )
    if not packageDir in sys.path: 
        sys.path.append( packageDir )

_fixImports()
from mtmax import *

if __name__ == '__main__':
    main()