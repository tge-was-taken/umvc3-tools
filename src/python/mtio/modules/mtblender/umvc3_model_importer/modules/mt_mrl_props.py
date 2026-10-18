import os
import json
import base64

import bpy
from bpy.props import ( StringProperty, FloatProperty, BoolProperty, EnumProperty, IntProperty,
                        CollectionProperty, PointerProperty )

from ..mtlib.immaterial import imMaterialInfo, imMaterialCmd, imMaterialLib

CMD_KINDS = [ ( 'flag', 'flag', 'Picks a shader feature implementation for a function slot', 'SETTINGS', 0 ),
              ( 'cbuffer', 'cbuffer', 'Constant buffer values', 'PROPERTIES', 1 ),
              ( 'samplerstate', 'samplerstate', 'Sampler state for a texture slot', 'TEXTURE_DATA', 2 ),
              ( 'texture', 'texture', 'Texture for a texture slot', 'TEXTURE', 3 ) ]
KIND_ICON = { k[0]: k[3] for k in CMD_KINDS }

_busy = False

def _mat_of( pg ):
    m = pg.id_data
    return m if isinstance( m, bpy.types.Material ) else None

def _value_edited( self, context ):
    if _busy:
        return
    mat = _mat_of( self )
    if mat is not None:
        sync( mat, source=mat )

def _structure_edited( self, context ):
    if _busy:
        return
    mat = _mat_of( self )
    if mat is not None:
        sync( mat, source=mat )
        for m in siblings( mat ):
            m['mt_needs_rebuild'] = True

def _image_edited( self, context ):
    global _busy
    if _busy:
        return
    mat = _mat_of( self )
    if mat is None:
        return
    if self.image is not None:
        # the image the shader was last built with (mt_images is written by every build)
        built = json.loads( mat.get( 'mt_images', '{}' ) or '{}' )
        _inherit_format( self.image, bpy.data.images.get( built.get( self.slot, '' ) ) )
        _busy = True
        try:
            self.value, note = texture_path( self.image, self.value )
        finally:
            _busy = False
        self.value, note = texture_path( self.image, self.value )
        if note:
            print( '[MT] ' + note )
    _structure_edited( self, context )


class MtMrlFloat( bpy.types.PropertyGroup ):
    value: FloatProperty( name='', precision=4, update=_value_edited )


class MtMrlCmd( bpy.types.PropertyGroup ):
    kind: EnumProperty( name='Type', items=CMD_KINDS, update=_structure_edited )
    slot: StringProperty( name='Name', update=_structure_edited,
                          description='The shader object this command sets: function slot, cbuffer, sampler or texture slot' )
    value: StringProperty( name='Value', update=_structure_edited,
                           description='Flag implementation, sampler state, or the texture path inside the game folder (no extension)' )
    floats: CollectionProperty( type=MtMrlFloat )
    image: PointerProperty( name='Image', type=bpy.types.Image, update=_image_edited,
                            description='The image shown for this texture slot. Picking one sets the path from where the image sits in the game folder' )


class MtMrlEntry( bpy.types.PropertyGroup ):
    name: StringProperty( name='Name', update=_value_edited )
    type: StringProperty( name='Type', update=_structure_edited )
    blendState: StringProperty( name='Blend State', update=_structure_edited )
    depthStencilState: StringProperty( name='Depth Stencil State', update=_value_edited )
    rasterizerState: StringProperty( name='Rasterizer State', update=_value_edited )
    cmdListFlags: StringProperty( name='Cmd List Flags', default='0x0', update=_value_edited )
    matFlags: StringProperty( name='Mat Flags', default='0x0', update=_value_edited )
    hasAnim: BoolProperty( name='Has Anim Data', update=_value_edited )
    animData: StringProperty( name='Anim Data', description='base64, written as is', update=_value_edited )
    cmds: CollectionProperty( type=MtMrlCmd )
    active: IntProperty( name='Active Cmd' )


CLASSES = ( MtMrlFloat, MtMrlCmd, MtMrlEntry )

