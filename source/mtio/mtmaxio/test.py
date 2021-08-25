import os

class mtutil:
    @staticmethod
    def getExtractedResourceFilePath( basePath, hash, ext ):
        '''Finds an existing path to a resource file with or without the hash suffix'''
        
        oldPath = basePath + '.' + hash + '.' + ext
        newPath = basePath + '.' + ext
        if os.path.exists( oldPath ):
            return ( oldPath, False )
        elif os.path.exists( newPath ):
            return ( newPath, True )
        else:
            return ( None, None )

class Test:
    def __init__( self ):
        self.basePath = "X:\\work\\umvc3_model\\samples\\UMVC3ModelSamples\\Ryu - Copy"
        #self.basePath = 'X:\\games\\pc\\Ultimate Marvel vs. Capcom 3\\nativePCx64\\chr\\archive\\0001_00\\chr\\Ryu\\model\\1p'
    
    def getPath( self, texturePath ):
        if texturePath == '':
            return None
        else:
            # load TEX and convert to DDS before loading the model
            
            # normalize texture path
            texturePathNrm = texturePath.replace( '\\', '/' )
            
            # find the root of the texture path relative to the current model directory
            texturePathParts = texturePathNrm.split( '/' )
            relTexturePathRoot = ''
            for i in range( 1, len( texturePathParts )):
                relTexturePathRoot += '../'
            texturePathRoot = os.path.join( self.basePath, relTexturePathRoot ) 
            texturePathRoot = os.path.realpath( texturePathRoot )
            
            # find the real texture path
            realTexturePath = os.path.join( texturePathRoot, texturePath )
            textureTEXPath, _ = mtutil.getExtractedResourceFilePath( realTexturePath, '241f5deb', 'tex' )
            if textureTEXPath == None:
                # failsafe: try to look for the tex files in the current model directory in case we don't find it 
                textureTEXPath, _ = mtutil.getExtractedResourceFilePath( self.basePath + '/' + os.path.basename( texturePath ), '241f5deb', 'tex' )
                textureDDSPath =  os.path.join( self.basePath, os.path.basename( texturePath ) + ".dds" ) # failsafe
                if textureTEXPath == None:
                    print( f'WARNING: TEX file not found: {texturePath}' )  
            else:
                textureDDSPath = os.path.splitext( textureTEXPath )[0] + '.dds'
            return textureDDSPath

test = Test()
test.getPath( 'chr\\Ryu\\model\\1p\\Ryu_tex3_BM' )
