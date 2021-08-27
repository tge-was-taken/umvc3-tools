import os
import sys
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))

from mtdds import *
from mtimmaterial import *
from mtimmodel import *
from mtjointinfo import *
from mtmetadata import *
import mtmodelutil
from mtncl import *
from mtrmaterial import *
from mtrmodel import *
from mtrshader import *
from mtrtexture import *
from mtshaderinfo import *
import mttarget
import mtutil
import mtvertexcodec
import mvc3materialdb
import mvc3shaderdb
import mvc3types
#import texconv