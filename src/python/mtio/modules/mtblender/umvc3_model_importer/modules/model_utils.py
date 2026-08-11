import os
import os.path
import bpy
import mathutils
import time
import math
import traceback
import numpy as np

from mathutils import Vector, Matrix
from mathutils import Euler
from bpy.props import StringProperty, BoolProperty
from bpy.types import Panel, Operator, EditBone
from bpy_extras import image_utils
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper
from mathutils import Quaternion
from ..mtlib.metadata import ModelMetadata
from ..mtlib.metadata import JointMetadata
from pathlib import Path
from . import blender_plugin
from .blender_plugin import *


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..mtlib.properties import UMVC3ModelImportProperties

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class SUB_PT_OT_ADD_REMOVE_MT_STUFF(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'    
    bl_category = 'MT Framework'
    bl_label = 'Utility'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.mode == "POSE" or context.mode == "OBJECT":
            return True
        return False
    
    def draw(self, context):
        
        layout = self.layout
        layout.use_property_split = False        
        obj: bpy.types.Object = context.active_object
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        row = layout.row()
        if obj is None:
            row.label(text="Select a primitive, joint, or group object first.")
        elif obj.type == 'ARMATURE' and context.mode != "POSE":
            row.label(text="Bones have to be selected in pose mode.")
        elif obj.type == 'MESH' and context.mode != "OBJECT":
            row.label(text="Select the mesh in Object Mode.")   
        elif obj.type == 'MESH' and context.mode == "OBJECT":
            layout.separator()
            row = layout.row(align=True)
            row.operator('sub.mod_op_add_mt_attributes', text = 'Add MT Attributes to Mesh')
            layout.separator()
            row = layout.row(align=True)
            row.operator('sub.mod_op_remove_mt_attributes', text = 'Delete MT Attributes from Mesh')
            layout.separator()
            row = layout.row(align=True)
            row.operator('sub.mod_op_cleanup_vertex_groups', text = 'Cleanup Vertex Groups on Selected Meshes')
        elif obj.type == 'EMPTY' and context.mode != "OBJECT":
            row.label(text="Select the Group Node in Object Mode.")               
        elif obj.type == 'EMPTY' and context.mode == "OBJECT":    
            layout.separator()
        elif obj.type == 'ARMATURE' and context.mode == "POSE":
            #Checks which pose bone is selected, if any at all.
            PoseBones = obj.pose.bones
            ChosenBone = None
            if len(bpy.context.selected_pose_bones) > 1:
                layout.separator()
                row = layout.row(align=True)
                row.operator('sub.mod_op_add_mt_attributes', text = 'Add MT Attributes to Mesh')
                layout.separator()
                row = layout.row(align=True)
                row.operator('sub.mod_op_remove_mt_attributes', text = 'Delete MT Attributes from Mesh')
            else:
                for Bone in PoseBones:
                    if Bone in bpy.context.selected_pose_bones:
                        ChosenBone = Bone

                        # row.prop(mip, 'anim_export_metadata_file')
                        # row = layout.row(align=True)
                        # row.operator(SUB_PT_MOD_OT_Choose_Anim_Export_Metadata_YML.bl_idname,icon='IMPORT',text= 'Choose metadata .yml file')
                        layout.separator()
                        row = layout.row(align=True)
                        row.operator('sub.mod_op_add_mt_attributes', text = 'Add MT Attributes to Mesh')
                        layout.separator()
                        row = layout.row(align=True)
                        row.operator('sub.mod_op_remove_mt_attributes', text = 'Delete MT Attributes from Mesh')
                        # row = layout.row(align=True)
                        # row.operator(SUB_OP_anim_export.bl_idname, icon='IMPORT', text='Export Marvel 3 .yml Animation')
                if ChosenBone == None:
                    row.label(text="Select a bone in pose mode.")  
        else:
            row.label(text="Select a primitive, joint, or group object first.")        

class SUB_OP_ADD_MT_ATTRIBUTES(bpy.types.Operator):
    bl_idname = 'sub.mod_op_add_mt_attributes'
    bl_label = "Add MT Attribute Data"

    def execute(self,context):
        scene = bpy.context.scene
        #Stores the object selected.
        obj = bpy.context.active_object

        if obj.type == 'MESH' and context.mode == "OBJECT":
            
            #Is this command necessary?
            BlenderNode = BlenderNodeProxy(obj)
            
            try:
                obj["flags"] = str(0)
                obj["groupId"] = str(0) 
                obj["lodIndex"] = str(0) 
                obj["matIndex"] = str(0) 
                obj["vertexFlags"] = str(0) 
                obj["vertexStride"] = str(0) 
                obj["renderFlags"] = str(0) 
                obj["vertexStartIndex"] = str(0) 
                obj["vertexBufferOffset"] = str(0) 
                obj["shaderName"] = ""
                obj["indexBufferOffset"] = str(0) 
                obj["indexCount"] = str(0) 
                obj["indexStartIndex"] = str(0) 
                obj["boneMapStartIndex"] = str(0) 
                obj["envelopeCount"] = str(0) 
                obj["envelopeIndex"] = str(0) 
                obj["id"] = str(0)
                obj["minVertexIndex"] = str(0) 
                obj["maxVertexIndex"] = str(0) 
                obj["field2c"] = str(0) 
                obj["envelopePtr"] = str(0) 
                obj["index"] = str(0) 
            except KeyError:
                print("MT Attribute data doesn't seem to exist on the selected item.")
                ShowMessageBox("MT Attribute data doesn't seem to exist on the selected item.\nYou may have already deleted them.")
        #For Group nodes.
        elif obj.type == 'EMPTY' and context.mode == "OBJECT":
            BlenderNode = BlenderNodeProxy(obj)
            try:
                obj["id"] = str(0)
                obj["field04"] = str(0)    
                obj["field08"] = str(0)
                obj["field0c"] = str(0)
                obj["boundingSphere"] = str(0.0)
                obj["index"] = str(0.0)
            except KeyError:
                print("MT Attribute data doesn't seem to exist on the selected item.")
                ShowMessageBox("MT Attribute data doesn't seem to exist on the selected item.\nYou may have already deleted them.")                
        #For Joints/Bones.
        elif obj.type == 'ARMATURE' and context.mode == "POSE":
            #Checks which pose bone is selected, if any at all.
            PoseBones = obj.pose.bones
            ChosenBone = None
            for Bone in bpy.context.selected_pose_bones:
                ChosenBone = Bone
                BlenderNode = BlenderNodeProxy(ChosenBone)
                try:
                    Bone["id"] = str(0)
                    Bone["parentIndex"] = str(0)
                    Bone["symmetryIndex"] = str(0)
                    Bone["symmetryName"] = str(0)
                    Bone["field03"] = str(0)
                    Bone["field04"] = str(0)
                    Bone["length"] = str(0.0)
                    Bone["offsetX"] = str(0.0)
                    Bone["offsetY"] = str(0.0)
                    Bone["offsetZ"] = str(0.0)
                    Bone["index"] = str(0)

                except KeyError:
                    print("MT Attribute data doesn't seem to exist on the selected item.")
                    ShowMessageBox("MT Attribute data doesn't seem to exist on the selected item.\nYou may have already deleted them.")

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)        
        return {'FINISHED'}       

