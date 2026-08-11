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
from ..mtlib import util

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..mtlib.properties import UMVC3ModelImportProperties
#from ..properties import UMVC3ModelImportProperties

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class SUB_PT_Model_Import(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'    
    bl_context = "objectmode"
    bl_category = 'MT Framework'
    bl_label = 'Model Importer'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

        #scene = context.scene
        layout = self.layout
        layout.use_property_split = False

        #For the File Import path. It's meant to update the input_modelpath variable when the user chooses a file, 
        #as well as allow text input.
        if mip.input_modelpath == '':
            row = layout.row(align=True)
            row.prop(mip, 'input_modelpath')
            row = layout.row(align=True)
            row.operator(SUB_OP_MOD_ImportModelPath.bl_idname, icon='IMPORT', text='Choose UMVC3 .mod file')
        else:
            row = layout.row(align=True)
            row.prop(mip, 'input_modelpath')
            row = layout.row(align=True)
            row.operator(SUB_OP_MOD_ImportModelPath.bl_idname, icon='IMPORT', text='Choose UMVC3 .mod file')            

        row = layout.row(align=True)
        row.prop(mip, 'import_withmetadata',text='Use Metadata when importing:')
        row = layout.row(align=True)
        row.prop(mip, 'metadata_file')
        row = layout.row(align=True)
        row.operator(SUB_PT_MOD_OT_Choose_Metadata_YML.bl_idname,icon='IMPORT',text= 'Choose metadata .yml file')

        layout.separator()
        row = layout.row(align=True)

        row.label(text="Import Filters", translate=True)
        #layout.separator()
        row = layout.row(align=True)
        row.prop(mip, 'import_weights',text='Weights')
        row.prop(mip, 'import_normals',text='Normals')
        row.prop(mip, 'import_groups',text='Groups')
        row = layout.row(align=True)       
        row.prop(mip, 'import_skeleton',text='Skeletons')
        row.prop(mip, 'import_meshes',text='Meshes')

        layout.separator()
        
        row = layout.row(align=True)
        row.label(text="Additional Options", translate=True)

        row = layout.row(align=True)
        row.prop(mip, 'model_scale',text='Scale')

        row = layout.row(align=True)
        row.prop(mip, 'flip_up_axis',text='Flip Up Axis')

        row = layout.row(align=True)
        # row.prop(mip, 'import_compatwithlukasscript',text='Compatibility With Lukas Script')

        row = layout.row(align=True)
        row.prop(mip, 'bake_scale',text='Bake Scale Into Translation')

        row = layout.row(align=True)
        row.prop(mip, 'convert_tex_to_dds',text='Convert Textures to DDS')

        row = layout.row(align=True)
        row.prop(mip, 'convert_mrl_to_yml',text='Convert MRL(Material) to YML')

        row = layout.row(align=True)
        row.prop(mip, 'create_layer',text='Create Layer')

        row = layout.row(align=True)
        row.prop(mip, 'inherit_scale',text='Inherit Scale')
        
        # row = layout.row(align=True)
        # row.prop(mip, 'normalize_bone_length',text='Normalize Bone Length')

        layout.separator()
        row = layout.row(align=True)
        #row.operator(SUB_PT_MOD_OT_import.bl_idname, text='Import',)
        row.operator('umvc3_model_importer.import_using_settings', text = 'Import Model')

        #all_requirements_met = True
        #min_requirements_met = True

class SUB_OP_MOD_ImportModelPath(bpy.types.Operator, ImportHelper):
    """Import UMVC3 MT Framework *.mod model"""

    bl_idname = "sub.mod_importmodelpath"
    bl_label = "Import Model"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_options = {'UNDO'}
    filename_ext = ".mod"
    filter_glob: StringProperty(default="*.mod", options={'HIDDEN'})

    def invoke(self, context, event):  # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}  

    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        print("You chose:\n", self.filepath)
        mip.input_modelpath = self.filepath
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mip.input_modelpath).split('.')[0] )
        if os.path.exists(newMetadataPath):
            mip.metadata_file = newMetadataPath
            print("Applied matching metadata path:\n", newMetadataPath)
        else:
            mip.metadata_file = ""
            print("This isn't a model file that's covered by metadata...")

        return {'FINISHED'}

