'''MTFramework Pixel Shader
'''
import os
import json

import bpy
import mathutils

from ..mtlib import mtshaders, sm3ir

RENDERER_DEFAULTS = {
    # key light: [0].w = ?, [1] = direction to the light (MT axes), [2] = colour
    'sLightParam0': [ ( 0.0, 0.0, 0.0, 0.9 ), ( 0.032362, 0.447458, 0.893719, 0.0 ), ( 1.15, 1.15, 1.15, 1.0 ), ( 0.0, 0.0, 0.0, 0.0 ) ],
    'sLightParam1': [ ( 0.0, 0.0, 0.0, 0.0 ), ( 0.0, 0.0, 0.0, 0.0 ), ( 0.0, 0.0, 0.0, 0.0 ), ( 0.0, 1.0, 0.0, 0.0 ) ],
    'CBAmbient__packed0': [ ( 0.0, 0.0, 0.0, 1.0 ) ],
    'CBAmbient__packed1': [ ( 0.75, 0.0, 0.0, 0.125 ) ],
    # rim light min height, max height, power
    'CBToon__packed0': [ ( 2.0, 15.0, 1.0, 0.0 ) ],
    # the stage sdl says ( 0, 2.326, 10 ); the game drew Ryu with 0.8 of that
    'fRimLightColorFactor': [ ( 0.0, 1.860466, 8.0, 1.0 ) ],
    'fCutInFactor': [ ( 1.0, 1.0, 1.0, 1.0 ) ],
    'fGlobalTransparency': [ ( 1.0, 0.0, 0.0, 0.0 ) ],
    'CBROPTest__packed0': [ ( 0.0, 0.0, 0.0, 0.999001 ) ],
    # the scene target holds colour * 0.5, post decodes * 2
    'CBHDRFactor__packed0': [ ( 0.5, 2.0, 1.0, 1.0 ) ],
    'fLightMaskSelector': [ ( 1.0, 0.0, 0.0, 0.0 ) ],
    'CBScreen__packed0': [ ( 0.0, 0.0, 1.0, 1.0 ) ],
    'CBScreen__packed1': [ ( 1600.0, 900.0, 1.0 / 1600.0, 1.0 / 900.0 ) ],
}

TEMPLATE_FILE = os.path.join( os.path.dirname( os.path.dirname( __file__ ) ), 'mtlib', 'res', 'renderer_templates.json' )

def renderer_templates():
    try:
        with open( TEMPLATE_FILE ) as f:
            return json.load( f )
    except Exception:
        return None

def scene_prop_name( ctab_name, row ):
    return 'mtc_%s_%d' % ( ctab_name, row )

def ensure_renderer_props( scene, values=None, overwrite=False ):
    '''Writes the renderer constants as scene props (mtc_<name>_<row>).'''
    values = values or RENDERER_DEFAULTS
    for name, rows in values.items():
        for r, v in enumerate( rows ):
            key = scene_prop_name( name, r )
            if overwrite or key not in scene.keys():
                scene[key] = [ float( x ) for x in tuple( v )[:4] ] + [ 0.0 ] * ( 4 - len( tuple( v )[:4] ) )

SKINNING = {
    'IASkinTB1wt': ( 'FSkinning1Weight', 'FSkinningPF1Weight' ),
    'IASkinTBC1wt': ( 'FSkinning1Weight', 'FSkinningPF1Weight' ),
    'IASkinTB2wt': ( 'FSkinning2Weight', 'FSkinningPF2Weight' ),
    'IASkinTB4wt': ( 'FSkinning4WeightBranch', 'FSkinningPF4WeightBranch' ),
    'IASkinTBC8wt': ( 'FSkinning8WeightBranch', 'FSkinningPF8WeightBranch' ),
    'IASkinBridge1wt': ( 'FSkinning1Weight', 'FSkinningPF1Weight' ),
    'IASkinBridge2wt': ( 'FSkinning2Weight', 'FSkinningPF2Weight' ),
    'IASkinBridge4wt': ( 'FSkinning4WeightBranch', 'FSkinningPF4WeightBranch' ),
    'IASkinBridge8wt': ( 'FSkinning8WeightBranch', 'FSkinningPF8WeightBranch' ),
}

def technique_for( material ):
    t = ( material.type or '' ).split( ':' )[-1]
    return 'T' + t if t else 'TMaterialChar'

def material_overrides( material, images ):
    named = {}
    for cmd in material.cmds:
        if cmd.type == 'flag' and cmd.data:
            named[cmd.name] = cmd.data
        elif cmd.type == 'texture':
            fmt = None
            img = images.get( cmd.name ) if images else None
            if img is not None:
                fmt = img.get( 'mt_tex_format' )
            named[cmd.name] = ( 'tex', mtshaders.TEX_TYPE.get( int( fmt ), 0 ) if fmt is not None else 0 )
    return named

def receives_shadows( prim_flags ):
    try:
        f = int( str( prim_flags ), 0 )
    except Exception:
        return True
    return ( f & 0x0104 ) == 0x0104

def wanted_renderer_state( scene, receive=True ):
    mip = getattr( scene, 'sub_scene_properties', None )
    point = getattr( mip, 'mt_point_light', None ) if mip is not None else None
    return {
        'FDynamicLight1': 'FPointLightD' if point is not None else None,
        'FLightMask': 'FLightMaskEnable' if receive else None,
        'FShadowReceiveFaceAttn': 'FShadowReceiveFaceAttnIncrease' if receive else 'FShadowReceiveFaceAttnCut',
    }

def template_order( temps, scene, receive=True ):
    want = wanted_renderer_state( scene, receive )
    def score( t ):
        return sum( 1 for k, v in want.items() if t.get( k ) == v )
    return sorted( range( len( temps ) ), key=lambda i: -score( temps[i] ) )

def pick_program( db, material, ia, images, scene, outenc=1, tech=None, receive=True ):
    templates = renderer_templates() or {}
    tech = tech or technique_for( material )
    temps = templates.get( '%s_%d' % ( tech, outenc ) ) or templates.get( 'TMaterialChar_%d' % outenc ) or [ {} ]
    order = template_order( temps, scene, receive )
    named_mat = material_overrides( material, images ) if material is not None else {}
    if tech == 'TMaterialCharAlpha':
        # the renderer turns alpha test on for every alpha character material (35 of 35
        # TMaterialCharAlpha keys in the shader log)
        named_mat.setdefault( 'FAlphaTest', 'FAlphaTestGreater' )
    for ti in order:
        if ti >= len( temps ):
            continue
        named = dict( temps[ti] )
        if ia in SKINNING:
            named['FSkinning'], named['FSkinningPF'] = SKINNING[ia]
        named.update( named_mat )
        prog = db.program( tech, 0, ia, outenc, named )
        if prog is not None:
            return prog, ti
    return None, None

def _is_sock( x ):
    return isinstance( x, bpy.types.NodeSocket )

