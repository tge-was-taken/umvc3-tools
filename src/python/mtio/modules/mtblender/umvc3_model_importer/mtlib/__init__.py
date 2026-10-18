import os
import sys
# if os.path.dirname(__file__) not in sys.path:
#     sys.path.append(os.path.dirname(__file__))

# Trying to force these to be relative to eliminate conflicts with global Blender modules and objects.
from . import libtarget
from .ncl import *
from .dds import *
from .immaterial import *
from .immodel import *
from .metadata import *
from . import modelutil
from .rmaterial import *
from .rmodel import *
from .rshader import *
from .rtexture import *
from .shaderinfo import *
from . import util
from . import vertexcodec
from . import mvc3materialnamedb
from . import mvc3shaderdb
from . import mvc3types
from . import target
from .base_editor import *
from .base_importer import *
#import texconv