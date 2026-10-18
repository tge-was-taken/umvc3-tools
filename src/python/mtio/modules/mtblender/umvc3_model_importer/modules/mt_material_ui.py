import os
import re
import json

import bpy

from . import mt_exact, mt_mrl_props
from ..mtlib import mtshaders


def _game_material( context ):
    obj = getattr( context, 'object', None )
    mat = getattr( context, 'material', None ) or ( obj.active_material if obj is not None else None )
    if mat is not None and ( mt_mrl_props.has_entry( mat ) or 'mt_mrl' in mat.keys() ):
        return mat
    return None

def _logger():
    try:
        from .blender_plugin import plugin
        return plugin.logger
    except Exception:
        return None

def _db( context ):
    native = context.scene.get( 'mt_game_native_dir', '' )
    if not native or not os.path.isdir( native ):
        return None
    try:
        return mtshaders.ShaderDB.get( native )
    except Exception:
        return None


MFX_TYPE = { 'cbuffer': 0, 'texture': 1, 'flag': 2, 'samplerstate': 3,
             'blendState': 4, 'depthStencilState': 5, 'rasterizerState': 6 }
PREFIX = { 'cbuffer': ( 'CB', '$' ), 'texture': ( 't', ), 'flag': ( 'F', ), 'samplerstate': ( 'SS', ),
           'blendState': ( 'BS', ), 'depthStencilState': ( 'DS', ), 'rasterizerState': ( 'RS', ) }

_names = {}

def object_names( context, kind ):
    if kind in _names:
        return _names[kind]
    from ..mtlib import mvc3shaderdb, mvc3types
    if kind == 'type':
        out = sorted( n for n in mvc3types.typeHashByName if n.startswith( 'nDraw::Material' ) )
    else:
        known = mvc3shaderdb.shaderObjectsByName
        db = _db( context )
        if db is not None:
            out = sorted( n for n, i in db.mfx.idx.items() if db.mfx.type[i] == MFX_TYPE[kind] and n in known )
        else:
            out = sorted( n for n in known if n.startswith( PREFIX[kind] ) )
        _names[kind] = out
    return out

_choices = {}

def flag_choices( context, mat, index ):
    e = mat.mt_entry
    cmd = e.cmds[index]
    slot, current = cmd.slot, cmd.value or cmd.slot
    info = mt_mrl_props.info_from_entry( mat )
    key = ( mat.name, index, json.dumps( [ ( c.type, c.name, c.data if isinstance( c.data, str ) else '' ) for c in info.cmds ] ),
            e.type, mat.get( 'mt_ia' ), mat.get( 'mt_receive' ) )
    if key in _choices:
        return _choices[key]
    db = _db( context )
    if db is None:
        return [ current ]
    scene = context.scene
    images = mt_mrl_props.entry_images( mat )
    mfx = db.mfx
    # implementations are named after their slot (FSpecular -> FSpecularMap) or after the
    # current one's family (FToonShader -> FToonShaderHigh); the program lookup decides
    stems = { slot }
    common = os.path.commonprefix( [ slot, current ] )
    if len( common ) >= 5:
        stems.add( common )
    words = re.findall( r'[A-Z][a-z0-9]*', current )
    for k in range( 2, len( words ) + 1 ):
        stem = ''.join( words[:k] )
        if len( stem ) >= 5:
            stems.add( stem )
    names = sorted( n for n, i in mfx.idx.items() if mfx.type[i] == 2 and any( n.startswith( st ) for st in stems ) )
    out = []
    for name in names:
        info.cmds[index].data = name
        try:
            prog, _ = mt_exact.pick_program( db, info, mat.get( 'mt_ia' ), images, scene,
                                             outenc=int( scene.get( 'mt_outenc', 1 ) ), receive=mat.get( 'mt_receive', True ) )
        except RecursionError:
            prog = None
        if prog is not None:
            out.append( name )
    if current not in out:
        out.insert( 0, current )
    _choices[key] = out
    return out

