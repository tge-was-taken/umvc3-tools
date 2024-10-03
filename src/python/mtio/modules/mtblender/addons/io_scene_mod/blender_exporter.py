from ....mtlib.base_editor import *
import blender_plugin
import bpy

class BlenderNodeProxy(EditorNodeProxy):
    def __init__(self, node):
        super().__init__(blender_plugin.plugin)
        self.node = node

    def unwrap(self) -> Any:
        return self.node

    def getTransform(self):
        return self.node.matrix_world

    def getParent(self):
        return BlenderNodeProxy(self.node.parent)

    def getName(self):
        return self.node.name

    def isHidden(self):
        return self.node.hide_viewport

    def isMeshNode(self):
        return isinstance(self.node, bpy.types.Mesh)

    def isGroupNode(self):
        return isinstance(self.node, bpy.types.Group)

    def isBoneNode(self):
        return isinstance(self.node, bpy.types.Armature)

    def isSplineNode(self):
        return isinstance(self.node, bpy.types.Curve)

class BlenderModelExporter(ModelExporterBase):
    def getObjects( self ):
        temp = list(bpy.data.objects)
        objects = []
        for o in temp:
            if not o in self._processedNodes:
                objects.append( BlenderNodeProxy( o ) )
        return objects