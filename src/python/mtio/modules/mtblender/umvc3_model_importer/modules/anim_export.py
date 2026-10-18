import os
import os.path
import bpy
import mathutils
import time
import re
import math
import yaml
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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..mtlib.properties import UMVC3ModelImportProperties

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class data():
   def __init__(self, X, Y, Z, W):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.W = W

class Keyframes():
    def __init__(self, Frame, TrackType, BoneID, data):
        self.Frame = Frame
        self.TrackType = TrackType
        self.BoneID = BoneID
        self.data = data

class LMTM3AEntry:
      yaml_loader = yaml.SafeLoader
      yaml_tag = u'!LMTM3AEntry'

      def __init__(self, version, Name, FrameCount, LoopFrame, KeyFrames):
        self.version = version
        self.Name = Name
        self.FrameCount = FrameCount
        self.LoopFrame = LoopFrame
        self.KeyFrames = KeyFrames

def LMTM3AEntry_constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> LMTM3AEntry:
  """Construct a LMTM3AEntry."""
  return LMTM3AEntry(**loader.construct_mapping(node))

def get_loader():
  """Add constructors to PyYAML loader."""
  loader = yaml.SafeLoader
  loader.add_constructor("!LMTM3AEntry", LMTM3AEntry_constructor)
  return loader

#From the SSBU Animation exporter.        
def get_heirarchy_order(bone_list: list[bpy.types.PoseBone]) -> list[bpy.types.PoseBone]:
    root_bone: bpy.types.PoseBone = None
    for bone in bone_list:
        if bone.parent is None:
            root_bone = bone
            break
    return [root_bone] + [c for c in root_bone.children_recursive if c in bone_list]

#Code from my 2023 Aniamtion importer, slightly adapted.
class Location():
    def __init__(self, x, y, z):
        self.x: float = x
        self.y: float = y
        self.z: float = z
    def __repr__(self) -> str:
        return f'[{self.x=}, {self.y=}, {self.z=}]'

class Rotation():
    def __init__(self, w, x, y, z):
        self.w: float = w
        self.x: float = x
        self.y: float = y
        self.z: float = z
    def __repr__(self) -> str:
        return f'[{self.w=}, {self.x=}, {self.y=}, {self.z=}]'

class Scale():
    def __init__(self, x, y, z):
        self.x: float = x
        self.y: float = y
        self.z: float = z
    def __repr__(self) -> str:
        return f'[{self.x=}, {self.y=}, {self.z=}]'

def keyframeCount(bone, start, end) -> int:

    N_keyframes = 0

    action = bpy.data.actions["ArmatureAction"]
    for fcu in action.fcurves:
        print(fcu.data_path + " channel " + str(fcu.array_index))     
        bonename = str(bone.name)      
        for keyframe in fcu.keyframe_points:
            if str(bone.name) in fcu.data_path:
                print(keyframe.co) #coordinates x,y
                N_keyframes += 1



    return N_keyframes

#Double Checking the bone name for conflicts.
def NameChecker(index, fcu, bonename) -> bool:
    #pdb.set_trace()