def rebuild_material( context, mat, logger=None ):
    if not mt_mrl_props.has_entry( mat ):
        mt_mrl_props.adopt_legacy( mat )
    mt_mrl_props.sync( mat )
    ok = True
    for m in mt_mrl_props.siblings( mat ):
        if 'mt_ia' not in m.keys():
            continue
        if not mt_exact.rebuild_from_entry( m, context, logger ):
            m['mt_needs_rebuild'] = True
            ok = False
    _choices.clear()
    return ok

def _rebuild_or_report( op, context, mat ):
    if not rebuild_material( context, mat, _logger() ):
        op.report( { 'WARNING' }, 'the game has no shader for this combination; the material keeps its last shader' )
        return False
    return True

TARGETS = [ ( t, t, '' ) for t in ( 'type', 'blendState', 'depthStencilState', 'rasterizerState', 'slot', 'value' ) ]
REBUILD_TARGETS = ( 'type', 'blendState', 'slot', 'value' )

class SUB_OP_MtPickName( bpy.types.Operator ):
    bl_idname = 'sub.mt_pick_name'
    bl_label = 'Pick'
    bl_property = 'value'
    bl_options = { 'UNDO' }

    target: bpy.props.EnumProperty( items=TARGETS )
    index: bpy.props.IntProperty( default=-1 )

    def _items( self, context ):
        mat = _game_material( context )
        kind = self.target
        if mat is not None and self.target in ( 'slot', 'value' ) and 0 <= self.index < len( mat.mt_entry.cmds ):
            kind = mat.mt_entry.cmds[self.index].kind
        names = object_names( context, kind ) or [ '' ]
        SUB_OP_MtPickName._keep = [ ( n, n, '' ) for n in names ]
        return SUB_OP_MtPickName._keep

    value: bpy.props.EnumProperty( items=_items )

    def invoke( self, context, event ):
        context.window_manager.invoke_search_popup( self )
        return { 'RUNNING_MODAL' }

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None or not self.value:
            return { 'CANCELLED' }
        e = mat.mt_entry
        owner = e.cmds[self.index] if self.target in ( 'slot', 'value' ) else e
        setattr( owner, self.target, self.value )
        if self.target in REBUILD_TARGETS:
            _rebuild_or_report( self, context, mat )
        return { 'FINISHED' }


class SUB_OP_SetGameFlag( bpy.types.Operator ):
    bl_idname = 'sub.mt_set_game_flag'
    bl_label = 'Set Flag'
    bl_property = 'value'
    bl_options = { 'UNDO' }

    index: bpy.props.IntProperty( default=-1 )

    def _items( self, context ):
        mat = _game_material( context )
        if mat is None or not mt_mrl_props.has_entry( mat ) or not 0 <= self.index < len( mat.mt_entry.cmds ):
            return [ ( '', '', '' ) ]
        SUB_OP_SetGameFlag._keep = [ ( n, n, '' ) for n in flag_choices( context, mat, self.index ) ]
        return SUB_OP_SetGameFlag._keep

    value: bpy.props.EnumProperty( items=_items )

    def invoke( self, context, event ):
        context.window_manager.invoke_search_popup( self )
        return { 'RUNNING_MODAL' }

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None or not self.value:
            return { 'CANCELLED' }
        cmd = mat.mt_entry.cmds[self.index]
        old = cmd.value
        cmd.value = self.value
        if not rebuild_material( context, mat, _logger() ):
            cmd.value = old
            rebuild_material( context, mat, _logger() )
            self.report( { 'ERROR' }, 'the game has no shader for %s = %s here' % ( cmd.slot, self.value ) )
            return { 'CANCELLED' }
        self.report( { 'INFO' }, '%s = %s (PS %s)' % ( cmd.slot, self.value, mat.get( 'mt_ps' ) ) )
        return { 'FINISHED' }