@bpy.app.handlers.persistent
def _live_sync( scene, depsgraph ):
    if _busy:
        return
    try:
        mats = set()
        for u in depsgraph.updates:
            idb = getattr( u.id, 'original', u.id )
            if isinstance( idb, bpy.types.Material ):
                mats.add( idb )
            elif isinstance( idb, bpy.types.ShaderNodeTree ):
                mats.update( m for m in bpy.data.materials if m.node_tree is not None and m.node_tree == idb )
        seen = set()
        for m in mats:
            if has_entry( m ) and entry_key( m ) not in seen:
                seen.add( entry_key( m ) )
                if any( pull_nodes( x ) for x in siblings( m ) ):
                    sync( m )
    except Exception as e:
        print( '[MT] live sync: %s' % e )

def _poll_active():
    try:
        if not _busy:
            vl = getattr( bpy.context, 'view_layer', None )
            obj = vl.objects.active if vl is not None else None
            mat = obj.active_material if obj is not None else None
            if has_entry( mat ) and any( pull_nodes( x ) for x in siblings( mat ) ):
                sync( mat )
    except Exception:
        pass
    return 0.5

def register():
    for c in CLASSES:
        try:
            bpy.utils.register_class( c )
        except ValueError:
            pass
    bpy.types.Material.mt_entry = PointerProperty( type=MtMrlEntry )
    if _live_sync not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append( _live_sync )
    if not bpy.app.timers.is_registered( _poll_active ):
        bpy.app.timers.register( _poll_active, first_interval=1.0, persistent=True )

def unregister():
    while _live_sync in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove( _live_sync )
    if bpy.app.timers.is_registered( _poll_active ):
        bpy.app.timers.unregister( _poll_active )
    try:
        del bpy.types.Material.mt_entry
    except Exception:
        pass
    for c in reversed( CLASSES ):
        try:
            bpy.utils.unregister_class( c )
        except Exception:
            pass

def _hex( v ):
    try:
        return '0x%x' % ( int( v ) & 0xffffffff )
    except Exception:
        return str( v )

def parse_int( s ):
    return int( str( s ).strip(), 0 ) & 0xffffffff

def has_entry( mat ):
    return mat is not None and 'mt_entry_key' in mat.keys()

def entry_key( mat ):
    return mat.get( 'mt_entry_key', '' )

def fill_entry( mat, info, images=None, source=None ):
    global _busy
    was, _busy = _busy, True
    try:
        e = mat.mt_entry
        old_images = { c.slot: c.image for c in e.cmds if c.kind == 'texture' and c.image is not None }
        e.cmds.clear()
        e.name = info.name or ''
        e.type = info.type or ''
        e.blendState = info.blendState or ''
        e.depthStencilState = info.depthStencilState or ''
        e.rasterizerState = info.rasterizerState or ''
        e.cmdListFlags = _hex( info.cmdListFlags or 0 )
        e.matFlags = _hex( info.matFlags or 0 )
        anim = info.animData
        e.hasAnim = anim is not None
        e.animData = base64.b64encode( bytes( anim ) ).decode( 'ascii' ) if anim is not None else ''
        e.active = 0
        for c in info.cmds:
            cmd = e.cmds.add()
            cmd.kind = c.type
            cmd.slot = c.name or ''
            if c.type == 'cbuffer':
                for x in ( c.data or [] ):
                    cmd.floats.add().value = float( x )
            else:
                cmd.value = c.data if isinstance( c.data, str ) else ''
            if c.type == 'texture':
                img = ( images or {} ).get( c.name ) or old_images.get( c.name )
                if img is not None and ( not cmd.value or img.get( 'mt_tex_path', cmd.value ) == cmd.value ):
                    cmd.image = img
                elif cmd.value:
                    cmd.image = next( ( i for i in bpy.data.images if i.get( 'mt_tex_path' ) == cmd.value ), None )
        if source is not None:
            mat['mt_mrl_path'] = source
        if 'mt_entry_key' not in mat.keys():
            mat['mt_entry_orig'] = e.name
            mat['mt_entry_key'] = '%s|%s' % ( os.path.normcase( os.path.abspath( mat.get( 'mt_mrl_path', '' ) or '.' ) ), e.name )
    finally:
        _busy = was

