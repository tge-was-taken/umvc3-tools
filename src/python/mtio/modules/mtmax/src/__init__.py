# 3ds Max MT Framework model import/export plugin
# Note: rollout classes must be defined in this module to be accessible to MaxScript

# fix imports
__package__ = 'modules.mtmax.src'
import os
import sys
import traceback

from pymxs import runtime as rt
from ...mtlib import *
from max_exporter import *
from max_importer import *
from max_plugin import plugin
from mtlib import log

def _handleException( e, brief ):
    plugin.logger.exception( e )
    plugin.showExceptionMessageBox( brief, e )
    if plugin.config.showLogOnError:
        plugin.openLogFile()
    else:
        plugin.openListener()

class MtRollout:
    @classmethod
    def onEvent( cls, e, *args ):
        try:
            plugin.logger.debug(f'received event: {e} with args: {args}')
            if hasattr(cls, e):
                getattr(cls, e)(*args)
            else:
                plugin.logger.debug(f'no event handler for {e}')

            if hasattr( cls, 'updateVisibility'): 
                cls.updateVisibility()
            else:
                plugin.logger.debug(f'no update visibility handler defined in {cls}')

            plugin.config.save()
        except Exception as e:
            _handleException( e, 'A fatal error occured while processing user input' )
            
    @classmethod
    def getMxsVar( cls ):
        assert( hasattr( rt, cls.__name__ ) )
        return getattr( rt, cls.__name__ )
    
class MtMaxInfoRollout(MtRollout):
    @staticmethod
    def loadConfig():
        self = MtMaxInfoRollout.getMxsVar()
    
class MtMaxSettingsRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        pass

    @staticmethod
    def loadConfig():
        self = MtMaxSettingsRollout.getMxsVar()
        self.chkFlipUpAxis.checked = plugin.config.flipUpAxis
        if plugin.config.target >= len(target.supported):
            plugin.config.target = 0
        self.ddlGame.selection = plugin.config.target+1
        target.setTarget( target.supported[plugin.config.target].name )
        self.chkLukasCompat.checked = plugin.config.lukasCompat
    
    @staticmethod
    def chkFlipUpAxisChanged( state ):
        plugin.config.flipUpAxis = state
    
    @staticmethod
    def ddlGameSelected( i ):
        i = i-1
        plugin.config.target = i
        target.setTarget( target.supported[i].name )
        
    @staticmethod
    def chkLukasCompatChanged( state ):
        plugin.config.lukasCompat = state
        
class MtMaxModelImportRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        rt.MtMaxModelImportRollout.btnImport.enabled = \
            os.path.isfile( plugin.config.importFilePath )
            
    @staticmethod
    def loadConfig():
        self = MtMaxModelImportRollout.getMxsVar()
        self.edtFile.text = plugin.config.importFilePath
        self.edtMetadata.text = plugin.config.importMetadataPath
        self.chkImportWeights.checked = plugin.config.importWeights
        self.chkImportNormals.checked = plugin.config.importNormals
        self.chkImportGroups.checked = plugin.config.importGroups
        self.chkImportSkeleton.checked = plugin.config.importSkeleton
        self.chkImportPrimitives.checked = plugin.config.importPrimitives
        self.chkConvertDDS.checked = plugin.config.importConvertTexturesToDDS
        self.chkSaveMrlYml.checked = plugin.config.importSaveMrlYml
        self.chkCreateLayer.checked = plugin.config.importCreateLayer
        self.spnScale.value = plugin.config.importScale
        self.chkBakeScale.checked = plugin.config.importBakeScale
        MtMaxModelImportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        plugin.config.importFilePath = path
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( plugin.config.importFilePath ).split('.')[0] )
        if os.path.exists( newMetadataPath ):
            plugin.config.importMetadataPath = newMetadataPath
        MtMaxModelImportRollout.loadConfig()
    
    @staticmethod
    def chkImportWeightsChanged( state ):
        plugin.config.importWeights = state
    
    @staticmethod
    def btnImportPressed():
        try:
            plugin.logger.clear()
            plugin.config.dump()
            
            importer = MaxModelImporter()
            importer.importModel( plugin.config.importFilePath )
            if plugin.logger.hasError():
                plugin.showErrorMessageBox( "Import completed with one or more errors.", '' )
                plugin.openListener()
            else:
                plugin.showMessageBox( 'Import completed successfully' )
        except Exception as e:
            _handleException( e, 'A fatal error occured during import.' )
            
        
        
    @staticmethod
    def btnFilePressed():
        path = plugin.selectOpenFile( 'MT Framework model', 'mod' )
        if path == None:
            return
        
        MtMaxModelImportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtMaxModelImportRollout.setFilePath( state )
        
    @staticmethod
    def edtMetadataChanged( state ):
        plugin.config.importMetadataPath = state
        
    @staticmethod
    def btnMetadataPressed():
        path = plugin.selectOpenFile( 'MT Framework model metadata', 'yml' )
        if path == None:
            return
        
        plugin.config.importMetadataPath = path
        
    @staticmethod
    def chkImportNormalsChanged( state ):
        plugin.config.importNormals = state
        
    @staticmethod
    def chkImportGroupsChanged( state ):
        plugin.config.importGroups = state
    
    @staticmethod
    def chkImportSkeletonChanged( state ):
        plugin.config.importSkeleton = state
        
    @staticmethod
    def chkConvertDDSChanged( state ):
        plugin.config.importConvertTexturesToDDS = state
        
    @staticmethod
    def chkSaveMrlYmlChanged( state ):
        plugin.config.importSaveMrlYml = state
        
    @staticmethod
    def chkImportPrimitivesChanged( state ):
        plugin.config.importPrimitives = state
        
    @staticmethod
    def chkCreateLayerChanged( state ):
        plugin.config.importCreateLayer = state
        
    @staticmethod
    def spnScaleChanged( state ):
        plugin.config.importScale = state
        
    @staticmethod
    def chkBakeScaleChanged( state ):
        plugin.config.importBakeScale = state

        
class MtMaxModelExportRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        self = MtMaxModelExportRollout.getMxsVar()
        self.btnExport.enabled = plugin.config.exportFilePath.strip() != '' and plugin.config.exportRoot.strip() != ''
        self.edtMrlYml.enabled = not plugin.config.exportGenerateMrl and plugin.config.exportExistingMrlYml
        self.btnMrlYml.enabled = not plugin.config.exportGenerateMrl and plugin.config.exportExistingMrlYml
        self.chkExportMrl.enabled = not plugin.config.exportGenerateMrl
        self.chkExportGenerateMrl.enabled = not plugin.config.exportExistingMrlYml
        self.cbxExportMaterialPreset.enabled = plugin.config.exportGenerateMrl
    
    @staticmethod
    def loadConfig():
        self = MtMaxModelExportRollout.getMxsVar()
        self.edtFile.text = plugin.config.exportFilePath
        self.edtMetadata.text = plugin.config.exportMetadataPath
        self.edtRef.text = plugin.config.exportRefPath
        self.edtMrlYml.text = plugin.config.exportMrlYmlPath
        self.edtRoot.text = plugin.config.exportRoot
        self.chkExportWeights.checked = plugin.config.exportWeights
        self.chkExportGroups.checked = plugin.config.exportGroups
        self.chkExportSkeleton.checked = plugin.config.exportSkeleton
        self.chkExportPrimitives.checked = plugin.config.exportPrimitives
        self.chkExportTex.checked = plugin.config.exportTexturesToTex
        self.chkExportMrl.checked = plugin.config.exportExistingMrlYml
        self.chkExportGenerateMrl.checked = plugin.config.exportGenerateMrl
        self.chkExportTexOverwrite.checked = plugin.config.exportOverwriteTextures
        self.spnScale.value = plugin.config.exportScale
        self.chkBakeScale.checked = plugin.config.exportBakeScale
        self.chkExportNormals.checked = plugin.config.exportNormals
        self.chkExportGroupPerMesh.checked = plugin.config.exportGroupPerMesh
        self.chkExportGenerateEnvelopes.checked = plugin.config.exportGenerateEnvelopes
        self.cbxExportMaterialPreset.items = plugin.toMaxArray( imMaterialInfo.TEMPLATE_MATERIALS )
        self.cbxExportMaterialPreset.selection = rt.findItem(self.cbxExportMaterialPreset.items, plugin.config.exportMaterialPreset)
        MtMaxModelExportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        plugin.config.exportFilePath = path
        if not os.path.exists( plugin.config.exportMetadataPath ): 
            newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( plugin.config.exportFilePath ).split('.')[0] )
            if os.path.exists( newMetadataPath ):
                plugin.config.exportMetadataPath = newMetadataPath
        MtMaxModelExportRollout.loadConfig()

    @staticmethod
    def setRefFilePath( path ):
        plugin.config.exportRefPath = path
        if not os.path.exists( plugin.config.exportMetadataPath ):
            newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( plugin.config.exportRefPath ).split('.')[0] )
            if os.path.exists( newMetadataPath ): 
                plugin.config.exportMetadataPath = newMetadataPath
        MtMaxModelExportRollout.loadConfig()
        
    @staticmethod
    def setMrlYmlFilePath( path ):
        plugin.config.exportMrlYmlPath = path
        MtMaxModelExportRollout.loadConfig()
    
    @staticmethod
    def chkExportWeightsChanged( state ):
        plugin.config.importWeights = state
    
    @staticmethod
    def btnExportPressed():
        try:
            plugin.logger.clear()
            plugin.config.dump()
            
            exporter = MaxModelExporter()
            #exporter = MtModelExporter()
            exporter.exportModel( plugin.config.exportFilePath )
            if plugin.logger.hasError():
                plugin.showErrorMessageBox( "Export completed with one or more errors." )
                plugin.openListener()
            else:
                plugin.showMessageBox( 'Export completed successfully' )
                
        except Exception as e:
            _handleException( e, 'A fatal error occured during export.' )
        
    @staticmethod
    def btnFilePressed():
        path = plugin.selectSaveFile( 'MT Framework model', 'mod' )
        if path == None:
            return
        
        MtMaxModelExportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtMaxModelExportRollout.setFilePath( state )
        
    @staticmethod
    def edtMetadataChanged( state ):
        plugin.config.exportMetadataPath = state
        
    @staticmethod
    def btnMetadataPressed():
        path = plugin.selectOpenFile( 'MT Framework model metadata', 'yml' )
        if path == None:
            return
        
        plugin.config.exportMetadataPath = path

    @staticmethod
    def edtRefChanged( state ):
        MtMaxModelExportRollout.setRefFilePath( state )
        
    @staticmethod
    def btnRefPressed():
        path = plugin.selectOpenFile( 'MT Framework model', 'mod' )
        if path == None:
            return
        
        MtMaxModelExportRollout.setRefFilePath( path )
        
    @staticmethod
    def edtMrlYmlChanged( state ):
        MtMaxModelExportRollout.setMrlYmlFilePath( state )
        
    @staticmethod
    def btnMrlYmlPressed():
        path = plugin.selectOpenFile( 'MT Framework MRL YML', 'yml' )
        if path == None:
            return
        
        MtMaxModelExportRollout.setMrlYmlFilePath( path )
        
    @staticmethod
    def chkExportNormalsChanged( state ):
        plugin.config.exportNormals = state
        
    @staticmethod
    def chkExportGroupsChanged( state ):
        plugin.config.exportGroups = state
    
    @staticmethod
    def chkExportSkeletonChanged( state ):
        plugin.config.exportSkeleton = state
        
    @staticmethod
    def chkExportTexChanged( state ):
        plugin.config.exportTexturesToTex = state
        
    @staticmethod
    def chkExportMrlChanged( state ):
        plugin.config.exportExistingMrlYml = state
        
    @staticmethod
    def chkExportPrimitivesChanged( state ):
        plugin.config.exportPrimitives = state
        
    @staticmethod
    def chkExportWeightsChanged( state ):
        plugin.config.exportWeights = state
        
    @staticmethod
    def chkExportGenerateMrlChanged( state ):
        plugin.config.exportGenerateMrl = state
        
    @staticmethod
    def edtRootChanged( state ):
        plugin.config.exportRoot = state
        
    @staticmethod
    def btnRootPressed():
        path = rt.getSavePath( caption="Select a folder", initialDir=os.path.dirname(plugin.config.exportFilePath) )
        if path == None:
            return
        
        plugin.config.exportRoot = os.path.abspath( path ).replace( "\\", "/" )
        MtMaxModelExportRollout.loadConfig()
        
    @staticmethod
    def chkExportTexOverwriteChanged( state ):
        plugin.config.exportOverwriteTextures = state
        
    @staticmethod
    def spnScaleChanged( state ):
        plugin.config.exportScale = state
        
    @staticmethod
    def chkBakeScaleChanged( state ):
        plugin.config.exportBakeScale = state
        
    @staticmethod
    def chkExportGroupPerMeshChanged( state ):
        plugin.config.exportGroupPerMesh = state
        
    @staticmethod
    def chkExportGenerateEnvelopesChanged( state ):
        plugin.config.exportGenerateEnvelopes = state
        
    @staticmethod
    def cbxExportMaterialPresetSelected( state ):
        plugin.config.exportMaterialPreset = state

