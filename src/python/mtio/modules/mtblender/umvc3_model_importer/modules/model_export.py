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
from pathlib import Path

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..mtlib.properties import UMVC3ModelImportProperties

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def syncExportConfigFromScene( config, mip ):
    # The panel writes to scene properties but the exporter reads plugin.config,
    # which gets loaded from a yml in %APPDATA% and was never updated from the UI.
    # Every checkbox on the export panel was doing nothing without this.
    config.flipUpAxis              = mip.export_flip_up_axis
    config.lukasCompat             = mip.export_compatwithlukasscript

    config.exportFilePath          = mip.export_modelpath
    # DEPRECATED: config.exportRoot was never read by anything
    # config.exportRoot              = mip.extracted_archive_directory

    config.exportWeights           = mip.export_weights
    config.exportNormals           = mip.export_normals
    config.exportGroups            = mip.export_groups
    config.exportSkeleton          = mip.export_skeleton
    config.exportPrimitives        = mip.export_meshes

    config.exportScale             = mip.export_model_scale
    config.exportBakeScale         = mip.export_bake_scale
    config.exportTexturesToTex     = mip.convert_tex_to_tex
    config.exportOverwriteTextures = mip.export_overwrite_textures
    config.exportGroupPerMesh      = mip.export_group_per_mesh
    config.exportGenerateEnvelopes = mip.generate_envelopes

    # DEPRECATED: mrl generation from the scene. Forced off so a leftover value in
    # the AppData yml can't switch the dead code paths back on.
    config.exportGenerateMrl       = False
    config.exportExistingMrlYml    = mip.use_existing_mrl
    config.exportMrlYmlPath        = mip.existing_mrl_yml

    config.exportMetadataPath      = mip.export_metadata_file if mip.export_withmetadata else ''
    config.exportRefPath           = mip.export_reference_model_file if mip.export_use_reference_model else ''

    # the ref toggles only mean anything when there is a ref to pull from
    useRef = mip.export_use_reference_model and mip.export_reference_model_file != ''
    config.exportUseRefJoints      = useRef
    config.exportUseRefEnvelopes   = useRef
    config.exportUseRefBounds      = useRef
    config.exportUseRefGroups      = useRef

