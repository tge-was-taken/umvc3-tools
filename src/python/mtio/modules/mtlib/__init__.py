import os
import sys
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))

from dds import *
from immaterial import *
from immodel import *
from metadata import *
import modelutil
from ncl import *
from rmaterial import *
from rmodel import *
from rshader import *
from rtexture import *
from shaderinfo import *
import libtarget
import util
import vertexcodec
import mvc3materialdb
import mvc3shaderdb
import mvc3types
#import texconv