#This is inteded to remove naming issues with the data path that result in redundant/incorrect keys being inserted for the bone.
    if bonename == "jnt_1":
        if "jnt_10" in fcu.data_path:
            return False
        if "jnt_11" in fcu.data_path:
            return False
        if "jnt_12" in fcu.data_path:
            return False
        if "jnt_13" in fcu.data_path:
            return False
        if "jnt_14" in fcu.data_path:
            return False
        if "jnt_15" in fcu.data_path:
            return False
        if "jnt_16" in fcu.data_path:
            return False
        if "jnt_17" in fcu.data_path:
            return False
        if "jnt_18" in fcu.data_path:
            return False
        if "jnt_19" in fcu.data_path:
            return False
        return True

    if bonename == "jnt_2":  
        if "jnt_20" in fcu.data_path:
            return False
        if "jnt_21" in fcu.data_path:
            return False
        if "jnt_22" in fcu.data_path:
            return False
        if "jnt_23" in fcu.data_path:
            return False
        if "jnt_24" in fcu.data_path:
            return False
        if "jnt_25" in fcu.data_path:
            return False
        if "jnt_26" in fcu.data_path:
            return False
        if "jnt_27" in fcu.data_path:
            return False
        if "jnt_28" in fcu.data_path:
            return False
        if "jnt_29" in fcu.data_path:
            return False
        return True

    if bonename == "jnt_3":   
        if "jnt_30" in fcu.data_path:
            return False
        if "jnt_31" in fcu.data_path:
            return False
        if "jnt_32" in fcu.data_path:
            return False
        if "jnt_33" in fcu.data_path:
            return False
        if "jnt_34" in fcu.data_path:
            return False
        if "jnt_35" in fcu.data_path:
            return False
        if "jnt_36" in fcu.data_path:
            return False
        if "jnt_37" in fcu.data_path:
            return False
        if "jnt_38" in fcu.data_path:
            return False
        if "jnt_39" in fcu.data_path:
            return False
        return True
        
    if bonename == "jnt_4":
        if "jnt_40" in fcu.data_path:
            return False
        if "jnt_41" in fcu.data_path:
            return False
        if "jnt_42" in fcu.data_path:
            return False
        if "jnt_43" in fcu.data_path:
            return False
        if "jnt_44" in fcu.data_path:
            return False
        if "jnt_45" in fcu.data_path:
            return False
        if "jnt_46" in fcu.data_path:
            return False
        if "jnt_47" in fcu.data_path:
            return False
        if "jnt_48" in fcu.data_path:
            return False
        if "jnt_49" in fcu.data_path:
            return False
        return True
        
    if bonename == "jnt_5": 
        if "jnt_50" in fcu.data_path:
            return False
        if "jnt_51" in fcu.data_path:
            return False
        if "jnt_52" in fcu.data_path:
            return False
        if "jnt_53" in fcu.data_path:
            return False
        if "jnt_54" in fcu.data_path:
            return False
        if "jnt_55" in fcu.data_path:
            return False
        if "jnt_56" in fcu.data_path:
            return False
        if "jnt_57" in fcu.data_path:
            return False
        if "jnt_58" in fcu.data_path:
            return False
        if "jnt_59" in fcu.data_path:
            return False
        return True     

    if bonename == "jnt_6":  
        if "jnt_60" in fcu.data_path:
            return False
        if "jnt_61" in fcu.data_path:
            return False
        if "jnt_62" in fcu.data_path:
            return False
        if "jnt_63" in fcu.data_path:
            return False
        if "jnt_64" in fcu.data_path:
            return False
        if "jnt_65" in fcu.data_path:
            return False
        if "jnt_66" in fcu.data_path:
            return False
        if "jnt_67" in fcu.data_path:
            return False
        if "jnt_68" in fcu.data_path:
            return False
        if "jnt_69" in fcu.data_path:
            return False 
        return True   

    if bonename == "jnt_7":
        if "jnt_70" in fcu.data_path:
            return False
        if "jnt_71" in fcu.data_path:
            return False
        if "jnt_72" in fcu.data_path:
            return False
        if "jnt_73" in fcu.data_path:
            return False
        if "jnt_74" in fcu.data_path:
            return False
        if "jnt_75" in fcu.data_path:
            return False
        if "jnt_76" in fcu.data_path:
            return False
        if "jnt_77" in fcu.data_path:
            return False
        if "jnt_78" in fcu.data_path:
            return False
        if "jnt_79" in fcu.data_path:
            return False 
        return True                          

    if bonename == "jnt_8":  
        if "jnt_80" in fcu.data_path:
            return False
        if "jnt_81" in fcu.data_path:
            return False
        if "jnt_82" in fcu.data_path:
            return False
        if "jnt_83" in fcu.data_path:
            return False
        if "jnt_84" in fcu.data_path:
            return False
        if "jnt_85" in fcu.data_path:
            return False
        if "jnt_86" in fcu.data_path:
            return False
        if "jnt_87" in fcu.data_path:
            return False
        if "jnt_88" in fcu.data_path:
            return False
        if "jnt_89" in fcu.data_path:
            return False
        return True
        
    if bonename == "jnt_9":    
        if "jnt_90" in fcu.data_path:
            return False
        if "jnt_91" in fcu.data_path:
            return False
        if "jnt_92" in fcu.data_path:
            return False
        if "jnt_93" in fcu.data_path:
            return False
        if "jnt_94" in fcu.data_path:
            return False
        if "jnt_95" in fcu.data_path:
            return False
        if "jnt_96" in fcu.data_path:
            return False
        if "jnt_97" in fcu.data_path:
            return False
        if "jnt_98" in fcu.data_path:
            return False
        if "jnt_99" in fcu.data_path:
            return False 
        return True           

    if bonename == "jnt_10":
        if "jnt_100" in fcu.data_path:
            return False    
        if "jnt_110" in fcu.data_path:
            return False
        if "jnt_101" in fcu.data_path:
            return False
        if "jnt_102" in fcu.data_path:
            return False
        if "jnt_103" in fcu.data_path:
            return False
        if "jnt_104" in fcu.data_path:
            return False
        if "jnt_105" in fcu.data_path:
            return False
        if "jnt_106" in fcu.data_path:
            return False
        if "jnt_107" in fcu.data_path:
            return False
        if "jnt_108" in fcu.data_path:
            return False
        if "jnt_109" in fcu.data_path:
            return False 
        return True    

    if bonename == "jnt_11":    
        if "jnt_110" in fcu.data_path:
            return False
        if "jnt_111" in fcu.data_path:
            return False
        if "jnt_112" in fcu.data_path:
            return False
        if "jnt_113" in fcu.data_path:
            return False
        if "jnt_114" in fcu.data_path:
            return False
        if "jnt_115" in fcu.data_path:
            return False
        if "jnt_116" in fcu.data_path:
            return False
        if "jnt_117" in fcu.data_path:
            return False
        if "jnt_118" in fcu.data_path:
            return False
        if "jnt_119" in fcu.data_path:
            return False 
        return True    

    if bonename == "jnt_12":    
        if "jnt_120" in fcu.data_path:
            return False
        if "jnt_121" in fcu.data_path:
            return False
        if "jnt_122" in fcu.data_path:
            return False
        if "jnt_123" in fcu.data_path:
            return False
        if "jnt_124" in fcu.data_path:
            return False
        if "jnt_125" in fcu.data_path:
            return False
        if "jnt_126" in fcu.data_path:
            return False
        if "jnt_127" in fcu.data_path:
            return False
        if "jnt_128" in fcu.data_path:
            return False
        if "jnt_129" in fcu.data_path:
            return False 
        return True    
    
    if bonename == "jnt_13":    
        if "jnt_130" in fcu.data_path:
            return False
        if "jnt_131" in fcu.data_path:
            return False
        if "jnt_132" in fcu.data_path:
            return False
        if "jnt_133" in fcu.data_path:
            return False
        if "jnt_134" in fcu.data_path:
            return False
        if "jnt_135" in fcu.data_path:
            return False
        if "jnt_136" in fcu.data_path:
            return False
        if "jnt_137" in fcu.data_path:
            return False
        if "jnt_138" in fcu.data_path:
            return False
        if "jnt_139" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_14":    
        if "jnt_140" in fcu.data_path:
            return False
        if "jnt_141" in fcu.data_path:
            return False
        if "jnt_142" in fcu.data_path:
            return False
        if "jnt_143" in fcu.data_path:
            return False
        if "jnt_144" in fcu.data_path:
            return False
        if "jnt_145" in fcu.data_path:
            return False
        if "jnt_146" in fcu.data_path:
            return False
        if "jnt_147" in fcu.data_path:
            return False
        if "jnt_148" in fcu.data_path:
            return False
        if "jnt_149" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_15":    
        if "jnt_150" in fcu.data_path:
            return False
        if "jnt_151" in fcu.data_path:
            return False
        if "jnt_152" in fcu.data_path:
            return False
        if "jnt_153" in fcu.data_path:
            return False
        if "jnt_154" in fcu.data_path:
            return False
        if "jnt_155" in fcu.data_path:
            return False
        if "jnt_156" in fcu.data_path:
            return False
        if "jnt_157" in fcu.data_path:
            return False
        if "jnt_158" in fcu.data_path:
            return False
        if "jnt_159" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_16":    
        if "jnt_160" in fcu.data_path:
            return False
        if "jnt_161" in fcu.data_path:
            return False
        if "jnt_162" in fcu.data_path:
            return False
        if "jnt_163" in fcu.data_path:
            return False
        if "jnt_164" in fcu.data_path:
            return False
        if "jnt_165" in fcu.data_path:
            return False
        if "jnt_166" in fcu.data_path:
            return False
        if "jnt_167" in fcu.data_path:
            return False
        if "jnt_168" in fcu.data_path:
            return False
        if "jnt_169" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_17":    
        if "jnt_170" in fcu.data_path:
            return False
        if "jnt_171" in fcu.data_path:
            return False
        if "jnt_172" in fcu.data_path:
            return False
        if "jnt_173" in fcu.data_path:
            return False
        if "jnt_174" in fcu.data_path:
            return False
        if "jnt_175" in fcu.data_path:
            return False
        if "jnt_176" in fcu.data_path:
            return False
        if "jnt_177" in fcu.data_path:
            return False
        if "jnt_178" in fcu.data_path:
            return False
        if "jnt_179" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_18":    
        if "jnt_180" in fcu.data_path:
            return False
        if "jnt_181" in fcu.data_path:
            return False
        if "jnt_182" in fcu.data_path:
            return False
        if "jnt_183" in fcu.data_path:
            return False
        if "jnt_184" in fcu.data_path:
            return False
        if "jnt_185" in fcu.data_path:
            return False
        if "jnt_186" in fcu.data_path:
            return False
        if "jnt_187" in fcu.data_path:
            return False
        if "jnt_188" in fcu.data_path:
            return False
        if "jnt_189" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_19":    
        if "jnt_190" in fcu.data_path:
            return False
        if "jnt_191" in fcu.data_path:
            return False
        if "jnt_192" in fcu.data_path:
            return False
        if "jnt_193" in fcu.data_path:
            return False
        if "jnt_194" in fcu.data_path:
            return False
        if "jnt_195" in fcu.data_path:
            return False
        if "jnt_196" in fcu.data_path:
            return False
        if "jnt_197" in fcu.data_path:
            return False
        if "jnt_198" in fcu.data_path:
            return False
        if "jnt_199" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_20":    
        if "jnt_200" in fcu.data_path:
            return False
        if "jnt_201" in fcu.data_path:
            return False
        if "jnt_202" in fcu.data_path:
            return False
        if "jnt_203" in fcu.data_path:
            return False
        if "jnt_204" in fcu.data_path:
            return False
        if "jnt_205" in fcu.data_path:
            return False
        if "jnt_206" in fcu.data_path:
            return False
        if "jnt_207" in fcu.data_path:
            return False
        if "jnt_208" in fcu.data_path:
            return False
        if "jnt_209" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_21":    
        if "jnt_210" in fcu.data_path:
            return False
        if "jnt_211" in fcu.data_path:
            return False
        if "jnt_212" in fcu.data_path:
            return False
        if "jnt_213" in fcu.data_path:
            return False
        if "jnt_214" in fcu.data_path:
            return False
        if "jnt_215" in fcu.data_path:
            return False
        if "jnt_216" in fcu.data_path:
            return False
        if "jnt_217" in fcu.data_path:
            return False
        if "jnt_218" in fcu.data_path:
            return False
        if "jnt_219" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_22":    
        if "jnt_220" in fcu.data_path:
            return False
        if "jnt_221" in fcu.data_path:
            return False
        if "jnt_222" in fcu.data_path:
            return False
        if "jnt_223" in fcu.data_path:
            return False
        if "jnt_224" in fcu.data_path:
            return False
        if "jnt_225" in fcu.data_path:
            return False
        if "jnt_226" in fcu.data_path:
            return False
        if "jnt_227" in fcu.data_path:
            return False
        if "jnt_228" in fcu.data_path:
            return False
        if "jnt_229" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_23":    
        if "jnt_230" in fcu.data_path:
            return False
        if "jnt_231" in fcu.data_path:
            return False
        if "jnt_232" in fcu.data_path:
            return False
        if "jnt_233" in fcu.data_path:
            return False
        if "jnt_234" in fcu.data_path:
            return False
        if "jnt_235" in fcu.data_path:
            return False
        if "jnt_236" in fcu.data_path:
            return False
        if "jnt_237" in fcu.data_path:
            return False
        if "jnt_238" in fcu.data_path:
            return False
        if "jnt_239" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_24":    
        if "jnt_240" in fcu.data_path:
            return False
        if "jnt_241" in fcu.data_path:
            return False
        if "jnt_242" in fcu.data_path:
            return False
        if "jnt_243" in fcu.data_path:
            return False
        if "jnt_244" in fcu.data_path:
            return False
        if "jnt_245" in fcu.data_path:
            return False
        if "jnt_246" in fcu.data_path:
            return False
        if "jnt_247" in fcu.data_path:
            return False
        if "jnt_248" in fcu.data_path:
            return False
        if "jnt_249" in fcu.data_path:
            return False 
        return True

    if bonename == "jnt_25":    
        if "jnt_250" in fcu.data_path:
            return False
        if "jnt_251" in fcu.data_path:
            return False
        if "jnt_252" in fcu.data_path:
            return False
        if "jnt_253" in fcu.data_path:
            return False
        if "jnt_254" in fcu.data_path:
            return False
        if "jnt_255" in fcu.data_path:
            return False
        if "jnt_256" in fcu.data_path:
            return False
        return True

    return True

