'''
Module containing a texconv wrapper interface to simplify calling texconv from python code.
'''

import subprocess
import os
import io
import mtutil

def _getScriptDir():
    return os.path.dirname(os.path.realpath(__file__))

def texconv( inPath, outPath, fileType = 'DDS', 
            featureLevel = 9.1, pow2 = True, fmt = 'DXT5', 
            overwrite = True, srgb = True):
    def arg( name, value ):
        if value == False:
            return []
        if value == True:
            return [name]
        if name == None:
            return [str(value)]   
        return [name, str(value)]
    
    '''
    texconv "path" -o "path" -ft DDS -fl 9.1 -pow2 -f DXT5 -y -srgb
    '''
    args = [mtutil.getResourceDir() + '/texconv.exe', 
            *arg( None, inPath ), *arg( '-o', outPath ), *arg('-ft', fileType), *arg('-fl', featureLevel), 
            *arg('-pow2', pow2),  *arg('-f', fmt), *arg('-y', overwrite), *arg('-srgb', srgb)]
    
    return subprocess.call(args, shell=True)
    
if __name__ == '__main__':
    texconv("C:/Users/Chris/Downloads/Nintendo 64 - The Legend of Zelda Ocarina of Time - Link Adult Low-Poly/Link (Adult)/Link_grp.png")
    