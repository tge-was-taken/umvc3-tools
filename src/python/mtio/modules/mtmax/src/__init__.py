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
import maxlog
import mtmaxver

class MtRollout:
    @classmethod
    def onEvent( cls, e, *args ):
        try:
            maxlog.debug(f'received event: {e} with args: {args}')
            if hasattr(cls, e):
                getattr(cls, e)(*args)
            else:
                maxlog.debug(f'no event handler for {e}')

            if hasattr( cls, 'updateVisibility'): 
                cls.updateVisibility()
            else:
                maxlog.debug(f'no update visibility handler defined in {cls}')

            mtmaxconfig.save()
        except Exception as e:
            maxlog.exception( e )
            mtmaxutil.showMessageBox( 'An error occured. See the log or the MaxScript listener for more details.', "Error" )

    @classmethod
    def getMxsVar( cls ):
        assert( hasattr( rt, cls.__name__ ) )
        return getattr( rt, cls.__name__ )
    
class MtInfoRollout(MtRollout):
    @staticmethod
    def loadConfig():
        self = MtInfoRollout.getMxsVar()
    
class MtSettingsRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        pass

    @staticmethod
    def loadConfig():
        self = MtSettingsRollout.getMxsVar()
        self.chkFlipUpAxis.checked = mtmaxconfig.flipUpAxis
        self.spnScale.value = mtmaxconfig.scale
    
    @staticmethod
    def chkFlipUpAxisChanged( state ):
        mtmaxconfig.flipUpAxis = state
        
    @staticmethod
    def spnScaleChanged( state ):
        mtmaxconfig.scale = state
        
class MtModelImportRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        rt.MtModelImportRollout.btnImport.enabled = \
            os.path.isfile( mtmaxconfig.importFilePath )
            
    @staticmethod
    def loadConfig():
        self = MtModelImportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.importFilePath
        self.edtMetadata.text = mtmaxconfig.importMetadataPath
        self.chkImportWeights.checked = mtmaxconfig.importWeights
        self.chkImportNormals.checked = mtmaxconfig.importNormals
        self.chkImportGroups.checked = mtmaxconfig.importGroups
        self.chkImportSkeleton.checked = mtmaxconfig.importSkeleton
        self.chkImportPrimitives.checked = mtmaxconfig.importPrimitives
        self.chkConvertDDS.checked = mtmaxconfig.importConvertTexturesToDDS
        self.chkSaveMrlYml.checked = mtmaxconfig.importSaveMrlYml
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        mtmaxconfig.importFilePath = path
        mtmaxconfig.importMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mtmaxconfig.importFilePath ).split('.')[0] )
        MtModelImportRollout.loadConfig()
    
    @staticmethod
    def chkImportWeightsChanged( state ):
        mtmaxconfig.importWeights = state
    
    @staticmethod
    def btnImportPressed():
        try:
            maxlog.clear()
            mtmaxconfig.dump()
            
            importer = MtModelImporter()
            importer.importModel( mtmaxconfig.importFilePath )
            if maxlog.hasError():
                mtmaxutil.showErrorMessageBox( "Import completed with one or more errors." )
            else:
                mtmaxutil.showMessageBox( 'Import completed successfully' )
        except Exception as e:
            maxlog.exception( e )
            mtmaxutil.showErrorMessageBox( "A fatal error occured during import." )
            
        
        
    @staticmethod
    def btnFilePressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model', 'mod' )
        if path == None:
            path = ''
        
        MtModelImportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtModelImportRollout.setFilePath( state )
        
    @staticmethod
    def edtMetadataChanged( state ):
        mtmaxconfig.importMetadataPath = state
        
    @staticmethod
    def btnMetadataPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model metadata', 'yml' )
        if path == None:
            path = ''
        
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
        
