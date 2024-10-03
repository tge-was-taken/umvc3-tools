bl_info = {
    "name": "MT Framework Blender IO plugin",
    "author": "TGE",
    "version": (2, 0, 0),
    "blender": (3, 4, 0),
    "location": "File > Import > MT Framework Model (.mod) ",
    "description": "Import MT Framework MOD models",
    "category": "Import-Export",
}

def isDebugEnv():
    import os
    return os.path.exists( os.path.join( os.path.dirname( __file__ ), '.debug' ) )

def attachDebugger():
    try:
        import ptvsd
        print( ptvsd.enable_attach() )
    except:
        pass

def reload():
    import os
    import glob
    import sys

    def _deleteModule(filename):
        modules = list(sys.modules.keys())
        if filename in modules:
            print(f'bootstrapper: deleting module {filename}')
            del sys.modules[filename]
    
    currentDir = os.path.basename(__file__)
    for file in glob.iglob(currentDir + "/**/*", recursive=True):
        fileName, _ = os.path.splitext(os.path.basename(file))
        qualName = f'{os.path.basename(os.path.dirname(file))}.{fileName}'
        _deleteModule(fileName)
        _deleteModule(qualName)
reload()

if "bpy" in locals():
    import importlib
    if "blender_exporter" in locals():
        importlib.reload(blender_exporter) 
    if "blender_importer" in locals():
        importlib.reload(blender_importer) 
    if "blender_plugin" in locals():
        importlib.reload(blender_plugin) 

import os
    
import bpy
from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        EnumProperty,
        CollectionProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        path_reference_mode,
        axis_conversion,
        )

def getConfigValue(name):
    from .blender_plugin import plugin
    assert hasattr(plugin.config,name)
    return getattr(plugin.config,name)

def setConfigValue(name,value):
    from .blender_plugin import plugin
    assert hasattr(plugin.config,name)
    setattr(plugin.config,name,value)

