'''MT Framework character shading for Blender'''
import math
import os
import struct

import bpy
import mathutils

try:
    import numpy as np
except ImportError:
    np = None

COORDS_GROUP = 'MT Toon Coords'
CHARACTER_GROUP = 'MT Character'
GROUP_VERSION = 4
KEY_LIGHT_NAME = 'MT Key Light'

SCENE_DEFAULTS = {
    'mt_light_dir':   ( 0.03236, -0.8937, 0.4475 ),
    'mt_light_color': ( 1.15, 1.15, 1.15 ),
    'mt_ambient':     ( 0.0, 0.0, 0.0 ),        # unknown for characters, see notes
    'mt_rim_color':   ( 0.0, 2.326, 10.0 ),     # ToonLight mRimLightColorFactor
    'mt_rim_power':   4.0,                      # ToonLight mRimLightPower
    'mt_rim_min_height': 2.0,                   # baked into the compiled shaders
    'mt_rim_max_height': 15.0,
    'mt_unit_scale':  1.0,                      # importer model scale, MT units -> blender
    'mt_scene_lights': 1.0,                     # 1: every light in the scene (Eevee), 0: key sun only
    'mt_world_ambient': 1.0,                    # world lighting counts as the ambient term
}

def mt_to_blender( v ):
    '''MT is y up, the importer flips to z up: (x, y, z) -> (x, -z, y).'''
    return ( v[0], -v[2], v[1] )

def ensure_scene_lighting( scene, unit_scale=None ):
    for k, v in SCENE_DEFAULTS.items():
        if k not in scene.keys():
            scene[k] = v
    if unit_scale is not None:
        scene['mt_unit_scale'] = float( unit_scale )
    ensure_key_light( scene )

def _is_sun( obj ):
    return obj is not None and obj.type == 'LIGHT' and obj.data is not None and obj.data.type == 'SUN'

def key_light( scene ):
    mip = getattr( scene, 'sub_scene_properties', None )
    obj = getattr( mip, 'mt_key_light', None ) if mip is not None else None
    if _is_sun( obj ):
        return obj
    obj = bpy.data.objects.get( KEY_LIGHT_NAME )
    return obj if _is_sun( obj ) else None

def ensure_key_light( scene ):
    obj = key_light( scene )
    if obj is None:
        old = bpy.data.objects.get( KEY_LIGHT_NAME )
        direction = scene.get( 'mt_light_dir', SCENE_DEFAULTS['mt_light_dir'] )
        if old is not None:
            # blends from before this change have an arrow empty here, keep its direction
            if old.type == 'EMPTY':
                direction = tuple( old.matrix_world.col[2][:3] )
            old.name = KEY_LIGHT_NAME + ' (old)'
        sun = bpy.data.lights.new( KEY_LIGHT_NAME, 'SUN' )
        obj = bpy.data.objects.new( KEY_LIGHT_NAME, sun )
        scene.collection.objects.link( obj )
        set_key_light_direction( scene, direction, obj )
        set_key_light_color( scene, scene.get( 'mt_light_color', SCENE_DEFAULTS['mt_light_color'] ), obj )
    mip = getattr( scene, 'sub_scene_properties', None )
    if mip is not None and hasattr( mip, 'mt_key_light' ) and not _is_sun( mip.mt_key_light ):
        mip.mt_key_light = obj
    _drive_from_key_light( scene )
    return obj

def set_key_light_direction( scene, direction, obj=None ):
    d = mathutils.Vector( direction )
    if d.length < 1e-8:
        return
    d.normalize()
    scene['mt_light_dir'] = tuple( d )
    obj = obj or key_light( scene )
    if obj is not None:
        # a sun shines down its -Z, so +Z points at the light like the game's mDir
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = d.to_track_quat( 'Z', 'Y' )

def _srgb_to_linear( c ):
    return c / 12.92 if c <= 0.04045 else ( ( c + 0.055 ) / 1.055 ) ** 2.4

def set_key_light_color( scene, color, obj=None ):
    c = [ float( x ) for x in tuple( color )[:3] ]
    strength = max( c ) if max( c ) > 0 else 0.0
    scene['mt_light_color'] = tuple( c )
    obj = obj or key_light( scene )
    if obj is not None:
        # colour x strength is the game's light value as is (the shaders light in gamma space)
        obj.data.color = [ x / strength for x in c ] if strength > 0 else ( 1.0, 1.0, 1.0 )
        obj.data.energy = strength

