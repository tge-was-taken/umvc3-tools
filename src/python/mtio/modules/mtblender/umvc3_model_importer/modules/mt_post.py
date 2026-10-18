import os, json, math
import numpy as np

from ..mtlib import mtshaders, sm3ir

RES = os.path.join( os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) ), 'mtlib', 'res' )
DEFAULT_RECIPE = os.path.join( RES, 'post_training_room.json' )

_recipes = {}
def load_recipe( path=None ):
    path = path or DEFAULT_RECIPE
    if path not in _recipes:
        with open( path ) as f:
            _recipes[path] = json.load( f )
    return _recipes[path]


def _sampler( img, filt, address ):
    H, W = img.shape[:2]
    border = address == 'border'
    if border:
        pad = np.zeros( ( H + 2, W + 2, img.shape[2] ), np.float32 )
        pad[1:-1, 1:-1] = img
    f32 = np.float32

    def point( c ):
        x = np.floor( c[:, 0].astype( f32 ) * f32( W ) ).astype( np.int64 )
        y = np.floor( c[:, 1].astype( f32 ) * f32( H ) ).astype( np.int64 )
        out = img[np.clip( y, 0, H - 1 ), np.clip( x, 0, W - 1 )]
        if border:
            out = np.where( ( ( x < 0 ) | ( x >= W ) | ( y < 0 ) | ( y >= H ) )[:, None], 0.0, out )
        return out

    def linear( c ):
        u = c[:, 0].astype( f32 ) * f32( W ) - f32( 0.5 )
        v = c[:, 1].astype( f32 ) * f32( H ) - f32( 0.5 )
        x0 = np.floor( u ); y0 = np.floor( v )
        # 8 bits of sub texel precision in the filter weights
        fx = ( np.round( ( u - x0 ) * 256 ) / 256 )[:, None]
        fy = ( np.round( ( v - y0 ) * 256 ) / 256 )[:, None]
        x0 = x0.astype( np.int64 ); y0 = y0.astype( np.int64 )
        if border:
            src = pad
            cx = lambda x: np.clip( x + 1, 0, W + 1 )
            cy = lambda y: np.clip( y + 1, 0, H + 1 )
        else:
            src = img
            cx = lambda x: np.clip( x, 0, W - 1 )
            cy = lambda y: np.clip( y, 0, H - 1 )
        a = src[cy( y0 ), cx( x0 )]; b = src[cy( y0 ), cx( x0 + 1 )]
        c_ = src[cy( y0 + 1 ), cx( x0 )]; d = src[cy( y0 + 1 ), cx( x0 + 1 )]
        return ( a * ( 1 - fx ) + b * fx ) * ( 1 - fy ) + ( c_ * ( 1 - fx ) + d * fx ) * fy

    return point if filt == 'point' else linear


BLEND = {
    1: lambda s, d: 0.0, 2: lambda s, d: 1.0,
    3: lambda s, d: s[..., :3], 4: lambda s, d: 1 - s[..., :3],
    5: lambda s, d: s[..., 3:4], 6: lambda s, d: 1 - s[..., 3:4],
    7: lambda s, d: d[..., 3:4], 8: lambda s, d: 1 - d[..., 3:4],
    9: lambda s, d: d[..., :3], 10: lambda s, d: 1 - d[..., :3],
}

def _blend( src, dst, sb, db ):
    out = np.empty_like( src )
    for sl in ( slice( 0, 3 ), slice( 3, 4 ) ):
        s, d = src[..., sl], dst[..., sl]
        fs = BLEND.get( sb, BLEND[2] )( src, dst ); fd = BLEND.get( db, BLEND[1] )( src, dst )
        if isinstance( fs, np.ndarray ) and fs.shape[-1] == 3 and sl.start == 3: fs = fs[..., :1]
        if isinstance( fd, np.ndarray ) and fd.shape[-1] == 3 and sl.start == 3: fd = fd[..., :1]
        if isinstance( fs, np.ndarray ) and fs.shape[-1] == 1 and sl.start == 0: fs = np.repeat( fs, 3, -1 )
        if isinstance( fd, np.ndarray ) and fd.shape[-1] == 1 and sl.start == 0: fd = np.repeat( fd, 3, -1 )
        out[..., sl] = s * fs + d * fd
    return out