class MtModelExportRollout(MtRollout):
    @staticmethod
    def updateVisibility():
        self = MtModelExportRollout.getMxsVar()
        self.btnExport.enabled = mtmaxconfig.exportFilePath.strip() != '' and mtmaxconfig.exportRoot.strip() != ''
        self.edtMrlYml.enabled = not mtmaxconfig.exportGenerateMrl and mtmaxconfig.exportExistingMrlYml
        self.btnMrlYml.enabled = not mtmaxconfig.exportGenerateMrl and mtmaxconfig.exportExistingMrlYml
        self.chkExportMrl.enabled = not mtmaxconfig.exportGenerateMrl
        #self.edtTextureRoot.enabled = not mtmaxconfig.exportExistingMrlYml and mtmaxconfig.exportGenerateMrl
        #self.btnTextureRoot.enabled = not mtmaxconfig.exportExistingMrlYml and mtmaxconfig.exportGenerateMrl
        self.chkExportGenerateMrl.enabled = not mtmaxconfig.exportExistingMrlYml
    
    @staticmethod
    def loadConfig():
        self = MtModelExportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.exportFilePath
        self.edtMetadata.text = mtmaxconfig.exportMetadataPath
        self.edtRef.text = mtmaxconfig.exportRefPath
        self.edtMrlYml.text = mtmaxconfig.exportMrlYmlPath
        self.edtRoot.text = mtmaxconfig.exportRoot
        #self.edtTextureRoot.text = mtmaxconfig.exportTextureRoot
        self.chkExportWeights.checked = mtmaxconfig.exportWeights
        #self.chkExportNormals.checked = mtmaxconfig.exportNormals
        self.chkExportGroups.checked = mtmaxconfig.exportGroups
        self.chkExportSkeleton.checked = mtmaxconfig.exportSkeleton
        self.chkExportPrimitives.checked = mtmaxconfig.exportPrimitives
        self.chkExportTex.checked = mtmaxconfig.exportTexturesToTex
        self.chkExportMrl.checked = mtmaxconfig.exportExistingMrlYml
        self.chkExportGenerateMrl.checked = mtmaxconfig.exportGenerateMrl
        MtModelExportRollout.updateVisibility()
        
    @staticmethod
    def setFilePath( path ):
        mtmaxconfig.exportFilePath = path
        if not os.path.exists(mtmaxconfig.exportMetadataPath): 
            mtmaxconfig.exportMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mtmaxconfig.exportFilePath ).split('.')[0] )
        MtModelExportRollout.loadConfig()

    @staticmethod
    def setRefFilePath( path ):
        mtmaxconfig.exportRefPath = path
        if not os.path.exists(mtmaxconfig.exportMetadataPath): 
            mtmaxconfig.exportMetadataPath = ModelMetadata.getDefaultFilePath( os.path.basename( mtmaxconfig.exportRefPath ).split('.')[0] )
        MtModelExportRollout.loadConfig()
        
    @staticmethod
    def setMrlYmlFilePath( path ):
        mtmaxconfig.exportMrlYmlPath = path
        MtModelExportRollout.loadConfig()
    
    @staticmethod
    def chkExportWeightsChanged( state ):
        mtmaxconfig.importWeights = state
    
    @staticmethod
    def btnExportPressed():
        try:
            maxlog.clear()
            mtmaxconfig.dump()
            
            exporter = MtModelExporter()
            exporter.exportModel( mtmaxconfig.exportFilePath )
            if maxlog.hasError():
                mtmaxutil.showErrorMessageBox( "Export completed with one or more errors." )
            else:
                mtmaxutil.showMessageBox( 'Export completed successfully' )
        except Exception as e:
            maxlog.exception( e )
            mtmaxutil.showErrorMessageBox( "An error occured during export." )
        
    @staticmethod
    def btnFilePressed():
        path = mtmaxutil.selectSaveFile( 'UMVC3 model', 'mod' )
        if path == None:
            path = ''
        
        MtModelExportRollout.setFilePath( path )
        
    @staticmethod
    def edtFileChanged( state ):
        MtModelExportRollout.setFilePath( state )
        
    @staticmethod
    def edtMetadataChanged( state ):
        mtmaxconfig.exportMetadataPath = state
        
    @staticmethod
    def btnMetadataPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model metadata', 'yml' )
        if path == None:
            path = ''
        
        mtmaxconfig.exportMetadataPath = path

    @staticmethod
    def edtRefChanged( state ):
        MtModelExportRollout.setRefFilePath( state )
        
    @staticmethod
    def btnRefPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 model', 'mod' )
        if path == None:
            path = ''
        
        MtModelExportRollout.setRefFilePath( path )
        
    @staticmethod
    def edtMrlYmlChanged( state ):
        MtModelExportRollout.setMrlYmlFilePath( state )
        
    @staticmethod
    def btnMrlYmlPressed():
        path = mtmaxutil.selectOpenFile( 'UMVC3 MRL YML', 'yml' )
        if path == None:
            path = ''
        
        MtModelExportRollout.setMrlYmlFilePath( path )
        
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
    def edtTextureRootChanged( state ):
        mtmaxconfig.exportTextureRoot = state
        
    @staticmethod
    def btnTextureRootPressed():
        path = rt.getSavePath( caption="Select a folder", initialDir=os.path.dirname(mtmaxconfig.exportFilePath) )
        if path == None:
            path = ''
        
        mtmaxconfig.exportTextureRoot = os.path.abspath( path ).replace( "\\", "/" )
        MtModelExportRollout.loadConfig()
        
    @staticmethod
    def edtRootChanged( state ):
        mtmaxconfig.exportRoot = state
        
    @staticmethod
    def btnRootPressed():
        path = rt.getSavePath( caption="Select a folder", initialDir=os.path.dirname(mtmaxconfig.exportFilePath) )
        if path == None:
            path = ''
        
        mtmaxconfig.exportRoot = os.path.abspath( path ).replace( "\\", "/" )
        MtModelExportRollout.loadConfig()

        