def _drive_from_key_light( scene ):
    if not hasattr( getattr( scene, 'sub_scene_properties', None ), 'mt_key_light' ):
        return
    for prop in ( 'mt_light_dir', 'mt_light_color' ):
        try:
            scene.driver_remove( '["%s"]' % prop )
        except Exception:
            pass
    base = 'sub_scene_properties.mt_key_light'
    try:
        for i in range( 3 ):
            drv = scene.driver_add( '["mt_light_dir"]', i ).driver
            drv.type = 'SCRIPTED'
            var = drv.variables.new()
            var.name = 'z'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = scene
            # RNA matrices are column major, so [2][i] is component i of the sun's +Z axis
            var.targets[0].data_path = '%s.matrix_world[2][%d]' % ( base, i )
            drv.expression = 'z'

            drv = scene.driver_add( '["mt_light_color"]', i ).driver
            drv.type = 'SCRIPTED'
            for name, path in ( ( 'c', '%s.data.color[%d]' % ( base, i ) ), ( 'e', '%s.data.energy' % base ) ):
                var = drv.variables.new()
                var.name = name
                var.targets[0].id_type = 'SCENE'
                var.targets[0].id = scene
                var.targets[0].data_path = path
            drv.expression = 'c * e'
    except Exception:
        pass

def set_view_transform_standard( scene ):
    try:
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
    except Exception:
        pass

_SDL_VALUE = { 6: ( '<i', 4 ), 7: ( '<q', 8 ), 8: ( '<4f', 16 ), 9: ( '<f', 4 ), 11: ( '<B', 1 ) }

def read_sdl( path ):
    d = open( path, 'rb' ).read()
    if d[:4] != b'SDL\0':
        return []
    count = struct.unpack_from( '<H', d, 6 )[0]
    strings = struct.unpack_from( '<Q', d, 0x18 )[0]
    def s( o ):
        e = d.index( b'\0', strings + o )
        return d[strings + o:e].decode( 'latin1' )
    tracks = []
    for i in range( count ):
        o = 0x20 + i * 0x30
        tt, pt, nf, parent = struct.unpack_from( '<BBHI', d, o )
        name = s( struct.unpack_from( '<Q', d, o + 8 )[0] )
        fo, vo = struct.unpack_from( '<QQ', d, o + 0x20 )
        val = None
        if tt in _SDL_VALUE and nf:
            fmt, size = _SDL_VALUE[tt]
            val = struct.unpack_from( fmt, d, vo )
            val = val if len( val ) > 1 else val[0]
        tracks.append( ( tt, parent, name, val ) )
    units = []
    for i, ( tt, parent, name, val ) in enumerate( tracks ):
        if tt == 2:
            units.append( { 'index': i, 'name': name, 'props': {} } )
    by_index = { u['index']: u for u in units }
    for i, ( tt, parent, name, val ) in enumerate( tracks ):
        if val is None:
            continue
        # props hang off their unit directly or through a Param track
        p = parent
        while p in range( len( tracks ) ) and p not in by_index and tracks[p][0] == 5:
            p = tracks[p][1]
        if p in by_index:
            by_index[p]['props'][name] = val
    return units

def load_stage_lighting( scene, sdl_folder ):
    units = []
    for fn in sorted( os.listdir( sdl_folder ) ):
        if fn.lower().endswith( '.sdl' ):
            try:
                for u in read_sdl( os.path.join( sdl_folder, fn ) ):
                    u['file'] = fn
                    units.append( u )
            except Exception:
                pass
    ensure_scene_lighting( scene )
    report = []

    def is_char_light( u ):
        g = u['props'].get( 'mGroup' )
        return 'InfiniteLight' in u['name'] and isinstance( g, int ) and ( g & 1 )
    lights = [ u for u in units if is_char_light( u ) and 'mDir' in u['props'] ]
    if not lights:
        lights = [ u for u in units if 'InfiniteLight' in u['name'] and 'mDir' in u['props'] ]
    if lights:
        u = lights[0]
        set_key_light_direction( scene, mt_to_blender( u['props']['mDir'] ) )
        if 'mColor' in u['props']:
            set_key_light_color( scene, u['props']['mColor'][:3] )
        report.append( f"key light {u['name']} ({u['file']})" )

    toons = [ u for u in units if u['name'] == 'ToonLight' ]
    toons.sort( key=lambda u: 0 if 'environment' in u['file'].lower() else 1 )
    if toons:
        p = toons[0]['props']
        if 'mRimLightColorFactor' in p:
            scene['mt_rim_color'] = tuple( p['mRimLightColorFactor'][:3] )
        if 'mRimLightPower' in p:
            scene['mt_rim_power'] = float( p['mRimLightPower'] )
        if 'mRimLightMinHeight' in p:
            scene['mt_rim_min_height'] = float( p['mRimLightMinHeight'] )
        if 'mRimLightMaxHeight' in p:
            scene['mt_rim_max_height'] = float( p['mRimLightMaxHeight'] )
        report.append( f"rim from {toons[0]['file']}" )

    for u in units:
        if 'mGeometryThick' in u['props']:
            scene['mt_outline_thickness'] = float( u['props']['mGeometryThick'] )
            break
    return ', '.join( report ) if report else 'no lights found'

