from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import log
import yaml
import os
import datetime
from ncl import NclMat44

class EditorArrayProxy(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def append(self, value):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def unwrap(self):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

class EditorLayerProxy(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def addNode(self, node):
        pass

    @abstractmethod
    def unwrap(self) -> Any:
        pass

class EditorCustomAttributeSetProxy(ABC):
    def __init__(self, ctx) -> None:
        self._ctx = ctx

    @abstractmethod
    def getCustomAttribute(self, name: str) -> Any:
        pass

    @abstractmethod
    def setCustomAttribute(self, name: str, value: Any):
        pass

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name != '_ctx':
            self.setCustomAttribute(__name, __value)
        else:
            super().__setattr__(__name,__value)

    def __getattr__(self, __name: str) -> Any:
        if __name != '_ctx':
            return self.getCustomAttribute(__name)
        else:
            super().__getattribute__(__name)

class EditorNodeProxy(ABC):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    @abstractmethod
    def getTransform() -> NclMat44:
        pass

    @abstractmethod
    def getParent() -> "EditorNodeProxy":
        pass

    @abstractmethod
    def getName() -> str:
        pass

    @abstractmethod
    def unwrap() -> Any:
        pass

    @abstractmethod
    def isHidden() -> bool:
        pass

    @abstractmethod
    def isMeshNode() -> bool:
        pass

    @abstractmethod
    def isGroupNode() -> bool:
        pass

    @abstractmethod
    def isBoneNode() -> bool:
        pass

    @abstractmethod
    def isSplineNode() -> bool:
        pass

    def __repr__(self) -> str:
        return self.getName()

    def __key(self):
        return (self.unwrap())

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, EditorNodeProxy):
            return self.__key() == __o.__key()
        else:
            return NotImplemented

class EditorMaterialProxy(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def unwrap( self ) -> Any:
        pass

    @abstractmethod
    def getName( self ) -> str:
        pass

class EditorMeshProxy(ABC):
    @abstractmethod
    def unwrap( self ) -> Any:
        pass

class EditorPluginConfigBase:
    _CURRENT_VERSION = 2

    def __init__(self, plugin: "EditorPluginBase") -> None:
        self._plugin = plugin

        # general
        self.version = self._CURRENT_VERSION
        self.flipUpAxis = True
        self.debug = False
        self.showLogOnError = True
        self.target = 0
        self.lukasCompat = False

        # import settings
        self.importWeights = True
        self.importFilePath = ''
        self.importConvertTexturesToDDS = True
        self.importMetadataPath = ''
        self.importNormals = True
        self.importGroups = True
        self.importSkeleton = True
        self.importPrimitives = True
        self.importSaveMrlYml = True
        self.importCreateLayer = True
        self.importScale = 1
        self.importBakeScale = True

        # export settings
        self.exportWeights = True
        self.exportFilePath = ''
        self.exportTexturesToTex = True
        self.exportMetadataPath = ''
        self.exportNormals = True
        self.exportGroups = True
        self.exportSkeleton = True
        self.exportPrimitives = True
        self.exportEnvelopes = True
        self.exportExistingMrlYml = False
        self.exportRefPath = ''
        self.exportMrlYmlPath = ''
        self.exportUseRefJoints = True
        self.exportUseRefEnvelopes = True
        self.exportUseRefBounds = True
        self.exportUseRefGroups = True
        self.exportGenerateMrl = True
        self.exportRoot = ''
        self.exportOverwriteTextures = False
        self.exportScale = 1
        self.exportBakeScale = True
        self.exportGroupPerMesh = False
        self.exportGenerateEnvelopes = True
        self.exportMaterialPreset = 'MVC3 MaterialChar'

        # debug settings
        self.debugForcePhysicalMaterial = False
        self.debugImportPrimitiveIdFilter = []
        self.debugDisableLog = False
        self.debugExportForceShader = ''
        self.debugDisableTransform = False

    def _getVariables( self ):
        variables = dict([(item, getattr(self, item)) for item in dir(self) if \
            not item.startswith('_') and 
            (
            isinstance(getattr(self, item), int) or 
            isinstance(getattr(self, item), bool) or
            isinstance(getattr(self, item), float) or
            isinstance(getattr(self, item), str) or 
            isinstance(getattr(self, item), list)
            )])
        return variables

    def save( self ):
        with open(self._plugin.getConfigFilePath(), 'w') as f:
            yaml.dump(self._getVariables(), f)

    def load( self ):
        if os.path.exists(self._plugin.getConfigFilePath()):
            with open(self._plugin.getConfigFilePath(), 'r') as f:
                temp = yaml.load(f, Loader=yaml.FullLoader)
                if temp != None:
                    for key in temp:
                        if hasattr(self, key):
                            setattr(self, key, temp[key])

                if self.version == 1:
                    self.exportEnvelopes = temp['exportPjl']
                    self.exportUseRefEnvelopes = temp['exportUseRefPjl']
                    self.exportGenerateEnvelopes = temp['exportGeneratePjl']

                self.version = self._CURRENT_VERSION
                            
        # fixup mutually exclusive options
        if self.exportExistingMrlYml and self.exportGenerateMrl:
            self.exportGenerateMrl = False
            
    def dump( self ):
        s = "config:\n"
        for key in self._getVariables():
            val = getattr(self, key)
            s += f"{key} = {val}\n"
        self._plugin.logger.debug( s )

class EditorPluginLoggerBase(log.LoggerBase):
    def __init__(self, plugin: "EditorPluginBase") -> None:
        super().__init__()
        self._plugin = plugin
        if os.path.exists( self._plugin.getLogFilePath() ):
            os.remove( self._plugin.getLogFilePath() )

    def log( self, level, msg, *args ):
        if self._plugin.config.debugDisableLog:
            return
        
        formattedMsg = self.formatMessage( level, msg )
        logToFileOnly = level == 'DEBUG' and not self._plugin.isDebugEnv()
        if not logToFileOnly:
            print( formattedMsg, *args )
        with open( self._plugin.getLogFilePath(), 'a' ) as f:
            f.write( formattedMsg + '\n' )

class EditorPluginBase(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.version: str = None
        self.config: EditorPluginConfigBase = None
        self.logger: EditorPluginLoggerBase = None
        self.logFilePath = None

    @abstractmethod
    def load():
        pass

    @abstractmethod
    def getLogFilePath() -> str:
        pass

    @abstractmethod
    def isDebugEnv() -> str:
        pass

    @abstractmethod
    def timeStamp( self ):
        pass

    @abstractmethod
    def disableSceneRedraw( self ):
        pass

    @abstractmethod
    def enableSceneRedraw( self ):
        pass

    @abstractmethod
    def getIndexBase( self ):
        pass

    @abstractmethod
    def updateUI( self ) -> bool:
        pass

    @abstractmethod
    def getNodeByName( self, name: str ) -> EditorNodeProxy:
        pass

    @abstractmethod
    def getAppDataDir( self ) -> str:
        pass

    def openLogFile( self ):
        os.system( self.getLogFilePath() )

    def getLogFilePath(self) -> str:
        if self.logFilePath is None:
            # create log file with unique name
            timeStr = datetime.datetime.today().strftime('%Y_%m_%d_%H_%M_%S_%f') 
            self.logFilePath = os.path.join( self.getAppDataDir(), f'log_{timeStr}.txt' )
            
            # resolve conflcit
            i = 0
            while os.path.exists( self.logFilePath ):
                self.logFilePath = os.path.join( self.getAppDataDir(), f'log_{timeStr}_{i}.txt' )
                i += 1
        
        return self.logFilePath

    def getConfigFilePath(self) -> str:
        return self.getAppDataDir() + '/config.yml'