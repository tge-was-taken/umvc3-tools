# 3ds Max MT Framework model import/export plugin
# Note: rollout classes must be defined in this module to be accessible to MaxScript

# fix imports
import os
import sys
if os.path.dirname(__file__) not in sys.path: sys.path.append(os.path.dirname(__file__))

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
from mtmaxexp import *
from mtmaximp import *
import mtmaxutil

# TODO
# - display msg box with errors during import
# - investigate createMaxPoint3 access violation

# def getScriptDir():
#     return os.path.dirname(os.path.realpath(__file__))
            
# def addSysPath( *paths ):
#     for path in paths:
#         normalizedPath = os.path.realpath( path )
#         if not normalizedPath in sys.path:
#             sys.path.append( normalizedPath )
            
# def dumpSysInfo():
#     print( 'PYTHON SYSTEM INFO' )
#     print( sys.version )
#     print( sys.version_info )
#     print( sys.path )

# really good code right here
#addSysPath( getScriptDir(), getScriptDir() + '/../' )
#dumpSysInfo()
    
class MtInfoRollout:
    @staticmethod
    def getMxsVar():
        return rt.MtInfoRollout
    
    @staticmethod
    def loadConfig():
        self = MtInfoRollout.getMxsVar()
    
class MtSettingsRollout:
    @staticmethod
    def getMxsVar():
        return rt.MtSettingsRollout
    
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
        
class MtModelImportRollout:
    @staticmethod
    def updateVisibility():
        rt.MtModelImportRollout.btnImport.enabled = \
            os.path.isfile( mtmaxconfig.importFilePath )
            
    @staticmethod
    def getMxsVar():
        return rt.MtModelImportRollout
            
    @staticmethod
    def loadConfig():
        self = MtModelImportRollout.getMxsVar()
        self.edtFile.text = mtmaxconfig.importFilePath
        self.edtProfile.text = mtmaxconfig.importProfile
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
        mtmaxconfig.importProfile = os.path.basename( mtmaxconfig.importFilePath ).split('.')[0]
        MtModelImportRollout.loadConfig()
    
    @staticmethod
    def chkImportWeightsChanged( state ):
        mtmaxconfig.importWeights = state
        MtModelImportRollout.updateVisibility()
    
    @staticmethod
    def btnImportPressed():
        mtmaxutil.clearLog()
        importer = MtModelImporter()
        importer.importModel( mtmaxconfig.importFilePath )
        MtModelImportRollout.updateVisibility()
        
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
    def edtProfileChanged( state ):
        mtmaxconfig.importProfile = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkImportNormalsChanged( state ):
        mtmaxconfig.importNormals = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkImportGroupsChanged( state ):
        mtmaxconfig.importGroups = state
        MtModelImportRollout.updateVisibility()
    
    @staticmethod
    def chkImportSkeletonChanged( state ):
        mtmaxconfig.importSkeleton = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkConvertDDSChanged( state ):
        mtmaxconfig.importConvertTexturesToDDS = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkSaveMrlYmlChanged( state ):
        mtmaxconfig.importSaveMrlYml = state
        MtModelImportRollout.updateVisibility()
        
    @staticmethod
    def chkImportPrimitivesChanged( state ):
        mtmaxconfig.importPrimitives = state
        MtModelImportRollout.updateVisibility()
        
class MtModelExportRollout:
    @staticmethod
    def getMxsVar():
        return rt.MtModelExportRollout
    
    @staticmethod
    def updateVisibility():
        pass
    
    @staticmethod
    def loadConfig():
        self = MtModelExportRollout.getMxsVar()
        
class MtLogRollout:
    @staticmethod
    def getMxsVar():
        return rt.MtLogRollout
    
    @staticmethod
    def loadConfig():
        self = MtLogRollout.getMxsVar()
    
def getMainWindow():
    return rt.g_mtWindow
    
def createMainWindow():
    # get coords of window if it's already opened
    x = 30
    y = 100
    w = 250
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
    rollouts = [MtInfoRollout, MtSettingsRollout, MtModelImportRollout, MtModelExportRollout, MtLogRollout]
    
    for rollout in rollouts:
        rt.addRollout( rollout.getMxsVar(), rt.g_mtWindow )
        rollout.loadConfig()
    
def main():
    rt.gc()
    rt.gc()
    
    mtmaxutil.clearLog()
    
    # import maxscript files
    mtmaxutil.runMaxScript( 'customattributes.ms' )
    mtmaxutil.runMaxScript( 'rollouts.ms' )
    createMainWindow()
    
    rt.gc()
    rt.gc()
    
if __name__ == '__main__':
    main()