class _NB:
    def __init__( self, tree ):
        self.tree = tree
        self.nodes = tree.nodes
        self.links = tree.links
        self.count = 0
        self.attr_cache = {}

    def node( self, kind, label=None, **props ):
        n = self.nodes.new( kind )
        col, row = divmod( self.count, 24 )
        n.location = ( -1400 + col * 220, 600 - row * 140 )
        self.count += 1
        for k, v in props.items():
            setattr( n, k, v )
        if label:
            n.label = label
        return n

    def feed( self, sock, val ):
        if isinstance( val, bpy.types.NodeSocket ):
            self.links.new( val, sock )
        elif val is not None:
            try:
                sock.default_value = val
            except Exception:
                if isinstance( val, ( int, float ) ):
                    sock.default_value = ( val, val, val )
                else:
                    raise

    def math( self, op, a, b=None, c=None, clamp=False, label=None ):
        n = self.node( 'ShaderNodeMath', label, operation=op, use_clamp=clamp )
        self.feed( n.inputs[0], a )
        if b is not None: self.feed( n.inputs[1], b )
        if c is not None: self.feed( n.inputs[2], c )
        return n.outputs[0]

    def vec( self, op, a, b=None, label=None ):
        n = self.node( 'ShaderNodeVectorMath', label, operation=op )
        self.feed( n.inputs[0], a )
        if b is not None:
            if op == 'SCALE':
                self.feed( n.inputs['Scale'], b )
            else:
                self.feed( n.inputs[1], b )
        out = 'Value' if op in ( 'DOT_PRODUCT', 'LENGTH', 'DISTANCE' ) else 'Vector'
        return n.outputs[out]

    def sep( self, v ):
        n = self.node( 'ShaderNodeSeparateXYZ' )
        self.feed( n.inputs[0], v )
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def comb( self, x, y, z ):
        n = self.node( 'ShaderNodeCombineXYZ' )
        self.feed( n.inputs[0], x ); self.feed( n.inputs[1], y ); self.feed( n.inputs[2], z )
        return n.outputs[0]

    def lerp_f( self, t, a, b ):
        '''a + t * (b - a) for floats'''
        return self.math( 'MULTIPLY_ADD', t, self.math( 'SUBTRACT', b, a ), a )

    def lerp_v( self, t, a, b ):
        return self.vec( 'ADD', a, self.vec( 'SCALE', self.vec( 'SUBTRACT', b, a ), t ) )

    def eq( self, a, value ):
        return self.math( 'COMPARE', a, value, 0.25 )

    def scene_value( self, name, kind ):
        key = ( name, kind )
        if key in self.attr_cache:
            return self.attr_cache[key]
        n = self.node( 'ShaderNodeAttribute', name )
        n.attribute_type = 'VIEW_LAYER'
        n.attribute_name = name
        out = n.outputs['Fac'] if kind == 'float' else n.outputs['Vector']
        self.attr_cache[key] = out
        return out

    def srgb_encode( self, v ):
        chans = []
        for c in self.sep( v ):
            c = self.math( 'MAXIMUM', c, 0.0 )
            lo = self.math( 'MULTIPLY', c, 12.92 )
            hi = self.math( 'SUBTRACT', self.math( 'MULTIPLY', self.math( 'POWER', c, 1.0 / 2.4 ), 1.055 ), 0.055 )
            is_hi = self.math( 'GREATER_THAN', c, 0.0031308 )
            chans.append( self.lerp_f( is_hi, lo, hi ) )
        return self.comb( *chans )

    def max3( self, v ):
        x, y, z = self.sep( v )
        return self.math( 'MAXIMUM', self.math( 'MAXIMUM', x, y ), z )

    def shader_to_rgb( self, shader_node ):
        n = self.node( 'ShaderNodeShaderToRGB' )
        self.links.new( shader_node.outputs[0], n.inputs[0] )
        return n.outputs['Color']

    def light_color( self, v ):
        m = self.math( 'MAXIMUM', self.max3( v ), 1e-6 )
        return self.vec( 'SCALE', self.srgb_encode( self.vec( 'SCALE', v, self.math( 'DIVIDE', 1.0, m ) ) ), m )

    def is_cycles( self ):
        em = self.node( 'ShaderNodeEmission', 'engine probe' )
        em.inputs['Color'].default_value = ( 0.0, 0.0, 0.0, 1.0 )
        n = self.node( 'ShaderNodeMath', 'is cycles', operation='MAXIMUM' )
        n.inputs[0].default_value = 1.0
        n.inputs[1].default_value = 0.0
        self.links.new( self.shader_to_rgb( em ), n.inputs[0] )
        return n.outputs[0]

    def srgb_decode( self, v ):
        chans = []
        for c in self.sep( v ):
            c = self.math( 'MAXIMUM', c, 0.0 )
            lo = self.math( 'DIVIDE', c, 12.92 )
            hi = self.math( 'POWER', self.math( 'DIVIDE', self.math( 'ADD', c, 0.055 ), 1.055 ), 2.4 )
            is_hi = self.math( 'GREATER_THAN', c, 0.04045 )
            chans.append( self.lerp_f( is_hi, lo, hi ) )
        return self.comb( *chans )