class SUB_PT_Model_Export(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'    
    bl_context = "objectmode"
    bl_category = 'MT Framework'
    bl_label = 'Model Exporter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

        #scene = context.scene
        layout = self.layout
        layout.use_property_split = False
        obj: bpy.types.Object = context.active_object
        row = layout.row()  

        if obj is None:
            row.label(text="Select an Armature first.")
        elif obj.select_get() is False:
            row.label(text="Select an Armature first.")   
        elif obj.type == 'ARMATURE':   
            row.prop(mip, 'export_modelpath')
            row = layout.row(align=True)
            row.operator(SUB_OP_MOD_ExportModelPath.bl_idname, icon='IMPORT', text='Choose UMVC3 .mod file')       
            # DEPRECATED: extracted archive directory, only fed the mrl texture paths
            # row = layout.row(align=True)
            # row.prop(mip, 'extracted_archive_directory')
            row = layout.row(align=True)

            row.prop(mip, 'export_use_reference_model',text='Use Reference Model when exporting:')
            row = layout.row(align=True)
            row.prop(mip, 'export_reference_model_file')
            row = layout.row(align=True)
            row.operator(SUB_PT_MOD_OT_Choose_Reference_Model_For_Export.bl_idname,icon='IMPORT',text= 'Choose Optional Reference Model file')
            row = layout.row(align=True)

            row.prop(mip, 'export_withmetadata',text='Use Metadata when exporting:')
            row = layout.row(align=True)
            row.prop(mip, 'export_metadata_file')
            row = layout.row(align=True)
            row.operator(SUB_PT_MOD_OT_Choose_Metadata_For_Export_YML.bl_idname,icon='IMPORT',text= 'Choose metadata .yml file')

            row = layout.row(align=True)
            row.prop(mip, 'export_flip_up_axis',text='Flip Up Axis')
            row = layout.row(align=True)
            row.prop(mip, 'export_compatwithlukasscript',text='Compatibility With Lukas Script')        
            row = layout.row() 

            layout.separator()
            # DEPRECATED: generating an mrl from the blender scene
            # row = layout.row(align=True)
            # row.prop(mip, 'generate_mrl',text='Generate MRL:')
            row = layout.row(align=True)
            row.prop(mip, 'use_existing_mrl',text='Use Existing MRL YML:')
            row = layout.row(align=True)
            row.prop(mip, 'existing_mrl_yml')
            row = layout.row(align=True)
            row.operator(SUB_PT_MOD_OT_Choose_MRL_YML.bl_idname,icon='IMPORT',text= 'Choose MRL .yml file')
            layout.separator()

            row = layout.row(align=True)
            row.label(text="Export Filters", translate=True)
            row = layout.row(align=True)
            row.prop(mip, 'export_weights',text='Weights')
            row.prop(mip, 'export_normals',text='Normals')
            row.prop(mip, 'export_groups',text='Groups')
            row = layout.row(align=True)       
            row.prop(mip, 'export_skeleton',text='Skeletons')
            row.prop(mip, 'export_meshes',text='Meshes')
            row = layout.row(align=True)
            layout.separator()

            row.label(text="Additional Options", translate=True)
            row = layout.row(align=True)            
            row.prop(mip, 'export_model_scale',text='Scale')
            row = layout.row(align=True)
            row.prop(mip, 'export_bake_scale',text='Bake Scale Into Translation:')
            row = layout.row(align=True)
            row.prop(mip, 'convert_tex_to_tex',text='Convert textures to TEX')
            row = layout.row(align=True)
            row.prop(mip, 'export_overwrite_textures',text='Overwrite Existing Textures')
            row = layout.row(align=True)
            row.prop(mip, 'export_group_per_mesh',text='Export group per mesh')           
            row = layout.row(align=True)
            row.prop(mip, 'generate_envelopes',text='Generate envelopes')
            layout.separator()
            row = layout.row(align=True)
            row.operator('umvc3_model_importer.export_using_settings', text = 'Export')

class SUB_OP_MOD_ExportModelPath(bpy.types.Operator, ImportHelper):
    """Import UMVC3 MT Framework *.mod model"""

    bl_idname = "sub.mod_exportmodelpath"
    bl_label = "Export Model"
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
        mip.export_modelpath = self.filepath
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mip.export_modelpath).split('.')[0] )
        if os.path.exists(newMetadataPath):
            mip.export_metadata_file = newMetadataPath
            print("Applied matching metadata path:\n", newMetadataPath)
        else:
            mip.export_metadata_file = ""
            print("This isn't a model file that's covered by metadata...")

        return {'FINISHED'}

class SUB_PT_MOD_OT_Choose_Reference_Model_For_Export(bpy.types.Operator, ImportHelper):
    """Choose which Metadata YML to Use"""
    bl_idname = "sub.mod_ot_choose_reference_model_for_export"
    bl_label = "Choose Reference Model(Optional)"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_options = {'UNDO'}
    filename_ext = ".mod"
    filter_glob: StringProperty(default="*.mod", options={'HIDDEN'})        
    #directory: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def invoke(self, context, event):  # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'} 

    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        print("For reference model, you chose:\n", self.filepath)
        mip.export_reference_model_file = self.filepath
        return {'FINISHED'}

class SUB_PT_MOD_OT_Choose_Metadata_For_Export_YML(bpy.types.Operator, ImportHelper):
    """Choose which Metadata YML to Use"""
    bl_idname = "sub.mod_ot_choose_export_metadata_yml"
    bl_label = "Import YML"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_options = {'UNDO', 'PRESET'}
    filename_ext = ".yml"
    filter_glob: StringProperty(default="*.yml", options={'HIDDEN'})        
    #directory: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def invoke(self, context, event):  # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'} 

    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        print("You chose:\n", self.filepath)
        mip.export_metadata_file = self.filepath
        return {'FINISHED'}
    