class MtLogRollout(MtRollout):
    @staticmethod
    def loadConfig():
        self = MtLogRollout.getMxsVar()

class MtUtilitiesRollout(MtRollout):
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
        MtUtilitiesRollout._addAttributeToSelection( rt.mtJointAttributesInstance )

    @staticmethod
    def btnAddGroupAttribsPressed():
        MtUtilitiesRollout._addAttributeToSelection( rt.mtModelGroupAttributesInstance )

    @staticmethod
    def btnAddPrimAttribsPressed():
        MtUtilitiesRollout._addAttributeToSelection( rt.mtPrimitiveAttributesInstance )
        
    @staticmethod
    def btnRemJointAttribsPressed():
        MtUtilitiesRollout._removeAttributeFromSelection( rt.mtJointAttributesInstance )

    @staticmethod
    def btnRemGroupAttribsPressed():
        MtUtilitiesRollout._removeAttributeFromSelection( rt.mtModelGroupAttributesInstance )

    @staticmethod
    def btnRemPrimAttribsPressed():
        MtUtilitiesRollout._removeAttributeFromSelection( rt.mtPrimitiveAttributesInstance )

    @staticmethod
    def btnCreateGroupPressed():
        group = rt.dummy()
        group.name = "New group"
        rt.custAttributes.add( group, rt.mtModelGroupAttributesInstance )
        rt.select( group )
    
    
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
    rollouts = [MtInfoRollout, MtSettingsRollout, MtModelImportRollout, MtModelExportRollout, MtUtilitiesRollout]
    
    for rollout in rollouts:
        rollout.getMxsVar().width = w
        rollout.getMxsVar().height = h
        rt.addRollout( rollout.getMxsVar(), rt.g_mtWindow )
        rollout.loadConfig()
    
def main():
    rt.gc()
    rt.gc()
    
    maxlog.clear()
    mtmaxconfig.load()
    
    # import maxscript files
    mtmaxutil.runMaxScript( 'customattributes.ms' )
    mtmaxutil.runMaxScript( 'rollouts.ms' )
    createMainWindow()
    
    rt.gc()
    rt.gc()
    
if __name__ == '__main__':
    main()