def info_from_entry( mat ):
    e = mat.mt_entry
    info = imMaterialInfo()
    info.name = e.name; info.type = e.type; info.blendState = e.blendState
    info.depthStencilState = e.depthStencilState; info.rasterizerState = e.rasterizerState
    info.cmdListFlags = parse_int( e.cmdListFlags ); info.matFlags = parse_int( e.matFlags )
    info.animData = base64.b64decode( e.animData ) if e.hasAnim else None
    info.cmds = []
    for c in e.cmds:
        data = [ f.value for f in c.floats ] if c.kind == 'cbuffer' else c.value
        info.cmds.append( imMaterialCmd( c.kind, c.slot, data ) )
    info._from_entry = True
    return info

def entry_images( mat ):
    return { c.slot: c.image for c in mat.mt_entry.cmds if c.kind == 'texture' and c.image is not None }

def copy_entry( src, dst ):
    a, b = src.mt_entry, dst.mt_entry
    for k in ( 'name', 'type', 'blendState', 'depthStencilState', 'rasterizerState', 'cmdListFlags', 'matFlags', 'hasAnim', 'animData' ):
        if getattr( b, k ) != getattr( a, k ):
            setattr( b, k, getattr( a, k ) )
    same = len( a.cmds ) == len( b.cmds ) and all( x.kind == y.kind and x.slot == y.slot and len( x.floats ) == len( y.floats )
                                                   for x, y in zip( a.cmds, b.cmds ) )
    if not same:
        b.cmds.clear()
        for x in a.cmds:
            y = b.cmds.add(); y.kind = x.kind; y.slot = x.slot
            for f in x.floats:
                y.floats.add()
    for x, y in zip( a.cmds, b.cmds ):
        if y.value != x.value: y.value = x.value
        if y.image != x.image: y.image = x.image
        for f, g in zip( x.floats, y.floats ):
            if g.value != f.value: g.value = f.value
    b.active = min( a.active, max( 0, len( b.cmds ) - 1 ) )

def _inherit_format( img, old ):
    if img is not None and old is not None and old is not img and 'mt_tex_format' not in img.keys() and 'mt_tex_format' in old.keys():
        img['mt_tex_format'] = old['mt_tex_format']

def texture_path( img, original ):
    p = img.get( 'mt_tex_path' ) if img is not None else None
    if p:
        return p, None
    native = bpy.context.scene.get( 'mt_game_native_dir', '' )
    fp = bpy.path.abspath( img.filepath_raw or img.filepath ) if img is not None else ''
    if fp and native:
        rel = os.path.relpath( os.path.abspath( fp ), os.path.abspath( native ) )
        if not rel.startswith( '..' ):
            return os.path.splitext( rel )[0].replace( '/', '\\' ), None
    return original, f'image "{getattr( img, "name", "?" )}" is not inside the game folder, the path stays {original or "(empty)"}; type the game path in the texture cmd'

def _nodes( mat ):
    tree = mat.node_tree
    if tree is None:
        return None, None, {}
    sg = tree.nodes.get( 'MT Shader' )
    ug = tree.nodes.get( 'MT UV' )
    g = sg.node_tree if sg is not None and sg.type == 'GROUP' else None
    members = json.loads( g.get( 'mt_members', '{}' ) ) if g is not None else {}
    return sg, ug, members

def socket_map( mat ):
    from .mt_exact import member_sockets
    sg, ug, members = _nodes( mat )
    cmd_of = {}
    for i, c in enumerate( mat.mt_entry.cmds ):
        if c.kind == 'cbuffer':
            cmd_of.setdefault( c.slot, i )
    out = []
    for name, m in members.items():
        ci = cmd_of.get( m['cb'] )
        if ci is None:
            continue
        for label, stype, idx in member_sockets( name, m['size'] ):
            socks = [ n.inputs[label] for n in ( sg, ug ) if n is not None and label in n.inputs ]
            if socks:
                out.append( ( label, socks, ci, [ m['off'] + k for k in idx ] ) )
    return out

def member_socket( mat, cb, index ):
    for label, socks, ci, idx in socket_map( mat ):
        c = mat.mt_entry.cmds[ci]
        if c.slot == cb and index in idx:
            s = next( ( s for s in socks if not s.is_linked ), None )
            return s, idx
    return None, None

def _differs( a, b, eps=1e-6 ):
    return len( a ) != len( b ) or any( abs( x - y ) > eps for x, y in zip( a, b ) )

