__package__ = 'modules.mtmax.src'

from typing import Any, Iterable
from ...mtlib.base_editor import *
from ...mtlib import log
from pymxs import runtime as rt
import datetime
import sys
import os
from ...mtlib.ncl import *

def convertPoint3ToNclVec3( v: rt.Point3 ) -> NclVec3:
    return NclVec3((v[0], v[1], v[2]))

def convertPoint3ToNclVec4( v: rt.Point3, w ) -> NclVec4:
    return NclVec4((v[0], v[1], v[2], w))

def convertMatrix3ToNclMat44( v: rt.Matrix3 ):
    return nclCreateMat44((convertPoint3ToNclVec4(v[0], 0), 
                            convertPoint3ToNclVec4(v[1], 0), 
                            convertPoint3ToNclVec4(v[2], 0), 
                            convertPoint3ToNclVec4(v[3], 1)))

class MaxArrayProxy(EditorArrayProxy):
    def __init__(self) -> None:
        self.array = rt.Array()

    def append(self,value):
        rt.append(self.array, value)
    
    def __len__(self):
        return len(self.array)

    def unwrap(self):
        return self.array

    def __getitem__(self, key):
        return self.array[key]

    def __setitem__(self, key, value):
        self.array[key] = value

    def __repr__(self) -> str:
        return self.array.__repr__()

class MaxCustomAttributeSetProxy(EditorCustomAttributeSetProxy):
    def __init__(self, attribs) -> None:
        super().__init__(attribs)

    def getCustomAttribute(self, name: str) -> Any:
        return getattr(self._ctx, name)

    def setCustomAttribute(self, name: str, value: Any):
        return setattr(self._ctx, name, value)

class MaxLayerProxy(EditorLayerProxy):
    def __init__(self, layer) -> None:
        self.layer = layer
    
    def addNode(self, obj):
        self.layer.addNode(obj)

class MaxNodeProxy(EditorNodeProxy):
    def __init__(self, node):
        super().__init__(plugin)
        self.node = node

    def getTransform(self):
        return convertMatrix3ToNclMat44(self.node.transform)

    def getParent(self) -> "EditorNodeProxy":
        parent = self.node.parent
        if parent is None:
            return None
        return MaxNodeProxy(parent)

    def getName(self) -> str:
        return self.node.name

    def unwrap(self) -> Any:
        return self.node

    def isHidden(self) -> bool:
        return self.node.isHidden


    '''
    Table of node types
    Modifier                    classOf                                                 superClassOf
    Bone                        BoneGeometry                                            GeometryClass
    Editable Mesh / Edit Mesh   Editable_mesh                                           GeometryClass
    Editable Poly / Edit Poly   PolyMeshObject, Editable_poly                           GeometryClass
    Biped Object                Biped_Object                                            GeometryClass
    Line                        line                                                    shape
    Dummy (Group)               Dummy                                                   helper
    Dummy (Bone)                Dummy                                                   helper
    '''

    def isMeshNode( self ) -> bool:
        '''Returns if the node is a mesh'''

        # node is considered a mesh of it is an editable mesh or editable poly
        # TODO: investigate other possible types
        return rt.classOf( self.node ) in [rt.Editable_mesh, rt.Editable_poly, rt.PolyMeshObject]


    def isGroupNode( self ):
        '''Returns if the node represents a group'''
        
        # Groups have the same types as bones (Dummy), so we must
        # take extra care to disambiguate
        
        # groups should be a dummy node
        if rt.classOf( self.node ) not in [rt.Dummy]:
            return False
        
        # definitely not a group if it has joint attributes
        if hasattr( self.node, 'MtMaxJointAttributes' ):
            return False

        # definitely a group if it has group attributes
        if hasattr( self.node, 'MtMaxGroupAttributes' ):
            return True
        
        # a group should not be parented to anything
        if self.node.parent != None:
            return False
        
        # we can't determine the type based on the children if there are none
        # so assume it's not a group
        if len(self.node.children) == 0:
            return False
        
        # only meshes should be parented to groups
        # this doesn't allow empty groups, however the previous clauses 
        # should cover those
        for child in self.node.children:
            if not self.isMeshNode( child ):
                return False

        return True

    def isBoneNode( self ):
        '''Returns if the node is a bone'''

        # node is considered a bone node of it's bone geometry (helper)
        return rt.classOf( self.node ) in [rt.BoneGeometry, rt.Dummy, rt.Biped_Object] and not self.isGroupNode()
    
    def isSplineNode( self ):
        '''Return sif the node is spline shape'''
        return rt.superClassOf( self.node ) in [rt.shape]

    def __repr__(self) -> str:
        return self.node.__repr__()