def _interface_new( group, name, socket_type, in_out ):
    if hasattr( group, 'interface' ):
        return group.interface.new_socket( name=name, in_out=in_out, socket_type=socket_type )
    coll = group.inputs if in_out == 'INPUT' else group.outputs
    return coll.new( socket_type, name )

def _make_group( name, inputs, outputs ):
    group = bpy.data.node_groups.new( name, 'ShaderNodeTree' )
    group['mt_version'] = GROUP_VERSION
    for sname, stype, default in inputs:
        sock = _interface_new( group, sname, stype, 'INPUT' )
        if default is not None:
            try:
                sock.default_value = default
            except Exception:
                pass
    for sname, stype in outputs:
        _interface_new( group, sname, stype, 'OUTPUT' )
    gin = group.nodes.new( 'NodeGroupInput' ); gin.location = ( -1700, 0 )
    gout = group.nodes.new( 'NodeGroupOutput' ); gout.location = ( 1800, 0 )
    return group, gin.outputs, gout.inputs

def _current( name ):
    g = bpy.data.node_groups.get( name )
    if g is None:
        return None
    if g.get( 'mt_version', 1 ) >= GROUP_VERSION:
        return g
    g.name = name + ' (old)'
    return None


def get_coords_group():
    g = _current( COORDS_GROUP )
    if g is not None:
        return g
    group, I, O = _make_group( COORDS_GROUP, (
        ( 'Normal',                'NodeSocketVector', ( 0.0, 0.0, 1.0 ) ),
        ( 'Vertex Normal',         'NodeSocketVector', ( 0.0, 0.0, 1.0 ) ),
        ( 'fHalfLambertRevise',    'NodeSocketFloat', 0.5 ),
        ( 'fHalfLambertReviseRev', 'NodeSocketFloat', 0.5 ),
        ( 'Uroko',                 'NodeSocketFloat', 0.0 ),
        ( 'fUrokoFactor',          'NodeSocketFloat', 1.0 ),
    ), (
        ( 'Toon UV',        'NodeSocketVector' ),     # red channel (all three with one light)
        ( 'Toon UV G',      'NodeSocketVector' ),
        ( 'Toon UV B',      'NodeSocketVector' ),
        ( 'Rev UV',         'NodeSocketVector' ),
        ( 'Rev UV G',       'NodeSocketVector' ),
        ( 'Rev UV B',       'NodeSocketVector' ),
        ( 'View UV',        'NodeSocketVector' ),
        ( 'Shading Normal', 'NodeSocketVector' ),
        ( 'NdotL',          'NodeSocketFloat' ),
        ( 'Light Color',    'NodeSocketVector' ),
        ( 'Lambert Light',  'NodeSocketVector' ),
        ( 'Ambient Light',  'NodeSocketVector' ),
        ( 'World Light',    'NodeSocketVector' ),
        ( 'Scene Lights',   'NodeSocketFloat' ),
    ) )
    b = _NB( group )
    L = b.vec( 'NORMALIZE', b.scene_value( 'mt_light_dir', 'vector' ), label='L' )
    N = b.vec( 'NORMALIZE', I['Normal'] )
    Nv = b.vec( 'NORMALIZE', I['Vertex Normal'] )
    ndl = b.vec( 'DOT_PRODUCT', N, L, label='N.L' )

    p = b.math( 'MULTIPLY', I['Uroko'],
                b.math( 'POWER', b.math( 'MAXIMUM', b.math( 'MINIMUM', ndl, 1.0 ), 0.0 ), I['fUrokoFactor'] ) )
    Nb = b.vec( 'ADD', N, b.vec( 'SCALE', b.vec( 'SUBTRACT', Nv, N ), p ), label='uroko normal' )
    nbdl = b.vec( 'DOT_PRODUCT', Nb, L )
    use = b.math( 'MULTIPLY', b.scene_value( 'mt_scene_lights', 'float' ),
                  b.math( 'SUBTRACT', 1.0, b.is_cycles() ), label='use scene lights' )

    def probe( *normals ):
        total = None
        for n in normals:
            d = b.node( 'ShaderNodeBsdfDiffuse', 'light probe' )
            d.inputs['Color'].default_value = ( 1.0, 1.0, 1.0, 1.0 )
            b.feed( d.inputs['Normal'], n )
            c = b.shader_to_rgb( d )
            total = c if total is None else b.vec( 'ADD', total, c )
        return total

    # tangent frame around the shading normal
    zx = b.math( 'GREATER_THAN', b.math( 'ABSOLUTE', b.sep( Nb )[2] ), 0.9 )
    helper = b.lerp_v( zx, ( 0.0, 0.0, 1.0 ), ( 1.0, 0.0, 0.0 ) )
    T1 = b.vec( 'NORMALIZE', b.vec( 'CROSS_PRODUCT', Nb, helper ) )
    T2 = b.vec( 'CROSS_PRODUCT', Nb, T1 )
    neg = lambda v: b.vec( 'SCALE', v, -1.0 )
    Pf = probe( Nb )
    Pb = probe( neg( Nb ) )
    P1 = probe( T1, neg( T1 ) )
    P2 = probe( T2, neg( T2 ) )
    # light reaching both sides evenly is the world: it becomes ambient and is taken out
    W = b.vec( 'MINIMUM', Pf, Pb, label='world light' )
    W2 = b.vec( 'SCALE', W, 2.0 )
    pos = lambda v: b.vec( 'SCALE', b.vec( 'MAXIMUM', v, ( 0.0, 0.0, 0.0 ) ), math.pi )
    Ef = pos( b.vec( 'SUBTRACT', Pf, W ) )
    Eb = pos( b.vec( 'SUBTRACT', Pb, W ) )
    E1 = pos( b.vec( 'SUBTRACT', P1, W2 ) )
    E2 = pos( b.vec( 'SUBTRACT', P2, W2 ) )
    En = b.vec( 'ADD', Ef, Eb )
    sq = b.vec( 'ADD', b.vec( 'ADD', b.vec( 'MULTIPLY', En, En ), b.vec( 'MULTIPLY', E1, E1 ) ), b.vec( 'MULTIPLY', E2, E2 ) )
    I_lin = b.comb( *[ b.math( 'SQRT', c ) for c in b.sep( sq ) ] )
    X = b.vec( 'DIVIDE', b.vec( 'SUBTRACT', Ef, Eb ), b.vec( 'MAXIMUM', I_lin, ( 1e-6, 1e-6, 1e-6 ) ), label='scene N.L (rgb)' )
    Xr, Xg, Xb = b.sep( X )
    LC_scene = b.light_color( I_lin )
    LC_key = b.scene_value( 'mt_light_color', 'vector' )   # the key sun holds the game's value as is
    lam_key = b.vec( 'SCALE', LC_key, b.math( 'MAXIMUM', ndl, 0.0 ) )
    lam_scene = b.vec( 'MULTIPLY', LC_scene, b.vec( 'MAXIMUM', X, ( 0.0, 0.0, 0.0 ) ) )

    def ramp_u( s, d ):
        # u = max(0, s * N.L + saturate(1 - s))
        return b.math( 'MAXIMUM', b.math( 'MULTIPLY_ADD', s, d, b.math( 'SUBTRACT', 1.0, s, clamp=True ) ), 0.0 )
    toon_uv = [ b.comb( ramp_u( I['fHalfLambertRevise'], b.lerp_f( use, nbdl, xc ) ), 0.5, 0.0 ) for xc in ( Xr, Xg, Xb ) ]
    rev_uv = [ b.comb( ramp_u( I['fHalfLambertReviseRev'], b.lerp_f( use, ndl, xc ) ), 0.5, 0.0 ) for xc in ( Xr, Xg, Xb ) ]

    # sphere map / FUVViewNormal: view space vertex normal, (x, y) * 0.5 + 0.5
    vt = b.node( 'ShaderNodeVectorTransform', 'view normal' )
    vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    b.feed( vt.inputs[0], Nv )
    vn = b.vec( 'NORMALIZE', vt.outputs[0] )
    vx, vy, _ = b.sep( vn )
    O_view = b.comb( b.math( 'MULTIPLY_ADD', vx, 0.5, 0.5 ), b.math( 'MULTIPLY_ADD', vy, 0.5, 0.5 ), 0.0 )

    amb = b.vec( 'SCALE', b.srgb_encode( W ), b.math( 'MULTIPLY', use, b.scene_value( 'mt_world_ambient', 'float' ) ) )

    for name, sock in zip( ( 'Toon UV', 'Toon UV G', 'Toon UV B', 'Rev UV', 'Rev UV G', 'Rev UV B' ), toon_uv + rev_uv ):
        b.links.new( sock, O[name] )
    b.links.new( O_view, O['View UV'] )
    b.links.new( Nb, O['Shading Normal'] )
    b.links.new( b.lerp_f( use, ndl, b.max3( X ) ), O['NdotL'] )
    b.links.new( b.lerp_v( use, LC_key, LC_scene ), O['Light Color'] )
    b.links.new( b.lerp_v( use, lam_key, lam_scene ), O['Lambert Light'] )
    b.links.new( amb, O['Ambient Light'] )
    b.links.new( W, O['World Light'] )
    b.links.new( use, O['Scene Lights'] )
    return group

