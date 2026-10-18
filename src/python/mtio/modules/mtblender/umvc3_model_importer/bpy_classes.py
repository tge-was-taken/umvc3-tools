from . import modules
from . import mtlib
from .mtlib import properties

classes = [
    #modules.blender_plugin,
    modules.model_import.SUB_PT_Model_Import,    
    modules.model_import.SUB_PT_Model_Import_Rendering,
    modules.model_import.SUB_PT_MOD_OT_import,
    modules.model_import.SUB_OP_MOD_ImportModelPath,
    modules.model_import.SUB_OP_LoadStageLighting,
    modules.model_import.SUB_OP_RebuildGameShaders,
    modules.model_import.SUB_OP_RenderGamePost,
    modules.model_import.SUB_OP_ExportGameMRL,
    *modules.mt_material_ui.CLASSES,
    modules.model_import.SUB_OP_ApplyFaceGroup,
    modules.model_import.SUB_PT_MOD_OT_Choose_Metadata_YML,
    modules.anim_import.SUB_PT_Anim_Import,
    modules.anim_import.SUB_OP_anim_import,
    modules.anim_import.SUB_PT_MOD_OT_Choose_Anim_Metadata_YML,
    modules.anim_import.SUB_OP_ADD_JOINT_TWOFIFTYFIVE,
    modules.anim_import.SUB_OP_ADD_SIMPLE_IK,
    modules.anim_import.SUB_OP_SELECT_RELEVANT_JOINTS_FOR_BAKING,
    modules.anim_export.SUB_PT_Anim_Export,
    modules.anim_export.SUB_OP_anim_export,
    modules.anim_export.SUB_PT_MOD_OT_Choose_Anim_Export_Metadata_YML,
    modules.cam_import.SUB_PT_Cam_Import,
    modules.cam_import.SUB_OP_cam_import,
    modules.cam_import.SUB_OP_cam_export,
    modules.cam_import.SUB_OP_cam_follow,
    modules.model_export.SUB_PT_Model_Export,
    modules.model_export.SUB_PT_MOD_OT_export,
    modules.model_export.SUB_OP_MOD_ExportModelPath,
    modules.model_export.SUB_PT_MOD_OT_Choose_Reference_Model_For_Export,
    modules.model_export.SUB_PT_MOD_OT_Choose_Metadata_For_Export_YML,
    modules.model_export.SUB_PT_MOD_OT_Choose_MRL_YML,
    modules.model_utils.SUB_PT_OT_ADD_REMOVE_MT_STUFF,
    modules.model_utils.SUB_OP_ADD_MT_ATTRIBUTES,
    modules.model_utils.SUB_OP_REMOVE_MT_ATTRIBUTES,  
<<<<<<< Updated upstream
=======
    modules.model_utils.SUB_OP_CLEANUP_VERTEX_GROUPS,
    modules.model_utils.SUB_OP_SELECT_OBJECTS_BY_MATERIAL,
>>>>>>> Stashed changes
    mtlib.properties.UMVC3ModelImportProperties
    
]