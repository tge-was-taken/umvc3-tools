import bpy
import re
import os, sys, time, traceback, mathutils, re, subprocess, enum, math
import numpy as np
from bpy.types import Scene, Object, Armature, PropertyGroup, Camera, Material, Bone, Mesh, Collection
from bpy.props import IntProperty, StringProperty, EnumProperty, BoolProperty, FloatProperty, CollectionProperty, PointerProperty
from bpy.props import FloatVectorProperty
#import mtlib


def register():
        Scene.sub_scene_properties = PointerProperty(
        type=UMVC3ModelImportProperties
    )
        
class UMVC3ModelImportProperties(PropertyGroup):
    import_compatwithlukasscript: BoolProperty(
        name='Compatibility With Lukas'' script.',
        description='Imports in a way that is compatible with the classic 3ds maxscript(Not full functional at the moment!)',
        default=False,
    )
    input_modelpath: StringProperty(
        name = 'Model File Path',  
        description = 'The UMVC3 .mod file to import',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )
    import_withmetadata: BoolProperty(
        name='Import With Metadata.',
        description='Determines whether or not to use Metadata when importing. Disable when using custom skeletons',
        default=False,
    )
    metadata_file: StringProperty(
        name = 'Optional Metadata File',
        description = 'Load the model with a metadata file to get descriptive names on groups, primitives, and bones',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )
    import_weights: BoolProperty(
        name='Import Weights',
        description='Import Weights',
        default=True,
    )
    import_normals: BoolProperty(
        name='Import Normals',
        description='Import Normals',
        default=True,
    )
    import_groups: BoolProperty(
        name='Import Groups',
        description='Import Groups',
        default=True,
    )
    import_skeleton: BoolProperty(
        name='Import Skeleton',
        description='Import Skeleton',
        default=True,
    )
    import_meshes: BoolProperty(
        name='Import Meshes',
        description='Import Meshes',
        default=True,
    )
    model_scale: FloatProperty(
        name='Scale',
        description='Scale. Leave at 1.0 if unsure',
        default=1.0,
    )
    bake_scale: BoolProperty(
        name='Bake Scale',
        description='Bake scale of model in bones. Recommended to leave checked if not using 1.0 for scale',
        default=True,
    )
    convert_tex_to_dds: BoolProperty(
        name='Convert TEX to DDS',
        description='Converts any .TEX files in the same direcotry To .DDS files',
        default=True,
    )
    convert_mrl_to_yml: BoolProperty(
        name='Convert MRL to YML',
        description='Converts Material to .YML',
        default=True,
    ) 
    import_outline: BoolProperty(
        name='Add Ink Outline (EXPERIMENTAL)',
        description='DOES NOT CURRENTLY WORK',
        default=False,
    )
    outline_thickness: FloatProperty(
        name='Outline Thickness (EXPERIMENTAL)',
        description='DOES NOT CURRENTLY WORK',
        default=0.45,
        min=0.0,
        max=20.0,
    )
    import_exact_shading: BoolProperty(
        name='Game Shaders (exact)',
        description='Recreates games shaders from the game shaders (root.spkg). Needs the game folder',
        default=True,
    )
    game_native_dir: StringProperty(
        name='Game Folder',
        description='UMvC3 install folder (or its nativePCx64 folder).',
        default='',
        subtype='DIR_PATH',
    )
    mt_point_light: PointerProperty(
        name='Point Light',
        description='Point light the game shaders use as their second light (FPointLightD). Strength is the game value, falloff from the light\'s mt_falloff_start / mt_falloff_end props. Rebuild the game shaders after setting it',
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'LIGHT' and obj.data.type == 'POINT',
    )
    mt_key_light: PointerProperty(
        name='Key Light',
        description='Sun lamp the MT materials take their light direction and colour from (colour times strength)',
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'LIGHT' and obj.data.type == 'SUN',
    )
    import_toon_shading: BoolProperty(
        name='MT Shading',
        description='Rebuild each material with the game\'s own shading (toon ramps, half lambert, rim light, specular, colour correct) from the mrl. Works in Eevee and Cycles. Sets the view transform to Standard so colours match the game',
        default=False,
    )
    inherit_scale: BoolProperty(
        name='Inherit Scale',
        description='Enables child bones to inherit scale of parents in animations. Recommended to leave unchecked or false if model is to be used for animation',
        default=False,
    )                    
    create_layer: BoolProperty(
        name='Create_Collection',
        description='Creates a collection for the Imported Model. Recommended.',
        default=True,
    )
    normalize_bone_length: BoolProperty(
        name='Normalize Bone Length',
        description='Disregards bone length values from model file when importing. May be necessary for good IK setups.',
        default=False,
    )                                
    flip_up_axis: BoolProperty(
        name='Flip Up Axis',
        description='Converts the Up Axis from Y-Up to Z-up. Recommened to leave on',
        default=True,
    )                 
    # popupint: IntProperty(
    #     name='Pop Up Box Context Value ',
    #     default=0,
    # )
    #Anim Properties.===================================================================================================================
    anim_import_withmetadata: BoolProperty(
        name='Import With Metadata.',
        description='Determines whether or not to use Metadata when importing. Uncheck if using custom skeleton or unsure',
        default=False,
    )
    anim_metadata_file: StringProperty(
        name = 'Optional Metadata File',
        description = 'The metadata file used for dealing with animations. Leave unckecked if unsure',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )
    anim_export_metadata_file: StringProperty(
        name = 'Optional Metadata File',
        description = 'The metadata file referenced when exporting animations',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )    
    #Export Properties.===================================================================================================================
    export_flip_up_axis: BoolProperty(
        name='Flip Up Axis',
        description='Converts the Up Axis from Y-Up to Z-up',
        default=True,
    )
    export_modelpath: StringProperty(
        name = 'Model File Path',  
        description = 'The UMVC3 .mod file to import',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )
    extracted_archive_directory: StringProperty(
        name = 'Extracted Archive Path',  
        description = 'The unpacked archive path needed for export',
        default = '',
        maxlen=1024,
        subtype='DIR_PATH',
    )        
    export_compatwithlukasscript: BoolProperty(
        name='Compatibility With Lukas'' script.',
        description='Exports in a way that is compatible with the classic 3ds maxscript',
        default=False,
    )
    export_use_reference_model: BoolProperty(
        name='Use Reference Model',
        description='Determines whether or not to use a reference model when exporting',
        default=False,
    )
    export_reference_model_file: StringProperty(
        name = 'Optional Reference Model File Path',  
        description = 'The UMVC3 .mod file to import',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )
    export_withmetadata: BoolProperty(
        name='Import With Metadata.',
        description='Determines whether or not to use Metadata when exporting',
        default=False,
    )    
    export_metadata_file: StringProperty(
        name = 'Optional Metadata File',
        description = 'Load the model with a metadata file to get descriptive names on group and bones',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )    
    export_weights: BoolProperty(
        name='Export Weights',
        description='Export Weights',
        default=True,
    )
    export_normals: BoolProperty(
        name='Export Normals',
        description='Export Normals',
        default=True,
    )
    export_groups: BoolProperty(
        name='Export Groups',
        description='export Groups',
        default=True,
    )
    export_skeleton: BoolProperty(
        name='Export Skeleton',
        description='Export Skeleton',
        default=True,
    )
    export_meshes: BoolProperty(
        name='Export Meshes',
        description='Export Meshes',
        default=True,
    )
    generate_mrl: BoolProperty(
        name='Generate MRL YML',
        description='Export Meshes',
        default=False,
    )
    use_existing_mrl: BoolProperty(
        name='Generate MRL YML',
        description='Export Meshes',
        default=True,
    )    
    existing_mrl_yml: StringProperty(
        name = 'Material YML File Path',  
        description = 'The material YML to use to create the mrl',
        default = '',
        maxlen=1024,
        #subtype='FILE_PATH',
    )                                
    export_model_scale: FloatProperty(
        name='Scale',
        description='Scale',
        default=1.0,
    )
    export_bake_scale: BoolProperty(
        name='Bake Scale Into Translation',
        description='Bake scale of model in bones',
        default=True,
    )
    convert_tex_to_tex: BoolProperty(
        name='Convert Textures to TEX',
        description='Converts Textures To .TEX files',
        default=True,
    )
    # export_bake_scale: BoolProperty(
    #     name='Bake Scale Into Translation',
    #     description='Bake scale of model in bones(Not cleanly working at the moment!)',
    #     default=True,
    # )
    export_overwrite_textures: BoolProperty(
        name='Overwrite Existing Textures',
        description='Overwrites Existing Texture Files',
        default=False,
    )
    export_group_per_mesh: BoolProperty(
        name='Export Group Per Mesh',
        description='Exports Group Per Mesh. If unsure, leave unchecked',
        default=False,
    )
    generate_envelopes: BoolProperty(
        name='Generate Envelopes',
        description='Produces skin data for exporting. Leave unchecked if using a custom skeleton. Recommended to leave on for stages',
        default=True,
    )
    bones_in_front: BoolProperty(
        name='Display Model Bones In Front',
        description='Sets the imported Models Armature to display its bones in front',
        default=True,
    )
    material_to_filter_by: bpy.props.PointerProperty(
        name="Material",
        description='The Material to Filter Selection to.',
        type=bpy.types.Material,
    )