import os
import sys
import argparse

def getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

sys.path.append( os.path.realpath( os.path.dirname( __file__ ) + "/../" ) )
from modules.mtlib import *
from modules.mtlib import texconv
from modules.mtlib import textureutil

def hexOrDecimalInt( s ):
    return int( s, 0 )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "input", type=str, help='the input TEX/DDS/PNG/TGA/other file path' )
    parser.add_argument( "output", type=str, nargs='?', help='the output TEX/DDS/PNG/TGA/other file path' )
    parser.add_argument( '-orig', '--original', type=str, default=None, required=False, help='the path to the original texture file to use as reference' )
    parser.add_argument( '-fmt', '--format', type=hexOrDecimalInt, default=None, required=False, help='forces the texture format for conversion' )
    parser.add_argument( '--swap-normal-map-ra', type=bool, default=False, required=False, help='toggles swapping of the red and alpha channels for normal maps')
    parser.add_argument( '--invert-normal-map-g', type=bool, default=False, required=False, help='inverts the green channel of the normal map')
    args = parser.parse_args()
    textureutil.convertTexture( args.input, dstTexturePath=args.output, 
                               refTexturePath=args.original, forcedFormat=args.format,
                               swapNormalMapRAChannels=args.swap_normal_map_ra, invertNormalMapG=args.invert_normal_map_g )
    pass

if __name__ == '__main__':
    main()