def _cbuffer_size( cb ):
    for m in bpy.data.materials:
        if mt_mrl_props.has_entry( m ):
            for c in m.mt_entry.cmds:
                if c.kind == 'cbuffer' and c.slot == cb and len( c.floats ):
                    return len( c.floats )
    lay = mtshaders.cbuffer_layouts().get( cb, [] )
    return ( lay[-1][0] // 4 + 1 ) * 4 if lay else 4

class SUB_OP_MtCmdAdd( bpy.types.Operator ):
    bl_idname = 'sub.mt_cmd_add'
    bl_label = 'Add Cmd'
    bl_options = { 'UNDO' }

    kind: bpy.props.EnumProperty( items=[ k[:3] for k in mt_mrl_props.CMD_KINDS ] )
    slot: bpy.props.StringProperty( name='Name' )

    def _items( self, context ):
        SUB_OP_MtCmdAdd._keep = [ ( n, n, '' ) for n in object_names( context, self.kind ) ] or [ ( '', '', '' ) ]
        return SUB_OP_MtCmdAdd._keep

    pick: bpy.props.EnumProperty( items=_items )
    bl_property = 'pick'

    def invoke( self, context, event ):
        context.window_manager.invoke_search_popup( self )
        return { 'RUNNING_MODAL' }

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None:
            return { 'CANCELLED' }
        name = self.slot or self.pick
        e = mat.mt_entry
        mt_mrl_props._busy = True
        try:
            c = e.cmds.add()
            c.kind = self.kind
            c.slot = name
            if self.kind in ( 'flag', 'samplerstate' ):
                c.value = name           # the slot's default implementation / state
            elif self.kind == 'cbuffer':
                for k in range( _cbuffer_size( name ) ):
                    c.floats.add()
            at = min( e.active + 1, len( e.cmds ) - 1 ) if len( e.cmds ) > 1 else 0
            e.cmds.move( len( e.cmds ) - 1, at )
            e.active = at
        finally:
            mt_mrl_props._busy = False
        mt_mrl_props.sync( mat, source=mat )
        _rebuild_or_report( self, context, mat )
        return { 'FINISHED' }


class SUB_OP_MtCmdRemove( bpy.types.Operator ):
    bl_idname = 'sub.mt_cmd_remove'
    bl_label = 'Remove Cmd'
    bl_options = { 'UNDO' }

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None or not len( mat.mt_entry.cmds ):
            return { 'CANCELLED' }
        e = mat.mt_entry
        mt_mrl_props._busy = True
        try:
            e.cmds.remove( e.active )
            e.active = max( 0, min( e.active, len( e.cmds ) - 1 ) )
        finally:
            mt_mrl_props._busy = False
        mt_mrl_props.sync( mat, source=mat )
        _rebuild_or_report( self, context, mat )
        return { 'FINISHED' }


class SUB_OP_MtCmdMove( bpy.types.Operator ):
    bl_idname = 'sub.mt_cmd_move'
    bl_label = 'Move Cmd'
    bl_options = { 'UNDO' }

    direction: bpy.props.IntProperty( default=-1 )

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None:
            return { 'CANCELLED' }
        e = mat.mt_entry
        to = e.active + self.direction
        if not 0 <= to < len( e.cmds ):
            return { 'CANCELLED' }
        mt_mrl_props._busy = True
        try:
            e.cmds.move( e.active, to )
            e.active = to
        finally:
            mt_mrl_props._busy = False
        mt_mrl_props.sync( mat, source=mat )
        return { 'FINISHED' }


class SUB_OP_MtCbufferRows( bpy.types.Operator ):
    bl_idname = 'sub.mt_cbuffer_rows'
    bl_label = 'Cbuffer Rows'
    bl_options = { 'UNDO' }

    index: bpy.props.IntProperty()
    rows: bpy.props.IntProperty( default=1 )

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None:
            return { 'CANCELLED' }
        fl = mat.mt_entry.cmds[self.index].floats
        mt_mrl_props._busy = True
        try:
            for _ in range( 4 * abs( self.rows ) ):
                if self.rows > 0:
                    fl.add()
                elif len( fl ):
                    fl.remove( len( fl ) - 1 )
        finally:
            mt_mrl_props._busy = False
        mt_mrl_props.sync( mat, source=mat )
        _rebuild_or_report( self, context, mat )
        return { 'FINISHED' }


class SUB_OP_RebuildGameMaterial( bpy.types.Operator ):
    bl_idname = 'sub.mt_rebuild_game_material'
    bl_label = 'Rebuild Shader'
    bl_options = { 'UNDO' }

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None:
            return { 'CANCELLED' }
        if not rebuild_material( context, mat, _logger() ):
            self.report( { 'ERROR' }, 'the game has no shader for this combination; the material keeps its last shader' )
            return { 'CANCELLED' }
        return { 'FINISHED' }


def _yaml_text_name( mat ):
    return '%s.mrl.yml' % mat.mt_entry.name

class SUB_OP_MtEditYaml( bpy.types.Operator ):
    bl_idname = 'sub.mt_edit_yaml'
    bl_label = 'Edit as YML'

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None:
            return { 'CANCELLED' }
        if not mt_mrl_props.has_entry( mat ):
            mt_mrl_props.adopt_legacy( mat )
        mt_mrl_props.sync( mat )
        name = _yaml_text_name( mat )
        txt = bpy.data.texts.get( name ) or bpy.data.texts.new( name )
        txt.from_string( mt_mrl_props.entry_yaml( mat ) )
        mat['mt_yaml_text'] = txt.name
        shown = False
        for area in context.screen.areas if context.screen else []:
            if area.type == 'TEXT_EDITOR':
                area.spaces.active.text = txt
                shown = True
                break
        self.report( { 'INFO' }, f'"{txt.name}" is in the Text Editor' + ( '' if shown else ' (open one to see it)' ) + '; press Apply YML when done' )
        return { 'FINISHED' }


class SUB_OP_MtApplyYaml( bpy.types.Operator ):
    bl_idname = 'sub.mt_apply_yaml'
    bl_label = 'Apply YML'
    bl_options = { 'UNDO' }

    @classmethod
    def poll( cls, context ):
        mat = _game_material( context )
        return mat is not None and bpy.data.texts.get( mat.get( 'mt_yaml_text', '' ) ) is not None

    def execute( self, context ):
        mat = _game_material( context )
        txt = bpy.data.texts.get( mat.get( 'mt_yaml_text', '' ) )
        try:
            mt_mrl_props.apply_yaml( mat, txt.as_string() )
        except Exception as e:
            self.report( { 'ERROR' }, f'could not read the YML: {e}' )
            return { 'CANCELLED' }
        for p in mt_mrl_props.problems( mat ):
            self.report( { 'WARNING' }, p )
        _rebuild_or_report( self, context, mat )
        return { 'FINISHED' }


class SUB_OP_MtAdoptEntry( bpy.types.Operator ):
    bl_idname = 'sub.mt_adopt_entry'
    bl_label = 'Read MRL Entry'
    bl_options = { 'UNDO' }

    def execute( self, context ):
        mat = _game_material( context )
        if mat is None:
            return { 'CANCELLED' }
        try:
            mt_mrl_props.adopt_legacy( mat )
            mt_mrl_props.sync( mat )
        except Exception as e:
            self.report( { 'ERROR' }, str( e ) )
            return { 'CANCELLED' }
        return { 'FINISHED' }


class SUB_MT_MtCmdAdd( bpy.types.Menu ):
    bl_idname = 'SUB_MT_mt_cmd_add'
    bl_label = 'Add Cmd'

    def draw( self, context ):
        for k, label, desc, icon, _ in mt_mrl_props.CMD_KINDS:
            self.layout.operator( SUB_OP_MtCmdAdd.bl_idname, text=label, icon=icon ).kind = k


class SUB_UL_MtCmds( bpy.types.UIList ):
    bl_idname = 'SUB_UL_mt_cmds'

    def draw_item( self, context, layout, data, item, icon, active_data, active_propname, index ):
        row = layout.row( align=True )
        row.label( text=item.slot or '(no name)', icon=mt_mrl_props.KIND_ICON.get( item.kind, 'DOT' ) )
        if item.kind == 'cbuffer':
            row.label( text='%d floats' % len( item.floats ) )
        elif item.kind == 'texture':
            row.label( text=( item.value or '(none)' ).split( '\\' )[-1] )
        else:
            row.label( text=item.value if item.value != item.slot else '(default)' )

    def filter_items( self, context, data, propname ):
        items = getattr( data, propname )
        flt = []
        if self.filter_name:
            f = self.filter_name.lower()
            flt = [ self.bitflag_filter_item if ( f in it.slot.lower() or f in it.value.lower() or f in it.kind ) else 0 for it in items ]
        return flt, []

def _pick( row, target, index=-1, icon='VIEWZOOM' ):
    op = row.operator( SUB_OP_MtPickName.bl_idname, text='', icon=icon )
    op.target = target
    op.index = index

def _draw_cbuffer( layout, mat, index, cmd ):
    fl = cmd.floats
    n = len( fl )
    lay = mtshaders.cbuffer_layouts().get( cmd.slot, [] )
    sockets = {}
    for label, socks, ci, idx in mt_mrl_props.socket_map( mat ):
        if ci == index:
            s = next( ( s for s in socks if not s.is_linked ), None )
            if s is not None:
                sockets[idx[0]] = ( s, idx )
    starts = [ off for off, name, packed in lay if off < n ] or [ 0 ]
    names = { off: name for off, name, packed in lay }
    if starts[0] != 0:
        starts.insert( 0, 0 )
    col = layout.column( align=True )
    for k, off in enumerate( starts ):
        end = starts[k + 1] if k + 1 < len( starts ) else n
        name = names.get( off, 'c%d' % off )
        i = off
        while i < end:
            if i in sockets:
                s, idx = sockets[i]
                col.prop( s, 'default_value', text=s.name )
                i = max( idx ) + 1
                continue
            j = min( end, ( i // 4 + 1 ) * 4 )      # to the end of this row of 4
            row = col.row( align=True )
            split = row.split( factor=0.4, align=True )
            split.label( text=name if i == off else '%s +%d' % ( name, i - off ) )
            r = split.row( align=True )
            for q in range( i, j ):
                r.prop( fl[q], 'value', text='' )
            i = j
    row = layout.row( align=True )
    row.label( text='%d floats (%d rows)' % ( n, ( n + 3 ) // 4 ) )
    op = row.operator( SUB_OP_MtCbufferRows.bl_idname, text='', icon='ADD' ); op.index = index; op.rows = 1
    op = row.operator( SUB_OP_MtCbufferRows.bl_idname, text='', icon='REMOVE' ); op.index = index; op.rows = -1

def _draw_cmd( layout, context, mat, index, cmd ):
    box = layout.box()
    row = box.row( align=True )
    row.prop( cmd, 'kind', text='' )
    row.prop( cmd, 'slot', text='' )
    _pick( row, 'slot', index )
    if cmd.kind == 'flag':
        row = box.row( align=True )
        row.prop( cmd, 'value', text='Value' )
        op = row.operator( SUB_OP_SetGameFlag.bl_idname, text='', icon='CHECKMARK' ); op.index = index
        _pick( row, 'value', index )
        box.label( text='check: implementations with a game shader, search: every name', icon='INFO' )
    elif cmd.kind == 'samplerstate':
        row = box.row( align=True )
        row.prop( cmd, 'value', text='State' )
        _pick( row, 'value', index )
    elif cmd.kind == 'texture':
        tree = mat.node_tree
        node = next( ( nd for nd in ( tree.nodes if tree else [] ) if nd.type == 'TEX_IMAGE' and nd.name.startswith( 'mt_tex:' )
                       and nd.name[7:].split( ' ' )[0] == cmd.slot ), None )
        box.template_ID( node if node is not None else cmd, 'image', open='image.open' )
        box.prop( cmd, 'value', text='Path' )
        if node is None:
            box.label( text='sampled inside the shader group (ramp / env map)' if cmd.image else 'no image loaded for this slot', icon='INFO' )
    elif cmd.kind == 'cbuffer':
        _draw_cbuffer( box, mat, index, cmd )

def draw_game_material( layout, context ):
    mat = _game_material( context )
    if mat is None:
        layout.label( text='Not a game shader material' )
        return
    if not mt_mrl_props.has_entry( mat ):
        layout.label( text='Imported before the full MRL entry was kept', icon='ERROR' )
        layout.operator( SUB_OP_MtAdoptEntry.bl_idname, icon='IMPORT' )
        return
    e = mat.mt_entry
    sibs = mt_mrl_props.siblings( mat )
    head = layout.column( align=True )
    head.label( text='PS %s  VS %s  %s' % ( mat.get( 'mt_ps' ), mat.get( 'mt_vs' ), mat.get( 'mt_ia', '' ) ), icon='NODE_MATERIAL' )
    if len( sibs ) > 1:
        head.label( text='shared with %d other vertex layout variant%s' % ( len( sibs ) - 1, 's' if len( sibs ) > 2 else '' ), icon='LINKED' )

    box = layout.box()
    col = box.column( align=True )
    col.prop( e, 'name' )
    for target in ( 'type', 'blendState', 'depthStencilState', 'rasterizerState' ):
        row = col.row( align=True )
        row.prop( e, target )
        _pick( row, target )
    col.separator()
    row = col.row( align=True )
    row.prop( e, 'cmdListFlags', text='cmdListFlags' )
    row.prop( e, 'matFlags', text='matFlags' )
    row = col.row( align=True )
    row.prop( e, 'hasAnim', text='animData' )
    sub = row.row( align=True )
    sub.enabled = e.hasAnim
    sub.prop( e, 'animData', text='' )

    box = layout.box()
    box.label( text='cmds', icon='PRESET' )
    row = box.row()
    row.template_list( SUB_UL_MtCmds.bl_idname, '', e, 'cmds', e, 'active', rows=8 )
    side = row.column( align=True )
    side.menu( SUB_MT_MtCmdAdd.bl_idname, text='', icon='ADD' )
    side.operator( SUB_OP_MtCmdRemove.bl_idname, text='', icon='REMOVE' )
    side.separator()
    side.operator( SUB_OP_MtCmdMove.bl_idname, text='', icon='TRIA_UP' ).direction = -1
    side.operator( SUB_OP_MtCmdMove.bl_idname, text='', icon='TRIA_DOWN' ).direction = 1
    if 0 <= e.active < len( e.cmds ):
        _draw_cmd( box, context, mat, e.active, e.cmds[e.active] )

    probs = mt_mrl_props.problems( mat )
    if probs:
        col = layout.column( align=True )
        col.alert = True
        for p in probs:
            col.label( text=p, icon='ERROR' )
    row = layout.row( align=True )
    row.alert = any( m.get( 'mt_needs_rebuild' ) for m in sibs )
    row.operator( SUB_OP_RebuildGameMaterial.bl_idname, icon='FILE_REFRESH',
                  text='Rebuild Shader (out of date)' if row.alert else 'Rebuild Shader' )
    row = layout.row( align=True )
    row.operator( SUB_OP_MtEditYaml.bl_idname, icon='TEXT' )
    row.operator( SUB_OP_MtApplyYaml.bl_idname, icon='CHECKMARK' )


class SUB_PT_GameMaterial( bpy.types.Panel ):
    bl_idname = 'SUB_PT_GameMaterial'
    bl_label = 'MT Game Material'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll( cls, context ):
        return _game_material( context ) is not None

    def draw( self, context ):
        draw_game_material( self.layout, context )


class SUB_PT_GameMaterialNodes( bpy.types.Panel ):
    bl_idname = 'SUB_PT_GameMaterialNodes'
    bl_label = 'MT Game Material'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'MT Material'

    @classmethod
    def poll( cls, context ):
        sd = getattr( context, 'space_data', None )
        return getattr( sd, 'tree_type', '' ) == 'ShaderNodeTree' and _game_material( context ) is not None

    def draw( self, context ):
        draw_game_material( self.layout, context )


CLASSES = ( SUB_OP_MtPickName, SUB_OP_SetGameFlag, SUB_OP_MtCmdAdd, SUB_OP_MtCmdRemove, SUB_OP_MtCmdMove,
            SUB_OP_MtCbufferRows, SUB_OP_RebuildGameMaterial, SUB_OP_MtEditYaml, SUB_OP_MtApplyYaml,
            SUB_OP_MtAdoptEntry, SUB_MT_MtCmdAdd, SUB_UL_MtCmds, SUB_PT_GameMaterial, SUB_PT_GameMaterialNodes )
