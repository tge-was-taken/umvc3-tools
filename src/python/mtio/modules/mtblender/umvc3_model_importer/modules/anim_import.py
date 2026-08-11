import os
import os.path
import bpy
import mathutils
import re
import collections
import time
import math
import traceback
import subprocess
import yaml
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

def loadMetadata( self, path ):
    metadata = ModelMetadata()
    if os.path.exists( path ):
        #self.logger.info(f'loading metadata file from {path}')
        metadata.loadFile( path )
    return metadata

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

def ApplyTheTrack(Track, obj, joint, jointEdit, AnimName, import_legacy, usingmetadata, type_b, ArmName):
    
    Frame = 0
    Bone = Track[0]['BoneID']
    
    if usingmetadata == True:
        if bpy.data.objects[ArmName].data.bones.get(joint.name) is None:
            return
        
        for ID, Keyframe in enumerate(Track):
    
            if import_legacy == True:
                    
                if(Track[0]['TrackType'] == "localscale" or Track[0]['TrackType'] == "xpto"):
                    print("A scale Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[joint.name]
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.scale = (float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                        #print(joint.scale)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (joint.name, "scale"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying scalar keyframe.",sc, "\n", traceback.format_exc())
                        continue          
            
                if(Track[0]['TrackType'] == "localposition" or Track[0]['TrackType'] == "absoluteposition"):
                    print("A Translation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[joint.name]
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.location = (float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                        print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (joint.name, "location"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying translation keyframe.",sc, "\n", traceback.format_exc())
                        continue              
                    
                if(Track[0]['TrackType'] == "localrotation" or Track[0]['TrackType'] == "absoluterotation"):
                    print("A Rotation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[joint.name]
                    print(str(joint))
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        Thing = mathutils.Quaternion((float(Keyframe['data']['W']), float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z'])))
                        print(Thing)                                                
                        joint.rotation_quaternion = Thing
                        print(joint.rotation_quaternion)
                        
                        #print(obj.pose.bones[0].rotation_mode)
                        
                        obj.keyframe_insert(data_path=joint.path_from_id("rotation_quaternion"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying rotational keyframe.",sc, "\n", traceback.format_exc())
                        continue

            else:
                    
                if(Track[0]['TrackType'] == "localscale" or Track[0]['TrackType'] == "xpto"):
                    print("A scale Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[joint.name]
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.scale = (float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                        #print(joint.scale)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (joint.name, "scale"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying scalar keyframe.",sc, "\n", traceback.format_exc())
                        continue          
            
                if(Track[0]['TrackType'] == "localposition" or Track[0]['TrackType'] == "absoluteposition"):
                    print("A Translation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[joint.name]
                    #Do Stuff here.
                    try:

                        if joint.name == 'jnt_255':

                            Frame = int(Keyframe['Frame'])
                            joint.location = ((float(Keyframe['data']['X'])), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                            print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                            
                            obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                            (joint.name, "location"), frame=(Frame), group=AnimName)
                        
                        else:

                            Frame = int(Keyframe['Frame'])
                            joint.location = (-(float(Keyframe['data']['Y'])), float(Keyframe['data']['X']), float(Keyframe['data']['Z']))
                            print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                            
                            obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                            (joint.name, "location"), frame=(Frame), group=AnimName)
                                            
                    except Exception as sc:
                        print("Problem applying translation keyframe.",sc, "\n", traceback.format_exc())
                        continue              
                    
                if(Track[0]['TrackType'] == "localrotation" or Track[0]['TrackType'] == "absoluterotation"):
                    print("A Rotation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[joint.name]
                    print(str(joint))
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        Thing = mathutils.Quaternion((float(Keyframe['data']['W']), -(float(Keyframe['data']['Y'])), float(Keyframe['data']['X']), float(Keyframe['data']['Z'])))
                        print(Thing)                                                
                        joint.rotation_quaternion = Thing
                        print(joint.rotation_quaternion)
                        
                        #print(obj.pose.bones[0].rotation_mode)
                        
                        obj.keyframe_insert(data_path=joint.path_from_id("rotation_quaternion"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying rotational keyframe.",sc, "\n", traceback.format_exc())
                        continue

    else:
        #Checks if the bone exists on the Armature in the scene and will skip if it doesn't.
        if bpy.data.objects[ArmName].data.bones.get(f'jnt_{Bone}') is None:
            return
    
        for ID, Keyframe in enumerate(Track):
        
            if import_legacy == True:
                    
                if(Track[0]['TrackType'] == "localscale" or Track[0]['TrackType'] == "xpto"):
                    print("A scale Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.scale = (float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                        #print(joint.scale)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (f'jnt_{Bone}', "scale"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying scalar keyframe.",sc, "\n", traceback.format_exc())
                        continue          
            
                if(Track[0]['TrackType'] == "localposition" or Track[0]['TrackType'] == "absoluteposition"):
                    print("A Translation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.location = (float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                        print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (f'jnt_{Bone}', "location"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying translation keyframe.",sc, "\n", traceback.format_exc())
                        continue              
                    
                if(Track[0]['TrackType'] == "localrotation" or Track[0]['TrackType'] == "absoluterotation"):
                    print("A Rotation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    print(str(joint))
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        Thing = mathutils.Quaternion((float(Keyframe['data']['W']), float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z'])))
                        print(Thing)                                                
                        joint.rotation_quaternion = Thing
                        print(joint.rotation_quaternion)
                        
                        #print(obj.pose.bones[0].rotation_mode)
                        
                        obj.keyframe_insert(data_path=joint.path_from_id("rotation_quaternion"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying rotational keyframe.",sc, "\n", traceback.format_exc())
                        continue

                if type(Track[0]['TrackType']) is int:
                    print("jnt_" + str(joint) + " has a weird tracktype that isn't documented: "+ str(Track[0]['TrackType']) +" so this keyframe is getting skipped.")

            elif type_b == True:

                if(Track[0]['TrackType'] == "localscale" or Track[0]['TrackType'] == "xpto"):
                    print("A scale Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.scale = (float(Keyframe['data']['Z']), float(Keyframe['data']['Y']), float(Keyframe['data']['X']))
                        #print(joint.scale)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (f'jnt_{Bone}', "scale"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying scalar keyframe.",sc, "\n", traceback.format_exc())
                        continue          
            
                if(Track[0]['TrackType'] == "localposition" or Track[0]['TrackType'] == "absoluteposition"):
                    print("A Translation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    #Do Stuff here.
                    try:
                        if joint.name == 'jnt_255':

                            Frame = int(Keyframe['Frame'])
                            joint.location = ((float(Keyframe['data']['X'])), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                            print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                            
                            obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                            (joint.name, "location"), frame=(Frame), group=AnimName)
                        
                        else:

                            Frame = int(Keyframe['Frame'])
                            joint.location = ((float(Keyframe['data']['Z'])), -(float(Keyframe['data']['Y'])), float(Keyframe['data']['X']))
                            print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                            
                            obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                            (joint.name, "location"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying translation keyframe.",sc, "\n", traceback.format_exc())
                        continue              
                    
                if(Track[0]['TrackType'] == "localrotation" or Track[0]['TrackType'] == "absoluterotation"):
                    print("A Rotation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    print(str(joint))
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        Thing = mathutils.Quaternion((float(Keyframe['data']['Z']), (float(Keyframe['data']['Y'])), float(Keyframe['data']['W']), float(Keyframe['data']['X'])))
                        print(Thing)                                                
                        joint.rotation_quaternion = Thing
                        print(joint.rotation_quaternion)
                        
                        #print(obj.pose.bones[0].rotation_mode)
                        
                        obj.keyframe_insert(data_path=joint.path_from_id("rotation_quaternion"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying rotational keyframe.",sc, "\n", traceback.format_exc())
                        continue

                if type(Track[0]['TrackType']) is int:
                    print("jnt_" + str(joint) + " has a weird tracktype that isn't documented: "+ str(Track[0]['TrackType']) +" so this keyframe is getting skipped.")

            else:
                    
                if(Track[0]['TrackType'] == "localscale" or Track[0]['TrackType'] == "xpto"):
                    print("A scale Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        joint.scale = (float(Keyframe['data']['X']), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                        #print(joint.scale)
                        
                        obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                        (f'jnt_{Bone}', "scale"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying scalar keyframe.",sc, "\n", traceback.format_exc())
                        continue          
            
                if(Track[0]['TrackType'] == "localposition" or Track[0]['TrackType'] == "absoluteposition"):
                    print("A Translation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    #Do Stuff here.
                    try:
                        if joint.name == 'jnt_255':

                            Frame = int(Keyframe['Frame'])
                            joint.location = ((float(Keyframe['data']['X'])), float(Keyframe['data']['Y']), float(Keyframe['data']['Z']))
                            print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                            
                            obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                            (joint.name, "location"), frame=(Frame), group=AnimName)
                        
                        else:

                            Frame = int(Keyframe['Frame'])
                            joint.location = (-(float(Keyframe['data']['Y'])), float(Keyframe['data']['X']), float(Keyframe['data']['Z']))
                            print("Bone: ", joint.name ,"Translation Keyframe: ",joint.location)
                            
                            obj.keyframe_insert(data_path='pose.bones["%s"].%s' %
                                            (joint.name, "location"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying translation keyframe.",sc, "\n", traceback.format_exc())
                        continue              
                    
                if(Track[0]['TrackType'] == "localrotation" or Track[0]['TrackType'] == "absoluterotation"):
                    print("A Rotation Track.")
                    obj = bpy.data.objects[ArmName]
                    joint = obj.pose.bones[f'jnt_{Bone}']
                    print(str(joint))
                    #Do Stuff here.
                    try:
                        Frame = int(Keyframe['Frame'])
                        Thing = mathutils.Quaternion((float(Keyframe['data']['W']), -(float(Keyframe['data']['Y'])), float(Keyframe['data']['X']), float(Keyframe['data']['Z'])))
                        print(Thing)                                                
                        joint.rotation_quaternion = Thing
                        print(joint.rotation_quaternion)
                        
                        #print(obj.pose.bones[0].rotation_mode)
                        
                        obj.keyframe_insert(data_path=joint.path_from_id("rotation_quaternion"), frame=(Frame), group=AnimName)
                        
                                            
                    except Exception as sc:
                        print("Problem applying rotational keyframe.",sc, "\n", traceback.format_exc())
                        continue

                if type(Track[0]['TrackType']) is int:
                    print("jnt_" + str(joint) + " has a weird tracktype that isn't documented: "+ str(Track[0]['TrackType']) +" so this keyframe is getting skipped.")

def readM3AanimationData(self,context,filepath):
    global AnimName; AnimName = ""
    GroupCount = 0
    global FrameCount; FrameCount = 0
    NodeCount = 0
    global AnimGroups; AnimGroups = {}
    keycount = 0
    os.system('cls')
    PrevBoneID = -1
    print(self.files); print(filepath)
    
    #Stores the object selected.
    obj = bpy.context.active_object

    #Changes the blender mode to Pose Mode.
    bpy.ops.object.mode_set(mode = 'POSE', toggle=False)    
        
    #This block forces ALL bones to use quaternion rotation & sets each bone to the Identity Matrix.
    for bone in obj.pose.bones:
        bone.matrix_basis.identity()
        bone.rotation_mode = 'QUATERNION'
    SelObj = bpy.context.selected_objects
    ArmName = (SelObj[(len((bpy.context.selected_objects))- 1)].name)
    bpy.data.objects[ArmName].rotation_mode = 'QUATERNION'
    #bpy.data.objects["Armature"].rotation_mode = 'QUATERNION'
    
    for AnimYAML in self.files:
        AnimYAMLPath = os.path.join(os.path.dirname(filepath), AnimYAML.name)
        if os.path.isfile(AnimYAMLPath):
            AnimName = os.path.basename(AnimYAMLPath)
            try:
                obj.animation_data.action
            except:
                obj.animation_data_create()

            action = bpy.data.actions.new(AnimName)
            obj.animation_data.action = action
            if self.save_fake_users is True:
                action.use_fake_user = True


            try:
                #Opens the yml and deserializes.
                data_loaded = yaml.load(open(AnimYAMLPath, "rb"), Loader=get_loader())
                
                print(data_loaded.version)
                print(data_loaded.Name)
                print(data_loaded.FrameCount)
                print(data_loaded.LoopFrame)
                keycount = 0
                counter = 0
                
                #Adjust the animation timeline to fit the animation and set the current frame to zero.
                #Gets The Current Scene.
                RScene = bpy.context.scene

                RScene.frame_start = 0
                context.scene.frame_start = 0

                RScene.frame_end = data_loaded.FrameCount
                context.scene.frame_end = data_loaded.FrameCount
                bpy.context.scene.frame_set(0)
                
                ATure = bpy.data.objects[ArmName]
                pose_bones = ATure.pose.bones
                NewJointName = ""
                for x in range(len(pose_bones)):
                    print(pose_bones[x])
                    
                
                #for idx, data_loaded.KeyFrames in enumerate(data_loaded.Keyframes):
                        #if data_loaded.KeyFrames[idx]['BoneID'] == 255:
                            #continue
                
                
                #Checks if the bone exists on the Armature in the scene and will skip if it doesn't.
                #if bpy.data.objects["Armature"].data.bones.get(f'jnt_{BID}') is None:
                    #contnniue
                
                mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

                if mip.anim_import_withmetadata == True and mip.anim_metadata_file != "":
                    #This part applies it to the scene, but to Metadata bones.
                    Track = []
                    for id, Keyframe in enumerate(data_loaded.KeyFrames):
                        
                        BID = data_loaded.KeyFrames[id]['BoneID']

                        if BID == 255:
                            jointName = "jnt_255"
                        else:
                            #Gets The metadata name of the bone.
                            metadata = loadMetadata( self,mip.anim_metadata_file )
                            jointName = metadata.getJointName( BID )

                        #Checks if the bone exists on the Armature in the scene and will skip if it doesn't.
                        if bpy.data.objects[ArmName].data.bones.get(jointName) is None:
                            continue

                        #Selects the bone and deselects everything else.
                        bpy.context.active_object.select_set(False)
                        for obj in bpy.context.selected_objects:
                            bpy.context.view_layer.objects.active = obj

                        obj = bpy.data.objects[ArmName]
                        joint = obj.pose.bones[jointName]
                        jointEdit = bpy.data.armatures[ArmName].bones[jointName].matrix

                        #If the animation range is lower than the current frame, expand the animation range to accomodate.
                        if int(RScene.frame_end < data_loaded.FrameCount):
                            RScene.frame_end = data_loaded.FrameCount
                        
                        print(Keyframe['BoneID'])
                        if (id != 0):
                            #Thing.
                            if(Keyframe['BoneID'] != PrevBoneID or Keyframe['TrackType'] != PrevTrackType):
                                #Apply Stuff here.
                                                        
                                #Go To function when Track is used to apply all keyframes to specified bone.
                                ApplyTheTrack(Track, obj, joint, jointEdit, AnimName, self.import_legacy, mip.anim_import_withmetadata, self.type_b, ArmName)
                                    
                                #Then we empty the Track.
                                del Track[:]
                                    
                                #Then continue as usual.
                                Track.append(Keyframe)
                                PrevTrackType = Keyframe['TrackType']
                                PrevBoneID = Keyframe['BoneID']
                        
                            else:      
                                Track.append(Keyframe)
                                PrevTrackType = Keyframe['TrackType']
                                PrevBoneID = Keyframe['BoneID']
                
                        else:
                            Track.append(Keyframe)    
                            PrevTrackType = Keyframe['TrackType']
                            PrevBoneID = Keyframe['BoneID']
                else:    
                    Track = []
                    #This part applies it to the scene.
                    for id, Keyframe in enumerate(data_loaded.KeyFrames):
                        
                        BID = data_loaded.KeyFrames[id]['BoneID']

                        #Checks if the bone exists on the Armature in the scene and will skip if it doesn't.
                        if bpy.data.objects[ArmName].data.bones.get(f'jnt_{BID}') is None:

                            #Then we empty the Track.
                            del Track[:]
                                    
                            #Then continue as usual.
                            Track.append(Keyframe)
                            PrevTrackType = Keyframe['TrackType']
                            PrevBoneID = Keyframe['BoneID']

                            continue

                        #Selects the bone and deselects everything else.
                        bpy.context.active_object.select_set(False)
                        for obj in bpy.context.selected_objects:
                            bpy.context.view_layer.objects.active = obj

                        obj = bpy.data.objects[ArmName]
                        joint = obj.pose.bones[f'jnt_{BID}']
                        jointEdit = bpy.data.armatures[ArmName].bones[f'jnt_{BID}'].matrix

                        #If the animation range is lower than the current frame, expand the animation range to accomodate.
                        if int(RScene.frame_end < data_loaded.FrameCount):
                            RScene.frame_end = data_loaded.FrameCount
                        
                        print(Keyframe['BoneID'])
                        if (id != 0):
                            #Thing.
                            if(Keyframe['BoneID'] != PrevBoneID or Keyframe['TrackType'] != PrevTrackType):
                                #Apply Stuff here.
                                                        
                                #Go To function when Track is used to apply all keyframes to specified bone.
                                ApplyTheTrack(Track, obj, joint, jointEdit, AnimName, self.import_legacy, mip.anim_import_withmetadata, self.type_b, ArmName)
                                    
                                #Then we empty the Track.
                                del Track[:]
                                    
                                #Then continue as usual.
                                Track.append(Keyframe)
                                PrevTrackType = Keyframe['TrackType']
                                PrevBoneID = Keyframe['BoneID']
                        
                            else:      
                                Track.append(Keyframe)
                                PrevTrackType = Keyframe['TrackType']
                                PrevBoneID = Keyframe['BoneID']
                
                        else:
                            Track.append(Keyframe)    
                            PrevTrackType = Keyframe['TrackType']
                            PrevBoneID = Keyframe['BoneID']
                                    
                    #Meant to check for any remaining track data after iterating through the yml and ensures it's not forgotten.                
                    if Track is not None:
                        ApplyTheTrack(Track, obj, joint, jointEdit, AnimName, self.import_legacy, mip.anim_import_withmetadata, self.type_b, ArmName)      
                        del Track[:]
                
            
            except Exception as e:
                print("An error occured.",e, "\n", traceback.format_exc())    

#Parts of the code based on the Smash Ultimate Blender Animation Importer.
class SUB_PT_Anim_Import(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'    
    bl_category = 'MT Framework'
    bl_label = 'Animation Importer'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.mode == "POSE" or context.mode == "OBJECT":
            return True
        return False

    def draw(self, context):
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        layout = self.layout
        layout.use_property_split = False        
        obj: bpy.types.Object = context.active_object
        row = layout.row()
        if obj is None:
            row.label(text="Select an Armature first.")
        elif obj.select_get() is False:
            row.label(text="Select an Armature first.")   
        elif obj.type == 'ARMATURE':            
            row = layout.row(align=True)
            row.prop(mip, 'anim_import_withmetadata',text='Use Metadata when importing:')
            row = layout.row(align=True)
            row.prop(mip, 'anim_metadata_file')
            row = layout.row(align=True)
            row.operator(SUB_PT_MOD_OT_Choose_Anim_Metadata_YML.bl_idname,icon='IMPORT',text= 'Choose metadata .yml file')
            layout.separator()
            row = layout.row(align=True)
            row.operator('sub.mod_op_add_joint_twofiftyfive', text = 'Add jnt_255 to Selected Armature')
            layout.separator()
            row = layout.row(align=True)
            row.operator('sub.mod_op_add_simple_ik', text = 'Add Standard IKs Selected Armature')
            layout.separator()
            row = layout.row(align=True)
            row.operator('sub.op_select_relevant_joints_for_baking', text = 'Select Relevant Bones For Baking')
            layout.separator()            
            row = layout.row(align=True)
            row.operator(SUB_OP_anim_import.bl_idname, icon='IMPORT', text='Import Marvel 3 .yml Animation')

class SUB_OP_anim_import(Operator, ImportHelper):
    bl_idname = 'sub.import_anim'
    bl_label = 'Import Anim'
    #bl_options = {'UNDO'}

    filter_glob: StringProperty(
        default='*.yml',
        options={'HIDDEN'}
    )

    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    import_legacy: BoolProperty(
        name='Import Animations on Marvel 3 FBX Models.',
        description='Imports in a way that is compatible with the FBX Collection',
        default=False,
    )
    save_fake_users: BoolProperty(
        name='Import With Fake User',
        description='Saves each animation imported as a fake user to ensure they are not discarded when the scene is closed after saving',
        default=True,
    )
    type_b: BoolProperty(
        name='Type B',
        description='For Later use. If unsure, leave False/Unchecked',
        default=False,
    )

    #filepath: StringProperty(subtype="FILE_PATH")

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
        #keywords = self.as_keywords(ignore=("filter_glob","files"))
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
        if self.filepath == '' or Path(self.filepath).is_dir():
            self.report({"ERROR"}, f"There was no file selected......")
            ShowMessageBox("There was no file selected. Cancelling.", "Notice", 'ERROR')
            return {'CANCELLED'}
        #ShowMessageBox("There's Nothing Coded here yet.", "Notice")
        time_start = time.time()        
        readM3AanimationData(self, context, self.filepath)
        context.view_layer.update()
        time_end = time.time()
        time_elapsed = time_end - time_start
        print("Import done in "+ str(time_elapsed) + " seconds.", "Notice")
        ShowMessageBox("Import done in "+ str(time_elapsed) + " seconds.")
        return {'FINISHED'}
    
class SUB_PT_MOD_OT_Choose_Anim_Metadata_YML(bpy.types.Operator, ImportHelper):
    """Choose which Metadata YML to Use"""
    bl_idname = "sub.mod_ot_choose_anim_metadata_yml"
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
        mip.anim_metadata_file = self.filepath
        return {'FINISHED'}    
    
class SUB_OP_ADD_JOINT_TWOFIFTYFIVE(bpy.types.Operator):
    bl_idname = 'sub.mod_op_add_joint_twofiftyfive'
    bl_label = "Add jnt_255 to Armature"

    def execute(self,context):
        scene = bpy.context.scene
        #Stores the object selected.
        obj = bpy.context.active_object

        #Changes the blender mode to Edit Mode.
        bpy.ops.object.mode_set(mode = 'EDIT', toggle=False)    

        edit_bones = obj.data.edit_bones

        for bone in edit_bones:
            if bone.parent is None:
                bone.select = True
                root_bone = bone                
                copy_bone = obj.data.edit_bones.new("jnt_255")
                copy_bone.length = root_bone.length
                #Proper Bone Settings for jnt_255.
                copy_bone.roll = 0
                #copy_bone.radius = 0.05
                copy_bone.head[2] = 0
                root_bone.parent = copy_bone
                break

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)        
        return {'FINISHED'}       

class SUB_OP_ADD_SIMPLE_IK(bpy.types.Operator):
    bl_idname = 'sub.mod_op_add_simple_ik'
    bl_label = "Add Simple IK to Armature" 

    def execute(self,context):
        scene = bpy.context.scene
        #Stores the object selected.
        obj = bpy.context.active_object

        bpy.ops.object.mode_set(mode = 'EDIT', toggle=False)

        edit_bones = obj.data.edit_bones

        SelObj = bpy.context.selected_objects
        ArmName = (SelObj[(len((bpy.context.selected_objects))- 1)].name)

        arm = SelObj[(len((bpy.context.selected_objects))- 1)]

        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

        if mip.anim_import_withmetadata == True:
            
            metadata = loadMetadata( self,mip.anim_metadata_file )
            MetaKneeL = metadata.getJointName( 17 )
            MetaKneeR = metadata.getJointName( 21 )
            MetaLegL = metadata.getJointName( 16 )
            MetaLegR = metadata.getJointName( 20 )
            MetaFootL = metadata.getJointName( 18 )
            MetaFootR = metadata.getJointName( 22 )
            MetaHandL = metadata.getJointName( 11 )
            MetaHandR = metadata.getJointName( 15 )
            MetaElbowL = metadata.getJointName( 10 )
            MetaElbowR = metadata.getJointName( 14 )
            MetaArmL = metadata.getJointName( 9 )
            MetaArmR = metadata.getJointName( 13 )
            TwistA = metadata.getJointName( 27 )
            TwistB = metadata.getJointName( 42 )
            TwistC = metadata.getJointName( 28 )
            TwistD = metadata.getJointName( 44 )
            TwistE = metadata.getJointName( 33 )
            TwistF = metadata.getJointName( 34 )

            #Selects Leg & Knee Bones and moves them ever so slightly to ensure good bend.
            edit_bones[MetaLegL].tail[1] = edit_bones[MetaLegL].tail[1] - 0.2
            edit_bones[MetaLegR].tail[1] = edit_bones[MetaLegR].tail[1] - 0.2

            edit_bones[MetaKneeL].head[1] = edit_bones[MetaKneeL].head[1] - 0.2
            edit_bones[MetaKneeR].head[1] = edit_bones[MetaKneeR].head[1] - 0.2

            #Checks for Twist Bones and moves them as well.
            for bone in edit_bones:
                if bone.name == TwistA:
                    print("Found bone 27.")
                    edit_bones[TwistA].head[1] = edit_bones[TwistA].head[1] - 0.2

            for bone in edit_bones:
                if bone.name == TwistB:
                    print("Found bone 42.")
                    edit_bones[TwistB].head[1] = edit_bones[TwistB].head[1] - 0.2

            for bone in edit_bones:
                if bone.name == TwistC:
                    print("Found bone 28.")
                    edit_bones[TwistC].head[1] = edit_bones[TwistC].head[1] - 0.2

            for bone in edit_bones:
                if bone.name == TwistD:
                    print("Found bone 44.")
                    edit_bones[TwistD].head[1] = edit_bones[TwistD].head[1] - 0.2


            edit_bones[MetaArmL].tail[1] = edit_bones[MetaArmL].tail[1] + 0.25
            edit_bones[MetaArmR].tail[1] = edit_bones[MetaArmR].tail[1] + 0.25

            edit_bones[MetaElbowL].head[1] = edit_bones[MetaElbowL].head[1] + 0.25
            edit_bones[MetaElbowR].head[1] = edit_bones[MetaElbowR].head[1] + 0.25

            #Checks for Twist Bones and moves them as well.
            for bone in edit_bones:
                if bone.name == TwistE:
                    print("Found bone 33.")
                    edit_bones[TwistE].head[1] = edit_bones[TwistE].head[1] + 0.25

            for bone in edit_bones:
                if bone.name == TwistF:
                    print("Found bone 34.")
                    edit_bones[TwistF].head[1] = edit_bones[TwistF].head[1] + 0.25
                    

            IK_FootL = obj.data.edit_bones.new("IK_FootL")
            IK_FootL.head = edit_bones[MetaFootL].head
            IK_FootL.tail = edit_bones[MetaFootL].head
            IK_FootL.roll = edit_bones[MetaFootL].roll
            IK_FootL.parent = edit_bones["jnt_255"]
            IK_FootL.tail[1]= IK_FootL.tail[1] + 10
            IK_FootL.color.palette = 'THEME15'

            IK_FootR = obj.data.edit_bones.new("IK_FootR")
            IK_FootR.head = edit_bones[MetaFootR].head
            IK_FootR.tail = edit_bones[MetaFootR].head
            IK_FootR.roll = edit_bones[MetaFootR].roll
            IK_FootR.parent = edit_bones["jnt_255"]
            IK_FootR.tail[1]= IK_FootR.tail[1] + 10
            IK_FootR.color.palette = 'THEME01'
                    
            IK_KneeL = obj.data.edit_bones.new("IK_KneeL")
            IK_KneeL.head = edit_bones[MetaKneeL].head
            IK_KneeL.tail = edit_bones[MetaKneeL].head
            IK_KneeL.roll = math.radians(90)
            IK_KneeL.parent = edit_bones["jnt_255"]
            IK_KneeL.tail[1]= IK_KneeL.tail[1] - 20
            IK_KneeL.head[1]= IK_KneeL.head[1] - 30
            IK_KneeL.tail[1]= IK_KneeL.tail[1] - 30
            IK_KneeL.color.palette = 'THEME03'		

            IK_KneeR = obj.data.edit_bones.new("IK_KneeR")
            IK_KneeR.head = edit_bones[MetaKneeR].head
            IK_KneeR.tail = edit_bones[MetaKneeR].head
            IK_KneeR.roll = math.radians(90)
            IK_KneeR.parent = edit_bones["jnt_255"]
            IK_KneeR.tail[1]= IK_KneeR.tail[1] - 20
            IK_KneeR.head[1]= IK_KneeR.head[1] - 30
            IK_KneeR.tail[1]= IK_KneeR.tail[1] - 30
            IK_KneeR.color.palette = 'THEME01'		

            IK_HandL = obj.data.edit_bones.new("IK_HandL")
            IK_HandL.head = edit_bones[MetaHandL].head
            IK_HandL.tail = edit_bones[MetaHandL].head
            IK_HandL.roll = edit_bones[MetaHandL].roll
            IK_HandL.parent = edit_bones["jnt_255"]
            IK_HandL.tail[1]= IK_HandL.tail[1] + 10
            IK_HandL.color.palette = 'THEME15'

            IK_HandR = obj.data.edit_bones.new("IK_HandR")
            IK_HandR.head = edit_bones[MetaHandR].head
            IK_HandR.tail = edit_bones[MetaHandR].head
            IK_HandR.roll = edit_bones[MetaHandR].roll
            IK_HandR.parent = edit_bones["jnt_255"]
            IK_HandR.tail[1]= IK_HandR.tail[1] + 10
            IK_HandR.color.palette = 'THEME01'

            IK_ElbowL = obj.data.edit_bones.new("IK_ElbowL")
            IK_ElbowL.head = edit_bones[MetaElbowL].head
            IK_ElbowL.tail = edit_bones[MetaElbowL].head
            IK_ElbowL.roll = math.radians(180)
            IK_ElbowL.parent = edit_bones["jnt_255"]
            IK_ElbowL.tail[1]= IK_ElbowL.tail[1] + 20
            IK_ElbowL.head[1]= IK_ElbowL.head[1] + 40
            IK_ElbowL.tail[1]= IK_ElbowL.tail[1] + 40
            IK_ElbowL.color.palette = 'THEME03'		

            IK_ElbowR = obj.data.edit_bones.new("IK_ElbowR")
            IK_ElbowR.head = edit_bones[MetaElbowR].head
            IK_ElbowR.tail = edit_bones[MetaElbowR].head
            IK_ElbowR.roll = math.radians(180)
            IK_ElbowR.parent = edit_bones["jnt_255"]
            IK_ElbowR.tail[1]= IK_ElbowR.tail[1] + 20
            IK_ElbowR.head[1]= IK_ElbowR.head[1] + 40
            IK_ElbowR.tail[1]= IK_ElbowR.tail[1] + 40
            IK_ElbowR.color.palette = 'THEME01'		

            #Takes care of parenting to IK bones.
            #edit_bones[MetaFootL].parent = IK_FootL
            #edit_bones[MetaFootR].parent = IK_FootR
            #edit_bones[MetaHandL].parent = IK_HandL
            #edit_bones[MetaHandR].parent = IK_HandR

            bpy.ops.object.mode_set(mode = 'POSE', toggle=False)
            pose_bones = obj.pose.bones

            #Adds Constraints to Feet Bones.
            LFootBone = pose_bones[MetaFootL]
            clc = LFootBone.constraints.new('COPY_LOCATION')
            clc.target = arm
            clc.subtarget = pose_bones[MetaKneeL].name
            clc.head_tail = 1.0

            crc = LFootBone.constraints.new('COPY_ROTATION')
            crc.target = arm
            crc.subtarget = pose_bones["IK_FootL"].name
            crc.use_x = True
            crc.use_y = True
            crc.use_z = True
            crc.target_space = 'LOCAL_OWNER_ORIENT'
            crc.owner_space = 'LOCAL_WITH_PARENT'

            RFootBone = pose_bones[MetaFootR]
            rclc = RFootBone.constraints.new('COPY_LOCATION')
            rclc.target = arm
            rclc.subtarget = pose_bones[MetaKneeR].name
            rclc.head_tail = 1.0

            rcrc = RFootBone.constraints.new('COPY_ROTATION')
            rcrc.target = arm
            rcrc.subtarget = pose_bones["IK_FootR"].name
            rcrc.use_x = True
            rcrc.use_y = True
            rcrc.use_z = True
            rcrc.target_space = 'LOCAL_OWNER_ORIENT'
            rcrc.owner_space = 'LOCAL_WITH_PARENT'

            LKneeBone = pose_bones[MetaKneeL]
            lik = LKneeBone.constraints.new('IK')
            lik.target = arm
            lik.subtarget = pose_bones["IK_FootL"].name
            lik.pole_target = arm
            lik.pole_subtarget = pose_bones["IK_KneeL"].name
            lik.pole_angle = math.radians(180)
            lik.chain_count = 2

            RKneeBone = pose_bones[MetaKneeR]
            rik = RKneeBone.constraints.new('IK')
            rik.target = arm
            rik.subtarget = pose_bones["IK_FootR"].name
            rik.pole_target = arm
            rik.pole_subtarget = pose_bones["IK_KneeR"].name
            rik.pole_angle = math.radians(180)
            rik.chain_count = 2

            LHandBone = pose_bones[MetaHandL]
            lhclc = LHandBone.constraints.new('COPY_LOCATION')
            lhclc.target = arm
            lhclc.subtarget = pose_bones[MetaElbowL].name
            lhclc.head_tail = 1.0

            #Adds Constraints to Left Hand Bone.
            lhclc = LHandBone.constraints.new('COPY_ROTATION')
            lhclc.target = arm
            lhclc.subtarget = pose_bones["IK_HandL"].name
            lhclc.use_x = True
            lhclc.use_y = True
            lhclc.use_z = True
            lhclc.target_space = 'LOCAL_OWNER_ORIENT'
            lhclc.owner_space = 'LOCAL_WITH_PARENT'

            RHandBone = pose_bones[MetaHandR]
            rhclc = RHandBone.constraints.new('COPY_LOCATION')
            rhclc.target = arm
            rhclc.subtarget = pose_bones[MetaElbowR].name
            rhclc.head_tail = 1.0

            #Adds Constraints to Right Hand Bone.
            rhclc = RHandBone.constraints.new('COPY_ROTATION')
            rhclc.target = arm
            rhclc.subtarget = pose_bones["IK_HandR"].name
            rhclc.use_x = True
            rhclc.use_y = True
            rhclc.use_z = True
            rhclc.target_space = 'LOCAL_OWNER_ORIENT'
            rhclc.owner_space = 'LOCAL_WITH_PARENT'

            LElbowBone = pose_bones[MetaElbowL]
            lelik = LElbowBone.constraints.new('IK')
            lelik.target = arm
            lelik.subtarget = pose_bones["IK_HandL"].name
            lelik.pole_target = arm
            lelik.pole_subtarget = pose_bones["IK_ElbowL"].name
            lelik.chain_count = 2

            RElbowBone = pose_bones[MetaElbowR]
            relik = RElbowBone.constraints.new('IK')
            relik.target = arm
            relik.subtarget = pose_bones["IK_HandR"].name
            relik.pole_target = arm
            relik.pole_subtarget = pose_bones["IK_ElbowR"].name
            relik.chain_count = 2           
            
        else:

            #Selects Leg & Knee Bones and moves them ever so slightly to ensure good bend.
            edit_bones["jnt_16"].tail[1] = edit_bones["jnt_16"].tail[1] - 0.2
            edit_bones["jnt_20"].tail[1] = edit_bones["jnt_20"].tail[1] - 0.2

            edit_bones["jnt_17"].head[1] = edit_bones["jnt_17"].head[1] - 0.2
            edit_bones["jnt_21"].head[1] = edit_bones["jnt_21"].head[1] - 0.2

            #Checks for Twist Bones and moves them as well.
            for bone in edit_bones:
                if bone.name == "jnt_27":
                    print("Found bone 27.")
                    edit_bones["jnt_27"].head[1] = edit_bones["jnt_27"].head[1] - 0.2

            for bone in edit_bones:
                if bone.name == "jnt_42":
                    print("Found bone 42.")
                    edit_bones["jnt_42"].head[1] = edit_bones["jnt_42"].head[1] - 0.2

            for bone in edit_bones:
                if bone.name == "jnt_28":
                    print("Found bone 28.")
                    edit_bones["jnt_28"].head[1] = edit_bones["jnt_28"].head[1] - 0.2

            for bone in edit_bones:
                if bone.name == "jnt_44":
                    print("Found bone 44.")
                    edit_bones["jnt_44"].head[1] = edit_bones["jnt_44"].head[1] - 0.2


            edit_bones["jnt_9"].tail[1] = edit_bones["jnt_9"].tail[1] + 0.25
            edit_bones["jnt_13"].tail[1] = edit_bones["jnt_13"].tail[1] + 0.25

            edit_bones["jnt_10"].head[1] = edit_bones["jnt_10"].head[1] + 0.25
            edit_bones["jnt_14"].head[1] = edit_bones["jnt_14"].head[1] + 0.25

            #Checks for Twist Bones and moves them as well.
            for bone in edit_bones:
                if bone.name == "jnt_33":
                    print("Found bone 33.")
                    edit_bones["jnt_33"].head[1] = edit_bones["jnt_33"].head[1] + 0.25

            for bone in edit_bones:
                if bone.name == "jnt_34":
                    print("Found bone 34.")
                    edit_bones["jnt_34"].head[1] = edit_bones["jnt_34"].head[1] + 0.25
                    

            IK_FootL = obj.data.edit_bones.new("IK_FootL")
            IK_FootL.head = edit_bones["jnt_18"].head
            IK_FootL.tail = edit_bones["jnt_18"].head
            IK_FootL.roll = edit_bones["jnt_18"].roll
            IK_FootL.parent = edit_bones["jnt_255"]
            IK_FootL.tail[1]= IK_FootL.tail[1] + 10
            IK_FootL.color.palette = 'THEME15'

            IK_FootR = obj.data.edit_bones.new("IK_FootR")
            IK_FootR.head = edit_bones["jnt_22"].head
            IK_FootR.tail = edit_bones["jnt_22"].head
            IK_FootR.roll = edit_bones["jnt_22"].roll
            IK_FootR.parent = edit_bones["jnt_255"]
            IK_FootR.tail[1]= IK_FootR.tail[1] + 10
            IK_FootR.color.palette = 'THEME01'
                    
            IK_KneeL = obj.data.edit_bones.new("IK_KneeL")
            IK_KneeL.head = edit_bones["jnt_17"].head
            IK_KneeL.tail = edit_bones["jnt_17"].head
            IK_KneeL.roll = math.radians(90)
            IK_KneeL.parent = edit_bones["jnt_255"]
            IK_KneeL.tail[1]= IK_KneeL.tail[1] - 20
            IK_KneeL.head[1]= IK_KneeL.head[1] - 30
            IK_KneeL.tail[1]= IK_KneeL.tail[1] - 30
            IK_KneeL.color.palette = 'THEME03'		

            IK_KneeR = obj.data.edit_bones.new("IK_KneeR")
            IK_KneeR.head = edit_bones["jnt_21"].head
            IK_KneeR.tail = edit_bones["jnt_21"].head
            IK_KneeR.roll = math.radians(90)
            IK_KneeR.parent = edit_bones["jnt_255"]
            IK_KneeR.tail[1]= IK_KneeR.tail[1] - 20
            IK_KneeR.head[1]= IK_KneeR.head[1] - 30
            IK_KneeR.tail[1]= IK_KneeR.tail[1] - 30
            IK_KneeR.color.palette = 'THEME01'		

            IK_HandL = obj.data.edit_bones.new("IK_HandL")
            IK_HandL.head = edit_bones["jnt_11"].head
            IK_HandL.tail = edit_bones["jnt_11"].head
            IK_HandL.roll = edit_bones["jnt_11"].roll
            IK_HandL.parent = edit_bones["jnt_255"]
            IK_HandL.tail[1]= IK_HandL.tail[1] + 10
            IK_HandL.color.palette = 'THEME15'

            IK_HandR = obj.data.edit_bones.new("IK_HandR")
            IK_HandR.head = edit_bones["jnt_15"].head
            IK_HandR.tail = edit_bones["jnt_15"].head
            IK_HandR.roll = edit_bones["jnt_15"].roll
            IK_HandR.parent = edit_bones["jnt_255"]
            IK_HandR.tail[1]= IK_HandR.tail[1] + 10
            IK_HandR.color.palette = 'THEME01'

            IK_ElbowL = obj.data.edit_bones.new("IK_ElbowL")
            IK_ElbowL.head = edit_bones["jnt_10"].head
            IK_ElbowL.tail = edit_bones["jnt_10"].head
            IK_ElbowL.roll = math.radians(180)
            IK_ElbowL.parent = edit_bones["jnt_255"]
            IK_ElbowL.tail[1]= IK_ElbowL.tail[1] + 20
            IK_ElbowL.head[1]= IK_ElbowL.head[1] + 40
            IK_ElbowL.tail[1]= IK_ElbowL.tail[1] + 40
            IK_ElbowL.color.palette = 'THEME03'		

            IK_ElbowR = obj.data.edit_bones.new("IK_ElbowR")
            IK_ElbowR.head = edit_bones["jnt_14"].head
            IK_ElbowR.tail = edit_bones["jnt_14"].head
            IK_ElbowR.roll = math.radians(180)
            IK_ElbowR.parent = edit_bones["jnt_255"]
            IK_ElbowR.tail[1]= IK_ElbowR.tail[1] + 20
            IK_ElbowR.head[1]= IK_ElbowR.head[1] + 40
            IK_ElbowR.tail[1]= IK_ElbowR.tail[1] + 40
            IK_ElbowR.color.palette = 'THEME01'		

            #Takes care of parenting to IK bones.
            #edit_bones["jnt_18"].parent = IK_FootL
            #edit_bones["jnt_22"].parent = IK_FootR
            #edit_bones["jnt_11"].parent = IK_HandL
            #edit_bones["jnt_15"].parent = IK_HandR

            bpy.ops.object.mode_set(mode = 'POSE', toggle=False)
            pose_bones = obj.pose.bones

            #Adds Constraints to Feet Bones.
            LFootBone = pose_bones["jnt_18"]
            clc = LFootBone.constraints.new('COPY_LOCATION')
            clc.target = arm
            clc.subtarget = pose_bones["jnt_17"].name
            clc.head_tail = 1.0

            crc = LFootBone.constraints.new('COPY_ROTATION')
            crc.target = arm
            crc.subtarget = pose_bones["IK_FootL"].name
            crc.use_x = True
            crc.use_y = True
            crc.use_z = True
            crc.target_space = 'LOCAL_OWNER_ORIENT'
            crc.owner_space = 'LOCAL_WITH_PARENT'

            RFootBone = pose_bones["jnt_22"]
            rclc = RFootBone.constraints.new('COPY_LOCATION')
            rclc.target = arm
            rclc.subtarget = pose_bones["jnt_21"].name
            rclc.head_tail = 1.0

            rcrc = RFootBone.constraints.new('COPY_ROTATION')
            rcrc.target = arm
            rcrc.subtarget = pose_bones["IK_FootR"].name
            rcrc.use_x = True
            rcrc.use_y = True
            rcrc.use_z = True
            rcrc.target_space = 'LOCAL_OWNER_ORIENT'
            rcrc.owner_space = 'LOCAL_WITH_PARENT'

            LKneeBone = pose_bones["jnt_17"]
            lik = LKneeBone.constraints.new('IK')
            lik.target = arm
            lik.subtarget = pose_bones["IK_FootL"].name
            lik.pole_target = arm
            lik.pole_subtarget = pose_bones["IK_KneeL"].name
            lik.pole_angle = math.radians(180)
            lik.chain_count = 2

            RKneeBone = pose_bones["jnt_21"]
            rik = RKneeBone.constraints.new('IK')
            rik.target = arm
            rik.subtarget = pose_bones["IK_FootR"].name
            rik.pole_target = arm
            rik.pole_subtarget = pose_bones["IK_KneeR"].name
            rik.pole_angle = math.radians(180)
            rik.chain_count = 2

            LHandBone = pose_bones["jnt_11"]
            lhclc = LHandBone.constraints.new('COPY_LOCATION')
            lhclc.target = arm
            lhclc.subtarget = pose_bones["jnt_10"].name
            lhclc.head_tail = 1.0

            #Adds Constraints to Left Hand Bone.
            lhclc = LHandBone.constraints.new('COPY_ROTATION')
            lhclc.target = arm
            lhclc.subtarget = pose_bones["IK_HandL"].name
            lhclc.use_x = True
            lhclc.use_y = True
            lhclc.use_z = True
            lhclc.target_space = 'LOCAL_OWNER_ORIENT'
            lhclc.owner_space = 'LOCAL_WITH_PARENT'

            RHandBone = pose_bones["jnt_15"]
            rhclc = RHandBone.constraints.new('COPY_LOCATION')
            rhclc.target = arm
            rhclc.subtarget = pose_bones["jnt_14"].name
            rhclc.head_tail = 1.0

            #Adds Constraints to Right Hand Bone.
            rhclc = RHandBone.constraints.new('COPY_ROTATION')
            rhclc.target = arm
            rhclc.subtarget = pose_bones["IK_HandR"].name
            rhclc.use_x = True
            rhclc.use_y = True
            rhclc.use_z = True
            rhclc.target_space = 'LOCAL_OWNER_ORIENT'
            rhclc.owner_space = 'LOCAL_WITH_PARENT'

            LElbowBone = pose_bones["jnt_10"]
            lelik = LElbowBone.constraints.new('IK')
            lelik.target = arm
            lelik.subtarget = pose_bones["IK_HandL"].name
            lelik.pole_target = arm
            lelik.pole_subtarget = pose_bones["IK_ElbowL"].name
            lelik.chain_count = 2

            RElbowBone = pose_bones["jnt_14"]
            relik = RElbowBone.constraints.new('IK')
            relik.target = arm
            relik.subtarget = pose_bones["IK_HandR"].name
            relik.pole_target = arm
            relik.pole_subtarget = pose_bones["IK_ElbowR"].name
            relik.chain_count = 2

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)        
        return {'FINISHED'} 
    
class SUB_OP_SELECT_RELEVANT_JOINTS_FOR_BAKING(bpy.types.Operator):
    """Choose which Metadata YML to Use"""
    bl_idname = "sub.op_select_relevant_joints_for_baking"
    bl_label = "Selects Relevant Bones for Baking"


    def execute(self,context):
        bpy.ops.object.mode_set(mode = 'POSE', toggle=False)
        #Stores the object selected.
        obj = bpy.context.active_object
        pose_bones = obj.pose.bones

        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

        #Deselects Everything else and then selects the relevant bones.
        bpy.context.active_object.select_set(False)

        pose_bones['jnt_1'].bone.select = True
        pose_bones['jnt_2'].bone.select = True
        pose_bones['jnt_3'].bone.select = True

        
        #Primary Limb Bones.
        for x in range(4,24):
            try:
                BoneName = f'jnt_{x}'
                pose_bones[BoneName].bone.select = True
            except:
                print("Bone " + BoneName + " doesn't exist on this Armature.")

        #Twist Bones.
        for x in range(24,48):
            try:
                BoneName = f'jnt_{x}'
                pose_bones[BoneName].bone.select = True
            except:
                print("Bone " + BoneName + " doesn't exist on this Armature.")

        #Left Hand Bones.
        for x in range(50,67):
            try:
                BoneName = f'jnt_{x}'
                pose_bones[BoneName].bone.select = True
            except:
                print("Bone " + BoneName + " doesn't exist on this Armature.")

        #Right Hand Bones.
        for x in range(70,87):
            try:
                BoneName = f'jnt_{x}'
                pose_bones[BoneName].bone.select = True
            except:
                print("Bone " + BoneName + " doesn't exist on this Armature.")                

        print("Finished selecting bones for baking.")

        bpy.ops.object.mode_set(mode='POSE', toggle=False)        
        return {'FINISHED'}