#@orientation_helper(axis_forward='-Z', axis_up='Y')
class MOD_OT_import(bpy.types.Operator, ImportHelper):

    """Import MT Framework *.mod model"""
    bl_idname = "import_scene.mod"
    bl_label = "Import MOD"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".mod"
    filter_glob: StringProperty(default="*.mod", options={'HIDDEN'})
        
    def getTargetItems(self, context):
        from .mtlib import target

        items = []
        for i, t in enumerate(target.supported):
            items.append((str(i), t.description, t.description))
        return tuple(items)

    def getFlipUpAxis(self): return getConfigValue('flipUpAxis')
    def setFlipUpAxis(self, value): setConfigValue('flipUpAxis', value)

    def getLukasCompat(self): return getConfigValue('lukasCompat')
    def setLukasCompat(self, value): setConfigValue('lukasCompat', value)

    def getTarget(self): return getConfigValue('target')
    def setTarget(self, value): setConfigValue('target', value)
    
    def getImportFilePath(self): return getConfigValue('importFilePath')
    def setImportFilePath(self, value): 
        from .blender_plugin import plugin
        from .mtlib.metadata import ModelMetadata

        plugin.config.importFilePath = value
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( plugin.config.importFilePath ).split('.')[0] )
        if os.path.exists( newMetadataPath ):
            plugin.config.importMetadataPath = newMetadataPath
            self.importMetadataPath = newMetadataPath

    def getImportMetadataPath(self): return getConfigValue('importMetadataPath')
    def setImportMetadataPath(self, value): setConfigValue('importMetadataPath', value)
    
    def getImportWeights(self): return getConfigValue('importWeights')
    def setImportWeights(self, value): setConfigValue('importWeights', value)
    
    def getImportNormals(self): return getConfigValue('importNormals')
    def setImportNormals(self, value): setConfigValue('importNormals', value)
    
    def getImportGroups(self): return getConfigValue('importGroups')
    def setImportGroups(self, value): setConfigValue('importGroups', value)
    
    def getImportSkeleton(self): return getConfigValue('importSkeleton')
    def setImportSkeleton(self, value): setConfigValue('importSkeleton', value)
    
    def getImportPrimitives(self): return getConfigValue('importPrimitives')
    def setImportPrimitives(self, value): setConfigValue('importPrimitives', value)
    
    def getImportScale(self): return getConfigValue('importScale')
    def setImportScale(self, value): setConfigValue('importScale', value)
    
    def getImportBakeScale(self): return getConfigValue('importBakeScale')
    def setImportBakeScale(self, value): setConfigValue('importBakeScale', value)
    
    def getImportConvertTexturesToDDS(self): return getConfigValue('importConvertTexturesToDDS')
    def setImportConvertTexturesToDDS(self, value): setConfigValue('importConvertTexturesToDDS', value)

    def getImportSaveMrlYml(self): return getConfigValue('importSaveMrlYml')
    def setImportSaveMrlYml(self, value): setConfigValue('importSaveMrlYml', value)

    def getCreateLayer(self): return getConfigValue('importCreateLayer')
    def setCreateLayer(self, value): setConfigValue('importCreateLayer', value)

    # General settings
    flipUpAxis: BoolProperty(name="Flip up axis", get=getFlipUpAxis, set=setFlipUpAxis)
    lukasCompat: BoolProperty(name="Compatibility with Lukas' script", get=getLukasCompat, set=setLukasCompat)
    target: EnumProperty(name="Game", items=getTargetItems, get=getTarget, set=setTarget)

    # Import settings
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
        get=getImportFilePath,
        set=setImportFilePath,
    )
    importMetadataPath: StringProperty(name="Metadata file (optional)", subtype='FILE_PATH', 
        get=getImportMetadataPath, set=setImportMetadataPath)

    # Import filters
    importWeights: BoolProperty(name="Weights", get=getImportWeights, set=setImportWeights)
    importNormals: BoolProperty(name="Normals", get=getImportNormals, set=setImportNormals)
    importGroups: BoolProperty(name="Groups", get=getImportGroups, set=setImportGroups)
    importSkeleton: BoolProperty(name="Skeleton", get=getImportSkeleton, set=setImportSkeleton)
    importPrimitives: BoolProperty(name="Meshes", get=getImportPrimitives, set=setImportPrimitives)

    # Additional options
    importScale: FloatProperty(name="Scale", get=getImportScale, set=setImportScale)
    importBakeScale: BoolProperty(name="Bake scale into translation", get=getImportBakeScale, set=setImportBakeScale)
    importConvertTexturesToDDS: BoolProperty(name="Convert textures to DDS", get=getImportConvertTexturesToDDS, set=setImportConvertTexturesToDDS)
    importSaveMrlYml: BoolProperty(name="Convert MRL to YML", get=getImportSaveMrlYml, set=setImportSaveMrlYml)
    importCreateLayer: BoolProperty(name="Create layer", get=getCreateLayer, set=setCreateLayer)

    def updateVisibility( self ):
        pass

    def draw(self, context):
        pass

    def execute(self, context):
        from .blender_plugin import plugin
        from .blender_importer import BlenderModelImporter
        from .mtlib import target

        def _execute():
            plugin.logger.clear()
            plugin.config.save()
            plugin.config.dump()
            target.setTarget( target.supported[plugin.config.target].name )
            
            importer = BlenderModelImporter()
            importer.importModel( plugin.config.importFilePath )
            if plugin.logger.hasError():
                self.report( {'ERROR'}, "Import completed with one or more errors." )
            else:
                self.report( {'INFO'}, 'Import completed successfully' )
        if plugin.isDebugEnv():
            _execute()
        else:
            try:
                _execute()
            except Exception as e:
                self.report( {'ERROR'}, f'A fatal error occured during import.\n{e.message}' )
        return {'FINISHED'}