def _pass_consts( p, kind, sizes, target_size ):
    Wt, Ht = target_size
    out = {}
    cap_t = p['size']
    for name, rows_idx in p[kind + '_consts'].items():
        rows, idx = [ list( r ) for r in rows_idx[:-1] ], rows_idx[-1]
        if name == 'fScreenHalfPixelOffset':
            rows = [ [ 1.0 / Wt, 1.0 / Ht, 0.0, 0.0 ] ]
        elif name.endswith( '__invsize' ):
            tex = name[2:-len( '__invsize' )]
            for sname, inp in p['inputs'].items():
                if sname.endswith( '__' + tex ):
                    Ws, Hs = sizes[inp['src']]
                    rows = [ [ 1.0 / Ws, 1.0 / Hs ] + rows[0][2:] ]
        elif name == 'fBloomGaussOffsets':
            inp = next( iter( p['inputs'].values() ) )
            cw, ch = inp['size']
            Ws, Hs = sizes[inp['src']]
            rows = [ [ r[0] * cw / Ws, r[1] * ch / Hs ] + r[2:] for r in rows ]
        elif name.startswith( 'CBScreen' ):
            r = rows[0]
            if abs( r[0] - cap_t[0] ) < 0.5 and abs( r[1] - cap_t[1] ) < 0.5:
                rows = [ [ float( Wt ), float( Ht ), 1.0 / Wt, 1.0 / Ht ] ]
        for k, r in enumerate( rows ):
            out[idx + k] = np.array( r, np.float32 )
    return out


_ir_cache = {}
def _ir( db, kind, number, ints ):
    key = ( kind, number, tuple( map( tuple, ints ) ) )
    if key not in _ir_cache:
        loc = { g: i for i, g in enumerate( db.spk.vs_global if kind == 'vs' else db.spk.ps_global ) }
        sh = db.spk.vs( loc[number] ) if kind == 'vs' else db.spk.ps( loc[number] )
        _ir_cache[key] = ( sh, sm3ir.build( sh, ints={ k: tuple( ints[k] ) for k in range( 16 ) } ) )
    return _ir_cache[key]