class SUB_OP_REMOVE_MT_ATTRIBUTES(bpy.types.Operator):
    bl_idname = 'sub.mod_op_remove_mt_attributes'
    bl_label = "Delete MT Attribute Data"

    def execute(self,context):
        scene = bpy.context.scene
        #Stores the object selected.
        obj = bpy.context.active_object
        #Attempts to remove the MT Attributes from Primitives.
        if obj.type == 'MESH' and context.mode == "OBJECT":
            
            #Is this command necessary?
            BlenderNode = BlenderNodeProxy(obj)
            
            try:
                del obj["flags"] 
                del obj["groupId"] 
                del obj["lodIndex"] 
                del obj["matIndex"] 
                del obj["vertexFlags"] 
                del obj["vertexStride"] 
                del obj["renderFlags"] 
                del obj["vertexStartIndex"] 
                del obj["vertexBufferOffset"] 
                del obj["shaderName"] 
                del obj["indexBufferOffset"] 
                del obj["indexCount"] 
                del obj["indexStartIndex"] 
                del obj["boneMapStartIndex"] 
                del obj["envelopeCount"] 
                del obj["envelopeIndex"] 
                del obj["id"]
                del obj["minVertexIndex"] 
                del obj["maxVertexIndex"] 
                del obj["field2c"] 
                del obj["envelopePtr"] 
                del obj["index"] 
            except KeyError:
                print("MT Attribute data doesn't seem to exist on the selected item.")
                ShowMessageBox("MT Attribute data doesn't seem to exist on the selected item.\nYou may have already deleted them.")
        #For Group nodes.
        elif obj.type == 'EMPTY' and context.mode == "OBJECT":
            BlenderNode = BlenderNodeProxy(obj)
            try:
                del obj["id"]
                del obj["field04"]    
                del obj["field08"]
                del obj["field0c"]
                del obj["boundingSphere"]
                del obj["index"]
            except KeyError:
                print("MT Attribute data doesn't seem to exist on the selected item.")
                ShowMessageBox("MT Attribute data doesn't seem to exist on the selected item.\nYou may have already deleted them.")                
        #For Joints/Bones.
        elif obj.type == 'ARMATURE' and context.mode == "POSE":
            #Checks which pose bone is selected, if any at all.
            PoseBones = obj.pose.bones
            ChosenBone = None
            for Bone in bpy.context.selected_pose_bones:
                ChosenBone = Bone
                BlenderNode = BlenderNodeProxy(ChosenBone)
                try:
                    del Bone["id"]
                    del Bone["parentIndex"]
                    del Bone["symmetryIndex"]
                    del Bone["symmetryName"]
                    del Bone["field03"]
                    del Bone["field04"]
                    del Bone["length"]
                    del Bone["offsetX"]
                    del Bone["offsetY"]
                    del Bone["offsetZ"]
                    del Bone["index"]

                except KeyError:
                    print("MT Attribute data doesn't seem to exist on the selected item.")
                    ShowMessageBox("MT Attribute data doesn't seem to exist on the selected item.\nYou may have already deleted them.")        

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)        
        return {'FINISHED'}  

class SUB_OP_CLEANUP_VERTEX_GROUPS(bpy.types.Operator):
    bl_idname = 'sub.mod_op_cleanup_vertex_groups'
    bl_label = "Cleanup Vertex Groups"

    def execute(self,context):
        scene = bpy.context.scene

        #Stores the objects selected.
        for obj in bpy.context.selected_objects:
            if obj.type != 'MESH':
                continue

            #Check to see if the mesh has an Armature Modifier, and selects it.
            Armature = next(
                (
                    modifier.object
                    for modifier in obj.modifiers
                    if modifier.type == 'ARMATURE' and modifier.object
                ),
                None
            )
            if not Armature:
                continue

            #Gather the relevant bone names.
            RelevantBoneNames = {bone.name for bone in Armature.data.bones}
        
            #Discards the vertex groups that don't match bone names in the armature.
            for vertex_group in list(obj.vertex_groups):
                if vertex_group.name not in RelevantBoneNames:
                    obj.vertex_groups.remove(vertex_group)

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)        
        return {'FINISHED'}  