CHARACTER_INPUTS = (
    # textures
    ( 'Albedo',            'NodeSocketColor',  ( 0.8, 0.8, 0.8, 1.0 ) ),
    ( 'Alpha',             'NodeSocketFloat',  1.0 ),
    ( 'Normal',            'NodeSocketVector', ( 0.0, 0.0, 1.0 ) ),
    ( 'Shading Normal',    'NodeSocketVector', ( 0.0, 0.0, 1.0 ) ),
    ( 'Occlusion',         'NodeSocketFloat',  1.0 ),
    ( 'Specular Mask',     'NodeSocketFloat',  1.0 ),
    ( 'Toon Ramp',         'NodeSocketColor',  ( 1.0, 1.0, 1.0, 1.0 ) ),
    ( 'Toon Rev Ramp',     'NodeSocketColor',  ( 1.0, 1.0, 1.0, 1.0 ) ),
    ( 'Reflection',        'NodeSocketColor',  ( 0.0, 0.0, 0.0, 1.0 ) ),
    # lighting, from MT Toon Coords
    ( 'Lambert Light',     'NodeSocketVector', ( 1.15, 1.15, 1.15 ) ),
    ( 'Light Color',       'NodeSocketVector', ( 1.15, 1.15, 1.15 ) ),
    ( 'Ambient Light',     'NodeSocketVector', ( 0.0, 0.0, 0.0 ) ),
    ( 'World Light',       'NodeSocketVector', ( 0.0, 0.0, 0.0 ) ),
    ( 'Scene Lights',      'NodeSocketFloat',  0.0 ),
    # mrl constants, named as in the shader
    ( 'fAlbedoColor',      'NodeSocketColor',  ( 1.0, 1.0, 1.0, 1.0 ) ),
    ( 'fDiffuseColor',     'NodeSocketColor',  ( 1.0, 1.0, 1.0, 1.0 ) ),
    ( 'fSpecularColor',    'NodeSocketColor',  ( 1.0, 1.0, 1.0, 1.0 ) ),
    ( 'fShininess',        'NodeSocketFloat',  16.0 ),
    ( 'fReflectiveColor',  'NodeSocketColor',  ( 1.0, 1.0, 1.0, 1.0 ) ),
    ( 'fFresnelSchlick',   'NodeSocketFloat',  0.0 ),
    ( 'fFresnelLegacyFactor', 'NodeSocketFloat', 1.0 ),
    ( 'fFresnelLegacyBias', 'NodeSocketFloat', 0.0 ),
    ( 'fDiffuseColorCorectValue', 'NodeSocketFloat', 1.22 ),
    ( 'fTransparency',     'NodeSocketFloat',  1.0 ),
    # which building blocks the mrl flags picked
    ( 'Toon',              'NodeSocketFloat',  1.0 ),   # FBRDF FToonShader*, else lambert
    ( 'Color Correct',     'NodeSocketFloat',  0.0 ),   # FDiffuse FDiffuseColorCorect
    ( 'Specular',          'NodeSocketFloat',  1.0 ),   # 0 Disable, 1 MaskToon, 2 Map
    ( 'Rim',               'NodeSocketFloat',  1.0 ),   # FCalcRimLight (not None)
    ( 'Fresnel',           'NodeSocketFloat',  0.0 ),   # 0 none, 1 Schlick, 2 Legacy
    ( 'Use Alpha',         'NodeSocketFloat',  0.0 ),
)

