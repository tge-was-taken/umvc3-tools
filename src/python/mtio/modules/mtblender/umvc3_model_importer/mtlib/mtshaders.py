import os
import csv
import struct
import zlib
import collections

from .sm3 import Shader, regtype, USAGE
from . import sm3ir

try:
    import numpy as np
except ImportError:
    np = None

class MFX:
    def __init__( self, path ):
        d = self.d = open( path, 'rb' ).read()
        assert d[:4] == b'MFX\0', 'not an mfx'
        self.hash = struct.unpack_from( '<I', d, 8 )[0]
        self.n = struct.unpack_from( '<I', d, 0xc )[0]
        self.st = struct.unpack_from( '<Q', d, 0x10 )[0]
        self.ptr = [ struct.unpack_from( '<Q', d, 0x18 + 8 * i )[0] for i in range( self.n ) ]
        self.name = [ None ] * self.n
        self.type = [ None ] * self.n
        for i, o in enumerate( self.ptr ):
            if o:
                self.name[i] = self._s( struct.unpack_from( '<Q', d, o )[0] )
                self.type[i] = struct.unpack_from( '<I', d, o + 0x10 )[0] & 0x3f
        self.idx = { nm: i for i, nm in enumerate( self.name ) if nm }
        self._nodes()

    def _s( self, o ):
        d = self.d
        e = d.index( b'\0', self.st + o )
        return d[self.st + o:e].decode( 'latin1' )

    def crc( self, i ):
        return ( zlib.crc32( self.name[i].encode( 'latin1' ) ) ^ 0xffffffff ) & 0xfffff

    def id( self, name ):
        i = self.idx[name]
        return ( self.crc( i ) << 12 ) | i

    def _nodes( self ):
        self.nfunc = [ 0 ] * self.n
        self.refs = [ [] for _ in range( self.n ) ]
        for i, o in enumerate( self.ptr ):
            if not o or self.type[i] != 2:
                continue
            cnt = ( struct.unpack_from( '<I', self.d, o + 0x2c )[0] >> 10 ) & 0x1ff
            lp = struct.unpack_from( '<Q', self.d, o + 0x58 )[0]
            lst = list( struct.unpack_from( '<%dH' % cnt, self.d, lp ) ) if cnt else []
            f = [ x for x in lst if self.type[x] == 2 ]
            v = [ x for x in lst if self.type[x] != 2 ]
            self.nfunc[i] = len( f )
            self.refs[i] = f + v

    def default_table( self ):
        return [ i if self.type[i] == 2 else 0 for i in range( self.n ) ]

    def function_value( self, slot, impl ):
        return ( self.id( slot ) & 0xfffff000 ) ^ self.id( impl )

    def texture_value( self, slot, tex_type ):
        return ( self.id( slot ) & 0xfffff000 ) | ( tex_type & 0xfff )

    def _collect( self, sid, T, out ):
        if sid & 0xfffff000:
            out.append( sid & 0xfffff000 )
        i = sid & 0xfff
        nf = self.nfunc[i]
        refs = self.refs[i]
        for c in refs[:nf]:
            self._collect( T[c], T, out )
        for c in refs[nf:]:
            if T[c]:
                out.append( T[c] )
        return out

    def key( self, tech, pas, states, outenc, overrides ):
        T = self.default_table()
        for i, v in overrides.items():
            T[i] = v
        o = self.ptr[self.idx[tech]]
        p = struct.unpack_from( '<6I', self.d, o + ( pas + 1 ) * 0x30 )
        words = []
        for k, sv in enumerate( states ):
            if sv:
                words.append( ( sv & 0xfffff000 ) | k )
        words.append( outenc )
        for slot in ( 0, 3, 4, 2, 1, 5 ):
            if p[slot]:
                self._collect( p[slot], T, words )
        return ( _mtcrc( words ) << 32 ) | _fnv( words )


def _mktab():
    t = []
    for n in range( 256 ):
        c = n
        for _ in range( 8 ):
            c = ( c >> 1 ) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append( c )
    return t

_CRCT = _mktab()

def _mtcrc( words ):
    c = 0xffffffff
    for w in words:
        for sh in ( 24, 16, 8, 0 ):
            c = _CRCT[( ( w >> sh ) ^ c ) & 0xff] ^ ( c >> 8 )
    return c

