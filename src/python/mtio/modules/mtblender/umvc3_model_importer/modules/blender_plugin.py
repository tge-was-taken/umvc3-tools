from typing import Any, Iterable
from ..mtlib import *
from ..mtlib.base_editor import *
from ..mtlib import log
from ..mtlib.ncl import *

import datetime
import sys
import os

import bpy
import bpy_types

def convertPoint3ToNclVec4( v, w ) -> NclVec3:
    return NclVec4((v[0], v[1], v[2], w))
    
def convertMatrix3ToNclMat44( v ):
    return nclCreateMat44((convertPoint3ToNclVec4(v[0], 0), 
                            convertPoint3ToNclVec4(v[1], 0), 
                            convertPoint3ToNclVec4(v[2], 0), 
                            convertPoint3ToNclVec4(v[3], 1)))

class BlenderArrayProxy(EditorArrayProxy):
    def __init__(self) -> None:
        self.array = []

    def append(self,value):
        self.array.append(value)

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

class BlenderCustomAttributeSetProxy(EditorCustomAttributeSetProxy):
    def __init__(self, attribs) -> None:
        super().__init__(attribs)

    def _resolve(self):
        # Object mode Bone props aren't reachable from a script, so the importer
        # parks the MT attributes on the matching Pose bone. Both the read and the
        # write side have to go through here or they land on different datablocks.
        ctx = self._ctx
        if ctx is None:
            return None
        if isinstance(ctx, bpy.types.Bone):
            armature = ctx.id_data
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' and obj.data == armature:
                    return obj.pose.bones.get(ctx.name)
            return None
        return ctx

    def getCustomAttribute(self, name: str) -> Any:
        ctx = self._resolve()
        if ctx is None:
            return None
        try:
            return ctx[name]
        except (KeyError, TypeError):
            # missing key, not an error. callers treat None as "not set" and fall
            # back to defaults. raising KeyError here also broke getattr(_, _, None)
            # since getattr only swallows AttributeError.
            return None

    def setCustomAttribute(self, name: str, value: Any):
        ctx = self._resolve()
        if ctx is None:
            return
        ctx[name] = value

    def hasCustomAttribute(self, name: str) -> bool:
        ctx = self._resolve()
        if ctx is None:
            return False
        try:
            return name in ctx.keys()
        except (AttributeError, TypeError):
            return False

class BlenderLayerProxy(EditorLayerProxy):
    def __init__(self, layer) -> None:
        self.layer = layer

    def addNode(self,obj: EditorNodeProxy):
        self.layer.objects.link(obj.unwrap())

    def unwrap(self):
        return self.layer

class BlenderNodeProxy(EditorNodeProxy):
    def __init__(self, node):
        super().__init__(plugin)
        self.node = node

    def unwrap(self) -> Any:
        return self.node

    def getTransform(self):
        return convertMatrix3ToNclMat44(self.node.matrix_local)

    def getParent(self):
        parent = getattr(self.node, 'parent', None)
        if parent is None:
            # was wrapping None in a proxy, so `node.getParent() != None` was true
            # for every unparented object and the caller would blow up downstream
            return None
        return BlenderNodeProxy(parent)

    def getName(self):
        return self.node.name

    def isHidden(self):
        #Has to be rewritten to disambiguate between bones and not bones.
        if isinstance(self.node, bpy_types.Bone):
            return self.node.hide
        #Below is required for groups
        else:
            return self.node.hide_viewport

    def isBoneHidden(self):
        #To disambiguate between bones and not bones.
        if isinstance(self.node, bpy_types.Bone):
            return self.node.hide
        elif self.node is None:
            return True
        else:
            return self.node.hide

    def isMeshNode(self):
        return isinstance(self.node.data, bpy_types.Mesh)

    def isGroupNode(self):
        if self.node.type == 'EMPTY': #This is the primary difference in the node type I found.
            return True
        else:
            return False

    def isBoneNode(self):
        #return isinstance(self.node.data, bpy_types.Bone)
        return isinstance(self.node, bpy_types.Bone)

    def isSplineNode(self):
        return False # TODO

class BlenderBoneProxy(EditorNodeProxy):
    def __init__(self, data, tfm):
        super().__init__(plugin)
        self.data = data
        self.tfm = tfm

    def unwrap(self) -> Any:
        return self.data

    def getTransform(self):
        return self.tfm
        # matrix = self.data.matrix
        # parent = self.data.parent
        # while parent is not None:
        #     matrix *= parent.matrix
        #     parent = parent.parent

        # #matrix.transpose()
        # return convertMatrix3ToNclMat44(matrix)

    def getParent(self):
        if self.data.parent is None: return None
        return BlenderBoneProxy(self.data.parent)

    def getName(self):
        return self.data.name

    def isHidden(self):
        return self.data.id_data.hide_viewport

    def isMeshNode(self):
        return False

    def isGroupNode(self):
        return False

    def isBoneNode(self):
        return True

    def isSplineNode(self):
        return False

class BlenderEditBoneProxy(EditorNodeProxy):
    def __init__(self, editBone, tfm):
        super().__init__(plugin)
        self.editBone = editBone
        self.tfm = tfm
        self.name = editBone.name

    def unwrap(self) -> Any:
        return self.editBone

    def getTransform(self):
        return self.tfm

    def getParent(self):
        if self.editBone.parent is None: return None
        return BlenderEditBoneProxy(self.editBone.parent)

    def getName(self):
        return self.name

    def isHidden(self):
        return self.editBone.hide_viewport

    def isMeshNode(self):
        return False

    def isGroupNode(self):
        return False

    def isBoneNode(self):
        return True

    def isSplineNode(self):
        return False

class BlenderMaterialProxy(EditorMaterialProxy):
    def __init__(self, material):
        self.material = material

    def unwrap( self ) -> Any:
        return self.material

    def getName( self ) -> str:
        return self.material.name

class BlenderPluginConfig(EditorPluginConfigBase):
    def __init__(self, plugin) -> None:
        super().__init__(plugin)

class BlenderPluginLogger(EditorPluginLoggerBase):
    def __init__(self, plugin) -> None:
        super().__init__(plugin)

    def clear( self ):
        super().clear()

class BlenderPlugin(EditorPluginBase):
    def __init__(self):
        super().__init__()
        self.version = '2.0.0 Dev'
        self.config = BlenderPluginConfig(self)
        self.logger = BlenderPluginLogger(self)

    # Interface methods
    def load(self):
        self.config.load()
        log.setLogger(self.logger)

    def isDebugEnv(self):
        return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )

    def timeStamp( self ):
        import time
        return time.time()

    def disableSceneRedraw( self ):
        pass

    def enableSceneRedraw( self ):
        pass

    def getIndexBase( self ):
        return 0

    def updateUI( self ) -> bool:
        return False

    def getNodeByName(self, name: str) -> EditorNodeProxy:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            return BlenderNodeProxy(obj)
        # Bones are not objects, so an object only lookup meant every symmetry
        # lookup came back None and the exported skeleton had no symmetry at all.
        for armature in bpy.data.armatures:
            bone = armature.bones.get(name)
            if bone is not None:
                return BlenderNodeProxy(bone)
        return None

    def getAppDataDir( self ):
        path = os.path.expandvars( '%APPDATA%\\MtBlender' )
        os.makedirs( path, exist_ok=True )
        return path

    def getScriptDir( self ):
        return os.path.dirname(os.path.realpath(__file__))

plugin = BlenderPlugin()