class MaxMaterialProxy(EditorMaterialProxy):
    def __init__(self, material):
        self.material = material

    def unwrap( self ) -> Any:
        return self.material

    def getName( self ) -> str:
        return self.material.name

class MaxMeshProxy(EditorMeshProxy):
    def __init__(self, mesh) -> None:
        super().__init__()
        self.mesh = mesh

    def unwrap( self ) -> Any:
        return self.mesh

class MaxPluginConfig(EditorPluginConfigBase):
    def __init__(self, plugin) -> None:
        super().__init__(plugin)

class MaxPluginLogger(EditorPluginLoggerBase):
    def __init__(self, plugin) -> None:
        super().__init__(plugin)

    def clear( self ):
        super().clear()
        rt.clearListener()

class MaxPlugin(EditorPluginBase):
    def __init__(self):
        super().__init__()
        self.version = '2.0.0 Dev'
        self.logFilePath = None
        self.lastWindowUpdateTime = rt.timestamp()
        self.config = MaxPluginConfig(self)
        self.logger = MaxPluginLogger(self)

    # Interface methods
    def load(self):
        self.config.load()
        log.setLogger(self.logger)

    def isDebugEnv(self):
        return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )

    def timeStamp( self ):
        return rt.timeStamp()

    def disableSceneRedraw( self ):
        rt.disableSceneRedraw()

    def enableSceneRedraw( self ):
        rt.enableSceneRedraw()

    def getIndexBase( self ):
        return 1

    def updateUI( self ) -> bool:
        if rt.timestamp() - self.lastWindowUpdateTime > 2000:
            self.logger.debug('UI update triggered')
            rt.windows.processPostedMessages()
            self.lastWindowUpdateTime = rt.timestamp()
            return True
        return False

    def getNodeByName(self, name: str) -> EditorNodeProxy:
        node = rt.getNodeByName(name)
        if node is None:
            return None
        return MaxNodeProxy(node)

    # Max specific methods
    def getScriptDir( self ):
        return os.path.dirname(os.path.realpath(__file__))

    def selectOpenFile( self, category, ext ):
        return rt.getOpenFileName(
            caption=("Open " + category + " file"),
            types=( category + " (*." + ext + ")|*." + ext ),
            historyCategory=( category + " Object Presets" ) )

    def selectSaveFile( self, category, ext ):
        return rt.getSaveFileName(
            caption=("Save " + category + " file"),
            types=( category + " (*." + ext + ")|*." + ext ),
            historyCategory=( category + " Object Presets" ) )

    def showMessageBox( self, msg, title="Notice" ):
        rt.messageBox( msg, title=title, beep=True )

    def runMaxScript( self, name ):
        rt.fileIn( self.getScriptDir() + '/maxscript/' + name  )

    def showErrorMessageBox( self, brief, details = '' ):
        if self.config.showLogOnError:
            msg = \
            f'''
{brief}
        
{details}
        
See the log or the MaxScript listener for more details.
The log file will now be opened in your default text editor.
Please upload the entire log file whenever you file a bug report.
        
Script version: {self.version}
            '''
            
            self.showMessageBox( msg )
        else:
            msg = \
            f'''
{brief}
        
{details}
        
See the log or the MaxScript listener for more details.
The log file can be found at {self.getLogFilePath()}
Script version: {self.version}
            '''
            
            self.showMessageBox( msg )

    def showExceptionMessageBox( self, brief, e ):
        msg = ''
        if hasattr(e, 'args') and len(e.args) > 0:
            msg = e.args[0]
        self.showErrorMessageBox( brief, msg )

    def openListener( self ):
        rt.actionMan.executeAction( 0, "40472" )
    
    def toMaxArray( self, it: Iterable, converter=lambda x: x ):
        arr = rt.Array()
        for i in it:
            rt.append( arr, converter( i ) )
        return arr

    def getAppDataDir( self ):
        path = os.path.expandvars( '%APPDATA%\\MtMax' )
        os.makedirs( path, exist_ok=True )
        return path

plugin = MaxPlugin()