class MOD_PT_import_general(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "General"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "IMPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "flipUpAxis")
        layout.prop(operator, "lukasCompat")
        layout.prop(operator, "target")

class MOD_PT_import_import(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Import"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "IMPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "importMetadataPath")

class MOD_PT_import_filters(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Import filters"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "IMPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        
        layout.prop(operator, "importWeights")
        layout.prop(operator, "importNormals")
        layout.prop(operator, "importGroups")
        layout.prop(operator, "importSkeleton")
        layout.prop(operator, "importPrimitives")

class MOD_PT_import_additional(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Additional options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "IMPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "importScale")
        layout.prop(operator, "importBakeScale")
        layout.prop(operator, "importConvertTexturesToDDS")
        layout.prop(operator, "importSaveMrlYml")
        layout.prop(operator, "importCreateLayer")


#@orientation_helper(axis_forward='-Z', axis_up='Y')
class MOD_OT_export(bpy.types.Operator, ExportHelper):
    """Export MT Framework *.mod model"""
    bl_idname = "export_scene.mod"
    bl_label = "Export MOD"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".mod"
    filter_glob: StringProperty(default="*.mod", options={'HIDDEN'})

    def getMaterialPresets(self, context):
        from .mtlib.immaterial import imMaterialInfo

        items = []
        for presetName in imMaterialInfo.TEMPLATE_MATERIALS:
            items.append((presetName, presetName, presetName))
        return tuple(items)

    def getTargetItems(self, context):
        from .mtlib import target

        items = []
        for i, t in enumerate(target.supported):
            items.append((str(i), t.description, t.description))
        return tuple(items)

    def getFlipUpAxis(self): return getConfigValue('flipUpAxis')
    def setFlipUpAxis(self, value): setConfigValue('flipUpAxis', value)

    def getLukasCompat(self): return getConfigValue('lukasCompat')
    def setLukasCompat(self, value): setConfigValue('lukasCompat', value)

    def getTarget(self): return getConfigValue('target')
    def setTarget(self, value): setConfigValue('target', value)

    def getExportFilePath(self): return getConfigValue('exportFilePath')
    def setExportFilePath(self, value): 
        from .blender_plugin import plugin
        from .mtlib.metadata import ModelMetadata

        plugin.config.exportFilePath = value
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( plugin.config.exportFilePath ).split('.')[0] )
        if os.path.exists( newMetadataPath ):
            plugin.config.exportMetadataPath = newMetadataPath
            self.exportMetadataPath = newMetadataPath

    def getExportRoot(self): return getConfigValue('exportRoot')
    def setExportRoot(self, value): setConfigValue('exportRoot', value)

    def getExportRefPath(self): return getConfigValue('exportRefPath')
    def setExportRefPath(self, value): setConfigValue('exportRefPath', value)
    
    def getExportMetadataPath(self): return getConfigValue('exportMetadataPath')
    def setExportMetadataPath(self, value): setConfigValue('exportMetadataPath', value)

    def getExportWeights(self): return getConfigValue('exportWeights')
    def setExportWeights(self, value): setConfigValue('exportWeights', value)

    def getExportNormals(self): return getConfigValue('exportNormals')
    def setExportNormals(self, value): setConfigValue('exportNormals', value)

    def getExportGroups(self): return getConfigValue('exportGroups')
    def setExportGroups(self, value): setConfigValue('exportGroups', value)

    def getExportSkeleton(self): return getConfigValue('exportSkeleton')
    def setExportSkeleton(self, value): setConfigValue('exportSkeleton', value)

    def getExportPrimitives(self): return getConfigValue('exportPrimitives')
    def setExportPrimitives(self, value): setConfigValue('exportPrimitives', value)

    def getExportGenerateMrl(self): return getConfigValue('exportGenerateMrl')
    def setExportGenerateMrl(self, value): setConfigValue('exportGenerateMrl', value)

    def getExportMaterialPreset(self):
        from .blender_plugin import plugin
        from .mtlib.immaterial import imMaterialInfo
        for i, presetName in enumerate(imMaterialInfo.TEMPLATE_MATERIALS):
            if presetName == plugin.config.exportMaterialPreset:
                return i

    def setExportMaterialPreset(self, value):
        from .blender_plugin import plugin
        from .mtlib.immaterial import imMaterialInfo
        plugin.config.exportMaterialPreset = imMaterialInfo.TEMPLATE_MATERIALS[value]

    def getExportExistingMrlYml(self): return getConfigValue('exportExistingMrlYml')
    def setExportExistingMrlYml(self, value): setConfigValue('exportExistingMrlYml', value)

    def getExportMrlYmlPath(self): return getConfigValue('exportMrlYmlPath')
    def setExportMrlYmlPath(self, value): setConfigValue('exportMrlYmlPath', value)

    def getExportScale(self): return getConfigValue('exportScale')
    def setExportScale(self, value): setConfigValue('exportScale', value)

    def getExportBakeScale(self): return getConfigValue('exportBakeScale')
    def setExportBakeScale(self, value): setConfigValue('exportBakeScale', value)

    def getExportTexturesToTex(self): return getConfigValue('exportTexturesToTex')
    def setExportTexturesToTex(self, value): setConfigValue('exportTexturesToTex', value)

    def getExportOverwriteTextures(self): return getConfigValue('exportOverwriteTextures')
    def setExportOverwriteTextures(self, value): setConfigValue('exportOverwriteTextures', value)

    def getExportGroupPerMesh(self): return getConfigValue('exportGroupPerMesh')
    def setExportGroupPerMesh(self, value): setConfigValue('exportGroupPerMesh', value)

    def getExportGenerateEnvelopes(self): return getConfigValue('exportGenerateEnvelopes')
    def setExportGenerateEnvelopes(self, value): setConfigValue('exportGenerateEnvelopes', value)

    # General settings
    flipUpAxis: BoolProperty(name="Flip up axis", get=getFlipUpAxis, set=setFlipUpAxis)
    lukasCompat: BoolProperty(name="Compatibility with Lukas' script", get=getLukasCompat, set=setLukasCompat)
    target: EnumProperty(name="Game", items=getTargetItems, get=getTarget, set=setTarget)

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH',
        get=getExportFilePath,
        set=setExportFilePath,
    )
    exportRoot: StringProperty(name="Extracted archive directory", subtype="DIR_PATH", get=getExportRoot, set=setExportRoot)
    exportRefPath: StringProperty(name="Reference/original model file (optional)", subtype="FILE_PATH", get=getExportRefPath, set=setExportRefPath)
    exportMetadataPath: StringProperty(name="Metadata file (optional)", subtype="FILE_PATH", get=getExportMetadataPath, set=setExportMetadataPath)

    # Export filters
    exportWeights: BoolProperty(name="Weights", get=getExportWeights, set=setExportWeights)
    exportNormals: BoolProperty(name="Explicit normals", get=getExportNormals, set=setExportNormals)
    exportGroups: BoolProperty(name="Groups", get=getExportGroups, set=setExportGroups)
    exportSkeleton: BoolProperty(name="Skeleton", get=getExportSkeleton, set=setExportSkeleton)
    exportPrimitives: BoolProperty(name="Meshes", get=getExportPrimitives, set=setExportPrimitives)

    # Generate MRL
    exportGenerateMrl: BoolProperty(name="Enable", get=getExportGenerateMrl, set=setExportGenerateMrl)
    exportMaterialPreset: EnumProperty(name="Material preset",
        items=getMaterialPresets,
        get=getExportMaterialPreset,
        set=setExportMaterialPreset
    )

    # Use existing MRL YML
    exportExistingMrlYml: BoolProperty(name="Enable", get=getExportExistingMrlYml, set=setExportExistingMrlYml)
    exportMrlYmlPath: StringProperty(name="File path", subtype="FILE_PATH", get=getExportMrlYmlPath, set=setExportMrlYmlPath)

    # Additional options
    exportScale: FloatProperty(name="Scale", get=getExportScale, set=setExportScale)
    exportBakeScale: BoolProperty(name="Bake scale into translation", get=getExportBakeScale, set=setExportBakeScale)
    exportTexturesToTex: BoolProperty(name="Convert textures to TEX", get=getExportTexturesToTex, set=setExportTexturesToTex)
    exportOverwriteTextures: BoolProperty(name="Overwrite existing textures", get=getExportOverwriteTextures, set=setExportOverwriteTextures)
    exportGroupPerMesh: BoolProperty(name="Export group per mesh", get=getExportGroupPerMesh, set=setExportGroupPerMesh)
    exportGenerateEnvelopes: BoolProperty(name="Generate envelopes", get=getExportGenerateEnvelopes, set=setExportGenerateEnvelopes)

    def updateVisibility( self ):
        pass

    def draw(self, context):
        pass

    def execute(self, context):
        from .blender_plugin import plugin
        from .blender_exporter import BlenderModelExporter
        from .mtlib import target

        def _execute():
            plugin.logger.clear()
            plugin.config.save()
            plugin.config.dump()
            target.setTarget( target.supported[plugin.config.target].name )
            
            exporter = BlenderModelExporter()
            exporter.exportModel( plugin.config.exportFilePath )
            if plugin.logger.hasError():
                self.report( {'ERROR'}, "Export completed with one or more errors." )
            else:
                self.report( {'INFO'}, 'Export completed successfully' )
        if plugin.isDebugEnv():
            _execute()
        else:
            try:
                _execute()
            except Exception as e:
                self.report( {'ERROR'}, f'A fatal error occured during export.\n{e.message}' )
        return {'FINISHED'}

class MOD_PT_export_general(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "General"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "EXPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "flipUpAxis")
        layout.prop(operator, "lukasCompat")
        layout.prop(operator, "target")

class MOD_PT_export_export(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Export"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "EXPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "exportRoot")
        layout.prop(operator, "exportRefPath")
        layout.prop(operator, "exportMetadataPath")

class MOD_PT_export_filters(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Export filters"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "EXPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "exportWeights")
        layout.prop(operator, "exportNormals")
        layout.prop(operator, "exportGroups")
        layout.prop(operator, "exportSkeleton")
        layout.prop(operator, "exportPrimitives")

class MOD_PT_export_generate_mrl(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Generate MRL"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "EXPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "exportGenerateMrl")
        layout.prop(operator, "exportMaterialPreset")

class MOD_PT_export_existing_mrl(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Use existing MRL YML"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "EXPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "exportExistingMrlYml")
        layout.prop(operator, "exportMrlYmlPath")

class MOD_PT_export_additional(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Additional options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in "EXPORT_SCENE_OT_mod"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "exportScale")
        layout.prop(operator, "exportBakeScale")
        layout.prop(operator, "exportTexturesToTex")
        layout.prop(operator, "exportOverwriteTextures")
        layout.prop(operator, "exportGroupPerMesh")
        layout.prop(operator, "exportGenerateEnvelopes")


def menu_func_import(self, context):
    self.layout.operator(MOD_OT_import.bl_idname, text="MT Framework Model (.mod)")

def menu_func_export(self, context):
    self.layout.operator(MOD_OT_export.bl_idname, text="MT Framework Model (.mod)")

classes = (
    MOD_OT_import,
    MOD_PT_import_general,
    MOD_PT_import_import,
    MOD_PT_import_filters,
    MOD_PT_import_additional,

    MOD_OT_export,
    MOD_PT_export_general,
    MOD_PT_export_export,
    MOD_PT_export_filters,
    MOD_PT_export_generate_mrl,
    MOD_PT_export_existing_mrl,
    MOD_PT_export_additional
)

def register():
    reload()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    from .blender_plugin import plugin
    plugin.load()
    plugin.logger.info(f'script version: {plugin.version}')

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    bpy.ops.import_scene.mod('INVOKE_DEFAULT')