def loadMetadata( self, path ):
    metadata = ModelMetadata()
    if os.path.exists( path ):
        #self.logger.info(f'loading metadata file from {path}')
        metadata.loadFile( path )
    return metadata

# def getJointName( self, id ) -> str:
#     return self._getObjectName( JointMetadata, self.jointLookupById, id )

def WriteM3AanimationData(context,filepath, read_LoopFrame, self):
    global AnimName; AnimName = ""
    GroupCount = 0
    global FrameCount; FrameCount = 0
    NodeCount = 0
    global AnimGroups; AnimGroups = {}
    keycount = 0
    os.system('cls')
    
    #Stores the object selected.
    obj = bpy.context.active_object
    TrueKeys = []
    
    #Gets The Current Scene.
    Scene = bpy.context.scene

    #Changes the blender mode to Pose Mode.
    bpy.ops.object.mode_set(mode = 'POSE', toggle=False)

    #To get the export settings.
    mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

    try:

        #Gets info from the animation timeline to acquire the starting and ending frames of the animation. First one is always zero.
        FirstFrame = Scene.frame_start
        FrameCount = Scene.frame_end
        bpy.context.scene.frame_set(0)

        print("First frame: ", FirstFrame, "while the last frame is: ", FrameCount)

        #obj = bpy.data.objects["Armature"]

        #Attempts to actually gather all of the keyframes in the scene.
        
        if self.export_use_metadata_anim == True:
            #Borrowed from the Smash Uitimate animation exporter because the other methods don't get the keys I want without redundant data
            #that would bloat file size.
            metadata = loadMetadata( self,mip.anim_export_metadata_file )
            # Create value dicts ahead of time
            bone_name_to_location_values: dict[str, list[Location]] = {}
            bone_name_to_rotation_values: dict[str, list[Rotation]] = {}
            bone_name_to_scale_values: dict[str, list[Scale]] = {}
            bone_to_rel_matrix_local = {}
            reordered_pose_bones = get_heirarchy_order(list(obj.pose.bones))
            
            # Fill value dicts with default values. Not every bone will be animated, so for these the default values of a matrix basis will be needed
            for pose_bone in reordered_pose_bones:
                bone_name_to_location_values[pose_bone.name] = [Location(0.0, 0.0, 0.0) for _ in range(FirstFrame, FrameCount + 1)]
                bone_name_to_rotation_values[pose_bone.name] = [Rotation(1.0, 0.0, 0.0, 0.0) for _ in range(FirstFrame, FrameCount + 1)]
                bone_name_to_scale_values[pose_bone.name] = [Scale(1.0, 1.0, 1.0) for _ in range(FirstFrame, FrameCount + 1)]
                if pose_bone.parent: # non-root bones
                    bone_to_rel_matrix_local[pose_bone] = pose_bone.parent.bone.matrix_local.inverted() @ pose_bone.bone.matrix_local
                else: # root bones
                    bone_to_rel_matrix_local[pose_bone] = pose_bone.bone.matrix_local
            
            # Go through the pose bones' fcurves and store all the values at each frame.
            animated_pose_bones: set[bpy.types.PoseBone] = set()
            
            keycount = 0
            tracks = []

            for fcurve in obj.animation_data.action.fcurves:
                regex = r'pose\.bones\[\"(.*)\"\]\.(.*)'
                matches = re.match(regex, fcurve.data_path)
                if matches is None: # A fcurve in the action that isn't a bone transform, such as the user keyframing the Armature Object itself.
                    print("The fcurve with data path", fcurve.data_path,  "\nis not going to be exported because it's not matching bone fcurve patterns.")
                    continue
                if len(matches.groups()) != 2: # TODO: Is this possible?
                    print("The fcurve with data path", fcurve.data_path,  "\nis not going to be exported because it's not fully matching bone fcurve patterns.")
                    continue
                bone_name = matches.groups()[0]
                transform_subtype = matches.groups()[1]
                if transform_subtype == 'location':
                    for index, frame in enumerate(range(FirstFrame, FrameCount+1)):
                        if fcurve.array_index == 0:
                            bone_name_to_location_values[bone_name][index].x = fcurve.evaluate(frame)
                        elif fcurve.array_index == 1:
                            bone_name_to_location_values[bone_name][index].y = fcurve.evaluate(frame)
                        elif fcurve.array_index == 2:
                            bone_name_to_location_values[bone_name][index].z = fcurve.evaluate(frame)
                elif transform_subtype == 'rotation_quaternion':
                    for index, frame in enumerate(range(FirstFrame, FrameCount+1)):
                        if fcurve.array_index == 0:
                            bone_name_to_rotation_values[bone_name][index].w = fcurve.evaluate(frame)
                        elif fcurve.array_index == 1:
                            bone_name_to_rotation_values[bone_name][index].x = fcurve.evaluate(frame)
                        elif fcurve.array_index == 2:
                            bone_name_to_rotation_values[bone_name][index].y = fcurve.evaluate(frame)
                        elif fcurve.array_index == 3:
                            bone_name_to_rotation_values[bone_name][index].z = fcurve.evaluate(frame)
                elif transform_subtype == 'scale':
                    for index, frame in enumerate(range(FirstFrame, FrameCount+1)):
                        if fcurve.array_index == 0:
                            bone_name_to_scale_values[bone_name][index].x = fcurve.evaluate(frame)
                        elif fcurve.array_index == 1:
                            bone_name_to_scale_values[bone_name][index].y = fcurve.evaluate(frame)
                        elif fcurve.array_index == 2:
                            bone_name_to_scale_values[bone_name][index].z = fcurve.evaluate(frame)
                animated_pose_bone = obj.pose.bones.get(bone_name)
                if animated_pose_bone is not None:
                    animated_pose_bones.add(animated_pose_bone)
                    
            bone_to_world_matrix = {}
            '''
            sorted_fcurves = {}
            for i in bpy.data.actions:
                print (i.name)
                for fcu in i.fcurves:
                    print (fcu)
                    for keyframe in fcu.keyframe_points:
                        x, y = keyframe.co
                        print (x,y)
            '''
            #action = bpy.data.actions["ArmatureAction"]
            action = obj.animation_data.action
                                                    
        #with open('C:\\dump.txt', 'w') as f:
            for bone in reordered_pose_bones:
                
                #f.write("\n____________________________________________________________________________________________________")
                #f.write("\nBone ID: "+str(bone.name))
                print("_________________________________________________________________________\nNow Serving Bone ID: " + str(bone.name))          
                
                #Variables for holding Location, Rotational, and Scale Data.
                FramesL = []
                KeysL = []
                KeyTypesL = []
                InterpolationsL = []

                FramesR = []
                KeysR = []
                KeyTypesR = []
                InterpolationsR = []

                FramesS = []
                KeysS = []
                KeyTypesS = []
                InterpolationsS = []


                for index, _ in enumerate(range(FirstFrame, FrameCount+1)):
                    #Gets the needed values and prints them out in the console and in dump.txt.
                    trans_basis_vec = bone_name_to_location_values[bone.name][index]
                    trans_basis_quat = Quaternion([0, trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                    rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                    rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                    scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                    scale_basis_quat = Quaternion([0, scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z])
                    
                    #f.write("\nFrame : "+str(index))
                    #Checks for actual keys on the frame... in a roundabout way.      
                    for fcu in action.fcurves:
                        #Skips if the fcurve lacks the current bone name we're working with.
                        if bone.name in fcu.data_path:
                            
                            #Frame Check.
                            for keyframe in fcu.keyframe_points:                                
                                if keyframe.co[0] == index:
                                    #Now For Location/Rotation/Scale.

                                    #keycount += 1
                                    if "location" in fcu.data_path:   
                                        #f.write("\nTranslation: "+str(trans_basis_vec))
                                        #X
                                        #if fcu.array_index == 0:
                                        #print("BINGO! A location Keyframe.")
                                        #f.write("\nTranslation: "+str(trans_basis_vec.x))

                                        #Y
                                        #if fcu.array_index == 1:
                                            #print("BINGO! A location Keyframe.")
                                            #f.write("\nTranslation: "+str(trans_basis_vec.y))                                            
                                            #keycount += 1                                        
                                        #Z
                                        if fcu.array_index == 2:
                                            if NameChecker(index, fcu, bone.name):                                                
                                                print(fcu.data_path)
                                                pt = [pt for pt in fcu.keyframe_points if pt.co[0] == index][0]
                                                InterpolationsL.append(pt.interpolation)
                                                #f.write("\nTranslation: "+str(trans_basis_vec))
                                                keycount += 1
                                                KeyedT = True
                                                
                                                if self.export_legacy == True:

                                                    FramesL.append(index)
                                                    KeysL.append(trans_basis_quat)
                                                    KeyTypesL.append("location")
                                                    FrameText = bone.name
                                                    
                                                    KeyToInsert = data(trans_basis_vec.x,trans_basis_vec.y,trans_basis_vec.z,0)
                                                    if(bone.name == "jnt_255"):
                                                        FrameText = FrameText.replace(FrameText[:4], '')
                                                        TrueKeys.append(Keyframes(index,"absoluteposition",int(FrameText),KeyToInsert))
                                                    else:
                                                        FrameText = metadata.getJointByName(FrameText)
                                                        FrameText = FrameText.id
                                                        TrueKeys.append(Keyframes(index,"localposition",int(FrameText),KeyToInsert))

                                                else:    

                                                    FramesL.append(index)
                                                    KeysL.append(trans_basis_quat)
                                                    KeyTypesL.append("location")
                                                    FrameText = bone.name                                                    
                                                    #KeyToInsert = data(trans_basis_vec.x,trans_basis_vec.y,trans_basis_vec.z,0)
                                                    
                                                    if(bone.name == "jnt_255"):
                                                        FrameText = FrameText.replace(FrameText[:4], '')
                                                        KeyToInsert = data(trans_basis_vec.x,trans_basis_vec.y,trans_basis_vec.z,0)
                                                        TrueKeys.append(Keyframes(index,"absoluteposition",int(FrameText),KeyToInsert))
                                                    else:
                                                        FrameText = metadata.getJointByName(FrameText)
                                                        FrameText = FrameText.id
                                                        NewX = -1 * trans_basis_vec.x
                                                        KeyToInsert = data(trans_basis_vec.y,NewX,trans_basis_vec.z,0)
                                                        TrueKeys.append(Keyframes(index,"localposition",int(FrameText),KeyToInsert))


                                            #gen_track(bone.name,0,bone,trans_basis_vec, index)                                                                                            
                                        
                                                                                                                                                                                
                    
                #print(bone.name)
                print(len(FramesL))
                print(FramesL)
                print(len(FramesR))
                print(FramesR)
                print(len(FramesS))
                print(FramesS)                
                #print(len(Keys))
                #print(Keys)
                #print(("\n"))
                #print(Interpolations)
                #print(len(Interpolations))
        
            for bone in reordered_pose_bones:
                
                #f.write("\n____________________________________________________________________________________________________")
                #f.write("\nBone ID: "+str(bone.name))
                print("_________________________________________________________________________\nNow Serving Bone ID: " + str(bone.name))          
                
                #Variables for holding Location, Rotational, and Scale Data.
                FramesL = []
                KeysL = []
                KeyTypesL = []
                InterpolationsL = []

                FramesR = []
                KeysR = []
                KeyTypesR = []
                InterpolationsR = []

                FramesS = []
                KeysS = []
                KeyTypesS = []
                InterpolationsS = []


                for index, _ in enumerate(range(FirstFrame, FrameCount+1)):
                    #Gets the needed values and prints them out in the console and in dump.txt.
                    trans_basis_vec = bone_name_to_location_values[bone.name][index]
                    trans_basis_quat = Quaternion([0, trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                    rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                    rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                    scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                    scale_basis_quat = Quaternion([0, scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z])
                    
                    #f.write("\nFrame : "+str(index))
                    #Checks for actual keys on the frame... in a roundabout way.      
                    for fcu in action.fcurves:
                        #Skips if the fcurve lacks the current bone name we're working with.
                        if bone.name in fcu.data_path:
                            
                            #Frame Check.
                            for keyframe in fcu.keyframe_points:                                
                                if keyframe.co[0] == index:
                                    #Now For Location/Rotation/Scale.
                                            
                                    if "scale" in fcu.data_path:                                      

                                        #f.write("\nRotation: "+str(rot_basis_quat)) 
                                        #W
                                        #if fcu.array_index == 0:
                                            #print("BINGO! A rotation Keyframe.")
                                            #f.write("\nRotation: "+str(rot_basis_quat.w))                                            
                                            #keycount += 1                                        
                                        #X
                                        #if fcu.array_index == 1:
                                            #print("BINGO! A rotation Keyframe.")
                                            #f.write("\nRotation: "+str(rot_basis_quat.x))                                               
                                            #keycount += 1                                        
                                        #Y
                                        #if fcu.array_index == 2:
                                            #print("BINGO! A rotation Keyframe.")
                                            #f.write("\nRotation: "+str(rot_basis_quat.y))                                               
                                            #keycount += 1                                        
                                        #Z
                                        if fcu.array_index == 2:
                                            if NameChecker(index, fcu, bone.name):                                                   
                                                print(fcu.data_path)
                                                pt = [pt for pt in fcu.keyframe_points if pt.co[0] == index][0]
                                                InterpolationsR.append(pt.interpolation)
                                                #f.write("\scale: "+str(rot_basis_quat))                                               
                                                keycount += 1
                                                KeyedR = True

                                                FramesR.append(index)
                                                KeysR.append(scale_basis_vec)
                                                KeyTypesR.append("scale")
                                                FrameText = bone.name
                                                if bone.name == 'jnt_255':                                                    
                                                    FrameText = FrameText.replace(FrameText[:4], '')
                                                    KeyToInsert = data(scale_basis_vec.x,scale_basis_vec.y,scale_basis_vec.z,0)
                                                else:
                                                    FrameText = metadata.getJointByName(FrameText)
                                                    FrameText = FrameText.id
                                                    KeyToInsert = data(scale_basis_vec.x,scale_basis_vec.y,scale_basis_vec.z,0)     
                                                # FrameText = FrameText.replace(FrameText[:4], '')
                                                # KeyToInsert = data(scale_basis_vec.x,scale_basis_vec.y,scale_basis_vec.z,1)
                                                if(bone.name == "jnt_255"):
                                                    TrueKeys.append(Keyframes(index,"xpto",int(FrameText),KeyToInsert))                                               
                                                else:                                           
                                                    TrueKeys.append(Keyframes(index,"localscale",int(FrameText),KeyToInsert))                                                       
                                                                                                                                                            
                                        
                                                                                                                                                                                
                    
                #print(bone.name)
                print(len(FramesL))
                print(FramesL)
                print(len(FramesR))
                print(FramesR)
                print(len(FramesS))
                print(FramesS)                
                #print(len(Keys))
                #print(Keys)
                #print(("\n"))
                #print(Interpolations)
                #print(len(Interpolations))

            for bone in reordered_pose_bones:
                
                #f.write("\n____________________________________________________________________________________________________")
                #f.write("\nBone ID: "+str(bone.name))
                print("_________________________________________________________________________\nNow Serving Bone ID: " + str(bone.name))          
                
                #Variables for holding Location, Rotational, and Scale Data.
                FramesL = []
                KeysL = []
                KeyTypesL = []
                InterpolationsL = []

                FramesR = []
                KeysR = []
                KeyTypesR = []
                InterpolationsR = []

                FramesS = []
                KeysS = []
                KeyTypesS = []
                InterpolationsS = []


                for index, _ in enumerate(range(FirstFrame, FrameCount+1)):
                    #Gets the needed values and prints them out in the console and in dump.txt.
                    trans_basis_vec = bone_name_to_location_values[bone.name][index]
                    trans_basis_quat = Quaternion([0, trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                    rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                    rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                    scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                    scale_basis_quat = Quaternion([0, scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z])
                    
                    #f.write("\nFrame : "+str(index))
                    #Checks for actual keys on the frame... in a roundabout way.      
                    for fcu in action.fcurves:
                        #Skips if the fcurve lacks the current bone name we're working with.
                        if bone.name in fcu.data_path:
                            
                            #Frame Check.
                            for keyframe in fcu.keyframe_points:                                
                                if keyframe.co[0] == index:
                                    #Now For Scale.
                                                                                                                                                                            
                                    if "rotation_quaternion" in fcu.data_path:

                                        #f.write("\nScale: "+str(scale_basis_vec))                                        
                                        #X
                                        #if fcu.array_index == 0:
                                            #print("BINGO! A scale Keyframe.")
                                            #f.write("\nScale: "+str(scale_basis_vec.x))
                                            #keycount += 1                                        
                                        #Y
                                        #if fcu.array_index == 1:
                                            #print("BINGO! A scale Keyframe.")
                                            #f.write("\nScale: "+str(scale_basis_vec.y))
                                            #keycount += 1                                        
                                        #Z
                                        if fcu.array_index == 2:
                                            if NameChecker(index, fcu, bone.name):
                                                print(fcu.data_path)
                                                pt = [pt for pt in fcu.keyframe_points if pt.co[0] == index][0]
                                                InterpolationsS.append(pt.interpolation)
                                                #f.write("\rotation_quaternion: "+str(scale_basis_vec))
                                                keycount += 1
                                                KeyedR = True

                                                if self.export_legacy == True:

                                                    FramesS.append(index)
                                                    KeysS.append(scale_basis_quat)
                                                    KeyTypesS.append("rotation_quaternion")
                                                    FrameText = bone.name

                                                    if(bone.name == "jnt_255"):
                                                        FrameText = FrameText.replace(FrameText[:4], '')
                                                        KeyToInsert = data(rot_basis_vec.x,rot_basis_vec.y,rot_basis_vec.z,rot_basis_vec.w)
                                                        TrueKeys.append(Keyframes(index,"absoluterotation",int(FrameText),KeyToInsert))     
                                                    else:
                                                        FrameText = metadata.getJointByName(FrameText)
                                                        FrameText = FrameText.id
                                                        KeyToInsert = data(rot_basis_vec.x,rot_basis_vec.y,rot_basis_vec.z,rot_basis_vec.w)
                                                        TrueKeys.append(Keyframes(index,"localrotation",int(FrameText),KeyToInsert))          

                                                else:
                                                    FramesS.append(index)
                                                    KeysS.append(scale_basis_quat)
                                                    KeyTypesS.append("rotation_quaternion")
                                                    FrameText = bone.name
                                                    
                                                    if(bone.name == "jnt_255"):
                                                        FrameText = FrameText.replace(FrameText[:4], '')
                                                        KeyToInsert = data(rot_basis_vec.x,rot_basis_vec.y,rot_basis_vec.z,rot_basis_vec.w)                                                        
                                                        TrueKeys.append(Keyframes(index,"absoluterotation",int(FrameText),KeyToInsert))     
                                                    else:
                                                        FrameText = metadata.getJointByName(FrameText)
                                                        FrameText = FrameText.id
                                                        NewX = -1 * rot_basis_vec.x
                                                        KeyToInsert = data(rot_basis_vec.y,NewX,rot_basis_vec.z,rot_basis_vec.w)
                                                        TrueKeys.append(Keyframes(index,"localrotation",int(FrameText),KeyToInsert))                                      
                                        
                                                                                                                                                                                
                    
                #print(bone.name)
                print(len(FramesL))
                print(FramesL)
                print(len(FramesR))
                print(FramesR)
                print(len(FramesS))
                print(FramesS)                
                #print(len(Keys))
                #print(Keys)
                #print(("\n"))
                #print(Interpolations)
                #print(len(Interpolations))

        else:
            #Borrowed from the Smash Uitimate animation exporter because the other methods don't get the keys I want without redundant data
            #that would bloat file size.
            
            # Create value dicts ahead of time
            bone_name_to_location_values: dict[str, list[Location]] = {}
            bone_name_to_rotation_values: dict[str, list[Rotation]] = {}
            bone_name_to_scale_values: dict[str, list[Scale]] = {}
            bone_to_rel_matrix_local = {}
            reordered_pose_bones = get_heirarchy_order(list(obj.pose.bones))
            
            # Fill value dicts with default values. Not every bone will be animated, so for these the default values of a matrix basis will be needed
            for pose_bone in reordered_pose_bones:
                bone_name_to_location_values[pose_bone.name] = [Location(0.0, 0.0, 0.0) for _ in range(FirstFrame, FrameCount + 1)]
                bone_name_to_rotation_values[pose_bone.name] = [Rotation(1.0, 0.0, 0.0, 0.0) for _ in range(FirstFrame, FrameCount + 1)]
                bone_name_to_scale_values[pose_bone.name] = [Scale(1.0, 1.0, 1.0) for _ in range(FirstFrame, FrameCount + 1)]
                if pose_bone.parent: # non-root bones
                    bone_to_rel_matrix_local[pose_bone] = pose_bone.parent.bone.matrix_local.inverted() @ pose_bone.bone.matrix_local
                else: # root bones
                    bone_to_rel_matrix_local[pose_bone] = pose_bone.bone.matrix_local
            
            # Go through the pose bones' fcurves and store all the values at each frame.
            animated_pose_bones: set[bpy.types.PoseBone] = set()
            
            keycount = 0
            tracks = []

            for fcurve in obj.animation_data.action.fcurves:
                regex = r'pose\.bones\[\"(.*)\"\]\.(.*)'
                matches = re.match(regex, fcurve.data_path)
                if matches is None: # A fcurve in the action that isn't a bone transform, such as the user keyframing the Armature Object itself.
                    print("The fcurve with data path", fcurve.data_path,  "\nis not going to be exported because it's not matching bone fcurve patterns.")
                    continue
                if len(matches.groups()) != 2: # TODO: Is this possible?
                    print("The fcurve with data path", fcurve.data_path,  "\nis not going to be exported because it's not fully matching bone fcurve patterns.")
                    continue
                bone_name = matches.groups()[0]
                transform_subtype = matches.groups()[1]
                if transform_subtype == 'location':
                    for index, frame in enumerate(range(FirstFrame, FrameCount+1)):
                        if fcurve.array_index == 0:
                            bone_name_to_location_values[bone_name][index].x = fcurve.evaluate(frame)
                        elif fcurve.array_index == 1:
                            bone_name_to_location_values[bone_name][index].y = fcurve.evaluate(frame)
                        elif fcurve.array_index == 2:
                            bone_name_to_location_values[bone_name][index].z = fcurve.evaluate(frame)
                elif transform_subtype == 'rotation_quaternion':
                    for index, frame in enumerate(range(FirstFrame, FrameCount+1)):
                        if fcurve.array_index == 0:
                            bone_name_to_rotation_values[bone_name][index].w = fcurve.evaluate(frame)
                        elif fcurve.array_index == 1:
                            bone_name_to_rotation_values[bone_name][index].x = fcurve.evaluate(frame)
                        elif fcurve.array_index == 2:
                            bone_name_to_rotation_values[bone_name][index].y = fcurve.evaluate(frame)
                        elif fcurve.array_index == 3:
                            bone_name_to_rotation_values[bone_name][index].z = fcurve.evaluate(frame)
                elif transform_subtype == 'scale':
                    for index, frame in enumerate(range(FirstFrame, FrameCount+1)):
                        if fcurve.array_index == 0:
                            bone_name_to_scale_values[bone_name][index].x = fcurve.evaluate(frame)
                        elif fcurve.array_index == 1:
                            bone_name_to_scale_values[bone_name][index].y = fcurve.evaluate(frame)
                        elif fcurve.array_index == 2:
                            bone_name_to_scale_values[bone_name][index].z = fcurve.evaluate(frame)
                animated_pose_bone = obj.pose.bones.get(bone_name)
                if animated_pose_bone is not None:
                    animated_pose_bones.add(animated_pose_bone)
                    
            bone_to_world_matrix = {}
            '''
            sorted_fcurves = {}
            for i in bpy.data.actions:
                print (i.name)
                for fcu in i.fcurves:
                    print (fcu)
                    for keyframe in fcu.keyframe_points:
                        x, y = keyframe.co
                        print (x,y)
            '''
            #action = bpy.data.actions["ArmatureAction"]
            action = obj.animation_data.action
                                                    
        #with open('C:\\dump.txt', 'w') as f:
            for bone in reordered_pose_bones:
                
                #f.write("\n____________________________________________________________________________________________________")
                #f.write("\nBone ID: "+str(bone.name))
                print("_________________________________________________________________________\nNow Serving Bone ID: " + str(bone.name))          
                
                #Variables for holding Location, Rotational, and Scale Data.
                FramesL = []
                KeysL = []
                KeyTypesL = []
                InterpolationsL = []

                FramesR = []
                KeysR = []
                KeyTypesR = []
                InterpolationsR = []

                FramesS = []
                KeysS = []
                KeyTypesS = []
                InterpolationsS = []


                for index, _ in enumerate(range(FirstFrame, FrameCount+1)):
                    #Gets the needed values and prints them out in the console and in dump.txt.
                    trans_basis_vec = bone_name_to_location_values[bone.name][index]
                    trans_basis_quat = Quaternion([0, trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                    rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                    rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                    scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                    scale_basis_quat = Quaternion([0, scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z])
                    
                    #f.write("\nFrame : "+str(index))
                    #Checks for actual keys on the frame... in a roundabout way.      
                    for fcu in action.fcurves:
                        #Skips if the fcurve lacks the current bone name we're working with.
                        if bone.name in fcu.data_path:
                            
                            #Frame Check.
                            for keyframe in fcu.keyframe_points:                                
                                if keyframe.co[0] == index:
                                    #Now For Location/Rotation/Scale.

                                    #keycount += 1
                                    if "location" in fcu.data_path:   
                                        #f.write("\nTranslation: "+str(trans_basis_vec))
                                        #X
                                        #if fcu.array_index == 0:
                                        #print("BINGO! A location Keyframe.")
                                        #f.write("\nTranslation: "+str(trans_basis_vec.x))

                                        #Y
                                        #if fcu.array_index == 1:
                                            #print("BINGO! A location Keyframe.")
                                            #f.write("\nTranslation: "+str(trans_basis_vec.y))                                            
                                            #keycount += 1                                        
                                        #Z
                                        if fcu.array_index == 2:
                                            if NameChecker(index, fcu, bone.name):                                                
                                                print(fcu.data_path)
                                                pt = [pt for pt in fcu.keyframe_points if pt.co[0] == index][0]
                                                InterpolationsL.append(pt.interpolation)
                                                #f.write("\nTranslation: "+str(trans_basis_vec))
                                                keycount += 1
                                                KeyedT = True
                                                
                                                if self.export_legacy == True:

                                                    FramesL.append(index)
                                                    KeysL.append(trans_basis_quat)
                                                    KeyTypesL.append("location")
                                                    FrameText = bone.name
                                                    FrameText = FrameText.replace(FrameText[:4], '')
                                                    KeyToInsert = data(trans_basis_vec.x,trans_basis_vec.y,trans_basis_vec.z,0)
                                                    if(bone.name == "jnt_255"):
                                                        TrueKeys.append(Keyframes(index,"absoluteposition",int(FrameText),KeyToInsert))
                                                    else:
                                                        TrueKeys.append(Keyframes(index,"localposition",int(FrameText),KeyToInsert))

                                                else:    

                                                    FramesL.append(index)
                                                    KeysL.append(trans_basis_quat)
                                                    KeyTypesL.append("location")
                                                    FrameText = bone.name
                                                    FrameText = FrameText.replace(FrameText[:4], '')
                                                    #KeyToInsert = data(trans_basis_vec.x,trans_basis_vec.y,trans_basis_vec.z,0)

                                                    if(bone.name == "jnt_255"):
                                                        KeyToInsert = data(trans_basis_vec.x,trans_basis_vec.y,trans_basis_vec.z,0)
                                                        TrueKeys.append(Keyframes(index,"absoluteposition",int(FrameText),KeyToInsert))
                                                    else:
                                                        NewX = -1 * trans_basis_vec.x
                                                        KeyToInsert = data(trans_basis_vec.y,NewX,trans_basis_vec.z,0)
                                                        TrueKeys.append(Keyframes(index,"localposition",int(FrameText),KeyToInsert))


                                            #gen_track(bone.name,0,bone,trans_basis_vec, index)                                                                                            
                                        
                                                                                                                                                                                
                    
                #print(bone.name)
                print(len(FramesL))
                print(FramesL)
                print(len(FramesR))
                print(FramesR)
                print(len(FramesS))
                print(FramesS)                
                #print(len(Keys))
                #print(Keys)
                #print(("\n"))
                #print(Interpolations)
                #print(len(Interpolations))
        
            for bone in reordered_pose_bones:
                
                #f.write("\n____________________________________________________________________________________________________")
                #f.write("\nBone ID: "+str(bone.name))
                print("_________________________________________________________________________\nNow Serving Bone ID: " + str(bone.name))          
                
                #Variables for holding Location, Rotational, and Scale Data.
                FramesL = []
                KeysL = []
                KeyTypesL = []
                InterpolationsL = []

                FramesR = []
                KeysR = []
                KeyTypesR = []
                InterpolationsR = []

                FramesS = []
                KeysS = []
                KeyTypesS = []
                InterpolationsS = []


                for index, _ in enumerate(range(FirstFrame, FrameCount+1)):
                    #Gets the needed values and prints them out in the console and in dump.txt.
                    trans_basis_vec = bone_name_to_location_values[bone.name][index]
                    trans_basis_quat = Quaternion([0, trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                    rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                    rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                    scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                    scale_basis_quat = Quaternion([0, scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z])
                    
                    #f.write("\nFrame : "+str(index))
                    #Checks for actual keys on the frame... in a roundabout way.      
                    for fcu in action.fcurves:
                        #Skips if the fcurve lacks the current bone name we're working with.
                        if bone.name in fcu.data_path:
                            
                            #Frame Check.
                            for keyframe in fcu.keyframe_points:                                
                                if keyframe.co[0] == index:
                                    #Now For Location/Rotation/Scale.
                                            
                                    if "scale" in fcu.data_path:                                      

                                        #f.write("\nRotation: "+str(rot_basis_quat)) 
                                        #W
                                        #if fcu.array_index == 0:
                                            #print("BINGO! A rotation Keyframe.")
                                            #f.write("\nRotation: "+str(rot_basis_quat.w))                                            
                                            #keycount += 1                                        
                                        #X
                                        #if fcu.array_index == 1:
                                            #print("BINGO! A rotation Keyframe.")
                                            #f.write("\nRotation: "+str(rot_basis_quat.x))                                               
                                            #keycount += 1                                        
                                        #Y
                                        #if fcu.array_index == 2:
                                            #print("BINGO! A rotation Keyframe.")
                                            #f.write("\nRotation: "+str(rot_basis_quat.y))                                               
                                            #keycount += 1                                        
                                        #Z
                                        if fcu.array_index == 2:
                                            if NameChecker(index, fcu, bone.name):                                                   
                                                print(fcu.data_path)
                                                pt = [pt for pt in fcu.keyframe_points if pt.co[0] == index][0]
                                                InterpolationsR.append(pt.interpolation)
                                                #f.write("\scale: "+str(rot_basis_quat))                                               
                                                keycount += 1
                                                KeyedR = True

                                                FramesR.append(index)
                                                KeysR.append(scale_basis_vec)
                                                KeyTypesR.append("scale")
                                                FrameText = bone.name
                                                FrameText = FrameText.replace(FrameText[:4], '')
                                                KeyToInsert = data(scale_basis_vec.x,scale_basis_vec.y,scale_basis_vec.z,1)
                                                if(bone.name == "jnt_255"):
                                                    TrueKeys.append(Keyframes(index,"xpto",int(FrameText),KeyToInsert))                                               
                                                else:                                           
                                                    TrueKeys.append(Keyframes(index,"localscale",int(FrameText),KeyToInsert))                                                       
                                                                                                                                                            
                                        
                                                                                                                                                                                
                    
                #print(bone.name)
                print(len(FramesL))
                print(FramesL)
                print(len(FramesR))
                print(FramesR)
                print(len(FramesS))
                print(FramesS)                
                #print(len(Keys))
                #print(Keys)
                #print(("\n"))
                #print(Interpolations)
                #print(len(Interpolations))

            for bone in reordered_pose_bones:
                
                #f.write("\n____________________________________________________________________________________________________")
                #f.write("\nBone ID: "+str(bone.name))
                print("_________________________________________________________________________\nNow Serving Bone ID: " + str(bone.name))          
                
                #Variables for holding Location, Rotational, and Scale Data.
                FramesL = []
                KeysL = []
                KeyTypesL = []
                InterpolationsL = []

                FramesR = []
                KeysR = []
                KeyTypesR = []
                InterpolationsR = []

                FramesS = []
                KeysS = []
                KeyTypesS = []
                InterpolationsS = []


                for index, _ in enumerate(range(FirstFrame, FrameCount+1)):
                    #Gets the needed values and prints them out in the console and in dump.txt.
                    trans_basis_vec = bone_name_to_location_values[bone.name][index]
                    trans_basis_quat = Quaternion([0, trans_basis_vec.x, trans_basis_vec.y, trans_basis_vec.z])
                    rot_basis_vec = bone_name_to_rotation_values[bone.name][index]
                    rot_basis_quat = Quaternion([rot_basis_vec.w, rot_basis_vec.x, rot_basis_vec.y, rot_basis_vec.z])
                    scale_basis_vec = bone_name_to_scale_values[bone.name][index]
                    scale_basis_quat = Quaternion([0, scale_basis_vec.x, scale_basis_vec.y, scale_basis_vec.z])
                    
                    #f.write("\nFrame : "+str(index))
                    #Checks for actual keys on the frame... in a roundabout way.      
                    for fcu in action.fcurves:
                        #Skips if the fcurve lacks the current bone name we're working with.
                        if bone.name in fcu.data_path:
                            
                            #Frame Check.
                            for keyframe in fcu.keyframe_points:                                
                                if keyframe.co[0] == index:
                                    #Now For Scale.
                                                                                                                                                                            
                                    if "rotation_quaternion" in fcu.data_path:

                                        #f.write("\nScale: "+str(scale_basis_vec))                                        
                                        #X
                                        #if fcu.array_index == 0:
                                            #print("BINGO! A scale Keyframe.")
                                            #f.write("\nScale: "+str(scale_basis_vec.x))
                                            #keycount += 1                                        
                                        #Y
                                        #if fcu.array_index == 1:
                                            #print("BINGO! A scale Keyframe.")
                                            #f.write("\nScale: "+str(scale_basis_vec.y))
                                            #keycount += 1                                        
                                        #Z
                                        if fcu.array_index == 2:
                                            if NameChecker(index, fcu, bone.name):
                                                print(fcu.data_path)
                                                pt = [pt for pt in fcu.keyframe_points if pt.co[0] == index][0]
                                                InterpolationsS.append(pt.interpolation)
                                                #f.write("\rotation_quaternion: "+str(scale_basis_vec))
                                                keycount += 1
                                                KeyedR = True

                                                if self.export_legacy == True:

                                                    FramesS.append(index)
                                                    KeysS.append(scale_basis_quat)
                                                    KeyTypesS.append("rotation_quaternion")
                                                    FrameText = bone.name
                                                    FrameText = FrameText.replace(FrameText[:4], '')
                                                    KeyToInsert = data(rot_basis_vec.x,rot_basis_vec.y,rot_basis_vec.z,rot_basis_vec.w)
                                                    if(bone.name == "jnt_255"):
                                                        TrueKeys.append(Keyframes(index,"absoluterotation",int(FrameText),KeyToInsert))     
                                                    else:
                                                        TrueKeys.append(Keyframes(index,"localrotation",int(FrameText),KeyToInsert))          

                                                else:
                                                    FramesS.append(index)
                                                    KeysS.append(scale_basis_quat)
                                                    KeyTypesS.append("rotation_quaternion")
                                                    FrameText = bone.name
                                                    FrameText = FrameText.replace(FrameText[:4], '')
                                                    if(bone.name == "jnt_255"):
                                                        KeyToInsert = data(rot_basis_vec.x,rot_basis_vec.y,rot_basis_vec.z,rot_basis_vec.w)

                                                        TrueKeys.append(Keyframes(index,"absoluterotation",int(FrameText),KeyToInsert))     
                                                    else:
                                                        NewX = -1 * rot_basis_vec.x
                                                        KeyToInsert = data(rot_basis_vec.y,NewX,rot_basis_vec.z,rot_basis_vec.w)
                                                        TrueKeys.append(Keyframes(index,"localrotation",int(FrameText),KeyToInsert))     
                                                                                                                                                                                
                    
                #print(bone.name)
                print(len(FramesL))
                print(FramesL)
                print(len(FramesR))
                print(FramesR)
                print(len(FramesS))
                print(FramesS)                
                #print(len(Keys))
                #print(Keys)
                #print(("\n"))
                #print(Interpolations)
                #print(len(Interpolations))

    
    
    #f.close()        
        
        #Prints stuff out to check.
        print(str(keycount))
        bpy.context.scene.frame_set(0)

        FinalAnim = LMTM3AEntry(1,"AnimDataID0",FrameCount,read_LoopFrame,TrueKeys)
        yaml.emitter.Emitter.process_tag = lambda self, *args, **kw: None
        stream = open(filepath,'w')
        yaml.dump(FinalAnim,stream,sort_keys=False)

        #Adds in important tag.
        GoodTag = "!LMTM3AEntry\n"
        f = open(filepath,'r+')
        lines = f.readlines() # read old content
        f.seek(0) # go back to the beginning of the file
        f.write(GoodTag) # write new content at the beginning
        for line in lines: # write old content after new
            f.write(line)
        f.close()




    except Exception as e:
        print("An error occured.",e, "\n", traceback.format_exc())  

#Parts of the code based on the Smash Ultimate Blender Animation Importer.
class SUB_PT_Anim_Export(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'    
    bl_category = 'MT Framework'
    bl_label = 'Animation Exporter'
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
            row.label(text="Select an Armature first.")
        elif obj.select_get() is False:
            row.label(text="Select an Armature first.")   
        elif obj.type == 'ARMATURE':
            row.prop(mip, 'anim_export_metadata_file')
            row = layout.row(align=True)
            row.operator(SUB_PT_MOD_OT_Choose_Anim_Export_Metadata_YML.bl_idname,icon='IMPORT',text= 'Choose metadata .yml file')
            layout.separator()
            row = layout.row(align=True)
            row.operator(SUB_OP_anim_export.bl_idname, icon='IMPORT', text='Export Marvel 3 .yml Animation')
            
class SUB_OP_anim_export(Operator, ExportHelper):
    bl_idname = 'sub.export_anim'
    bl_label = 'Export Anim'
    filename_ext = ".yml"
    filter_glob: StringProperty(
        default='*.yml',
        options={'HIDDEN'}
    )
    export_legacy: BoolProperty(
        name='From Marvel 3 FBX Model',
        description='Exports in a way that is compatible with the FBX Collection',
        default=False,
    )
    export_use_metadata_anim: BoolProperty(
        name='Use Metadata File',
        description='Exports Animation on a Model with Metadata names. For Custom Characters, generally better to remain False/Unchecked',
        default=False,
    )    
    export_type_b: BoolProperty(
        name='Type B',
        description='For Later use. If unsure, leave False/Unchecked',
        default=False,
    )

    read_LoopFrame: bpy.props.IntProperty(
        name = "Loop Frame",
        description="The frame to loop the animation. Set to -1 to not loop it, as most animations have this set to -1",
        default=-1,
    )

    @classmethod
    def poll(cls, context):
        obj: bpy.types.Object = context.object
        if obj is None:
            return False
        elif obj.type != 'ARMATURE':
            return False
        return True
    
    def invoke(self, context, _event):
        self.first_blender_frame = context.scene.frame_start
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        keywords = self.as_keywords(ignore=("filter_glob","files"))
        time_start = time.time()
        WriteM3AanimationData(context, self.filepath, self.read_LoopFrame, self)
        context.view_layer.update()
        print("Script is Done.")
        ShowMessageBox("Script is Done.", "Notice")
        return {'FINISHED'}

class SUB_PT_MOD_OT_Choose_Anim_Export_Metadata_YML(bpy.types.Operator, ImportHelper):
    """Choose which Metadata YML to Use"""
    bl_idname = "sub.mod_ot_choose_anim_export_metadata_yml"
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
        mip.anim_export_metadata_file = self.filepath
        return {'FINISHED'}