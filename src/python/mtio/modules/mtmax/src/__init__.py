# 3ds Max MT Framework model import/export plugin
# Note: rollout classes must be defined in this module to be accessible to MaxScript

# fix imports
import os
import sys

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
from mtmaxexp import *
from mtmaximp import *
import mtmaxutil

class MtRollout:
    @classmethod
    def onEvent( cls, e, *args ):
        print(f'received event: {e} with args: {args}')
        if hasattr(cls, e):
            getattr(cls, e)(*args)
        else:
            print(f'no event handler for {e}')

        if hasattr( cls, 'updateVisibility'): 
            cls.updateVisibility()
        else:
            print(f'no update visibility handler defined in {cls}')

        mtmaxconfig.save()

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
        mtmaxutil.clearLog()
        importer = MtModelImporter()
        importer.importModel( mtmaxconfig.importFilePath )
        
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
        rt.MtModelExportRollout.btnExport.enabled = mtmaxconfig.exportFilePath.strip() != ''
    
    @staticmethod
    def loadConfig():
        self = MtModelExportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.exportFilePath
        self.edtMetadata.text = mtmaxconfig.exportMetadataPath
        self.edtRef.text = mtmaxconfig.exportRefPath
        self.edtMrlYml.text = mtmaxconfig.exportMrlYmlPath
        # self.chkExportWeights.checked = mtmaxconfig.exportWeights
        # self.chkExportNormals.checked = mtmaxconfig.exportNormals
        # self.chkExportGroups.checked = mtmaxconfig.exportGroups
        # self.chkExportSkeleton.checked = mtmaxconfig.exportSkeleton
        # self.chkExportPrimitives.checked = mtmaxconfig.exportPrimitives
        # self.chkConvertTEX.checked = mtmaxconfig.exportTexturesToTEX
        # self.chkConvertMrlYml.checked = mtmaxconfig.exportMrlYml
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
        mtmaxutil.clearLog()
        exporter = MtModelExporter()
        exporter.exportModel( mtmaxconfig.exportFilePath )
        
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
        mtmaxconfig.exportMrlYml = state
        
    @staticmethod
    def chkExportPrimitivesChanged( state ):
        mtmaxconfig.exportPrimitives = state

        
class MtLogRollout(MtRollout):
    @staticmethod
    def loadConfig():
        self = MtLogRollout.getMxsVar()

class MtUtilitiesRollout(MtRollout):
    @staticmethod
    def loadConfig():
        pass

    def _addAttributeToSelection(attr):
        if len(rt.selection) == 0:
            return
        for node in rt.selection: 
            rt.custAttributes.add( node, attr )

    @staticmethod
    def btnAddJointAttribsPressed():
        MtUtilitiesRollout._addAttributeToSelection( rt.mtJointAttributesInstance )

    @staticmethod
    def btnAddGroupAttribsPressed():
        MtUtilitiesRollout._addAttributeToSelection( rt.mtModelGroupAttributesInstance )

    #@staticmethod
    #def btnAddPmlAttribsPressed():
    #    rt.custAttributes.add( rt.selected, rt.mtModelGroupAttributesInstance )

    @staticmethod
    def btnAddPrimAttribsPressed():
        MtUtilitiesRollout._addAttributeToSelection( rt.mtPrimitiveAttributesInstance )

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
        #w = rt.g_mtWindow2.size.x
        #h = rt.g_mtWindow2.size.y
        rt.closeRolloutFloater( rt.g_mtWindow2 )
        
    # create plugin window
    rt.g_mtWindow = rt.newRolloutFloater( "MT Framework Max IO Plugin", w, h, x, y )
    rollouts = [MtInfoRollout, MtSettingsRollout, MtModelImportRollout, MtModelExportRollout, MtUtilitiesRollout, MtLogRollout]
    
    for rollout in rollouts:
        rollout.getMxsVar().width = w
        rollout.getMxsVar().height = h
        rt.addRollout( rollout.getMxsVar(), rt.g_mtWindow )
        rollout.loadConfig()
    
def main():
    rt.gc()
    rt.gc()
    
    mtmaxutil.clearLog()
    mtmaxconfig.load()
    
    # import maxscript files
    mtmaxutil.runMaxScript( 'customattributes.ms' )
    mtmaxutil.runMaxScript( 'rollouts.ms' )
    createMainWindow()
    
    rt.gc()
    rt.gc()
    
def test():
    print('test4')
    
if __name__ == '__main__':
    main()