def pull_nodes( mat ):
    from .mt_exact import _get_socket
    snap = json.loads( mat.get( 'mt_sock_snap', '{}' ) or '{}' )
    cmds = mat.mt_entry.cmds
    out = []
    for label, socks, ci, idx in socket_map( mat ):
        floats = cmds[ci].floats
        for s in socks:
            if s.is_linked:
                continue
            v = _get_socket( s )[:len( idx )]
            ref = snap.get( label )
            if ref is None:
                ref = [ floats[k].value if k < len( floats ) else 0.0 for k in idx ]
            if _differs( v, ref[:len( v )] ):
                out += [ ( 'f', ci, k, x ) for k, x in zip( idx, v ) ]
            break
    tree = mat.node_tree
    tsnap = json.loads( mat.get( 'mt_tex_snap', '{}' ) or '{}' )
    if tree is not None:
        for nd in tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.name.startswith( 'mt_tex:' ) and nd.image is not None:
                slot = nd.name[7:].split( ' ' )[0]
                ci = next( ( i for i, c in enumerate( cmds ) if c.kind == 'texture' and c.slot == slot ), None )
                if ci is None or cmds[ci].image is nd.image:
                    continue
                # only a change made on the node counts, not one the panel made to the entry
                if nd.name not in tsnap or tsnap[nd.name] != nd.image.name:
                    out.append( ( 't', ci, nd.image ) )
    return out

def apply_changes( mat, changes ):
    cmds = mat.mt_entry.cmds
    notes = []
    for ch in changes:
        if ch[0] == 'f':
            _, ci, k, x = ch
            fl = cmds[ci].floats
            while len( fl ) <= k:
                fl.add()
            fl[k].value = x
        else:
            _, ci, img = ch
            c = cmds[ci]
            _inherit_format( img, c.image )
            c.image = img
            c.value, note = texture_path( img, c.value )
            if note:
                notes.append( f'{mat.mt_entry.name} {c.slot}: {note}' )
    return notes

def push_nodes( mat ):
    from .mt_exact import _set_socket, _get_socket
    snap = {}
    cmds = mat.mt_entry.cmds
    for label, socks, ci, idx in socket_map( mat ):
        fl = cmds[ci].floats
        vals = [ fl[k].value if k < len( fl ) else 0.0 for k in idx ]
        for s in socks:
            if not s.is_linked and _differs( _get_socket( s )[:len( vals )], vals ):
                _set_socket( s, vals )
        snap[label] = vals
    _set_if( mat, 'mt_sock_snap', json.dumps( snap ) )
    tree = mat.node_tree
    tsnap = {}
    if tree is not None:
        for nd in tree.nodes:
            if nd.type == 'TEX_IMAGE' and nd.name.startswith( 'mt_tex:' ):
                slot = nd.name[7:].split( ' ' )[0]
                c = next( ( c for c in cmds if c.kind == 'texture' and c.slot == slot ), None )
                if c is not None and c.image is not None and nd.image is not c.image:
                    nd.image = c.image
                if nd.image is not None:
                    tsnap[nd.name] = nd.image.name
    _set_if( mat, 'mt_tex_snap', json.dumps( tsnap ) )

def _set_if( idb, key, value ):
    # every write is a depsgraph update; writing only changes keeps the live sync from looping
    if idb.get( key ) != value:
        idb[key] = value

def siblings( mat ):
    key = entry_key( mat )
    return sorted( ( m for m in bpy.data.materials if has_entry( m ) and entry_key( m ) == key ), key=lambda m: m.name )

def sync( mat=None, source=None ):
    global _busy
    if _busy:
        return []
    _busy = True
    notes = []
    try:
        if mat is not None:
            groups = [ siblings( mat ) ]
        else:
            byk = {}
            for m in bpy.data.materials:
                if has_entry( m ):
                    byk.setdefault( entry_key( m ), [] ).append( m )
            groups = [ sorted( v, key=lambda m: m.name ) for v in byk.values() ]
        for mats in groups:
            if not mats:
                continue
            changes = []
            src = source if source in mats else None
            for m in mats:
                ch = pull_nodes( m )
                if ch and src is None:
                    src = m
                changes += ch
            src = src or mats[0]
            notes += apply_changes( src, changes )
            for m in mats:
                if m is not src:
                    copy_entry( src, m )
            for m in mats:
                push_nodes( m )
    finally:
        _busy = False
    return notes

