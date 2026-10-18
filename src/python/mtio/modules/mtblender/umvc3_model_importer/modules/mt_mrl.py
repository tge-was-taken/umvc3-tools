import os
import collections

import bpy

from ..mtlib.immaterial import imMaterialLib, imMaterialTextureInfo
from . import mt_mrl_props


def game_materials( src=None ):
    '''{source mrl path: [blender materials]}'''
    out = collections.defaultdict( list )
    for m in bpy.data.materials:
        if not mt_mrl_props.has_entry( m ) and 'mt_mrl' not in m.keys():
            continue
        path = m.get( 'mt_mrl_path', '' )
        if src is None or os.path.normcase( os.path.abspath( path ) ) == os.path.normcase( os.path.abspath( src ) ):
            out[path].append( m )
    return out

def build_library( src, logger=None ):
    for ms in game_materials( src ).values():
        for m in ms:
            if not mt_mrl_props.has_entry( m ):
                mt_mrl_props.adopt_legacy( m )
    notes = mt_mrl_props.sync()
    lib = imMaterialLib()
    lib.loadBinaryFile( src )
    by_orig = {}
    for ms in game_materials( src ).values():
        for m in sorted( ms, key=lambda m: m.name ):
            by_orig.setdefault( m.get( 'mt_entry_orig', m.mt_entry.name ), m )
    errors = []
    for i, mi in enumerate( lib.materials ):
        m = by_orig.get( mi.name )
        if m is None:
            continue
        errors += [ f'{mi.name}: {p}' for p in mt_mrl_props.problems( m ) ]
        lib.materials[i] = mt_mrl_props.info_from_entry( m )
        for c in lib.materials[i].cmds:
            if c.type == 'texture':
                img = next( ( x.image for x in m.mt_entry.cmds if x.kind == 'texture' and x.slot == c.name ), None )
                if img is not None and not img.get( 'mt_tex_path' ):
                    notes.append( f'{mi.name} {c.name}: points at {c.data or "(empty)"}; the image "{img.name}" has to be exported there as a .tex' )
    names = [ x.name for x in lib.materials ]
    dup = sorted( { n for n in names if names.count( n ) > 1 } )
    if dup:
        errors.append( 'two materials share a name: ' + ', '.join( dup ) )
    if errors:
        raise ValueError( 'the .mrl can not be written:\n' + '\n'.join( errors ) )
    used = []
    for mi in lib.materials:
        for c in mi.cmds:
            if c.type == 'texture' and c.data and c.data not in used:
                used.append( c.data )
    kept = { t.path: t for t in lib.textures }
    lib.textures = []
    for p in used:
        t = kept.get( p )
        if t is None:
            t = imMaterialTextureInfo(); t.path = p; t.type = 'rTexture'
        lib.textures.append( t )
    return lib, notes

def export_mrl( out_path, src=None, write_yml=True, logger=None ):
    groups = game_materials()
    if src is None:
        if not groups:
            raise RuntimeError( 'no game shader materials in this file' )
        src = max( groups, key=lambda k: len( groups[k] ) )
    if not src or not os.path.exists( src ):
        raise RuntimeError( f'the source mrl {src!r} is gone; it holds the materials no mesh uses' )
    lib, notes = build_library( src, logger )
    lib.saveBinaryFile( out_path )
    if write_yml:
        lib.saveYamlFile( out_path + '.yml' )
    for n in notes:
        if logger: logger.warn( n )
    return src, notes
