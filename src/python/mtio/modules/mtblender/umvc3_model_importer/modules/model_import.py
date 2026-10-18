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
    bl_idname = 'SUB_PT_Model_Import'
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
        row.prop(mip, 'create_layer',text='Create Collection')

        row = layout.row(align=True)
        row.prop(mip, 'inherit_scale',text='Inherit Scale')

        row = layout.row(align=True)
        row.prop(mip, 'bones_in_front',text='Set Imported Model Bones To Display In Front')

        # row = layout.row(align=True)
        # row.prop(mip, 'normalize_bone_length',text='Normalize Bone Length')

        layout.separator()
        row = layout.row(align=True)
        #row.operator(SUB_PT_MOD_OT_import.bl_idname, text='Import',)
        row.operator('umvc3_model_importer.import_using_settings', text = 'Import Model')

        #all_requirements_met = True
        #min_requirements_met = True

class SUB_PT_Model_Import_Rendering(Panel):
    bl_idname = 'SUB_PT_Model_Import_Rendering'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'MT Framework'
    bl_parent_id = 'SUB_PT_Model_Import'
    bl_label = 'Rendering'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        layout = self.layout

        row = layout.row(align=True)
        row.prop(mip, 'import_toon_shading', text='MT Shading (game accurate)')
        row = layout.row(align=True)
        row.enabled = mip.import_toon_shading
        row.prop(mip, 'import_exact_shading')
        row = layout.row(align=True)
        row.enabled = mip.import_toon_shading and mip.import_exact_shading
        row.prop(mip, 'game_native_dir')

        row = layout.row(align=True)
        row.prop(mip, 'import_outline', text='Add Ink Outline')
        row = layout.row(align=True)
        row.enabled = mip.import_outline
        row.prop(mip, 'outline_thickness')

        # the scene lighting the MT Character group reads, normally filled from a stage sdl
        scene = context.scene
        layout.separator()
        layout.label(text='MT Lighting')
        row = layout.row(align=True)
        row.operator(SUB_OP_LoadStageLighting.bl_idname, icon='LIGHT_SUN', text='Load Stage Lighting (sdl folder)')
        if 'mt_light_color' in scene.keys():
            row = layout.row(align=True)
            row.prop(mip, 'mt_key_light')
            sun = mip.mt_key_light
            if sun is not None and sun.type == 'LIGHT':
                row = layout.row(align=True)
                row.prop(sun.data, 'color', text='Colour')
                row.prop(sun.data, 'energy', text='Strength')
            for key, label in (('mt_scene_lights', 'Use All Scene Lights (Eevee)'),
                               ('mt_world_ambient', 'World As Ambient'),
                               ('mt_ambient', 'Extra Ambient'),
                               ('mt_rim_color', 'Rim Colour'), ('mt_rim_power', 'Rim Power')):
                if key in scene.keys():
                    row = layout.row(align=True)
                    row.prop(scene, '["%s"]' % key, text=label)
            layout.label(text='Eevee: any light works. Cycles: key light only')
            if scene.get('mt_game_native_dir'):
                layout.separator()
                layout.label(text='Game Shaders')
                row = layout.row(align=True)
                row.prop(mip, 'mt_point_light')
                for key, label in (('mt_light_mask', 'Light Mask'), ('mt_outenc', 'Shader Set (1 fight, 0 super cut-in)'),
                                   ('mt_outline_push', 'Outline Push Back (renders only)')):
                    if key in scene.keys():
                        row = layout.row(align=True)
                        row.prop(scene, '["%s"]' % key, text=label)
                if 'mt_face_group' in scene.keys():
                    row = layout.row(align=True)
                    row.prop(scene, '["mt_face_group"]', text='Face Group (70 default)')
                    row.operator(SUB_OP_ApplyFaceGroup.bl_idname, icon='HIDE_OFF', text='')
                row = layout.row(align=True)
                row.operator(SUB_OP_RebuildGameShaders.bl_idname, icon='FILE_REFRESH', text='Rebuild Game Shaders')
                row = layout.row(align=True)
                row.operator(SUB_OP_ExportGameMRL.bl_idname, icon='EXPORT', text='Export MRL')
                row = layout.row(align=True)
                row.operator(SUB_OP_RenderGamePost.bl_idname, icon='RENDER_STILL', text='Render With Game Bloom')