class MtMaxUtilitiesRollout(MtRollout):
    @staticmethod
    def loadConfig():
        pass

    def _addAttributeToSelection(attr):
        selection = list(rt.selection)
        
        if len(selection) == 0:
            return
        for node in selection: 
            rt.custAttributes.add( node, attr )
            
    def _removeAttributeFromSelection(attr):
        selection = list(rt.selection)
        
        if len(selection) == 0:
            return
        for node in selection: 
            rt.custAttributes.delete( node, attr )

    @staticmethod
    def btnAddJointAttribsPressed():
        MtMaxUtilitiesRollout._addAttributeToSelection( rt.MtMaxJointAttributesInstance )

    @staticmethod
    def btnAddGroupAttribsPressed():
        MtMaxUtilitiesRollout._addAttributeToSelection( rt.MtMaxGroupAttributesInstance )

    @staticmethod
    def btnAddPrimAttribsPressed():
        MtMaxUtilitiesRollout._addAttributeToSelection( rt.MtMaxPrimitiveAttributesInstance )
        
    @staticmethod
    def btnRemJointAttribsPressed():
        MtMaxUtilitiesRollout._removeAttributeFromSelection( rt.MtMaxJointAttributesInstance )

    @staticmethod
    def btnRemGroupAttribsPressed():
        MtMaxUtilitiesRollout._removeAttributeFromSelection( rt.MtMaxGroupAttributesInstance )

    @staticmethod
    def btnRemPrimAttribsPressed():
        MtMaxUtilitiesRollout._removeAttributeFromSelection( rt.MtMaxPrimitiveAttributesInstance )

    @staticmethod
    def btnCreateGroupPressed():
        group = rt.dummy()
        group.name = "New group"
        rt.custAttributes.add( group, rt.MtMaxGroupAttributesInstance )
        rt.select( group )
        
class MtMaxDebugRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        self = MtMaxDebugRollout.getMxsVar()
    
    @staticmethod
    def loadConfig():
        self = MtMaxDebugRollout.getMxsVar()
        self.chkDisableLog.checked = plugin.config.debugDisableLog
        self.chkDisableTransform.checked = plugin.config.debugDisableTransform
        MtMaxDebugRollout.updateVisibility()
        
    @staticmethod
    def chkDisableLogChanged( state ):
        plugin.config.debugDisableLog = state
        
    @staticmethod
    def edtExportForceShaderChanged( state ):
        plugin.config.debugExportForceShader = state
        
    @staticmethod
    def chkDisableTransformChanged( state ):
        plugin.config.debugDisableTransform = state
    
    
def getMainWindow():
    return rt.g_mtWindow
    
def createMainWindow():
    # get coords of window if it's already opened
    x = 30
    y = 100
    w = 600
    h = 700
    
    # ensure a variable exists even if it hasnt been created yet
    rt.execute( 'g_mtWindow2 = g_mtWindow' )
    if rt.g_mtWindow2 != None:
        x = rt.g_mtWindow2.pos.x
        y = rt.g_mtWindow2.pos.y
        w = rt.g_mtWindow2.size.x
        h = rt.g_mtWindow2.size.y
        rt.closeRolloutFloater( rt.g_mtWindow2 )
        
    # create plugin window
    rt.g_mtWindow = rt.newRolloutFloater( "MT Framework Max IO Plugin", w, h, x, y )
    rollouts = [MtMaxInfoRollout, MtMaxSettingsRollout, MtMaxModelImportRollout, MtMaxModelExportRollout, MtMaxUtilitiesRollout]
    if plugin.isDebugEnv():
        rollouts.insert(0, MtMaxDebugRollout)
        
    for rollout in rollouts:
        rollout.getMxsVar().width = w
        rollout.getMxsVar().height = h
        rt.addRollout( rollout.getMxsVar(), rt.g_mtWindow )
        rollout.loadConfig()
    
def main():
    plugin.load()
    rt.MtMaxVersion = plugin.version
    
    plugin.logger.info(f'script version: {plugin.version}')
    
    # increase heap size to improve stability
    heapSize = 512
    while rt.heapSize < heapSize: 
        try:
            rt.heapSize = 1024 * 1024 * heapSize
        except:
            heapSize /= 2
    
    # force garbage colleciton
    rt.gc()
    rt.gc()
    
    # import maxscript files
    plugin.runMaxScript( 'customattributes.ms' )
    plugin.runMaxScript( 'rollouts.ms' )
    createMainWindow()
    
    rt.gc()
    rt.gc()
    
if __name__ == '__main__':
    main()