class SUB_PT_MOD_OT_Choose_MRL_YML(bpy.types.Operator, ImportHelper):
    """Choose which MRL YML to Use"""
    bl_idname = "sub.mod_ot_choose_export_mrl_yml"
    bl_label = "Import MRL YML"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_options = {'UNDO', 'PRESET'}
    filename_ext = ".yml"
    filter_glob: StringProperty(default="*.yml", options={'HIDDEN'})        
    #directory: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def invoke(self, context, event):  # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'} 

    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        print("You chose:\n", self.filepath)
        mip.existing_mrl_yml = self.filepath
        return {'FINISHED'}

class SUB_PT_MOD_OT_export(bpy.types.Operator):
    bl_idname = 'umvc3_model_importer.export_using_settings'
    bl_label = "Export_Model_Using_Settings"

    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

        # This body used to sit inline while the dispatch below still called
        # _execute(), so an export would run fine and then die on a NameError.
        def _execute():
            print("Variable Check!\n")
            print("Model Chosen: ", mip.export_modelpath)
            # print("Chosen Archive Directory: ", mip.extracted_archive_directory)

            if mip.export_use_reference_model == True:
                print("\n Reference Model to be used: ", mip.export_reference_model_file)
            else:
                print("No Reference Model to be used")

            if mip.export_withmetadata == True:
                print("\n Metadata is to be used: ", mip.export_metadata_file)
            else:
                print("No Metadata to be used")

            if mip.use_existing_mrl:
                print("\n MRL YML File to be used: ", mip.existing_mrl_yml)
            else:
                print("No MRL will be written")

            print("==========Import Filters==========")
            print(mip.export_weights)
            print(mip.export_normals)
            print(mip.export_groups)
            print(mip.export_skeleton)
            print(mip.export_meshes)

            print("==========Additional Options==========")

            print("Model Scale: ",str(mip.export_model_scale))
            print("Flip Up Axis = ",mip.export_flip_up_axis)
            print("Importing in the style of the old Maxscript = ",mip.export_compatwithlukasscript)
            print("Bake Scale Into Translation = ",mip.export_bake_scale)
            print("Convert Textures to Tex = ",mip.convert_tex_to_tex)
            print("Overwrite Existing Textures = ",mip.export_overwrite_textures)
            print("Export Group Per Mesh = ",mip.export_group_per_mesh)
            print("Generate Envelopes = ",mip.generate_envelopes)

            newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mip.export_modelpath).split('.')[0] )
            print("Path Test:\n", newMetadataPath)

            if '' == mip.export_modelpath:
                #mip.popupint = 0
                ShowMessageBox("You need to choose a model file before anything can be exported.", "Notice")
                print("You need to choose a model file before anything can be exported.")
            else:
                print("This is where the model importing begins.\n")

                #Below code adapted from TGE's MOD_OT_export function. 
                from .blender_plugin import plugin
                from .blender_exporter import BlenderModelExporter
                from ..mtlib import target

                plugin.logger.clear()
                syncExportConfigFromScene( plugin.config, mip )
                plugin.config.save()
                plugin.config.dump()
                target.setTarget( target.supported[plugin.config.target].name )

                exporter = BlenderModelExporter()
                exporter.exportModel( mip.export_modelpath, context )
                if plugin.logger.hasError():
                    self.report( {'ERROR'}, "Export completed with one or more errors." )
                else:
                    self.report( {'INFO'}, 'Export completed successfully' )

        from .blender_plugin import plugin
        if plugin.isDebugEnv():
            _execute()
        else:
            try:
                _execute()
            except Exception as e:
                self.report( {'ERROR'}, f'A fatal error occured during export.\n{e.args}' )
                ShowMessageBox("A fatal error occured during export.\n")
                ShowMessageBox(str(e.args))

        return {'FINISHED'}