def entry_yaml( mat ):
    import io
    lib = imMaterialLib()
    info = info_from_entry( mat )
    lib.materials = [ info ]
    from ..mtlib.immaterial import imMaterialTextureInfo
    for c in info.cmds:
        if c.type == 'texture' and c.data and c.data not in [ t.path for t in lib.textures ]:
            t = imMaterialTextureInfo(); t.path = c.data; t.type = 'rTexture'
            lib.textures.append( t )
    f = io.StringIO()
    lib.saveYamlIO( f )
    return f.getvalue()

def apply_yaml( mat, text ):
    lib = imMaterialLib()
    lib.loadYamlString( text )
    if len( lib.materials ) != 1:
        raise ValueError( 'the text has %d materials, expected the one being edited' % len( lib.materials ) )
    info = lib.materials[0]
    if isinstance( info.cmdListFlags, str ): info.cmdListFlags = parse_int( info.cmdListFlags )
    if isinstance( info.matFlags, str ): info.matFlags = parse_int( info.matFlags )
    for c in info.cmds:
        if c.type == 'cbuffer':
            c.data = [ float( x ) for x in ( c.data or [] ) ]
        elif c.data is None:
            c.data = ''
        else:
            c.data = str( c.data )
    fill_entry( mat, info )
    global _busy
    _busy = True
    try:
        for m in siblings( mat ):
            if m is not mat:
                copy_entry( mat, m )
            m['mt_needs_rebuild'] = True
    finally:
        _busy = False
    for m in siblings( mat ):
        push_nodes( m )

def problems( mat ):
    from ..mtlib import mvc3shaderdb, mvc3types
    e = mat.mt_entry
    out = []
    known = mvc3shaderdb.shaderObjectsByName
    def obj( what, n ):
        if n and not n.startswith( '_0x' ) and n not in known:
            out.append( f'{what} "{n}" is not a shader object the game knows' )
    obj( 'blend state', e.blendState ); obj( 'depth stencil state', e.depthStencilState ); obj( 'rasterizer state', e.rasterizerState )
    if e.type and not e.type.startswith( '_0x' ) and e.type not in getattr( mvc3types, 'typeHashByName', {} ):
        out.append( f'type "{e.type}" is not a known type name' )
    for k in ( 'cmdListFlags', 'matFlags' ):
        try:
            parse_int( getattr( e, k ) )
        except Exception:
            out.append( f'{k} "{getattr( e, k )}" is not a number' )
    if e.hasAnim:
        try:
            base64.b64decode( e.animData, validate=True )
        except Exception:
            out.append( 'animData is not valid base64' )
    for i, c in enumerate( e.cmds ):
        obj( f'cmd {i} name', c.slot )
        if not c.slot:
            out.append( f'cmd {i} has no name' )
        if c.kind in ( 'flag', 'samplerstate' ):
            obj( f'cmd {i} ({c.slot}) value', c.value )
    return out


def adopt_legacy( mat ):
    d = json.loads( mat.get( 'mt_mrl', '{}' ) or '{}' )
    src = mat.get( 'mt_mrl_path', '' )
    info = None
    if src and os.path.exists( src ):
        lib = imMaterialLib()
        lib.loadBinaryFile( src )
        info = lib.getMaterialByName( d.get( 'name', '' ) )
    if info is None:
        info = imMaterialInfo()
        info.name = d.get( 'name', '' ); info.type = d.get( 'type', '' ); info.blendState = d.get( 'blendState', '' ) or ''
        info.cmds = [ imMaterialCmd( t, n, v ) for t, n, v in d.get( 'cmds', [] ) ]
        info.cmds += [ imMaterialCmd( 'cbuffer', n, list( v ) ) for n, v in d.get( 'cbuffers', {} ).items() ]
    else:
        flags = { n: v for t, n, v in d.get( 'cmds', [] ) if t == 'flag' }
        for c in info.cmds:
            if c.type == 'flag' and c.name in flags:
                c.data = flags[c.name]
            elif c.type == 'cbuffer' and c.name in d.get( 'cbuffers', {} ):
                v = d['cbuffers'][c.name]
                if len( v ) == len( c.data ):
                    c.data = list( v )
    images = { k: bpy.data.images.get( v ) for k, v in json.loads( mat.get( 'mt_images', '{}' ) or '{}' ).items() }
    fill_entry( mat, info, { k: v for k, v in images.items() if v is not None } )