class SUB_PT_MOD_OT_Choose_Metadata_YML(bpy.types.Operator, ImportHelper):
    """Choose which Metadata YML to Use"""
    bl_idname = "sub.mod_ot_choose_metadata_yml"
    bl_label = "Import YML"
    #paththing = util.getResourceDir() + '/metadata/'
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_options = {'UNDO', 'PRESET'}
    filename_ext = ".yml"
    filter_glob: StringProperty(default="*.yml", options={'HIDDEN'})        
    #directory: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def invoke(self, context, event):  # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'} 

    def execute(self, context):
        #paththing = util.getResourceDir() + '/metadata/'
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        print("You chose:\n", self.filepath)
        mip.metadata_file = self.filepath
        return {'FINISHED'}

class SUB_PT_MOD_OT_import(bpy.types.Operator):
    bl_idname = 'umvc3_model_importer.import_using_settings'
    bl_label = "Import_Model_Using_Settings"

    # def invoke(self, context, event):  # pragma: no cover
    #     context.window_manager.fileselect_add(self)
    #     return {'RUNNING_MODAL'}

    # @classmethod
    # def poll(self, context):  # pragma: no cover
    #     if not bpy.context.selected_objects:
    #         return False
    #     return True

    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        print("Variable Check!\n")
        print("Model Chosen: ", mip.input_modelpath)
        if mip.import_withmetadata == True:
            print("\n Metadata is to be used: ", mip.metadata_file)
        else:
            print("No Metadata to be used")
        print("==========Import Filters==========")
        print(mip.import_weights)
        print(mip.import_normals)
        print(mip.import_groups)
        print(mip.import_skeleton)
        print(mip.import_meshes)

        print("==========Additional Options==========")

        print("Model Scale: ",str(mip.model_scale))

        print("Flip Up Axis = ",mip.flip_up_axis)
        # print("Importing in the style of the old Maxscript = ",mip.import_compatwithlukasscript)
        print("Bake Scale Into Translation = ",mip.bake_scale)
        print("Convert Textures to DDS = ",mip.convert_tex_to_dds)
        print("Convert MRL(Material) to YML = ",mip.convert_mrl_to_yml)
        print("Create Layer = ",mip.create_layer)
        print("Make Child Bones Inherit Scale = ",mip.inherit_scale)
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mip.input_modelpath).split('.')[0] )
        print("Path Test:\n", newMetadataPath)

        if '' == mip.input_modelpath:
            mip.popupint = 0
            ShowMessageBox("You need to choose a model file before anything can be imported.", "Notice")
            print("You need to choose a model file before anything can be imported.")
        else:
            print("This is where the model importing code would begin.")

            #Below code adapted from TGE's MOD_OT_import function. 
            from .blender_plugin import plugin
            from .blender_importer import BlenderModelImporter
            from ..mtlib import target

            importer = BlenderModelImporter()

            importer.importModel( mip.input_modelpath, context )
            if plugin.logger.hasError():
                self.report( {'ERROR'}, "Import completed with one or more errors." )
                ShowMessageBox("Import Completed, but there are errors.\nCheck the log file for details", "Notice", 'ERROR')
            else:
                self.report( {'INFO'}, 'Import completed successfully' )
                ShowMessageBox("Import Complete!")




        return {'FINISHED'}
        
# class MessageBoxOperator(bpy.types.Operator):
    
#     bl_idname = "wm.myop"
#     bl_label = "Notice"

#     def execute(self, context):
#         self.report({'INFO'}, "This is a test")
#         return {'FINISHED'}