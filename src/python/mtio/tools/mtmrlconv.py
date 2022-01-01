import os
import sys
import argparse

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

sys.path.append( os.path.realpath( os.path.dirname( __file__ ) + "/../" ) )
from modules.mtlib import *

def noneOrEmpty( s ):
    return s == None or len( s ) == 0

def processFile( path, outPath ):
    # detect paths
    basePath, baseName, exts = util.splitPath( path )
    if len( exts ) == 1:
        modPath = os.path.join( basePath, baseName + '.mod' )
        mrlPath = os.path.join( basePath, baseName + '.mrl' )
        ymlPath = os.path.join( basePath, baseName + '.mrl.yml' )
    else:
        modPath = os.path.join( basePath, baseName + '.58a15856.mod' )
        mrlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl' )
        ymlPath = os.path.join( basePath, baseName + '.2749c8a8.mrl.yml' )
    
    lastExt = exts[len(exts) - 1]
    if lastExt == 'mrl':
        mrlPath = path
    elif lastExt == 'mod':
        modPath = path
    elif lastExt in ['yml', 'yaml']:
        ymlPath = path
    
    if lastExt in ['mrl', 'mod']:
        if os.path.exists( modPath ):
            model = rModelData()
            model.read( NclBitStream( util.loadIntoByteArray( modPath ) ) )
            mvc3materialdb.addNames( model.materials )
            
        if not os.path.exists( mrlPath ):
            print( "mrl file {} does not exist".format( mrlPath ) )
            return
            
        matLib = imMaterialLib()
        matLib.loadBinary( NclBitStream( util.loadIntoByteArray( mrlPath ) ) )
        
        if noneOrEmpty( outPath ):
            outPath = ymlPath
        
        matLib.saveYamlFile( outPath )
    elif lastExt in ['yml', 'yaml']:
        matLib = imMaterialLib()
        matLib.loadYamlFile( ymlPath )
        
        if noneOrEmpty( outPath ):
            outPath = mrlPath
        
        with open( outPath, "wb" ) as f:
            stream = NclBitStream()
            matLib.saveBinaryStream(stream)
            f.write(stream.getBuffer())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "input" )
    parser.add_argument( "output", nargs='?' )
    args = parser.parse_args()
    processFile( args.input, args.output )

if __name__ == '__main__':
    main()