def _fnv( words ):
    h = 0x811C9DC5
    for w in words:
        w ^= 0x14DA14DA
        for sh in ( 0, 8, 16, 24 ):
            h = ( ( h * 0x01000193 ) & 0xffffffff ) ^ ( ( w >> sh ) & 0xff )
    return h


# texture format byte -> texture type in the key (MtTexture::resolveFormatAndUsage)
TEX_TYPE = { 0x0F: 0xA, 0x19: 5, 0x1E: 1, 0x1F: 3, 0x20: 8, 0x23: 8, 0x21: 9, 0x24: 9, 0x25: 0xF,
             0x29: 0x14, 0x2A: 0x15, 0x2B: 0x16, 0x2F: 0x18 }

class SPK:
    def __init__( self, path ):
        s = self.s = open( path, 'rb' ).read()
        assert s[:4] == b'SPK\0', 'not an spkg'
        self.mfx_hash = struct.unpack_from( '<I', s, 4 )[0]
        self.nprog, self.nvs, self.nps = struct.unpack_from( '<3H', s, 0xa )
        core = lambda o: struct.unpack_from( '<Q', s, o )[0] + 0x30
        self.blob = struct.unpack_from( '<Q', s, 0x28 )[0]
        H = core( 0x78 )
        self.combo = {}
        k = 0
        while H + 16 * k < self.blob:
            key, nxt, rec = struct.unpack_from( '<QII', s, H + 16 * k )
            if key:
                self.combo[key] = rec
            k += 1
        self.prog = [ struct.unpack_from( '<8Q', s, 0x8080 + 0x40 * i ) for i in range( self.nprog ) ]
        self.vs_tab = [ struct.unpack_from( '<QQ', s, core( 0x48 ) + 16 * k ) for k in range( self.nvs ) ]
        self.ps_tab = [ struct.unpack_from( '<QQ', s, core( 0x50 ) + 16 * k ) for k in range( self.nps ) ]
        # global numbering (blob order), the one used in the RE notes and shader dumps
        order = { o: i for i, o in enumerate( sorted( [ t[1] for t in self.vs_tab ] + [ t[1] for t in self.ps_tab ] ) ) }
        self.vs_global = [ order[t[1]] for t in self.vs_tab ]
        self.ps_global = [ order[t[1]] for t in self.ps_tab ]
        self._cache = {}

    def lookup( self, key ):
        r = self.combo.get( key )
        if r is None:
            return None
        p = self.prog[r]
        return r, p[3], p[4]

    def _shader( self, tab, i ):
        if ( id( tab ), i ) in self._cache:
            return self._cache[( id( tab ), i )]
        size, off = tab[i]
        o = self.blob + off
        n = ( size >> 12 ) or 16384
        n = min( n, ( len( self.s ) - o ) // 4 )
        sh = Shader( list( struct.unpack_from( '<%dI' % n, self.s, o ) ) )
        self._cache[( id( tab ), i )] = sh
        return sh

    def vs( self, i ):
        return self._shader( self.vs_tab, i )

    def ps( self, i ):
        return self._shader( self.ps_tab, i )

_LAYOUT = None

def cbuffer_layouts():
    global _LAYOUT
    if _LAYOUT is None:
        _LAYOUT = collections.defaultdict( list )
        path = os.path.join( os.path.dirname( __file__ ), 'res', 'cbuffer_layouts.csv' )
        with open( path ) as f:
            for r in csv.DictReader( f ):
                _LAYOUT[r['cbuffer']].append( ( int( r['float_offset'] ), r['member'], r['packed'] == 'True' ) )
        for k in _LAYOUT:
            _LAYOUT[k].sort()
    return _LAYOUT

def ctab_location( name ):
    lay = cbuffer_layouts()
    if '__packed' in name:
        cb, row = name.split( '__packed' )
        if cb == 'Globals':
            cb = '$Globals'
        return cb, int( row ) * 4
    for cb, members in lay.items():
        for off, member, packed in members:
            if member == name:
                return cb, off
    return None, None


def _decls( sh ):
    ins, outs = {}, {}
    for t, a in sh.insts:
        if t & 0xffff == 31 and regtype( a[1] ) in ( 1, 6 ):
            usage = USAGE.get( a[0] & 0x1f, '?' )
            ui = ( a[0] >> 16 ) & 0xf
            ( ins if regtype( a[1] ) == 1 else outs )[a[1] & 0x7ff] = ( usage, ui, ( a[1] >> 16 ) & 0xf )
    return ins, outs

def ps_inputs( sh ):
    '''pixel shader v register -> (usage, usage index)'''
    out = {}
    for t, a in sh.insts:
        if t & 0xffff == 31 and regtype( a[1] ) == 1:
            out[a[1] & 0x7ff] = ( USAGE.get( a[0] & 0x1f, '?' ), ( a[0] >> 16 ) & 0xf )
    return out

def classify_vs( sh, seed=1 ):
    N = 96
    b = sm3ir.build( sh )
    ins, outs = _decls( sh )
    rng = np.random.default_rng( seed )
    names = { c['name']: c for c in ( sh.ctab['consts'] if sh.ctab else [] ) }
    consts = {}
    for c in ( sh.ctab['consts'] if sh.ctab else [] ):
        if c['set'] == 2:
            for j in range( c['cnt'] ):
                consts[c['idx'] + j] = rng.uniform( -1, 1, 4 )
    if 'CBSkinning__packed0' in names:
        consts[names['CBSkinning__packed0']['idx']] = np.array( [ 0.0, 0.5, 0.5, 0.0 ] )
    if '__tMatrixMap__invsize' in names:
        consts[names['__tMatrixMap__invsize']['idx']] = np.array( [ 0.25, 0.25, 0.0, 0.0 ] )
    eye_reg = names.get( 'CBViewProjection__packed4', {} ).get( 'idx' )

    def matrix_texel( c ):
        k = np.clip( np.round( ( c[:, 0] - 0.5 ) / 0.25 ), 0, 3 ).astype( int )
        return np.eye( 4 )[k]

    samplers = {}
    for c in ( sh.ctab['consts'] if sh.ctab else [] ):
        if c['set'] == 3:
            samplers[c['idx']] = matrix_texel if 'Matrix' in c['name'] else ( lambda c: np.zeros( ( len( c ), 4 ) ) )
    inputs, raw = {}, {}
    for reg, ( usage, ui, mask ) in ins.items():
        v = rng.uniform( 0.05, 0.95, ( N, 4 ) )
        inputs[reg] = v
        raw[( usage, ui )] = v
    out, _ = sm3ir.evaluate( b, consts, inputs, samplers, n=N )
    out = { k: v.astype( np.float64 ) for k, v in out.items() }

    def norm( v ):
        return v / np.maximum( np.linalg.norm( v, axis=1, keepdims=True ), 1e-12 )
    Q = {}
    pos = raw.get( ( 'position', 0 ) )
    if pos is not None:
        for k in range( 3 ):
            Q['pos.' + 'xyz'[k]] = pos[:, k]
        if eye_reg is not None:
            E = consts[eye_reg][:3]
            vd = norm( pos[:, :3] - E )
            for k in range( 3 ):
                Q['view.' + 'xyz'[k]] = vd[:, k]
                Q['eyevec.' + 'xyz'[k]] = pos[:, k] - E[k]
            Q['eyedist'] = np.linalg.norm( pos[:, :3] - E, axis=1 )
    nrm = raw.get( ( 'normal', 0 ) )
    if nrm is not None:
        n = norm( nrm[:, :3] * 2 - 1 )
        for k in range( 3 ):
            Q['normal.' + 'xyz'[k]] = n[:, k]
        Q['occlusion'] = nrm[:, 3] * 2 - 1
        tan = raw.get( ( 'tangent', 0 ) )
        if tan is not None:
            t = norm( tan[:, :3] * 2 - 1 )
            sgn = tan[:, 3] * 2 - 1
            bn = norm( np.cross( n, t ) * sgn[:, None] )
            for k in range( 3 ):
                Q['tangent.' + 'xyz'[k]] = t[:, k]
                Q['binormal.' + 'xyz'[k]] = bn[:, k]
    lin_basis, lin_names = [], []
    for ( usage, ui ), v in raw.items():
        for k in range( 4 ):
            lin_basis.append( v[:, k] )
            lin_names.append( '%s%d.%s' % ( usage, ui, 'xyzw'[k] ) )
    A = np.stack( lin_basis + [ np.ones( N ) ], 1 )
    res = {}
    for reg, ( usage, ui, mask ) in outs.items():
        o = out.get( 'o%d' % reg )
        comps = []
        for k in range( 4 ):
            if not ( mask & ( 1 << k ) ):
                comps.append( None )
                continue
            y = o[:, k] if o is not None else np.zeros( N )
            hit = None
            if np.allclose( y, y[0], atol=1e-6 ):
                hit = 'const %.9g' % y[0]
            if hit is None:
                for name, q in Q.items():
                    if np.allclose( y, q, atol=1e-4 ):
                        hit = name
                        break
                    if np.allclose( y, -q, atol=1e-4 ):
                        hit = '-' + name
                        break
            if hit is None:
                coef = np.linalg.lstsq( A, y, rcond=None )[0]
                if np.allclose( A @ coef, y, atol=1e-4 ):
                    terms = [ '%.9g*%s' % ( c, n ) for c, n in zip( coef, lin_names + [ '1' ] ) if abs( c ) > 1e-6 ]
                    hit = 'lin ' + ' '.join( terms )
            comps.append( hit or '?' )
        res[( usage, ui )] = comps
    return res

class Program:
    def __init__( self, db, key, record, vs_index, ps_index ):
        self.db = db
        self.key = key
        self.record = record
        self.vs_index = vs_index
        self.ps_index = ps_index

    @property
    def vs( self ):
        return self.db.spk.vs( self.vs_index )

    @property
    def ps( self ):
        return self.db.spk.ps( self.ps_index )

    @property
    def ps_number( self ):
        return self.db.spk.ps_global[self.ps_index]

    @property
    def vs_number( self ):
        return self.db.spk.vs_global[self.vs_index]


class ShaderDB:
    _instances = {}

    @classmethod
    def find_native( cls, *hints ):
        cands = []
        for h in hints:
            if not h:
                continue
            p = os.path.abspath( h )
            for _ in range( 12 ):
                cands.append( p )
                cands.append( os.path.join( p, 'nativePCx64' ) )
                parent = os.path.dirname( p )
                if parent == p:
                    break
                p = parent
        for c in cands:
            if os.path.isfile( os.path.join( c, 'sa', 'DX9_64', 'root.spkg' ) ) and \
               os.path.isfile( os.path.join( c, 'UserShader', 'UserShaderPackage.mfx' ) ):
                return c
        return None

    @classmethod
    def get( cls, native_dir ):
        native_dir = os.path.abspath( native_dir )
        if native_dir not in cls._instances:
            cls._instances[native_dir] = cls( native_dir )
        return cls._instances[native_dir]

    def __init__( self, native_dir ):
        self.native_dir = native_dir
        self.mfx = MFX( os.path.join( native_dir, 'UserShader', 'UserShaderPackage.mfx' ) )
        self.spk = SPK( os.path.join( native_dir, 'sa', 'DX9_64', 'root.spkg' ) )
        self._sem = {}

    def overrides_by_name( self, named ):
        out = {}
        for slot, v in named.items():
            if slot not in self.mfx.idx:
                continue
            i = self.mfx.idx[slot]
            if isinstance( v, int ):
                out[i] = v
            elif isinstance( v, tuple ) and v[0] == 'tex':
                out[i] = self.mfx.texture_value( slot, v[1] )
            elif isinstance( v, str ) and v in self.mfx.idx:
                if v != slot:
                    out[i] = self.mfx.function_value( slot, v )
        return out

    def program( self, tech, pas, ia, outenc, named_overrides ):
        ov = self.overrides_by_name( named_overrides )
        states = [ self.mfx.id( ia ) if ia in self.mfx.idx else 0, 0, 0, 0 ]
        key = self.mfx.key( tech, pas, states, outenc, ov )
        r = self.spk.lookup( key )
        if r is None:
            return None
        return Program( self, key, r[0], r[1], r[2] )

    def vs_semantics( self, vs_index ):
        if vs_index not in self._sem:
            self._sem[vs_index] = classify_vs( self.spk.vs( vs_index ), seed=vs_index + 1 )
        return self._sem[vs_index]