def get_character_group():
    g = _current( CHARACTER_GROUP )
    if g is not None:
        return g
    group, I, O = _make_group( CHARACTER_GROUP, CHARACTER_INPUTS, (
        ( 'Shader', 'NodeSocketShader' ),
        ( 'Color',  'NodeSocketColor' ),
    ) )
    b = _NB( group )
    L = b.vec( 'NORMALIZE', b.scene_value( 'mt_light_dir', 'vector' ), label='L' )
    LC = I['Light Color']
    AMB = b.vec( 'ADD', b.scene_value( 'mt_ambient', 'vector' ), I['Ambient Light'] )
    geo = b.node( 'ShaderNodeNewGeometry' )
    V = geo.outputs['Incoming']
    N = b.vec( 'NORMALIZE', I['Normal'] )
    Ns = b.vec( 'NORMALIZE', I['Shading Normal'] )
    ndv = b.vec( 'DOT_PRODUCT', N, V, label='N.V' )

    # diffuse light: (light * ramp + ambient), or plain lambert for non toon FBRDF
    d_toon = b.vec( 'ADD', b.vec( 'MULTIPLY', LC, I['Toon Ramp'] ), AMB )
    d_lam = b.vec( 'ADD', I['Lambert Light'], AMB )
    D = b.lerp_v( I['Toon'], d_lam, d_toon )
    Dlit = b.vec( 'SCALE', b.vec( 'MULTIPLY', D, I['fDiffuseColor'] ), I['Occlusion'], )

    # albedo, saturated like the shader's mul_sat
    am = b.node( 'ShaderNodeMix', 'albedo x fAlbedoColor' )
    am.data_type = 'RGBA'; am.blend_type = 'MULTIPLY'; am.clamp_result = True
    am.inputs['Factor'].default_value = 1.0
    b.feed( am.inputs[6], I['Albedo'] ); b.feed( am.inputs[7], I['fAlbedoColor'] )
    A = am.outputs[2]

    # FDiffuseColorCorect: saturation boost from how grey the light is
    s = b.math( 'DIVIDE', b.vec( 'DOT_PRODUCT', Dlit, ( 1.0, 1.0, 1.0 ) ),
                b.math( 'MAXIMUM', b.vec( 'LENGTH', Dlit ), 1e-6 ) )
    k = b.math( 'MULTIPLY',
                b.math( 'SUBTRACT', 1.0, b.math( 'EXPONENT', b.math( 'MULTIPLY', I['fDiffuseColorCorectValue'], -1.0 ) ) ),
                b.math( 'SUBTRACT', 1.0, b.math( 'DIVIDE', s, 3.0 ) ) )
    hsv = b.node( 'ShaderNodeHueSaturation', 'color correct' )
    hsv.inputs['Hue'].default_value = 0.5
    b.feed( hsv.inputs['Saturation'], b.math( 'ADD', 1.0, k ) )
    b.feed( hsv.inputs['Value'], b.math( 'MULTIPLY', s, 0.583333 ) )
    hsv.inputs['Fac'].default_value = 1.0
    b.feed( hsv.inputs['Color'], A )
    A2 = b.lerp_v( I['Color Correct'], A, hsv.outputs['Color'] )
    diffuse = b.vec( 'MULTIPLY', Dlit, A2, label='diffuse' )

    # Blinn specular on the (uroko) shading normal
    H = b.vec( 'NORMALIZE', b.vec( 'ADD', L, V ) )
    ndh = b.vec( 'DOT_PRODUCT', Ns, H )
    on = b.math( 'GREATER_THAN', ndh, 1e-5 )
    pw = b.math( 'MULTIPLY', b.math( 'POWER', b.math( 'MAXIMUM', ndh, 1e-5 ), I['fShininess'] ), on )
    spec_key = b.vec( 'SCALE', LC, pw )
    alpha = b.math( 'SQRT', b.math( 'DIVIDE', 2.0, b.math( 'ADD', I['fShininess'], 2.0 ) ) )
    gl = b.node( 'ShaderNodeBsdfGlossy', 'scene specular' )
    gl.inputs['Color'].default_value = ( 1.0, 1.0, 1.0, 1.0 )
    b.feed( gl.inputs['Roughness'], b.math( 'SQRT', alpha ) )
    b.feed( gl.inputs['Normal'], Ns )
    g_raw = b.vec( 'MAXIMUM', b.vec( 'SUBTRACT', b.shader_to_rgb( gl ), I['World Light'] ), ( 0.0, 0.0, 0.0 ) )
    spec_scene = b.vec( 'SCALE', g_raw, b.math( 'MULTIPLY', b.math( 'MULTIPLY', alpha, alpha ), 4.0 * math.pi * 0.9 ) )
    spec = b.vec( 'MULTIPLY', b.lerp_v( I['Scene Lights'], spec_key, spec_scene ), I['fSpecularColor'] )
    spec = b.vec( 'SCALE', spec, b.math( 'GREATER_THAN', I['Specular'], 0.5 ) )
    refl = b.vec( 'MULTIPLY', I['Reflection'], I['fReflectiveColor'] )
    sr = b.vec( 'ADD', spec, refl )

    f5 = b.math( 'POWER', b.math( 'MAXIMUM', b.math( 'SUBTRACT', 1.0, ndv ), 0.0 ), 5.0 )
    schlick = b.math( 'MULTIPLY_ADD', f5, b.math( 'SUBTRACT', 1.0, I['fFresnelSchlick'] ), I['fFresnelSchlick'] )
    legacy = b.math( 'SUBTRACT', 1.0,
                     b.math( 'MULTIPLY_ADD', f5, I['fFresnelLegacyFactor'], I['fFresnelLegacyBias'], clamp=True ) )
    F = b.lerp_f( b.eq( I['Fresnel'], 1.0 ), 1.0, schlick )
    F = b.lerp_f( b.eq( I['Fresnel'], 2.0 ), F, legacy )
    # MaskToon skips the vertex occlusion, Map and the no spec map case apply it
    occ_f = b.lerp_f( b.eq( I['Specular'], 1.0 ), I['Occlusion'], 1.0 )
    spec_out = b.vec( 'SCALE', sr, b.math( 'MULTIPLY', b.math( 'MULTIPLY', F, I['Specular Mask'] ), occ_f ), )

    # rim: (1 - N.V)^2 ^ power * light * rev ramp * height fade * rim colour * spec mask
    r = b.math( 'POWER', b.math( 'MAXIMUM', b.math( 'SUBTRACT', 1.0, ndv ), 1e-5 ), 2.0 )
    rp = b.math( 'POWER', r, b.scene_value( 'mt_rim_power', 'float' ) )
    pz = b.sep( geo.outputs['Position'] )[2]
    h = b.math( 'DIVIDE', pz, b.math( 'MAXIMUM', b.scene_value( 'mt_unit_scale', 'float' ), 1e-6 ) )
    hmin = b.scene_value( 'mt_rim_min_height', 'float' )
    hmax = b.scene_value( 'mt_rim_max_height', 'float' )
    fade = b.math( 'DIVIDE', b.math( 'SUBTRACT', h, hmin ),
                   b.math( 'MAXIMUM', b.math( 'SUBTRACT', hmax, hmin ), 1e-6 ), clamp=True )
    rim = b.vec( 'MULTIPLY', b.vec( 'MULTIPLY', LC, I['Toon Rev Ramp'] ), b.scene_value( 'mt_rim_color', 'vector' ) )
    rim = b.vec( 'SCALE', rim, b.math( 'MULTIPLY', b.math( 'MULTIPLY', rp, fade ),
                                       b.math( 'MULTIPLY', I['Specular Mask'], I['Rim'] ) ) )

    total = b.vec( 'ADD', b.vec( 'ADD', diffuse, spec_out ), rim, label='game colour' )
    shown = b.srgb_decode( total )

    emit = b.node( 'ShaderNodeEmission' )
    b.feed( emit.inputs['Color'], shown )
    trans = b.node( 'ShaderNodeBsdfTransparent' )
    alpha = b.lerp_f( I['Use Alpha'], 1.0, b.math( 'MULTIPLY', I['Alpha'], I['fTransparency'] ) )
    mix = b.node( 'ShaderNodeMixShader' )
    b.feed( mix.inputs['Fac'], alpha )
    b.links.new( trans.outputs[0], mix.inputs[1] )
    b.links.new( emit.outputs[0], mix.inputs[2] )
    b.links.new( mix.outputs[0], O['Shader'] )
    b.links.new( total, O['Color'] )
    return group

