# 3ds Max MT Framework model import/export plugin
# Note: rollout classes must be defined in this module to be accessible to MaxScript

# fix imports
import os
import sys
import traceback

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
from mtmaxexp import *
from mtmaximp import *
import mtmaxutil
import mtmaxlog
import mtmaxver
from mtlib import log

def _handleException( e, brief ):
    mtmaxlog.exception( e )
    mtmaxutil.showExceptionMessageBox( brief, e )
    if mtmaxconfig.showLogOnError:
        mtmaxutil.openLogFile()
    else:
        mtmaxutil.openListener()

class MtRollout:
    @classmethod
    def onEvent( cls, e, *args ):
        try:
            mtmaxlog.debug(f'received event: {e} with args: {args}')
            if hasattr(cls, e):
                getattr(cls, e)(*args)
            else:
                mtmaxlog.debug(f'no event handler for {e}')

            if hasattr( cls, 'updateVisibility'): 
                cls.updateVisibility()
            else:
                mtmaxlog.debug(f'no update visibility handler defined in {cls}')

            mtmaxconfig.save()
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
        self.chkFlipUpAxis.checked = mtmaxconfig.flipUpAxis
    
    @staticmethod
    def chkFlipUpAxisChanged( state ):
        mtmaxconfig.flipUpAxis = state
        
class MtMaxModelImportRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        rt.MtMaxModelImportRollout.btnImport.enabled = \
            os.path.isfile( mtmaxconfig.importFilePath )
            
    @staticmethod
    def loadConfig():
        self = MtMaxModelImportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.importFilePath
        self.edtMetadata.text = mtmaxconfig.importMetadataPath
        self.chkImportWeights.checked = mtmaxconfig.importWeights
        self.chkImportNormals.checked = mtmaxconfig.importNormals
        self.chkImportGroups.checked = mtmaxconfig.importGroups
        self.chkImportSkeleton.checked = mtmaxconfig.importSkeleton
        self.chkImportPrimitives.checked = mtmaxconfig.importPrimitives
        self.chkConvertDDS.checked = mtmaxconfig.importConvertTexturesToDDS
        self.chkSaveMrlYml.checked = mtmaxconfig.importSaveMrlYml
        self.chkCreateLayer.checked = mtmaxconfig.importCreateLayer
        self.spnScale.value = mtmaxconfig.importScale
        self.chkBakeScale.checked = mtmaxconfig.importBakeScale
        MtMaxModelImportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        mtmaxconfig.importFilePath = path
        newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mtmaxconfig.importFilePath ).split('.')[0] )
        if os.path.exists( newMetadataPath ):
            mtmaxconfig.importMetadataPath = newMetadataPath
        MtMaxModelImportRollout.loadConfig()
    
    @staticmethod
    def chkImportWeightsChanged( state ):
        mtmaxconfig.importWeights = state
    
    @staticmethod
    def btnImportPressed():
        try:
            mtmaxlog.clear()
            mtmaxconfig.dump()
            
            importer = MtModelImporter()
            importer.importModel( mtmaxconfig.importFilePath )
            if mtmaxlog.hasError():
                mtmaxutil.showErrorMessageBox( "Import completed with one or more errors.", '' )
                mtmaxutil.openListener()
            else:
                mtmaxutil.showMessageBox( 'Import completed successfully' )
        except Exception as e:
            _handleException( e, 'A fatal error occured during import.' )
            
        
        
    @staticmethod
    def btnFilePressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model', 'mod' )
        if path == None:
            return
        
        MtMaxModelImportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtMaxModelImportRollout.setFilePath( state )
        
    @staticmethod
    def edtMetadataChanged( state ):
        mtmaxconfig.importMetadataPath = state
        
    @staticmethod
    def btnMetadataPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model metadata', 'yml' )
        if path == None:
            return
        
        mtmaxconfig.importMetadataPath = path
        
    @staticmethod
    def chkImportNormalsChanged( state ):
        mtmaxconfig.importNormals = state
        
    @staticmethod
    def chkImportGroupsChanged( state ):
        mtmaxconfig.importGroups = state
    
    @staticmethod
    def chkImportSkeletonChanged( state ):
        mtmaxconfig.importSkeleton = state
        
    @staticmethod
    def chkConvertDDSChanged( state ):
        mtmaxconfig.importConvertTexturesToDDS = state
        
    @staticmethod
    def chkSaveMrlYmlChanged( state ):
        mtmaxconfig.importSaveMrlYml = state
        
    @staticmethod
    def chkImportPrimitivesChanged( state ):
        mtmaxconfig.importPrimitives = state
        
    @staticmethod
    def chkCreateLayerChanged( state ):
        mtmaxconfig.importCreateLayer = state
        
    @staticmethod
    def spnScaleChanged( state ):
        mtmaxconfig.importScale = state
        
    @staticmethod
    def chkBakeScaleChanged( state ):
        mtmaxconfig.importBakeScale = state

        
class MtMaxModelExportRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        self = MtMaxModelExportRollout.getMxsVar()
        self.btnExport.enabled = mtmaxconfig.exportFilePath.strip() != '' and mtmaxconfig.exportRoot.strip() != ''
        self.edtMrlYml.enabled = not mtmaxconfig.exportGenerateMrl and mtmaxconfig.exportExistingMrlYml
        self.btnMrlYml.enabled = not mtmaxconfig.exportGenerateMrl and mtmaxconfig.exportExistingMrlYml
        self.chkExportMrl.enabled = not mtmaxconfig.exportGenerateMrl
        self.chkExportGenerateMrl.enabled = not mtmaxconfig.exportExistingMrlYml
        self.cbxExportMaterialPreset.enabled = mtmaxconfig.exportGenerateMrl
    
    @staticmethod
    def loadConfig():
        self = MtMaxModelExportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.exportFilePath
        self.edtMetadata.text = mtmaxconfig.exportMetadataPath
        self.edtRef.text = mtmaxconfig.exportRefPath
        self.edtMrlYml.text = mtmaxconfig.exportMrlYmlPath
        self.edtRoot.text = mtmaxconfig.exportRoot
        self.chkExportWeights.checked = mtmaxconfig.exportWeights
        self.chkExportGroups.checked = mtmaxconfig.exportGroups
        self.chkExportSkeleton.checked = mtmaxconfig.exportSkeleton
        self.chkExportPrimitives.checked = mtmaxconfig.exportPrimitives
        self.chkExportTex.checked = mtmaxconfig.exportTexturesToTex
        self.chkExportMrl.checked = mtmaxconfig.exportExistingMrlYml
        self.chkExportGenerateMrl.checked = mtmaxconfig.exportGenerateMrl
        self.chkExportTexOverwrite.checked = mtmaxconfig.exportOverwriteTextures
        self.spnScale.value = mtmaxconfig.exportScale
        self.chkBakeScale.checked = mtmaxconfig.exportBakeScale
        self.chkExportNormals.checked = mtmaxconfig.exportNormals
        self.chkExportGroupPerMesh.checked = mtmaxconfig.exportGroupPerMesh
        self.chkExportGeneratePjl.checked = mtmaxconfig.exportGeneratePjl
        self.cbxExportMaterialPreset.items = mtmaxutil.toMaxArray( imMaterialInfo.TEMPLATE_MATERIALS )
        self.cbxExportMaterialPreset.selection = rt.findItem(self.cbxExportMaterialPreset.items, mtmaxconfig.exportMaterialPreset)
        MtMaxModelExportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        mtmaxconfig.exportFilePath = path
        if not os.path.exists( mtmaxconfig.exportMetadataPath ): 
            newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mtmaxconfig.exportFilePath ).split('.')[0] )
            if os.path.exists( newMetadataPath ):
                mtmaxconfig.exportMetadataPath = newMetadataPath
        MtMaxModelExportRollout.loadConfig()

    @staticmethod
    def setRefFilePath( path ):
        mtmaxconfig.exportRefPath = path
        if not os.path.exists( mtmaxconfig.exportMetadataPath ):
            newMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mtmaxconfig.exportRefPath ).split('.')[0] )
            if os.path.exists( newMetadataPath ): 
                mtmaxconfig.exportMetadataPath = newMetadataPath
        MtMaxModelExportRollout.loadConfig()
        
    @staticmethod
    def setMrlYmlFilePath( path ):
        mtmaxconfig.exportMrlYmlPath = path
        MtMaxModelExportRollout.loadConfig()
    
    @staticmethod
    def chkExportWeightsChanged( state ):
        mtmaxconfig.importWeights = state
    
    @staticmethod
    def btnExportPressed():
        try:
            mtmaxlog.clear()
            mtmaxconfig.dump()
            
            exporter = MtModelExporter()
            exporter.exportModel( mtmaxconfig.exportFilePath )
            if mtmaxlog.hasError():
                mtmaxutil.showErrorMessageBox( "Export completed with one or more errors." )
                mtmaxutil.openListener()
            else:
                mtmaxutil.showMessageBox( 'Export completed successfully' )
                
        except Exception as e:
            _handleException( e, 'A fatal error occured during export.' )
        
    @staticmethod
    def btnFilePressed():
        path = mtmaxutil.selectSaveFile( 'UMVC3 model', 'mod' )
        if path == None:
            return
        
        MtMaxModelExportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtMaxModelExportRollout.setFilePath( state )
        
    @staticmethod
    def edtMetadataChanged( state ):
        mtmaxconfig.exportMetadataPath = state
        
    @staticmethod
    def btnMetadataPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model metadata', 'yml' )
        if path == None:
            return
        
        mtmaxconfig.exportMetadataPath = path

    @staticmethod
    def edtRefChanged( state ):
        MtMaxModelExportRollout.setRefFilePath( state )
        
    @staticmethod
    def btnRefPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model', 'mod' )
        if path == None:
            return
        
        MtMaxModelExportRollout.setRefFilePath( path )
        
    @staticmethod
    def edtMrlYmlChanged( state ):
        MtMaxModelExportRollout.setMrlYmlFilePath( state )
        
    @staticmethod
    def btnMrlYmlPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 MRL YML', 'yml' )
        if path == None:
            return
        
        MtMaxModelExportRollout.setMrlYmlFilePath( path )
        
    @staticmethod
    def chkExportNormalsChanged( state ):
        mtmaxconfig.exportNormals = state
        
    @staticmethod
    def chkExportGroupsChanged( state ):
        mtmaxconfig.exportGroups = state
    
    @staticmethod
    def chkExportSkeletonChanged( state ):
        mtmaxconfig.exportSkeleton = state
        
    @staticmethod
    def chkExportTexChanged( state ):
        mtmaxconfig.exportTexturesToTex = state
        
    @staticmethod
    def chkExportMrlChanged( state ):
        mtmaxconfig.exportExistingMrlYml = state
        
    @staticmethod
    def chkExportPrimitivesChanged( state ):
        mtmaxconfig.exportPrimitives = state
        
    @staticmethod
    def chkExportWeightsChanged( state ):
        mtmaxconfig.exportWeights = state
        
    @staticmethod
    def chkExportGenerateMrlChanged( state ):
        mtmaxconfig.exportGenerateMrl = state
        
    @staticmethod
    def edtRootChanged( state ):
        mtmaxconfig.exportRoot = state
        
    @staticmethod
    def btnRootPressed():
        path = rt.getSavePath( caption="Select a folder", initialDir=os.path.dirname(mtmaxconfig.exportFilePath) )
        if path == None:
            return
        
        mtmaxconfig.exportRoot = os.path.abspath( path ).replace( "\\", "/" )
        MtMaxModelExportRollout.loadConfig()
        
    @staticmethod
    def chkExportTexOverwriteChanged( state ):
        mtmaxconfig.exportOverwriteTextures = state
        
    @staticmethod
    def spnScaleChanged( state ):
        mtmaxconfig.exportScale = state
        
    @staticmethod
    def chkBakeScaleChanged( state ):
        mtmaxconfig.exportBakeScale = state
        
    @staticmethod
    def chkExportGroupPerMeshChanged( state ):
        mtmaxconfig.exportGroupPerMesh = state
        
    @staticmethod
    def chkExportGeneratePjlChanged( state ):
        mtmaxconfig.exportGeneratePjl = state
        
    @staticmethod
    def cbxExportMaterialPresetSelected( state ):
        mtmaxconfig.exportMaterialPreset = state

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
        self.chkDisableLog.checked = mtmaxconfig.debugDisableLog
        MtMaxDebugRollout.updateVisibility()
        
    @staticmethod
    def chkDisableLogChanged( state ):
        mtmaxconfig.debugDisableLog = state
        
    @staticmethod
    def edtExportForceShaderChanged( state ):
        mtmaxconfig.debugExportForceShader = state
    
    
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
    if mtmaxutil.isDebugEnv():
        rollouts.insert(0, MtMaxDebugRollout)
        
    for rollout in rollouts:
        rollout.getMxsVar().width = w
        rollout.getMxsVar().height = h
        rt.addRollout( rollout.getMxsVar(), rt.g_mtWindow )
        rollout.loadConfig()
    
class MaxLogger():
    def debug( self, msg, *args ):
        mtmaxlog.debug( msg, *args )
    
    def info( self, msg, *args ):
        mtmaxlog.info( msg, *args )
    
    def warn( self, msg, *args ):
        mtmaxlog.warn( msg, *args )
    
    def error( self, msg, *args ):
        mtmaxlog.error( msg, *args )
    
def main():
    rt.MtMaxVersion = mtmaxver.version
    
    mtmaxlog.info(f'script version: {mtmaxver.version}')
    
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

    log.setLogger(MaxLogger())
    mtmaxconfig.load()
    
    # import maxscript files
    mtmaxutil.runMaxScript( 'customattributes.ms' )
    mtmaxutil.runMaxScript( 'rollouts.ms' )
    createMainWindow()
    
    rt.gc()
    rt.gc()
    
if __name__ == '__main__':
    main()