def run( db, scene_img, recipe=None, log=None ):
    recipe = recipe or load_recipe()
    H, W = scene_img.shape[:2]
    images = { 'scene': np.round( np.clip( scene_img, 0, 1 ) * 255 ) / 255 }
    sizes = { 'scene': ( W, H ) }
    f32 = np.float32
    for p in recipe['passes']:
        dx, dy = p['div']
        Wt, Ht = max( 1, W // dx ), max( 1, H // dy )
        n = Wt * Ht
        vs, bv = _ir( db, 'vs', p['vs'], p['vs_ints'] )
        ps, bp = _ir( db, 'ps', p['ps'], p['ps_ints'] )
        vsc = _pass_consts( p, 'vs', sizes, ( Wt, Ht ) )
        psc = _pass_consts( p, 'ps', sizes, ( Wt, Ht ) )
        jj, ii = np.mgrid[0:Ht, 0:Wt]
        u = ( ii.astype( f32 ) + f32( 0.5 ) ) / f32( Wt )
        v = ( jj.astype( f32 ) + f32( 0.5 ) ) / f32( Ht )
        for _ in range( 2 ):
            u = np.nextafter( u, f32( 0 ) ); v = np.nextafter( v, f32( 0 ) )
        u = u.ravel(); v = v.ravel()
        v0 = np.stack( [ u * 2 - 1, 1 - v * 2, u, v ], 1 )
        vres, _ = sm3ir.evaluate( bv, vsc, { 0: v0 }, {}, n=n )
        _, vouts = mtshaders._decls( vs )
        pins, _ = mtshaders._decls( ps )
        inputs = {}
        for reg, ( usage, ui, mask ) in pins.items():
            for oreg, ( ou, oui, om ) in vouts.items():
                if ( ou, oui ) == ( usage, ui ):
                    inputs[reg] = vres['o%d' % oreg]
        smp = {}
        for sname, inp in p['inputs'].items():
            img = images.get( inp['src'] )
            if img is None:
                img = np.zeros( ( 1, 1, 4 ), np.float32 )
            smp[inp['reg']] = _sampler( img, inp['filter'], inp['address'] )
        res, _ = sm3ir.evaluate( bp, psc, inputs, smp, n=n )
        # NaN becomes 0 on a UNORM target
        src = np.clip( np.nan_to_num( res['oC0'].reshape( Ht, Wt, 4 ), nan=0.0, posinf=1.0, neginf=0.0 ), 0, 1 )
        enable, sb, dbl, op = p['blend']
        if enable:
            dst = images.get( p['target'] )
            if dst is None or dst.shape != src.shape:
                dst = np.zeros_like( src )
            src = np.clip( _blend( src, dst, sb, dbl ), 0, 1 )
        images[p['target']] = np.round( src * 255 ) / 255
        sizes[p['target']] = ( Wt, Ht )
        if log:
            log( 'post pass %d ps %d -> %s %dx%d' % ( p['draw'], p['ps'], p['target'], Wt, Ht ) )
    return images[recipe['output']]

def srgb_encode( x ):
    x = np.maximum( x, 0 )
    return np.where( x <= 0.0031308, x * 12.92, 1.055 * np.power( x, 1 / 2.4 ) - 0.055 )

def render_with_post( context, recipe_path=None, image_name='MT Game Render', log=None ):
    import bpy, tempfile
    from . import mt_exact
    scene = context.scene
    if int( scene.get( 'mt_outenc', 1 ) ) == 0:
        raise RuntimeError( 'the super cut-in shaders draw after the game\'s post processing, a plain render already matches' )
    native = scene.get( 'mt_game_native_dir', '' )
    db = mtshaders.ShaderDB.get( native )
    rs = scene.render
    keep = ( rs.filepath, rs.image_settings.file_format, rs.image_settings.color_depth,
             rs.image_settings.color_mode )
    tmp = os.path.join( tempfile.gettempdir(), 'mt_post_render.exr' )
    try:
        rs.filepath = tmp
        rs.image_settings.file_format = 'OPEN_EXR'
        rs.image_settings.color_depth = '32'
        rs.image_settings.color_mode = 'RGBA'
        bpy.ops.render.render( write_still=True )
    finally:
        rs.filepath, rs.image_settings.file_format, rs.image_settings.color_depth, \
            rs.image_settings.color_mode = keep
    img = bpy.data.images.load( tmp, check_existing=False )
    W, H = img.size
    lin = np.empty( W * H * 4, np.float32 )
    img.pixels.foreach_get( lin )
    bpy.data.images.remove( img )
    try:
        os.remove( tmp )
    except OSError:
        pass
    lin = lin.reshape( H, W, 4 )[::-1]
    # exact materials show srgb_decode( oC0 * fHDRCompressDecode ); undo that
    hdr = scene.get( mt_exact.scene_prop_name( 'CBHDRFactor__packed0', 0 ) )
    dec = float( hdr[1] ) if hdr is not None else 2.0
    if scene.get( 'mt_debug_raw', 0 ):
        raw = lin.copy()
    else:
        raw = np.empty_like( lin )
        raw[..., :3] = srgb_encode( lin[..., :3] ) / dec
        raw[..., 3] = lin[..., 3]
    final = run( db, raw, load_recipe( recipe_path ), log )
    alpha = raw[..., 3:4]
    if scene.render.film_transparent:
        # the glow spreads past the silhouette; keep what bloom added as coverage
        base = np.clip( np.round( np.clip( raw[..., :3], 0, 1 ) * 255 ) / 255 * dec, 0, 1 )
        glow = np.clip( final[..., :3] - base, 0, 1 )
        alpha = np.maximum( alpha, glow.max( -1, keepdims=True ) )
    else:
        alpha = np.ones_like( alpha )
    out = np.concatenate( [ final[..., :3], alpha ], -1 )
    im = bpy.data.images.get( image_name )
    if im is None or im.size[0] != W or im.size[1] != H:
        if im is not None:
            bpy.data.images.remove( im )
        im = bpy.data.images.new( image_name, W, H, alpha=True, float_buffer=False )
    im.alpha_mode = 'PREMUL'
    # a byte image takes its pixels as display values, which is what the game shows
    im.pixels.foreach_set( np.ascontiguousarray( out[::-1] ).ravel() )
    im.update()
    return im