class Bind:

    def __init__( self, tree, material, images, prog, db, scene, x0=-5000 ):
        self.tree = tree
        self.n = tree.nodes
        self.l = tree.links
        self.material = material
        self.images = images or {}
        self.prog = prog
        self.db = db
        self.scene = scene
        self.x0 = x0
        self.cache = {}
        self.ps = prog.ps
        self.ctab = sorted( [ c for c in ( self.ps.ctab['consts'] if self.ps.ctab else [] ) ], key=lambda c: c['idx'] )
        self.ps_in = mtshaders.ps_inputs( self.ps )
        self.sem = db.vs_semantics( prog.vs_index )
        self.y = 0

    # -- small helpers
    def node( self, kind, **props ):
        nd = self.n.new( kind )
        for k, v in props.items():
            setattr( nd, k, v )
        nd.location = ( self.x0 - 600, self.y )
        self.y -= 60
        nd.hide = True
        return nd

    def feed( self, sock, v ):
        if _is_sock( v ):
            self.l.new( v, sock )
        elif v is not None:
            sock.default_value = v

    def m( self, op, a, b=None, c=None ):
        nd = self.node( 'ShaderNodeMath', operation=op )
        for i, x in enumerate( ( a, b, c ) ):
            if x is not None:
                self.feed( nd.inputs[i], x )
        return nd.outputs[0]

    def sep( self, vec ):
        nd = self.node( 'ShaderNodeSeparateXYZ' )
        self.feed( nd.inputs[0], vec )
        return nd.outputs[0], nd.outputs[1], nd.outputs[2]

    def vmath( self, op, a, b=None ):
        nd = self.node( 'ShaderNodeVectorMath', operation=op )
        self.feed( nd.inputs[0], a )
        if b is not None:
            if op == 'SCALE':
                self.feed( nd.inputs['Scale'], b )
            else:
                self.feed( nd.inputs[1], b )
        return nd.outputs['Value' if op in ( 'DOT_PRODUCT', 'LENGTH', 'DISTANCE' ) else 'Vector']

    def mt_axes( self, vec, scale=False ):
        x, y, z = self.sep( vec )
        out = [ x, z, self.m( 'MULTIPLY', y, -1.0 ) ]
        if scale:
            s = self.scene_float( 'mt_unit_scale', 1.0 )
            out = [ self.m( 'DIVIDE', c, s ) for c in out ]
        return out

    def scene_float( self, name, default ):
        key = ( 'sf', name )
        if key not in self.cache:
            if name not in self.scene.keys():
                return default
            a = self.node( 'ShaderNodeAttribute', attribute_type='VIEW_LAYER', attribute_name=name )
            self.cache[key] = a.outputs['Fac']
        return self.cache[key]

    def scene_vec4( self, prop ):
        key = ( 'sv', prop )
        if key not in self.cache:
            a = self.node( 'ShaderNodeAttribute', attribute_type='VIEW_LAYER', attribute_name=prop )
            a.label = prop
            x, y, z = self.sep( a.outputs['Vector'] )
            self.cache[key] = [ x, y, z, a.outputs['Alpha'] ]
        return self.cache[key]

    # -- constants
    def ctab_entry( self, reg, ctab=None ):
        for c in ( ctab if ctab is not None else self.ctab ):
            if c['set'] == 2 and c['idx'] <= reg < c['idx'] + c['cnt']:
                return c, reg - c['idx']
        return None, 0

    def const( self, reg, comp, ctab=None ):
        c, row = self.ctab_entry( reg, ctab )
        if c is None:
            return 0.0
        cb, off = mtshaders.ctab_location( c['name'] )
        if cb is not None:
            data = self.material.getCBuffer( cb )
            if data is not None:
                i = off + row * 4 + comp
                if i < len( data ):
                    return float( data[i] )
                return 0.0
        prop = scene_prop_name( c['name'], row )
        if prop not in self.scene.keys():
            self.scene[prop] = [ 0.0, 0.0, 0.0, 0.0 ]
        return self.scene_vec4( prop )[comp]

    # -- interpolators
    def geometry( self ):
        if 'geo' not in self.cache:
            self.cache['geo'] = self.node( 'ShaderNodeNewGeometry' )
        return self.cache['geo']

    def frame_vec( self, which ):
        key = ( 'frame', which )
        if key not in self.cache:
            nm = self.node( 'ShaderNodeNormalMap' )
            nm.space = 'TANGENT'
            try:
                nm.uv_map = 'UVPrimary'
            except Exception:
                pass
            nm.inputs['Color'].default_value = ( 1.0, 0.5, 0.5, 1.0 ) if which == 'tangent' else ( 0.5, 1.0, 0.5, 1.0 )
            nm.inputs['Strength'].default_value = 1.0
            self.cache[key] = self.mt_axes( nm.outputs['Normal'] )
        return self.cache[key]

    def game_frame( self ):
        if 'gframe' in self.cache:
            return self.cache['gframe']
        geo = self.geometry()
        nm_t = self.node( 'ShaderNodeNormalMap', space='TANGENT' )
        nm_b = self.node( 'ShaderNodeNormalMap', space='TANGENT' )
        for nm, col in ( ( nm_t, ( 1.0, 0.5, 0.5, 1.0 ) ), ( nm_b, ( 0.5, 1.0, 0.5, 1.0 ) ) ):
            try:
                nm.uv_map = 'UVPrimary'
            except Exception:
                pass
            nm.inputs['Color'].default_value = col
        T_b, B_b, N_b = nm_t.outputs['Normal'], nm_b.outputs['Normal'], geo.outputs['Normal']
        coef = self.node( 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='mt_tan_coef' )
        sgn = self.node( 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='mt_tan_sign' )
        cx, cy, cz = self.sep( coef.outputs['Vector'] )
        Tg = self.vmath( 'ADD', self.vmath( 'ADD', self.vmath( 'SCALE', T_b, cx ), self.vmath( 'SCALE', B_b, cy ) ),
                         self.vmath( 'SCALE', N_b, cz ) )
        Tg = self.vmath( 'NORMALIZE', Tg )
        have = self.m( 'GREATER_THAN', self.vmath( 'LENGTH', coef.outputs['Vector'] ), 0.5 )
        mixT = self.node( 'ShaderNodeMix', data_type='VECTOR' )
        self.feed( mixT.inputs[0], have ); self.feed( mixT.inputs[4], T_b ); self.feed( mixT.inputs[5], Tg )
        T = self.vmath( 'NORMALIZE', mixT.outputs[1] )
        # sign: the game's when stored, else Blender's (both define it as sign * cross(N, T)
        # and agree on it for 99% of corners)
        s_have = self.m( 'MULTIPLY', sgn.outputs['Fac'], have )
        Bg = self.vmath( 'SCALE', self.vmath( 'NORMALIZE', self.vmath( 'CROSS_PRODUCT', N_b, T ) ), s_have )
        mixB = self.node( 'ShaderNodeMix', data_type='VECTOR' )
        self.feed( mixB.inputs[0], have ); self.feed( mixB.inputs[4], B_b ); self.feed( mixB.inputs[5], Bg )
        self.cache['gframe'] = ( self.mt_axes( T ), self.mt_axes( mixB.outputs[1] ) )
        return self.cache['gframe']

    def uv( self ):
        if 'uv' not in self.cache:
            u = self.node( 'ShaderNodeUVMap' )
            u.uv_map = 'UVPrimary'
            x, y, _ = self.sep( u.outputs['UV'] )
            self.cache['uv'] = ( x, self.m( 'SUBTRACT', 1.0, y ) )      # game v runs down
        return self.cache['uv']

    def semantic( self, s ):
        if s is None:
            return 0.0
        neg = s.startswith( '-' )
        if neg:
            s = s[1:]
        v = self._semantic( s )
        if neg:
            v = self.m( 'MULTIPLY', v, -1.0 ) if _is_sock( v ) else -v
        return v

    def _semantic( self, s ):
        key = ( 'sem', s )
        if key in self.cache:
            return self.cache[key]
        geo = self.geometry()
        comp = 'xyz'.index( s[-1] ) if '.' in s and s[-1] in 'xyz' else 0
        if s.startswith( 'const ' ):
            v = float( s.split()[1] )
        elif s.startswith( 'normal.' ):
            v = self._vec( 'normal', lambda: self.mt_axes( geo.outputs['Normal'] ) )[comp]
        elif s.startswith( 'pos.' ):
            v = self._vec( 'pos', lambda: self.mt_axes( geo.outputs['Position'], scale=True ) )[comp]
        elif s.startswith( 'tangent.' ):
            v = self.game_frame()[0][comp]
        elif s.startswith( 'binormal.' ):
            v = self.game_frame()[1][comp]
        elif s.startswith( 'view.' ):
            v = self._vec( 'view', lambda: self.mt_axes( self.vmath( 'SCALE', geo.outputs['Incoming'], -1.0 ) ) )[comp]
        elif s.startswith( 'eyevec.' ):
            def ev():
                cam = self.node( 'ShaderNodeCameraData' )
                return self.mt_axes( self.vmath( 'SCALE', geo.outputs['Incoming'],
                                                 self.m( 'MULTIPLY', cam.outputs['View Distance'], -1.0 ) ), scale=True )
            v = self._vec( 'eyevec', ev )[comp]
        elif s == 'eyedist':
            cam = self.node( 'ShaderNodeCameraData' )
            v = self.m( 'DIVIDE', cam.outputs['View Distance'], self.scene_float( 'mt_unit_scale', 1.0 ) )
        elif s == 'occlusion':
            a = self.node( 'ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='mt_ao_darken' )
            v = self.m( 'SUBTRACT', 1.0, a.outputs['Fac'] )
        elif s.startswith( 'lin ' ):
            v = self.linear( s[4:] )
        else:
            v = 0.0
        self.cache[key] = v
        return v

    def _vec( self, name, make ):
        key = ( 'vec', name )
        if key not in self.cache:
            self.cache[key] = make()
        return self.cache[key]

    RAW_SKIP = ( 'position', 'normal', 'tangent', 'blendweight', 'blendindices' )

    def raw_input( self, name ):
        usage = name.rstrip( '0123456789.xyzw' )
        comp = name[-1]
        if usage in self.RAW_SKIP:
            return 0.0
        if usage == 'color':
            return 1.0
        u, v = self.uv()
        return { 'x': u, 'y': v, 'z': 0.0, 'w': 0.0 }[comp]

    def linear( self, expr ):
        acc = None
        for term in expr.split():
            coef, name = term.split( '*', 1 )
            coef = float( coef )
            val = coef if name == '1' else self.raw_input( name )
            if name != '1':
                if _is_sock( val ):
                    val = val if abs( coef - 1.0 ) < 1e-6 else self.m( 'MULTIPLY', val, coef )
                else:
                    val = val * coef
            acc = val if acc is None else ( self.m( 'ADD', acc, val ) if ( _is_sock( acc ) or _is_sock( val ) ) else acc + val )
        return acc if acc is not None else 0.0

    GEOMETRIC = ( 'normal.', 'pos.', 'tangent.', 'binormal.', 'view.', 'eyevec.', 'eyedist', 'occlusion',
                  '-normal.', '-pos.', '-tangent.', '-binormal.', '-view.', '-eyevec.' )

    def input( self, reg, comp ):
        usage = self.ps_in.get( reg )
        if usage is None:
            return 0.0
        comps = self.sem.get( usage )
        if not comps or comps[comp] is None:
            return 0.0
        s = comps[comp]
        if s.startswith( self.GEOMETRIC ):
            return self.semantic( s )
        # anything else (uv transforms, constants the VS passes through, vertex colour):
        # run that part of the vertex shader itself, on the interpolated inputs
        return self.vs_output( usage, comp )

    def vs_output( self, usage, comp ):
        key = ( 'vsout', usage, comp )
        if key in self.cache:
            return self.cache[key]
        if 'vsir' not in self.cache:
            vs = self.prog.vs
            self.cache['vsir'] = ( vs, sm3ir.build( vs ), mtshaders._decls( vs ) )
        vs, vb, ( ins, outs ) = self.cache['vsir']
        reg = next( ( r for r, ( u, ui, m ) in outs.items() if ( u, ui ) == usage ), None )
        if reg is None:
            return 0.0
        node = vb.outputs.get( 'o%d' % reg )
        if node is None:
            return 0.0
        if 'vsemit' not in self.cache:
            from ..mtlib import sm3nodes
            self.cache['vsemit'] = sm3nodes.Emitter( self.tree, vb, VSBind( self, vs, ins ), x0=self.x0 - 2500, y0=-3000 )
        v = self.cache['vsemit'].emit_roots( [ node[comp] ] )[0]
        self.cache[key] = v
        return v

    def vface( self ):
        if 'vface' not in self.cache:
            # the game sees front faces as negative
            self.cache['vface'] = self.m( 'SUBTRACT', self.m( 'MULTIPLY', self.geometry().outputs['Backfacing'], 2.0 ), 1.0 )
        return self.cache['vface']

    def vpos( self, comp ):
        key = ( 'vpos', comp )
        if key not in self.cache:
            tc = self.node( 'ShaderNodeTexCoord' )
            x, y, _ = self.sep( tc.outputs['Window'] )
            size = self.scene_vec4( scene_prop_name( 'CBScreen__packed1', 0 ) )
            # D3D9 vPos is the pixel's integer corner (the shaders add 0.5 themselves),
            # Blender's window coordinate is the pixel centre
            if comp == 0:
                self.cache[key] = self.m( 'SUBTRACT', self.m( 'MULTIPLY', x, size[0] ), 0.5 )
            elif comp == 1:
                self.cache[key] = self.m( 'SUBTRACT', self.m( 'MULTIPLY', self.m( 'SUBTRACT', 1.0, y ), size[1] ), 0.5 )
            else:
                self.cache[key] = 0.0
        return self.cache[key]

    # -- textures
    def sampler_name( self, s ):
        for c in self.ctab:
            if c['set'] == 3 and c['idx'] == s:
                return c['name']
        return ''

    def texture( self, s, kind, coords, loc ):
        name = self.sampler_name( s )
        state, _, slot = name.partition( '__' )
        img = self.images.get( slot )
        if img is None and self.scene.get( 'mt_systex_' + slot ):
            img = bpy.data.images.get( self.scene['mt_systex_' + slot] )
        if img is None or kind != '2d':
            # system textures the game renders itself (light mask, fog table, ...) and cube
            # maps: a flat value until they're captured
            val = self.node( 'ShaderNodeRGB' )
            val.outputs[0].default_value = ( 0.0, 0.0, 0.0, 1.0 )
            val.label = slot or name
            a = self.node( 'ShaderNodeValue' )
            a.outputs[0].default_value = 0.0
            return val.outputs[0], a.outputs[0]
        t = self.n.new( 'ShaderNodeTexImage' )
        t.location = loc
        t.label = slot
        t.image = img
        try:
            img.colorspace_settings.name = 'Non-Color'
            img.alpha_mode = 'CHANNEL_PACKED'
        except Exception:
            pass
        t.interpolation = 'Closest' if 'Point' in state else 'Linear'
        t.extension = 'EXTEND' if state in ( 'SSToonMap', 'SSClamp' ) or 'Clamp' in state or 'Border' in state else 'REPEAT'
        comb = self.node( 'ShaderNodeCombineXYZ' )
        self.feed( comb.inputs[0], coords[0] )
        self.feed( comb.inputs[1], self.m( 'SUBTRACT', 1.0, coords[1] ) if _is_sock( coords[1] ) else 1.0 - coords[1] )
        self.l.new( comb.outputs[0], t.inputs['Vector'] )
        return t.outputs['Color'], t.outputs['Alpha']


class VSBind:
    SKIN = { 'CBSkinning__packed0': ( 0.0, 0.5, 0.5, 0.0 ), '__tMatrixMap__invsize': ( 0.25, 0.25, 0.0, 0.0 ) }

    def __init__( self, ps_bind, vs, ins ):
        self.p = ps_bind
        self.vs = vs
        self.ins = ins
        self.ctab = sorted( vs.ctab['consts'] if vs.ctab else [], key=lambda c: c['idx'] )

    def const( self, reg, comp ):
        c, row = self.p.ctab_entry( reg, self.ctab )
        if c is not None and c['name'] in self.SKIN:
            return self.SKIN[c['name']][comp]
        return self.p.const( reg, comp, self.ctab )

    def input( self, reg, comp ):
        usage, ui, mask = self.ins.get( reg, ( None, 0, 0 ) )
        p = self.p
        if usage == 'position':
            return p.semantic( 'pos.' + 'xyz'[comp] ) if comp < 3 else 1.0
        if usage == 'normal':
            if comp < 3:
                return p.m( 'MULTIPLY_ADD', p.semantic( 'normal.' + 'xyz'[comp] ), 0.5, 0.5 )
            return p.m( 'MULTIPLY_ADD', p.semantic( 'occlusion' ), 0.5, 0.5 )
        if usage == 'tangent':
            if comp < 3:
                return p.m( 'MULTIPLY_ADD', p.semantic( 'tangent.' + 'xyz'[comp] ), 0.5, 0.5 )
            return 1.0
        if usage in ( 'blendweight', 'blendindices' ):
            return 0.0
        if usage == 'color':
            return 1.0
        u, v = p.uv()
        return ( u, v, 0.0, 0.0 )[comp]

    def vface( self ):
        return -1.0

    def vpos( self, comp ):
        return 0.0

    def texture( self, s, kind, coords, loc ):
        # bone matrix texture: identity rows, picked by texel column like the classifier sets up
        p = self.p
        x = coords[0]
        k = p.m( 'ROUND', p.m( 'MULTIPLY', p.m( 'SUBTRACT', x, 0.5 ), 4.0 ) ) if _is_sock( x ) else round( ( x - 0.5 ) * 4 )
        rows = []
        for i in range( 4 ):
            rows.append( p.m( 'COMPARE', k, float( i ), 0.25 ) if _is_sock( k ) else ( 1.0 if k == i else 0.0 ) )
        comb = p.node( 'ShaderNodeCombineColor' )
        for i in range( 3 ):
            p.feed( comb.inputs[i], rows[i] )
        a = rows[3]
        if not _is_sock( a ):
            val = p.node( 'ShaderNodeValue' )
            val.outputs[0].default_value = a
            a = val.outputs[0]
        return comb.outputs[0], a


class StoredMaterial:
    def __init__( self, d ):
        self.name = d.get( 'name', '' )
        self.type = d.get( 'type', '' )
        self.blendState = d.get( 'blendState' )
        self.cmds = [ _Cmd( *c ) for c in d.get( 'cmds', [] ) ]
        self._cb = d.get( 'cbuffers', {} )
        self._alpha = d.get( 'alpha', False )

    def getCBuffer( self, name ):
        return self._cb.get( name )

    def isAlphaBlended( self ):
        return self._alpha

    @staticmethod
    def dump( material ):
        cmds, cbs = [], {}
        for c in material.cmds:
            if c.type == 'cbuffer':
                try:
                    cbs[c.name] = [ float( x ) for x in c.data ]
                except Exception:
                    pass
            elif c.type in ( 'flag', 'texture' ):
                cmds.append( ( c.type, c.name, c.data if isinstance( c.data, str ) else '' ) )
        return json.dumps( dict( name=getattr( material, 'name', '' ), type=material.type, blendState=material.blendState,
                                 cmds=cmds, cbuffers=cbs, alpha=bool( material.isAlphaBlended() ) ) )

class _Cmd:
    def __init__( self, type, name, data ):
        self.type, self.name, self.data = type, name, data


def _srgb_decode( b, sock ):
    '''exact sRGB -> linear'''
    c = b.m( 'MAXIMUM', sock, 0.0 )
    lo = b.m( 'DIVIDE', c, 12.92 )
    hi = b.m( 'POWER', b.m( 'DIVIDE', b.m( 'ADD', c, 0.055 ), 1.055 ), 2.4 )
    t = b.m( 'GREATER_THAN', c, 0.04045 )
    mix = b.node( 'ShaderNodeMix', data_type='FLOAT' )
    b.feed( mix.inputs[0], t ); b.feed( mix.inputs[2], lo ); b.feed( mix.inputs[3], hi )
    return mix.outputs[0]

SHADER_GROUP_VERSION = 2
MATERIAL_CBUFFERS_EDITABLE = ( '$Globals', 'CBMaterial', 'CBHalfLambert', 'CBToon2', 'CBDiffuseColorCorect' )

def _iface_sockets( tree, in_out ):
    if hasattr( tree, 'interface' ):
        return [ it for it in tree.interface.items_tree if getattr( it, 'item_type', 'SOCKET' ) == 'SOCKET' and it.in_out == in_out ]
    return list( tree.inputs if in_out == 'INPUT' else tree.outputs )

def cbuffer_member( cb, index, data_len ):
    '''float index inside a cbuffer -> (member, first float, float count)'''
    members = mtshaders.cbuffer_layouts().get( cb, [] )
    best = None
    for k, ( off, name, packed ) in enumerate( members ):
        if off <= index:
            nxt = members[k + 1][0] if k + 1 < len( members ) else data_len
            best = ( name, off, max( 1, nxt - off ) )
        else:
            break
    if best is None:
        return 'c%d' % index, index, 1
    return best

def _is_colour( name ):
    return 'Color' in name or 'Colour' in name

def member_sockets( name, size ):
    out = []
    rows = [ list( range( r, min( r + 4, size ) ) ) for r in range( 0, size, 4 ) ]
    for ri, idx in enumerate( rows ):
        label = name if len( rows ) == 1 else '%s[%d]' % ( name, ri )
        if len( idx ) == 1:
            out.append( ( label, 'NodeSocketFloat', idx ) )
            continue
        head, tail = idx[:3], idx[3:]
        stype = 'NodeSocketColor' if ( _is_colour( name ) and len( head ) == 3 ) else 'NodeSocketVector'
        out.append( ( label, stype, head ) )
        for t in tail:
            out.append( ( label + '.w', 'NodeSocketFloat', [ t ] ) )
    return out


class GroupBind( Bind ):

    def __init__( self, tree, material, images, prog, db, scene, x0=-5000 ):
        super().__init__( tree, material, images, prog, db, scene, x0 )
        self.gin = self.n.new( 'NodeGroupInput' )
        self.gin.location = ( x0 - 1200, 0 )
        self.members = {}          # member -> dict(cb, off, size, sockets {float idx: socket})
        self.external = {}         # ir tex id -> input name
        self.order = []            # interface order (names)

    def _input( self, name, stype ):
        names = [ s.name for s in _iface_sockets( self.tree, 'INPUT' ) ]
        if name not in names:
            _gn_socket( self.tree, name, stype, 'INPUT' )
            self.order.append( name )
        return self.gin.outputs[name]

    def param( self, cb, index, data ):
        name, off, size = cbuffer_member( cb, index, len( data ) )
        m = self.members.get( name )
        if m is None:
            m = self.members[name] = dict( cb=cb, off=off, size=size, comps={} )
        k = index - off
        if k not in m['comps']:
            for label, stype, idx in member_sockets( name, size ):
                if k in idx:
                    sock = self._input( label, stype )
                    if len( idx ) == 1:
                        m['comps'][k] = sock
                    else:
                        sep = self.node( 'ShaderNodeSeparateColor' if stype == 'NodeSocketColor' else 'ShaderNodeSeparateXYZ' )
                        self.l.new( sock, sep.inputs[0] )
                        for j, fi in enumerate( idx ):
                            m['comps'][fi] = sep.outputs[j]
                    break
        return m['comps'].get( k, 0.0 )

    def const( self, reg, comp, ctab=None ):
        c, row = self.ctab_entry( reg, ctab )
        if c is None:
            return 0.0
        cb, off = mtshaders.ctab_location( c['name'] )
        if cb is not None:
            data = self.material.getCBuffer( cb )
            if data is not None:
                i = off + row * 4 + comp
                if i >= len( data ):
                    return 0.0
                if cb in MATERIAL_CBUFFERS_EDITABLE:
                    return self.param( cb, i, data )
                return float( data[i] )
        return super().const( reg, comp, ctab )

    def external_texture( self, i, sampler ):
        name = self.external[i]
        col = self._input( name, 'NodeSocketColor' )
        a = self._input( name + ' Alpha', 'NodeSocketFloat' )
        return col, a

    def tidy( self ):
        '''textures first, then constants in cbuffer order'''
        if not hasattr( self.tree, 'interface' ):
            return
        tex = [ n for n in self.order if n in self.external.values() or n[:-6] in self.external.values() ]
        rank = {}
        for name, m in self.members.items():
            for label, stype, idx in member_sockets( name, m['size'] ):
                cbi = MATERIAL_CBUFFERS_EDITABLE.index( m['cb'] ) if m['cb'] in MATERIAL_CBUFFERS_EDITABLE else 99
                rank[label] = ( 1, cbi, m['off'] + idx[0] )
        for k, n in enumerate( tex ):
            rank[n] = ( 0, k, 0 )
        want = sorted( ( it.name for it in _iface_sockets( self.tree, 'INPUT' ) ), key=lambda n: rank.get( n, ( 2, 0, 0 ) ) )
        for pos, n in enumerate( want ):
            items = _iface_sockets( self.tree, 'INPUT' )
            base = min( it.position for it in items )
            it = next( x for x in items if x.name == n )
            try:
                self.tree.interface.move( it, base + pos )
            except Exception:
                pass


def _texture_slot_name( bind, sampler ):
    state, _, slot = bind.sampler_name( sampler ).partition( '__' )
    return state, slot

def _editable_fetches( b, bind, material, images ):
    from ..mtlib import sm3nodes
    slots = { c.name for c in material.cmds if c.type == 'texture' }
    out = {}
    seen = {}
    for i, s in sorted( sm3nodes.independent_textures( b ).items() ):
        if b.g.nodes[i][2] != '2d':
            continue
        state, slot = _texture_slot_name( bind, s )
        if slot not in slots or images.get( slot ) is None:
            continue
        seen[slot] = seen.get( slot, 0 ) + 1
        name = slot if seen[slot] == 1 else '%s %d' % ( slot, seen[slot] )
        out[i] = ( name, slot, state )
    return out

def _internal_images( b, probe, images, fetches ):
    out = {}
    for i, node in enumerate( b.g.nodes ):
        if node[0] == 'tex' and i not in fetches:
            state, slot = _texture_slot_name( probe, node[1] )
            img = ( images or {} ).get( slot )
            if img is not None:
                out[slot] = img
    return sorted( out.items() )

def _group_key( prog, scene, material, images, fetches, receive, internal ):
    internal = [ ( k, v.name ) for k, v in internal ]
    # which cbuffers the MRL has decides socket or renderer default; values of the ones that
    # aren't shown as sockets are baked into the group
    cbs = sorted( ( c.name, len( c.data or [] ), None if c.name in MATERIAL_CBUFFERS_EDITABLE else [ float( x ) for x in c.data ] )
                  for c in material.cmds if c.type == 'cbuffer' )
    return json.dumps( [ SHADER_GROUP_VERSION, prog.record, int( scene.get( 'mt_outenc', 1 ) ),
                         bool( scene.get( 'mt_debug_raw', 0 ) ), bool( material.isAlphaBlended() ),
                         bool( receive ), internal, cbs ] )

def _find_group( kind, key ):
    for g in bpy.data.node_groups:
        if g.get( 'mt_kind' ) == kind and g.get( 'mt_key' ) == key:
            return g
    return None

def _shader_group( prog, db, scene, material, images, fetches, receive, internal, ia=None, logger=None ):
    key = _group_key( prog, scene, material, images, fetches, receive, internal )
    g = _find_group( 'shader', key )
    if g is not None:
        return g, _find_group( 'uv', key ), json.loads( g['mt_members'] )
    names = [ os.path.splitext( v.name )[0] for k, v in internal ]
    ia_short = str( ia or '' ).replace( 'IASkin', '' ).replace( 'IA', '' )
    base = 'MT Shader PS%d %s' % ( prog.ps_number, ia_short ) + ( ' (%s)' % ', '.join( names ) if names else '' )
    g = bpy.data.node_groups.new( base, 'ShaderNodeTree' )
    g['mt_kind'] = 'shader'; g['mt_key'] = key
    from ..mtlib import sm3nodes
    b = sm3ir.build( prog.ps )
    bind = GroupBind( g, material, images, prog, db, scene )
    bind.external = { i: f[0] for i, f in fetches.items() }
    res, kill, em = sm3nodes.emit( g, b, bind, x0=-4000, y0=0, external=fetches.keys() )
    oc = res.get( 'oC0' )
    if oc is None:
        bpy.data.node_groups.remove( g )
        return None, None, None
    gout = g.nodes.new( 'NodeGroupOutput' ); gout.location = ( 800, 0 )
    _gn_socket( g, 'Shader', 'NodeSocketShader', 'OUTPUT' )
    _gn_socket( g, 'Color', 'NodeSocketColor', 'OUTPUT' )
    _gn_socket( g, 'Alpha', 'NodeSocketFloat', 'OUTPUT' )
    # HDR compress: the scene target holds colour * fHDRCompressEncode, post multiplies by
    # fHDRCompressDecode.
    hdr = bind.scene_vec4( scene_prop_name( 'CBHDRFactor__packed0', 0 ) )
    raw = bool( scene.get( 'mt_debug_raw', 0 ) )
    rgb = []
    for k in range( 3 ):
        c = oc[k]
        if _is_sock( c ) and not raw:
            c = bind.m( 'MULTIPLY', c, hdr[1] ) if _uses_hdr( prog ) else c
            rgb.append( _srgb_decode( bind, c ) )
        else:
            rgb.append( c if _is_sock( c ) else float( c ) )
    comb = bind.node( 'ShaderNodeCombineColor' )
    for k in range( 3 ):
        bind.feed( comb.inputs[k], rgb[k] )
    emit = g.nodes.new( 'ShaderNodeEmission' ); emit.location = ( 400, 0 )
    g.links.new( comb.outputs[0], emit.inputs['Color'] )
    alpha = oc[3] if material.isAlphaBlended() else 1.0
    if kill is not None:
        keep = bind.m( 'SUBTRACT', 1.0, bind.m( 'GREATER_THAN', kill, 0.0 ) ) if _is_sock( kill ) else ( 0.0 if kill > 0 else 1.0 )
        alpha = bind.m( 'MULTIPLY', keep, alpha ) if ( _is_sock( keep ) or _is_sock( alpha ) ) else keep * alpha
    a = bind.m( 'MINIMUM', bind.m( 'MAXIMUM', alpha, 0.0 ), 1.0 ) if _is_sock( alpha ) else float( alpha )
    tr = g.nodes.new( 'ShaderNodeBsdfTransparent' ); tr.location = ( 400, -150 )
    mx = g.nodes.new( 'ShaderNodeMixShader' ); mx.location = ( 600, 0 )
    bind.feed( mx.inputs['Fac'], a )
    g.links.new( tr.outputs[0], mx.inputs[1] )
    g.links.new( emit.outputs[0], mx.inputs[2] )
    g.links.new( mx.outputs[0], gout.inputs['Shader'] )
    g.links.new( comb.outputs[0], gout.inputs['Color'] )
    bind.feed( gout.inputs['Alpha'], a )
    bind.tidy()
    g['mt_blend'] = 'BLEND' if material.isAlphaBlended() else ( 'CLIP' if kill is not None else 'OPAQUE' )

    uvg = None
    if fetches:
        uvg = bpy.data.node_groups.new( 'MT UV PS%d %s' % ( prog.ps_number, ia_short ), 'ShaderNodeTree' )
        uvg['mt_kind'] = 'uv'; uvg['mt_key'] = key
        ub = GroupBind( uvg, material, images, prog, db, scene )
        ue = sm3nodes.Emitter( uvg, b, ub, x0=-3000, y0=0 )
        uout = uvg.nodes.new( 'NodeGroupOutput' ); uout.location = ( 600, 0 )
        for i, ( name, slot, state ) in sorted( fetches.items(), key=lambda kv: kv[1][0] ):
            coords = ue.emit_roots( list( b.g.nodes[i][3][:2] ) )
            _gn_socket( uvg, name + ' UV', 'NodeSocketVector', 'OUTPUT' )
            cmb = ub.node( 'ShaderNodeCombineXYZ' )
            ub.feed( cmb.inputs[0], coords[0] )
            ub.feed( cmb.inputs[1], ub.m( 'SUBTRACT', 1.0, coords[1] ) if _is_sock( coords[1] ) else 1.0 - coords[1] )
            uvg.links.new( cmb.outputs[0], uout.inputs[name + ' UV'] )
        ub.tidy()
        bind.members.update( { k: v for k, v in ub.members.items() if k not in bind.members } )
    members = { k: dict( cb=v['cb'], off=v['off'], size=v['size'] ) for k, v in bind.members.items() }
    g['mt_members'] = json.dumps( members )
    if logger:
        logger.info( f'{g.name}: {em.created} nodes, {len( members )} material constants, {len( fetches )} textures outside' )
    return g, uvg, members


def _sampler_settings( node, state, material=None ):
    # the MRL's samplerstate cmd for this sampler, when it picks another state
    if material is not None:
        state = next( ( c.data for c in material.cmds if c.type == 'samplerstate' and c.name == state and c.data ), state )
    node.interpolation = 'Closest' if 'Point' in state else 'Linear'
    node.extension = 'EXTEND' if state in ( 'SSToonMap', 'SSClamp' ) or 'Clamp' in state or 'Border' in state else 'REPEAT'

def _set_socket( sock, values ):
    try:
        if sock.type == 'RGBA':
            sock.default_value = ( values[0], values[1], values[2], 1.0 )
        elif sock.type == 'VECTOR':
            sock.default_value = tuple( values[:3] ) + ( 0.0, ) * ( 3 - len( values[:3] ) )
        else:
            sock.default_value = values[0]
    except Exception:
        pass

def _get_socket( sock ):
    v = sock.default_value
    if sock.type == 'RGBA':
        return [ float( v[0] ), float( v[1] ), float( v[2] ) ]
    if sock.type == 'VECTOR':
        return [ float( v[0] ), float( v[1] ), float( v[2] ) ]
    return [ float( v ) ]

def _member_values( material, cb, off, size ):
    data = material.getCBuffer( cb ) or []
    return [ float( data[off + k] ) if off + k < len( data ) else 0.0 for k in range( size ) ]


def build_exact_material( bpy_material, material, ia, images, context, logger=None, receive=True ):
    scene = context.scene
    native = scene.get( 'mt_game_native_dir', '' )
    if not native or not os.path.isdir( native ):
        return None
    try:
        db = mtshaders.ShaderDB.get( native )
    except Exception as e:
        if logger: logger.warn( f'could not read the game shaders from {native}: {e}' )
        return None
    images = images or {}
        # icl im not sure if this works as intended
    prog, ti = pick_program( db, material, ia, images, scene, outenc=int( scene.get( 'mt_outenc', 1 ) ), receive=receive )
    if prog is None:
        if logger: logger.warn( f'no game shader for {material.name} ({ia})' )
        return None
    ensure_renderer_props( scene )
    probe = GroupBind.__new__( GroupBind )
    probe.ctab = sorted( prog.ps.ctab['consts'] if prog.ps.ctab else [], key=lambda c: c['idx'] )
    psb = sm3ir.build( prog.ps )
    fetches = _editable_fetches( psb, probe, material, images )
    internal = _internal_images( psb, probe, images, fetches )
    g, uvg, members = _shader_group( prog, db, scene, material, images, fetches, receive, internal, ia, logger )
    if g is None:
        return None

    tree = bpy_material.node_tree
    for nd in list( tree.nodes ):
        tree.nodes.remove( nd )
    out = tree.nodes.new( 'ShaderNodeOutputMaterial' ); out.location = ( 500, 0 )
    sg = tree.nodes.new( 'ShaderNodeGroup' ); sg.node_tree = g
    sg.name = sg.label = 'MT Shader'; sg.location = ( 150, 0 ); sg.width = 260
    tree.links.new( sg.outputs['Shader'], out.inputs['Surface'] )
    ug = None
    if uvg is not None:
        ug = tree.nodes.new( 'ShaderNodeGroup' ); ug.node_tree = uvg
        ug.name = ug.label = 'MT UV'; ug.location = ( -650, 0 ); ug.width = 200
    y = 150
    for i, ( name, slot, state ) in sorted( fetches.items(), key=lambda kv: kv[1][0] ):
        t = tree.nodes.new( 'ShaderNodeTexImage' )
        t.name = 'mt_tex:' + name
        t.label = name
        t.location = ( -350, y ); y -= 280
        img = images.get( slot )
        t.image = img
        try:
            img.colorspace_settings.name = 'Non-Color'
            img.alpha_mode = 'CHANNEL_PACKED'
        except Exception:
            pass
        _sampler_settings( t, state, material )
        tree.links.new( ug.outputs[name + ' UV'], t.inputs['Vector'] )
        tree.links.new( t.outputs['Color'], sg.inputs[name] )
        tree.links.new( t.outputs['Alpha'], sg.inputs[name + ' Alpha'] )
    # this material's own constant values on the group sockets
    for name, m in members.items():
        vals = _member_values( material, m['cb'], m['off'], m['size'] )
        for label, stype, idx in member_sockets( name, m['size'] ):
            for node in ( sg, ug ):
                if node is not None and label in node.inputs:
                    _set_socket( node.inputs[label], [ vals[k] for k in idx ] )
    try:
        bpy_material.blend_method = g.get( 'mt_blend', 'OPAQUE' )
    except Exception:
        pass
    try:
        if not isinstance( material, StoredMaterial ):
            bpy_material['mt_mrl'] = StoredMaterial.dump( material )
        bpy_material['mt_images'] = json.dumps( { k: v.name for k, v in images.items() if v is not None } )
    except Exception:
        pass
    from . import mt_mrl_props
    if not isinstance( material, StoredMaterial ) and not getattr( material, '_from_entry', False ):
        # the import: the full MRL entry becomes the material's editable copy
        mt_mrl_props.fill_entry( bpy_material, material, images )
    if mt_mrl_props.has_entry( bpy_material ):
        mt_mrl_props.push_nodes( bpy_material )
    if 'mt_needs_rebuild' in bpy_material.keys():
        del bpy_material['mt_needs_rebuild']
    bpy_material['mt_receive'] = bool( receive )
    bpy_material['mt_program'] = prog.record
    bpy_material['mt_ps'] = prog.ps_number
    bpy_material['mt_vs'] = prog.vs_number
    bpy_material['mt_ia'] = ia
    bpy_material['mt_key'] = '%016X' % prog.key
    bpy_material['mt_template'] = ti
    if logger:
        logger.info( f'{material.name} ({ia}): program {prog.record}, PS {prog.ps_number}, VS {prog.vs_number} -> {g.name}' )
    return prog


def read_material_edits( bpy_material ):
    stored = json.loads( bpy_material.get( 'mt_mrl', '{}' ) or '{}' )
    cbs = { k: list( v ) for k, v in stored.get( 'cbuffers', {} ).items() }
    tex = {}
    tree = bpy_material.node_tree
    if tree is None:
        return dict( cbuffers=cbs, textures=tex )
    sg = tree.nodes.get( 'MT Shader' )
    ug = tree.nodes.get( 'MT UV' )
    g = sg.node_tree if sg is not None and sg.type == 'GROUP' else None
    members = json.loads( g.get( 'mt_members', '{}' ) ) if g is not None else {}
    for name, m in members.items():
        data = cbs.setdefault( m['cb'], [] )
        if len( data ) < m['off'] + m['size']:
            data.extend( [ 0.0 ] * ( m['off'] + m['size'] - len( data ) ) )
        for label, stype, idx in member_sockets( name, m['size'] ):
            for node in ( sg, ug ):
                if node is not None and label in node.inputs and not node.inputs[label].is_linked:
                    vals = _get_socket( node.inputs[label] )
                    for j, k in enumerate( idx ):
                        if j < len( vals ):
                            data[m['off'] + k] = vals[j]
                    break
    for nd in tree.nodes:
        if nd.type == 'TEX_IMAGE' and nd.name.startswith( 'mt_tex:' ) and nd.image is not None:
            slot = nd.name[len( 'mt_tex:' ):].split( ' ' )[0]
            tex.setdefault( slot, nd.image )
    return dict( cbuffers=cbs, textures=tex )

def store_material_edits( bpy_material ):
    from . import mt_mrl_props
    if mt_mrl_props.has_entry( bpy_material ):
        mt_mrl_props.sync( bpy_material )
        return
    if 'mt_mrl' not in bpy_material.keys():
        return
    e = read_material_edits( bpy_material )
    stored = json.loads( bpy_material['mt_mrl'] )
    stored['cbuffers'] = e['cbuffers']
    bpy_material['mt_mrl'] = json.dumps( stored )
    imgs = json.loads( bpy_material.get( 'mt_images', '{}' ) or '{}' )
    for slot, img in e['textures'].items():
        old = bpy.data.images.get( imgs.get( slot, '' ) )
        # the texture format is part of the shader key; a new image without one keeps the
        # slot's (re-export the texture in the same format)
        if old is not None and old is not img and 'mt_tex_format' not in img.keys() and 'mt_tex_format' in old.keys():
            img['mt_tex_format'] = old['mt_tex_format']
        imgs[slot] = img.name
    bpy_material['mt_images'] = json.dumps( imgs )


def _uses_hdr( prog ):
    return any( c['name'].startswith( 'CBHDRFactor' ) for c in ( prog.ps.ctab['consts'] if prog.ps.ctab else [] ) )

def blender_to_mt( v ):
    return ( v[0], v[2], -v[1] )

def _drive( scene, prop, index, expr, variables ):
    try:
        fc = scene.driver_add( '["%s"]' % prop, index )
    except Exception:
        return
    drv = fc.driver
    drv.type = 'SCRIPTED'
    for v in list( drv.variables ):
        drv.variables.remove( v )
    for name, id_type, idb, path in variables:
        var = drv.variables.new()
        var.name = name
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = id_type
        var.targets[0].id = idb
        var.targets[0].data_path = path
    drv.expression = expr

def link_scene_drivers( scene ):
    ensure_renderer_props( scene )
    base = 'sub_scene_properties.mt_key_light'
    # MT (x, y, z) = blender (x, z, -y); matrix_world[2] is the sun's +Z axis (towards the light)
    for i, ( comp, sign ) in enumerate( ( ( 0, 1.0 ), ( 2, 1.0 ), ( 1, -1.0 ) ) ):
        _drive( scene, scene_prop_name( 'sLightParam0', 1 ), i, 'z * %g' % sign,
                [ ( 'z', 'SCENE', scene, '%s.matrix_world[2][%d]' % ( base, comp ) ) ] )
        _drive( scene, scene_prop_name( 'sLightParam0', 2 ), i, 'c * e',
                [ ( 'c', 'SCENE', scene, '%s.data.color[%d]' % ( base, i ) ),
                  ( 'e', 'SCENE', scene, '%s.data.energy' % base ) ] )
    for i in range( 3 ):
        if 'mt_rim_color' in scene.keys():
            _drive( scene, scene_prop_name( 'fRimLightColorFactor', 0 ), i, 'v', [ ( 'v', 'SCENE', scene, '["mt_rim_color"][%d]' % i ) ] )
        if 'mt_ambient' in scene.keys():
            _drive( scene, scene_prop_name( 'CBAmbient__packed0', 0 ), i, 'v', [ ( 'v', 'SCENE', scene, '["mt_ambient"][%d]' % i ) ] )
    for i, key in ( ( 0, 'mt_rim_min_height' ), ( 1, 'mt_rim_max_height' ), ( 2, 'mt_rim_power' ) ):
        if key in scene.keys():
            _drive( scene, scene_prop_name( 'CBToon__packed0', 0 ), i, 'v', [ ( 'v', 'SCENE', scene, '["%s"]' % key ) ] )
    link_point_light( scene )


def rebuild_all( context, logger=None ):
    from . import mt_mrl_props
    done = 0
    for mat in bpy.data.materials:
        if 'mt_mrl' in mat.keys() and 'mt_ia' in mat.keys() and not mt_mrl_props.has_entry( mat ):
            try:
                mt_mrl_props.adopt_legacy( mat )
            except Exception as e:
                if logger: logger.warn( f'could not read the MRL entry of {mat.name}: {e}' )
    mt_mrl_props.sync()
    for mat in bpy.data.materials:
        if 'mt_ia' not in mat.keys() or not mt_mrl_props.has_entry( mat ):
            continue
        try:
            if rebuild_from_entry( mat, context, logger ):
                done += 1
        except Exception as e:
            if logger: logger.warn( f'could not rebuild {mat.name}: {e}' )
    link_scene_drivers( context.scene )
    refresh_outlines( context )
    return done


def rebuild_from_entry( mat, context, logger=None ):
    from . import mt_mrl_props
    info = mt_mrl_props.info_from_entry( mat )
    images = mt_mrl_props.entry_images( mat )
    return build_exact_material( mat, info, mat['mt_ia'], images, context, logger, receive=mat.get( 'mt_receive', True ) ) is not None


def link_point_light( scene ):
    mip = getattr( scene, 'sub_scene_properties', None )
    if mip is None or not hasattr( mip, 'mt_point_light' ):
        return
    base = 'sub_scene_properties.mt_point_light'
    obj = mip.mt_point_light
    if obj is not None:
        if 'mt_falloff_start' not in obj.keys():
            obj['mt_falloff_start'] = 0.0
        if 'mt_falloff_end' not in obj.keys():
            obj['mt_falloff_end'] = 300.0
    us = [ ( 's', 'SCENE', scene, '["mt_unit_scale"]' ) ] if 'mt_unit_scale' in scene.keys() else []
    sc = ' / s' if us else ''
    for i, ( comp, sign ) in enumerate( ( ( 0, 1.0 ), ( 2, 1.0 ), ( 1, -1.0 ) ) ):
        _drive( scene, scene_prop_name( 'sLightParam1', 0 ), i, '(p * %g)%s' % ( sign, sc ),
                [ ( 'p', 'SCENE', scene, '%s.matrix_world[3][%d]' % ( base, comp ) ) ] + us )
        _drive( scene, scene_prop_name( 'sLightParam1', 2 ), i, 'c * e',
                [ ( 'c', 'SCENE', scene, '%s.data.color[%d]' % ( base, i ) ),
                  ( 'e', 'SCENE', scene, '%s.data.energy' % base ) ] )
    _drive( scene, scene_prop_name( 'sLightParam1', 3 ), 0, 'a%s' % sc, [ ( 'a', 'SCENE', scene, '%s["mt_falloff_start"]' % base ) ] + us )
    _drive( scene, scene_prop_name( 'sLightParam1', 3 ), 1, '1.0 / max(b - a, 1e-4)%s' % ( ' * s' if us else '' ),
            [ ( 'a', 'SCENE', scene, '%s["mt_falloff_start"]' % base ), ( 'b', 'SCENE', scene, '%s["mt_falloff_end"]' % base ) ] + us )


RENDERER_DEFAULTS.update( {
    'fOutlineChannelMask': [ ( 1.0, 0.0, 0.0, 0.0 ) ],
    'fOutlineColor0': [ ( 1.0, 1.0, 1.0, 1.0 ) ],
    'CBOutlineFilter__packed9': [ ( 0.0, 0.0001, 0.0, 0.00092 ) ],
} )

# lowkey this doesnt work :sob:
OUTLINE_GROUP = 'MT Outline Hull'

def _gn_socket( group, name, stype, in_out ):
    if hasattr( group, 'interface' ):
        return group.interface.new_socket( name=name, in_out=in_out, socket_type=stype )
    coll = group.inputs if in_out == 'INPUT' else group.outputs
    return coll.new( stype, name )

OUTLINE_GROUP_VERSION = 5

# I DO NOT KNOW IF ANY OF THIS WORKS :DDDDDDD
def outline_group():
    g = bpy.data.node_groups.get( OUTLINE_GROUP )
    if g is not None and g.get( 'mt_version' ) == OUTLINE_GROUP_VERSION:
        return g
    if g is not None:
        g.name = OUTLINE_GROUP + ' (old)'
    g = bpy.data.node_groups.new( OUTLINE_GROUP, 'GeometryNodeTree' )
    g['mt_version'] = OUTLINE_GROUP_VERSION
    _gn_socket( g, 'Geometry', 'NodeSocketGeometry', 'INPUT' )
    _gn_socket( g, 'Material', 'NodeSocketMaterial', 'INPUT' )
    _gn_socket( g, 'Camera', 'NodeSocketObject', 'INPUT' )
    s = _gn_socket( g, 'Width', 'NodeSocketFloat', 'INPUT' ); s.default_value = 0.00092
    s = _gn_socket( g, 'Ortho Depth', 'NodeSocketFloat', 'INPUT' ); s.default_value = 0.0
    s = _gn_socket( g, 'Keep Mesh', 'NodeSocketBool', 'INPUT' ); s.default_value = True
    s = _gn_socket( g, 'Weld Normals', 'NodeSocketFloat', 'INPUT' ); s.default_value = 0.0
    s = _gn_socket( g, 'Push Back', 'NodeSocketFloat', 'INPUT' ); s.default_value = 60.0
    _gn_socket( g, 'Geometry', 'NodeSocketGeometry', 'OUTPUT' )
    N, L = g.nodes, g.links
    gi = N.new( 'NodeGroupInput' ); gi.location = ( -1200, 0 )
    go = N.new( 'NodeGroupOutput' ); go.location = ( 900, 0 )
    def node( kind, x, y, **kw ):
        n = N.new( kind ); n.location = ( x, y )
        for k, v in kw.items(): setattr( n, k, v )
        return n
    merge = node( 'GeometryNodeMergeByDistance', -900, -300 )
    merge.inputs['Distance'].default_value = 1e-4
    L.new( gi.outputs['Geometry'], merge.inputs['Geometry'] )
    pos = node( 'GeometryNodeInputPosition', -900, -500 )
    near = node( 'GeometryNodeSampleNearest', -650, -400 )
    L.new( merge.outputs['Geometry'], near.inputs['Geometry'] )
    L.new( pos.outputs['Position'], near.inputs['Sample Position'] )
    nrm = node( 'GeometryNodeInputNormal', -650, -600 )
    samp = node( 'GeometryNodeSampleIndex', -400, -450, data_type='FLOAT_VECTOR', domain='POINT' )
    L.new( merge.outputs['Geometry'], samp.inputs['Geometry'] )
    L.new( nrm.outputs['Normal'], samp.inputs[3] if len( samp.inputs ) > 3 else samp.inputs['Value'] )
    L.new( near.outputs['Index'], samp.inputs['Index'] )
    # depth from the camera (clip w), or a fixed value for an orthographic camera
    cam = node( 'GeometryNodeObjectInfo', -900, 300, transform_space='RELATIVE' )
    L.new( gi.outputs['Camera'], cam.inputs['Object'] )
    fwd = node( 'ShaderNodeVectorRotate', -650, 300, rotation_type='EULER_XYZ' )
    fwd.inputs['Vector'].default_value = ( 0.0, 0.0, -1.0 )
    L.new( cam.outputs['Rotation'], fwd.inputs['Rotation'] )
    rel = node( 'ShaderNodeVectorMath', -650, 100, operation='SUBTRACT' )
    L.new( pos.outputs['Position'], rel.inputs[0] ); L.new( cam.outputs['Location'], rel.inputs[1] )
    dep = node( 'ShaderNodeVectorMath', -400, 200, operation='DOT_PRODUCT' )
    L.new( rel.outputs[0], dep.inputs[0] ); L.new( fwd.outputs[0], dep.inputs[1] )
    useo = node( 'ShaderNodeMath', -400, 0, operation='GREATER_THAN' )
    L.new( gi.outputs['Ortho Depth'], useo.inputs[0] ); useo.inputs[1].default_value = 0.0
    mixd = node( 'ShaderNodeMix', -200, 100, data_type='FLOAT' )
    L.new( useo.outputs[0], mixd.inputs[0] ); L.new( dep.outputs['Value'], mixd.inputs[2] ); L.new( gi.outputs['Ortho Depth'], mixd.inputs[3] )
    amt = node( 'ShaderNodeMath', 0, 100, operation='MULTIPLY' )
    L.new( mixd.outputs[0], amt.inputs[0] ); L.new( gi.outputs['Width'], amt.inputs[1] )
    # the game normal stored at import (mt_game_normal), Blender's normal where it's missing
    gattr = node( 'GeometryNodeInputNamedAttribute', -650, -800, data_type='FLOAT_VECTOR' )
    gattr.inputs['Name'].default_value = 'mt_game_normal'
    bnorm = node( 'GeometryNodeInputNormal', -650, -950 )
    glen = node( 'ShaderNodeVectorMath', -450, -850, operation='LENGTH' )
    L.new( [ o for o in gattr.outputs if o.type == 'VECTOR' ][0], glen.inputs[0] )
    has = node( 'ShaderNodeMath', -300, -850, operation='GREATER_THAN' )
    L.new( glen.outputs['Value'], has.inputs[0] ); has.inputs[1].default_value = 0.5
    own = node( 'ShaderNodeMix', -250, -950, data_type='VECTOR' )
    L.new( has.outputs[0], own.inputs[0] )
    ov = [ s for s in own.inputs if s.type == 'VECTOR' and s.name in ( 'A', 'B' ) ]
    L.new( bnorm.outputs['Normal'], ov[0] )
    L.new( [ o for o in gattr.outputs if o.type == 'VECTOR' ][0], ov[1] )
    pick = node( 'ShaderNodeMix', -150, -500, data_type='VECTOR' )
    L.new( gi.outputs['Weld Normals'], pick.inputs[0] )
    vec_in = [ s for s in pick.inputs if s.type == 'VECTOR' and s.name in ( 'A', 'B' ) ]
    vec_out = [ s for s in pick.outputs if s.type == 'VECTOR' ][0]
    L.new( [ o for o in own.outputs if o.type == 'VECTOR' ][0], vec_in[0] )
    L.new( samp.outputs[0] if samp.outputs[0].enabled else samp.outputs['Value'], vec_in[1] )
    nn = node( 'ShaderNodeVectorMath', 0, -500, operation='NORMALIZE' )
    L.new( vec_out, nn.inputs[0] )
    off = node( 'ShaderNodeVectorMath', 200, -200, operation='SCALE' )
    L.new( nn.outputs[0], off.inputs[0] )
    L.new( amt.outputs[0], off.inputs['Scale'] )
    # pushed = cam + (p - cam) * (depth + push) / depth  (perspective), p + fwd * push (ortho)
    pos2 = node( 'ShaderNodeVectorMath', 300, -350, operation='ADD' )
    L.new( pos.outputs['Position'], pos2.inputs[0] ); L.new( off.outputs[0], pos2.inputs[1] )
    rel2 = node( 'ShaderNodeVectorMath', 300, -500, operation='SUBTRACT' )
    L.new( pos2.outputs[0], rel2.inputs[0] ); L.new( cam.outputs['Location'], rel2.inputs[1] )
    dep2 = node( 'ShaderNodeVectorMath', 300, -650, operation='DOT_PRODUCT' )
    L.new( rel2.outputs[0], dep2.inputs[0] ); L.new( fwd.outputs[0], dep2.inputs[1] )
    dsafe = node( 'ShaderNodeMath', 450, -650, operation='MAXIMUM' )
    L.new( dep2.outputs['Value'], dsafe.inputs[0] ); dsafe.inputs[1].default_value = 1e-3
    ratio = node( 'ShaderNodeMath', 600, -650, operation='DIVIDE' )
    L.new( gi.outputs['Push Back'], ratio.inputs[0] ); L.new( dsafe.outputs[0], ratio.inputs[1] )
    persp = node( 'ShaderNodeVectorMath', 750, -550, operation='SCALE' )
    L.new( rel2.outputs[0], persp.inputs[0] ); L.new( ratio.outputs[0], persp.inputs['Scale'] )
    ortho = node( 'ShaderNodeVectorMath', 750, -750, operation='SCALE' )
    L.new( fwd.outputs[0], ortho.inputs[0] ); L.new( gi.outputs['Push Back'], ortho.inputs['Scale'] )
    pushv = node( 'ShaderNodeMix', 900, -650, data_type='VECTOR' )
    L.new( useo.outputs[0], pushv.inputs[0] )
    pv = [ x for x in pushv.inputs if x.type == 'VECTOR' and x.name in ( 'A', 'B' ) ]
    L.new( persp.outputs[0], pv[0] ); L.new( ortho.outputs[0], pv[1] )
    total = node( 'ShaderNodeVectorMath', 1050, -400, operation='ADD' )
    L.new( off.outputs[0], total.inputs[0] ); L.new( [ x for x in pushv.outputs if x.type == 'VECTOR' ][0], total.inputs[1] )
    setp = node( 'GeometryNodeSetPosition', 400, -100 )
    L.new( gi.outputs['Geometry'], setp.inputs['Geometry'] ); L.new( total.outputs[0], setp.inputs['Offset'] )
    flip = node( 'GeometryNodeFlipFaces', 550, -100 )
    L.new( setp.outputs[0], flip.inputs[0] )
    setm = node( 'GeometryNodeSetMaterial', 700, -100 )
    L.new( flip.outputs[0], setm.inputs['Geometry'] ); L.new( gi.outputs['Material'], setm.inputs['Material'] )
    join = node( 'GeometryNodeJoinGeometry', 750, 100 )
    L.new( gi.outputs['Geometry'], join.inputs[0] ); L.new( setm.outputs[0], join.inputs[0] )
    sw = node( 'GeometryNodeSwitch', 820, 0, input_type='GEOMETRY' )
    L.new( gi.outputs['Keep Mesh'], sw.inputs[0] )
    false_in = [ s for s in sw.inputs if s.name == 'False' and s.enabled ][0]
    true_in = [ s for s in sw.inputs if s.name == 'True' and s.enabled ][0]
    L.new( setm.outputs[0], false_in ); L.new( join.outputs[0], true_in )
    out = [ s for s in sw.outputs if s.enabled ][0]
    L.new( out, go.inputs['Geometry'] )
    return g


def outline_material( db, ia, context, logger=None ):
    name = 'MT Outline@%s' % ia
    mat = bpy.data.materials.get( name )
    if mat is not None and mat.get( 'mt_ps' ) is not None:
        return mat
    scene = context.scene
    ensure_renderer_props( scene )
    dummy = StoredMaterial( {} )
    prog = None
    templates = renderer_templates() or {}
    for t in templates.get( 'TMaterialOutline_101', [ {} ] ):
        named = dict( t )
        if ia in SKINNING:
            named['FSkinning'], named['FSkinningPF'] = SKINNING[ia]
        prog = db.program( 'TMaterialOutline', 1, ia, 1, named )
        if prog is not None:
            break
    if prog is None:
        if logger: logger.warn( f'no game outline shader for {ia}' )
        return None
    if mat is None:
        mat = bpy.data.materials.new( name )
    mat.use_nodes = True
    tree = mat.node_tree
    for nd in list( tree.nodes ):
        tree.nodes.remove( nd )
    out = tree.nodes.new( 'ShaderNodeOutputMaterial' ); out.location = ( 400, 0 )
    b = sm3ir.build( prog.ps )
    bind = Bind( tree, dummy, {}, prog, db, scene )
    from ..mtlib import sm3nodes
    res, kill, em = sm3nodes.emit( tree, b, bind, x0=-2500, y0=0 )
    oc = res['oC0']
    hdr = bind.scene_vec4( scene_prop_name( 'CBHDRFactor__packed0', 0 ) )
    comb = bind.node( 'ShaderNodeCombineColor' )
    for k in range( 3 ):
        c = oc[k]
        if _is_sock( c ):
            c = _srgb_decode( bind, bind.m( 'MULTIPLY', c, hdr[1] ) if _uses_hdr( prog ) else c )
        bind.feed( comb.inputs[k], c )
    emit = tree.nodes.new( 'ShaderNodeEmission' ); emit.location = ( 0, 0 )
    tree.links.new( comb.outputs[0], emit.inputs['Color'] )
    # the hull's faces are flipped: the side facing the camera must not cover the mesh
    geo = bind.geometry()
    front = bind.m( 'SUBTRACT', 1.0, geo.outputs['Backfacing'] )
    a = oc[3]
    a = bind.m( 'MULTIPLY', front, bind.m( 'MINIMUM', bind.m( 'MAXIMUM', a, 0.0 ), 1.0 ) ) if _is_sock( a ) else bind.m( 'MULTIPLY', front, float( a ) )
    tr = tree.nodes.new( 'ShaderNodeBsdfTransparent' )
    mx = tree.nodes.new( 'ShaderNodeMixShader' ); mx.location = ( 200, 0 )
    bind.feed( mx.inputs['Fac'], a )
    tree.links.new( tr.outputs[0], mx.inputs[1] )
    tree.links.new( emit.outputs[0], mx.inputs[2] )
    tree.links.new( mx.outputs[0], out.inputs['Surface'] )
    for attr, val in ( ( 'blend_method', 'HASHED' ), ( 'shadow_method', 'NONE' ) ):
        try:
            setattr( mat, attr, val )
        except Exception:
            pass
    mat['mt_ps'] = prog.ps_number
    mat['mt_vs'] = prog.vs_number
    mat['mt_ia'] = ia
    if logger:
        logger.info( f'outline ({ia}): PS {prog.ps_number}, VS {prog.vs_number}' )
    return mat


def add_outline( obj, ia, context, logger=None, outline_only=False ):
    scene = context.scene
    native = scene.get( 'mt_game_native_dir', '' )
    if not native:
        return False
    db = mtshaders.ShaderDB.get( native )
    mat = outline_material( db, ia, context, logger )
    if mat is None:
        return False
    mod = obj.modifiers.get( 'MT Outline' ) or obj.modifiers.new( 'MT Outline', 'NODES' )
    mod.node_group = outline_group()
    try:
        while obj.modifiers.find( mod.name ) > 0:
            idx = obj.modifiers.find( mod.name )
            obj.modifiers.move( idx, idx - 1 )
    except Exception:
        pass
    set_outline_inputs( obj, mod, mat, scene, outline_only )
    obj['mt_outline_ia'] = ia
    obj['mt_outline_only'] = bool( outline_only )
    return True

def set_outline_inputs( obj, mod, mat, scene, outline_only ):
    try:
        if mod.node_group is None or mod.node_group.get( 'mt_version' ) != OUTLINE_GROUP_VERSION:
            mod.node_group = outline_group()
    except Exception:
        pass
    cam = scene.camera
    width = scene.get( scene_prop_name( 'CBOutlineFilter__packed9', 0 ), [ 0, 0, 0, 0.00092 ] )[3]
    for item in ( mod.node_group.interface.items_tree if hasattr( mod.node_group, 'interface' ) else mod.node_group.inputs ):
        ident = getattr( item, 'identifier', None )
        nm = getattr( item, 'name', '' )
        if ident is None or getattr( item, 'in_out', 'INPUT' ) != 'INPUT':
            continue
        try:
            if nm == 'Material': mod[ident] = mat
            elif nm == 'Camera' and cam is not None: mod[ident] = cam
            elif nm == 'Width': mod[ident] = float( width )
            elif nm == 'Ortho Depth':
                mod[ident] = 400.0 if cam is None else ( float( cam.data.ortho_scale ) if cam.data.type == 'ORTHO' else 0.0 )
            elif nm == 'Keep Mesh': mod[ident] = not outline_only
            elif nm == 'Push Back': mod[ident] = _push_value( scene )
        except Exception:
            pass
    try:
        mod.node_group = mod.node_group
    except Exception:
        pass
    obj.update_tag()

def refresh_outlines( context ):
    '''points every outline at the scene camera again (after adding or switching cameras)'''
    for obj in context.scene.objects:
        mod = obj.modifiers.get( 'MT Outline' ) if obj.type == 'MESH' else None
        if mod is None:
            continue
        mat = bpy.data.materials.get( 'MT Outline@%s' % obj.get( 'mt_outline_ia', '' ) )
        set_outline_inputs( obj, mod, mat, context.scene, obj.get( 'mt_outline_only', False ) )


MATERIAL_CBUFFERS = ( '$Globals', 'Globals', 'CBMaterial', 'CBHalfLambert', 'CBToon2', 'CBDiffuseColorCorect' )

def load_capture_constants( scene, draws_json, draw_indices, native_dir ):
    db = mtshaders.ShaderDB.get( native_dir )
    draws = json.load( open( draws_json ) ) if isinstance( draws_json, str ) else draws_json
    loc = { g: i for i, g in enumerate( db.spk.ps_global ) }
    import collections
    votes = collections.defaultdict( collections.Counter )
    for di in draw_indices:
        d = draws[di]
        if d.get( 'ps' ) is None or d['ps'] not in loc:
            continue
        sh = db.spk.ps( loc[d['ps']] )
        F = d['ps_raw']
        for c in ( sh.ctab['consts'] if sh.ctab else [] ):
            if c['set'] != 2:
                continue
            cb, off = mtshaders.ctab_location( c['name'] )
            if cb in MATERIAL_CBUFFERS:
                continue
            for r in range( c['cnt'] ):
                votes[scene_prop_name( c['name'], r )][tuple( float( x ) for x in F[c['idx'] + r] )] += 1
    for key, cnt in votes.items():
        scene[key] = list( cnt.most_common( 1 )[0][0] )
    sync_lighting_from_constants( scene )
    return len( votes )

def sync_lighting_from_constants( scene ):
    from . import mt_shading
    g = lambda name, row=0: scene.get( scene_prop_name( name, row ) )
    lp1, lp2 = g( 'sLightParam0', 1 ), g( 'sLightParam0', 2 )
    if lp1 is not None:
        mt_shading.set_key_light_direction( scene, mt_shading.mt_to_blender( tuple( lp1[:3] ) ) )
    if lp2 is not None:
        mt_shading.set_key_light_color( scene, tuple( lp2[:3] ) )
    rim = g( 'fRimLightColorFactor' )
    if rim is not None:
        scene['mt_rim_color'] = tuple( rim[:3] )
    toon = g( 'CBToon__packed0' )
    if toon is not None:
        scene['mt_rim_min_height'], scene['mt_rim_max_height'], scene['mt_rim_power'] = float( toon[0] ), float( toon[1] ), float( toon[2] )
    amb = g( 'CBAmbient__packed0' )
    if amb is not None:
        scene['mt_ambient'] = tuple( amb[:3] )


FACE_GROUPS = range( 70, 80 )
UNUSED_GROUPS = ( 127, )

def apply_face_group( scene, objects=None ):
    if 'mt_face_group' not in scene.keys():
        scene['mt_face_group'] = 70
    face = int( scene['mt_face_group'] )
    objs = objects if objects else [ o for o in scene.objects if o.type == 'MESH' and 'mt_group' in o.keys() ]
    present = { int( o['mt_group'] ) for o in objs if 'mt_group' in o.keys() }
    faces = sorted( g for g in present if g in FACE_GROUPS )
    if faces and face not in faces:
        face = 70 if 70 in faces else faces[0]
    hidden = 0
    for o in objs:
        if 'mt_group' not in o.keys():
            continue
        g = int( o['mt_group'] )
        hide = g in UNUSED_GROUPS or ( g in FACE_GROUPS and g != face )
        # outline-only geometry: the game never draws it in the colour pass
        if o.get( 'mt_bridge' ) and not o.modifiers.get( 'MT Outline' ):
            hide = True
        o.hide_viewport = hide
        o.hide_render = hide
        hidden += hide
    return hidden


_last_camera = {}

@bpy.app.handlers.persistent
def _camera_watch( scene, depsgraph=None ):
    try:
        cam = scene.camera.name if scene.camera else ''
        if _last_camera.get( scene.name ) != cam:
            _last_camera[scene.name] = cam
            if any( o.type == 'MESH' and o.modifiers.get( 'MT Outline' ) for o in scene.objects ):
                refresh_outlines( bpy.context )
    except Exception:
        pass

_rendering = { 'on': False }

def _push_value( scene ):
    if not _rendering['on']:
        return 0.0
    return float( scene.get( 'mt_outline_push', 60.0 ) ) * float( scene.get( 'mt_unit_scale', 1.0 ) or 1.0 )

def _set_push_all( scene ):
    for obj in scene.objects:
        mod = obj.modifiers.get( 'MT Outline' ) if obj.type == 'MESH' else None
        if mod is None or mod.type != 'NODES' or mod.node_group is None:
            continue
        for item in ( mod.node_group.interface.items_tree if hasattr( mod.node_group, 'interface' ) else mod.node_group.inputs ):
            if getattr( item, 'name', '' ) == 'Push Back' and getattr( item, 'in_out', 'INPUT' ) == 'INPUT':
                try:
                    mod[item.identifier] = _push_value( scene )
                except Exception:
                    pass
        obj.update_tag()

@bpy.app.handlers.persistent
def _render_pre( scene, *args ):
    _rendering['on'] = True
    _set_push_all( scene )

@bpy.app.handlers.persistent
def _render_post( scene, *args ):
    _rendering['on'] = False
    _set_push_all( scene )

_HANDLERS = ( ( 'depsgraph_update_post', _camera_watch ), ( 'render_pre', _render_pre ),
              ( 'render_post', _render_post ), ( 'render_cancel', _render_post ) )

def register_handlers():
    for name, fn in _HANDLERS:
        lst = getattr( bpy.app.handlers, name )
        if fn not in lst:
            lst.append( fn )

def unregister_handlers():
    for name, fn in _HANDLERS:
        lst = getattr( bpy.app.handlers, name )
        if fn in lst:
            lst.remove( fn )


def ensure_game_camera( scene, unit_scale=1.0 ):
    if scene.camera is not None:
        return scene.camera
    import math, mathutils
    cam = bpy.data.objects.new( 'MT Game Camera', bpy.data.cameras.new( 'MT Game Camera' ) )
    scene.collection.objects.link( cam )
    cam.data.sensor_fit = 'VERTICAL'
    cam.data.angle_y = math.radians( 32.0 )
    cam.data.clip_start = 1.0 * unit_scale
    cam.data.clip_end = 10000.0 * unit_scale
    cam.location = mathutils.Vector( ( 0.0, -525.0, 70.0 ) ) * unit_scale
    fwd = mathutils.Vector( ( 0.0, 0.9923, 0.1238 ) )
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = fwd.to_track_quat( '-Z', 'Y' )
    scene.camera = cam
    return cam


def split_outlines( objects ):
    made = []
    for obj in objects:
        mod = obj.modifiers.get( 'MT Outline' )
        if mod is None or mod.type != 'NODES' or obj.get( 'mt_outline_only' ):
            continue
        dup = bpy.data.objects.new( obj.name + ' outline', obj.data )
        for coll in obj.users_collection:
            coll.objects.link( dup )
        dup.parent = obj.parent
        dup.parent_type = obj.parent_type
        dup.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
        dup.matrix_basis = obj.matrix_basis.copy()
        for k in ( 'mt_group', 'mt_outline_ia' ):
            if k in obj.keys():
                dup[k] = obj[k]
        dup['mt_outline_only'] = True
        dup['mt_outline_of'] = obj.name
        dup.hide_viewport = obj.hide_viewport
        dup.hide_render = obj.hide_render
        # vertex group names live on the shared mesh, the armature finds them as is
        nm = dup.modifiers.new( 'MT Outline', 'NODES' )
        nm.node_group = mod.node_group
        for src in obj.modifiers:
            if src.type == 'ARMATURE':
                am = dup.modifiers.new( src.name, 'ARMATURE' )
                for a in ( 'object', 'use_vertex_groups', 'use_bone_envelopes', 'use_deform_preserve_volume' ):
                    try: setattr( am, a, getattr( src, a ) )
                    except Exception: pass
        mat = bpy.data.materials.get( 'MT Outline@%s' % obj.get( 'mt_outline_ia', '' ) )
        obj.modifiers.remove( mod )
        set_outline_inputs( dup, nm, mat, bpy.context.scene, True )
        made.append( dup )
    return made