def _pixels( img ):
    w, h = img.size
    buf = np.empty( w * h * 4, dtype=np.float32 )
    img.pixels.foreach_get( buf )
    return buf.reshape( h, w, 4 )

def _new_image( name, w, h, px, path=None, non_color=False ):
    out = bpy.data.images.new( name, w, h, alpha=True )
    # colour space first, changing it later regenerates a generated image and wipes it
    if non_color:
        try:
            out.colorspace_settings.name = 'Non-Color'
        except Exception:
            pass
    out.pixels.foreach_set( np.ascontiguousarray( px, dtype=np.float32 ).ravel() )
    out.update()
    if path:
        try:
            out.filepath_raw = path
            out.file_format = 'PNG'
            out.save()
        except Exception:
            out.pack()
    else:
        out.pack()
    return out

YUV_OFFSET = 123.0 / 255.0     # the game's decode, from the material and GUI shaders

def decode_yuv_image( img, png_path=None ):
    if np is None or img is None:
        return img
    px = _pixels( img ).astype( np.float64 )
    v = px[..., 0] - YUV_OFFSET
    a = px[..., 1]
    u = px[..., 2] - YUV_OFFSET
    y = px[..., 3]
    out = np.empty_like( px )
    out[..., 0] = y + 1.402 * v
    out[..., 1] = y - 0.34414 * u - 0.71414 * v
    out[..., 2] = y + 1.772 * u
    out[..., 3] = a
    out = np.clip( out, 0.0, 1.0 )
    h, w = px.shape[:2]
    new = _new_image( img.name.rsplit( '.', 1 )[0] + '_rgb', w, h, out, png_path )
    new['mt_tex_format'] = 42
    return new

def bake_toon_high_ramp( img, toon_factor ):
    from ..mtlib import mtramp
    if np is None or img is None:
        return img
    key = '%s_high_%.4f_%.4f_%.4f' % ( img.name, toon_factor[0], toon_factor[1], toon_factor[2] )
    existing = bpy.data.images.get( key )
    if existing is not None:
        return existing
    px = _pixels( img )
    h, w = px.shape[:2]
    rgb = mtramp.toon_high( px[..., :3].reshape( -1, 3 ), toon_factor ).reshape( h, w, 3 )
    out = np.concatenate( [ rgb, px[..., 3:4] ], axis=2 )
    new = _new_image( key, w, h, out, None, non_color=True )
    return new