class SUB_OP_RebuildGameShaders(bpy.types.Operator):
    bl_idname = "sub.mt_rebuild_game_shaders"
    bl_label = "Rebuild Game Shaders"
    bl_options = {'UNDO'}

    def execute(self, context):
        from . import mt_exact
        from .blender_plugin import plugin
        n = mt_exact.rebuild_all(context, plugin.logger)
        self.report({'INFO'}, f'rebuilt {n} materials')
        return {'FINISHED'}


class SUB_OP_ApplyFaceGroup(bpy.types.Operator):
    bl_idname = "sub.mt_apply_face_group"
    bl_label = "Show Face Group"
    bl_options = {'UNDO'}

    def execute(self, context):
        from . import mt_exact
        n = mt_exact.apply_face_group(context.scene)
        self.report({'INFO'}, f'face group {context.scene.get("mt_face_group")}, {n} primitives hidden')
        return {'FINISHED'}


class SUB_OP_ExportGameMRL(bpy.types.Operator, ExportHelper):
    bl_idname = "sub.mt_export_mrl"
    bl_label = "Export MRL"
    filename_ext = ".mrl"
    filter_glob: bpy.props.StringProperty(default="*.mrl", options={'HIDDEN'})
    write_yml: bpy.props.BoolProperty(name="Also write .mrl.yml", default=True)

    def invoke(self, context, event):  # pragma: no cover
        from . import mt_mrl
        groups = mt_mrl.game_materials()
        if groups and not self.filepath:
            src = max(groups, key=lambda k: len(groups[k]))
            self.filepath = src
        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        from . import mt_mrl
        from .blender_plugin import plugin
        try:
            src, notes = mt_mrl.export_mrl(self.filepath, write_yml=self.write_yml, logger=plugin.logger)
        except Exception as e:
            self.report({'ERROR'}, 'MRL export failed: %s' % e)
            return {'CANCELLED'}
        self.report({'WARNING'} if notes else {'INFO'},
                    'wrote %s%s' % (os.path.basename(self.filepath), (' (%d notes in the log)' % len(notes)) if notes else ''))
        return {'FINISHED'}


class SUB_OP_RenderGamePost(bpy.types.Operator):
    bl_idname = "sub.mt_render_game_post"
    bl_label = "Render With Game Bloom"

    def execute(self, context):
        from . import mt_post
        from .blender_plugin import plugin
        if not context.scene.get('mt_game_native_dir'):
            self.report({'ERROR'}, 'Import with Game Shaders (exact) first')
            return {'CANCELLED'}
        try:
            im = mt_post.render_with_post(context, log=plugin.logger.debug if hasattr(plugin.logger, 'debug') else None)
        except Exception as e:
            self.report({'ERROR'}, 'game post failed: %s' % e)
            return {'CANCELLED'}
        for area in context.screen.areas if context.screen else []:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = im
                break
        self.report({'INFO'}, 'saved to image "%s"' % im.name)
        return {'FINISHED'}


class SUB_OP_LoadStageLighting(bpy.types.Operator):
    bl_idname = "sub.mt_load_stage_lighting"
    bl_label = "Load Stage Lighting"
    bl_options = {'UNDO'}
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):  # pragma: no cover
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from . import mt_shading
        if not self.directory or not os.path.isdir(self.directory):
            self.report({'ERROR'}, 'Pick the folder that holds the stage .sdl files')
            return {'CANCELLED'}
        mip = context.scene.sub_scene_properties
        mt_shading.ensure_scene_lighting(context.scene, getattr(mip, 'model_scale', 1.0))
        msg = mt_shading.load_stage_lighting(context.scene, self.directory)
        self.report({'INFO'}, 'MT lighting: ' + msg)
        return {'FINISHED'}


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
        print("Create Collection = ",mip.create_layer)
        print("Make Child Bones Inherit Scale = ",mip.inherit_scale)
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mip.input_modelpath).split('.')[0] )
        print("Path Test:\n", newMetadataPath)
        print("Display Bones in Front:\n", mip.bones_in_front)
        
        if '' == mip.input_modelpath:
            # popupint is commented out in properties.py, so this raises before the
            # message box the user actually needs to see.
            # mip.popupint = 0
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