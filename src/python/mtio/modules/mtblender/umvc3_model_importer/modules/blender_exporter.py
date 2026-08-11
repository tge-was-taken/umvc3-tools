from typing import Dict
from ..mtlib import *
from ..mtlib.ncl import *
from ..mtlib.base_editor import *
from ..mtlib.base_exporter import *
from .blender_plugin import *
import bpy
import mathutils

def progressCallback( what, i, count ):
    pass

def assertBlenderMode(expectedMode:str):
    try:
        bpy.context.object.mode == expectedMode
    except AttributeError:
        return expectedMode == 'OBJECT'

class BlenderModelExporter(ModelExporterBase):
    def __init__(self) -> None:
        super().__init__(plugin)
        self.progressCallback = progressCallback
        self._armatureObj = None

    def getObjects( self ):
        temp = list(bpy.data.objects)
        objects = []
        for o in temp:
            if not o in self.processedNodes:
                objects.append( BlenderNodeProxy( o ) )
        return objects

    #Based on the above method to ensure that we get joints as they are not included in bpy.data.objects.
    def getObjectBones( self ):
        temp = list(bpy.data.objects)
        objects = []
        for o in temp:
            if not o in self.processedNodes:
                #Ensures we only get the bones from the Armature selected and adds all of them.
                if o.type == 'ARMATURE' and o.name == bpy.context.selected_objects[0].name:
                    # for ChildNode in enumerate(bpy.data.armatures[o.name].bones):
                    for ChildNode in bpy.data.armatures[o.name].bones:
                        #o.node = ChildNode
                        objects.append( BlenderNodeProxy( ChildNode ) )


        return objects

    # def getObjectBones( self ):
    #     temp = list(bpy.data.objects)
    #     objects = []
    #     for o in temp:
    #         if not o in self.processedNodes:
    #             if o.type == 'ARMATURE' and o.name == bpy.context.selected_objects[0].name:
    #                 for ChildNode in enumerate(bpy.data.armatures[o.name].bones):
    #                     objects.append( BlenderNodeProxy( ChildNode ) )


    #     return objects


    def updateProgress( self, what, value, count = 0 ):
        self.logger.debug( f'updateProgress({what},{value},{count})')
        
    def updateSubProgress( self, what, value, count = 0 ):
        self.logger.debug( f'updateSubProgress({what},{value},{count})')

    def _attribSetOrNone( self, ctx, markers ):
        # Hand back a proxy only if the datablock actually carries MT attributes. A mesh
        # built from scratch in Blender has none, and the exporter has fallback paths for
        # that case which never ran while this always returned a proxy.
        if ctx is None:
            return None
        proxy = BlenderCustomAttributeSetProxy(ctx)
        for marker in markers:
            if proxy.hasCustomAttribute(marker):
                return proxy
        return None

    def getEditorGroupCustomAttributeData( self, node: EditorNodeProxy  ) -> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        if node is None: return None
        return self._attribSetOrNone(node.unwrap(), ('id', 'bsphere'))

    def getEditorPrimitiveCustomAttributeData( self, node: EditorNodeProxy  ) -> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        if node is None: return None
        return self._attribSetOrNone(node.unwrap(), ('shaderName', 'flags', 'groupId'))

    def getEditorJointCustomAttributeData( self, node: EditorNodeProxy  ) -> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        if node is None: return None
        return self._attribSetOrNone(node.unwrap(), ('id', 'symmetryName'))

    def getEditorMaterialCustomAttributeData( self, material ) -> EditorCustomAttributeSetProxy:
        if material is None:
            return None
        if hasattr(material, 'unwrap'):
            material = material.unwrap()
        return self._attribSetOrNone(material, ('type', 'matFlags'))

    def convertPoint3ToNclVec3( self, v ) -> NclVec3:
        return NclVec3((v[0], v[1], v[2]))

    def convertPoint3ToNclVec3UV( self, v ) -> NclVec3:
        return NclVec3((v[0], 1 - v[1], v[2]))
        
    def convertPoint3ToNclVec4( self, v, w ) -> NclVec3:
        return NclVec4((v[0], v[1], v[2], w))
    
    def convertMatrix3ToNclMat43( self, v ) -> NclMat43:
        return nclCreateMat43((self.convertPoint3ToNclVec3(v[0]), 
                               self.convertPoint3ToNclVec3(v[1]), 
                               self.convertPoint3ToNclVec3(v[2]), 
                               self.convertPoint3ToNclVec3(v[3])))
        
    def convertMatrix3ToNclMat44( self, v ):
        return nclCreateMat44((self.convertPoint3ToNclVec4(v[0], 0), 
                               self.convertPoint3ToNclVec4(v[1], 0), 
                               self.convertPoint3ToNclVec4(v[2], 0), 
                               self.convertPoint3ToNclVec4(v[3], 1)))

    def nclVec4Multiply(self, vec4, scale_tuple):
        return [vec4[i] * scale_tuple[i] for i in range(4)]

    def convertNclVec4ToPoint4( self, value ):
        return mathutils.Vector((value[0], value[1], value[2], value[3]))    

    def convertPoint4ToNclVec4(self, point4):
        # Ensure we can handle both mathutils.Vector and simple tuples/lists.
        if hasattr(point4, "to_tuple"):
            return list(point4.to_tuple(4))
        else:
            # Fallback.
            return [float(point4[0]), float(point4[1]), float(point4[2]), float(point4[3])]

    def convertMatrixToNclMat44(self, matrix):
        """Reverse of convertNclMat44ToMatrix()"""
        mtx = matrix.copy()
        mtx.transpose()  # Blender is column-major, NCL is row-major

        ncl_mat = [
            self.convertPoint4ToNclVec4(mtx[0]),
            self.convertPoint4ToNclVec4(mtx[1]),
            self.convertPoint4ToNclVec4(mtx[2]),
            self.convertPoint4ToNclVec4(mtx[3]),
        ]
        return ncl_mat

    def convertNclVec4ToPoint4( self, value ):
        return mathutils.Vector((value[0], value[1], value[2], value[3]))
        
    def convertNclMat44ToMatrix( self, value ):
        matrix = mathutils.Matrix((
            self.convertNclVec4ToPoint4( value[0] ),
            self.convertNclVec4ToPoint4( value[1] ),
            self.convertNclVec4ToPoint4( value[2] ),
            self.convertNclVec4ToPoint4( value[3] )
        ))
        matrix.transpose()
        return matrix

    # ------------------------------------------------------------------
    # materials
    # ------------------------------------------------------------------

    # the importer creates these by name, in this order
    UV_LAYER_SLOTS = ( 'UVPrimary', 'UVSecondary', 'UVUnique', 'UVExtend' )

    def getMaterialName( self, material ):
        # Blender uniquifies datablock names, so a second copy of char_body comes back
        # as char_body.001 and stops matching anything in the mrl. Strip the suffix.
        if material is None:
            return 'default_material'
        name = material.name if hasattr( material, 'name' ) else material.getName()
        if len( name ) > 4 and name[-4] == '.' and name[-3:].isdigit():
            name = name[:-4]
        return name

    def _getMaterialTexturePath( self, material, inputName, default ):
        # walk back from a Principled BSDF input to whatever image feeds it
        try:
            if material is None or not material.use_nodes:
                return self.getTextureMapResourcePathInternal( default )
            bsdf = None
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    bsdf = node
                    break
            if bsdf is None or inputName not in bsdf.inputs:
                return self.getTextureMapResourcePathInternal( default )

            visited = set()
            stack = [ l.from_node for l in bsdf.inputs[inputName].links ]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add( node )
                if node.type == 'TEX_IMAGE' and node.image is not None:
                    return self.getTextureMapResourcePathOrDefault( node.image.filepath, default, None )
                for inp in node.inputs:
                    for link in inp.links:
                        stack.append( link.from_node )
        except Exception as e:
            self.logger.debug( 'texture lookup failed for ' + str( inputName ) + ': ' + str( e ) )
        return self.getTextureMapResourcePathInternal( default )

    def processMaterial( self, material ):
        if material is None:
            return
        if material in self.materialCache:
            return
        self.materialCache[material] = True

        name = self.getMaterialName( material )
        self.logger.info( f'processing material: {name}' )

        # whatever the importer recorded off the original mrl entry
        preserved = self.getMaterialCustomAttributeData( material )

        # DEPRECATED: mrl generation. Everything below built the mrl entry for this
        # material. The attribute read above is kept because it costs nothing and
        # documents what the importer preserved.
        return

        # if not self.config.exportGenerateMrl or self.mrl is None:
        # return

        # # an existing mrl already holds the real thing, don't clobber it
        # for existing in self.mrl.materials:
        # if existing.name == name:
        # self.applyMaterialCustomAttributeData( existing, preserved )
        # return

        # preset = self.config.exportMaterialPreset
        # if preserved.type != None:
        # # prefer the material type the model actually shipped with
        # candidate = preserved.type.replace( 'nDraw::', '' )
        # for template in imMaterialInfo.TEMPLATE_MATERIALS:
        # if template.replace( ' ', '' ).endswith( candidate ):
        # preset = template
        # break

        # materialInstance = imMaterialInfo.createFromTemplate(
        # preset,
        # name,
        # normalMap=self._getMaterialTexturePath( material, 'Normal', imMaterialInfo.DEFAULT_NORMAL_MAP ),
        # albedoMap=self._getMaterialTexturePath( material, 'Base Color', imMaterialInfo.DEFAULT_ALBEDO_MAP ),
        # specularMap=self._getMaterialTexturePath( material, 'Specular IOR Level', imMaterialInfo.DEFAULT_SPECULAR_MAP ),
        # )

        # self.applyMaterialCustomAttributeData( materialInstance, preserved )
        # self.copyUsedDefaultTexturesToOutput( materialInstance )
        # self.mrl.materials.append( materialInstance )

    # ------------------------------------------------------------------
    # meshes
    # ------------------------------------------------------------------

    def _getArmatureObj( self ):
        # bones export in armature space, so meshes have to as well or moving the
        # armature in object mode silently shifts the mesh away from the skeleton
        if getattr( self, '_armatureObj', None ) is not None:
            return self._armatureObj
        selected = bpy.context.selected_objects
        for o in selected:
            if o.type == 'ARMATURE':
                self._armatureObj = o
                return o
        for o in bpy.data.objects:
            if o.type == 'ARMATURE':
                self._armatureObj = o
                return o
        return None

    def _getSceneMtx( self, obj ):
        arm = self._getArmatureObj()
        if arm is None:
            return obj.matrix_world
        return arm.matrix_world.inverted_safe() @ obj.matrix_world

    def _evaluateMesh( self, obj ):
        # Snapshot with modifiers applied, minus the armature. Leaving the armature on
        # bakes the current pose into the vertices and the mod comes out permanently posed.
        suppressed = []
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.show_viewport:
                mod.show_viewport = False
                suppressed.append( mod )

        depsgraph = bpy.context.evaluated_depsgraph_get()
        evalObj = obj.evaluated_get( depsgraph )
        mesh = evalObj.to_mesh( preserve_all_data_layers=True, depsgraph=depsgraph )

        def cleanup():
            try:
                evalObj.to_mesh_clear()
            except Exception:
                pass
            for m in suppressed:
                m.show_viewport = True

        return mesh, cleanup

    def _getLoopNormals( self, mesh ):
        # per loop normals indexed by loop index. 4.1 dropped calc_normals_split in
        # favour of the corner_normals collection, so handle both.
        if not self.config.exportNormals:
            return None
        try:
            if hasattr( mesh, 'calc_normals_split' ):
                mesh.calc_normals_split()
                return [ tuple( l.normal ) for l in mesh.loops ]
            if hasattr( mesh, 'corner_normals' ):
                return [ tuple( n.vector ) for n in mesh.corner_normals ]
        except Exception as e:
            self.logger.debug( 'split normals unavailable, using vertex normals: ' + str( e ) )
        return None

    def _getColorLayer( self, mesh ):
        # written by the importer for the stage formats that carry baked colour.
        # POINT domain so it indexes by vertex; CORNER is handled too in case the
        # user made their own.
        for name in ( 'VertexColor', 'Color', 'Col' ):
            layer = mesh.color_attributes.get( name ) if hasattr( mesh, 'color_attributes' ) else None
            if layer is not None:
                return layer
        if hasattr( mesh, 'color_attributes' ) and len( mesh.color_attributes ) > 0:
            return mesh.color_attributes[0]
        return None

    def _getUvLayers( self, mesh ):
        layers = dict()
        for slot in self.UV_LAYER_SLOTS:
            layer = mesh.uv_layers.get( slot )
            if layer is not None:
                layers[slot] = layer.data
        if 'UVPrimary' not in layers and len( mesh.uv_layers ) > 0:
            # mesh authored in Blender, whatever the first channel is becomes primary
            layers['UVPrimary'] = mesh.uv_layers[0].data
        return layers

    def _getBoneIndexByVertexGroup( self, obj ):
        # vertex group index -> joint index. Groups that don't name a bone in the
        # skeleton get dropped rather than silently mapped onto the root.
        mapping = dict()
        if self.jointIdxByName is None:
            return mapping
        for i, vg in enumerate( obj.vertex_groups ):
            if vg.name in self.jointIdxByName:
                mapping[i] = self.jointIdxByName[vg.name]
        return mapping

    def _getFallbackWeight( self ):
        # characters need a weight on every vertex, mirrors the max exporter
        weight = imVertexWeight()
        if len( self.model.joints ) == 0:
            return weight
        rootIndex = 0 if len( self.model.joints ) < 3 else 2
        weight.weights.append( 1.0 )
        weight.indices.append( rootIndex )
        return weight

    def _buildVertexWeight( self, vertex, boneIndexByGroup ):
        weight = imVertexWeight()
        for g in vertex.groups:
            if g.group not in boneIndexByGroup:
                continue
            if g.weight < 0.001:
                continue
            weight.weights.append( g.weight )
            weight.indices.append( boneIndexByGroup[g.group] )
        if len( weight.weights ) == 0:
            return self._getFallbackWeight()
        return weight

    def processMesh( self, editorNode: EditorNodeProxy ):
        obj = editorNode.unwrap()
        self.logger.info( f'processing mesh: {obj.name}' )

        attribs = self.getPrimitiveCustomAttributeData( editorNode )
        mesh, cleanup = self._evaluateMesh( obj )

        try:
            mesh.calc_loop_triangles()
            triangles = mesh.loop_triangles
            if len( triangles ) == 0:
                self.logger.warning( f'mesh {obj.name} has no faces, skipping' )
                return

            loopNormals = self._getLoopNormals( mesh )
            uvLayers = self._getUvLayers( mesh )
            colorLayer = self._getColorLayer( mesh )

            worldMtx = self._getSceneMtx( obj )
            normalMtx = worldMtx.to_3x3().inverted_safe().transposed()

            boneIndexByGroup = self._getBoneIndexByVertexGroup( obj )
            hasSkin = self.config.exportWeights and len( boneIndexByGroup ) > 0
            needsWeights = len( self.model.joints ) > 0

            if self.config.exportWeights and needsWeights and len( obj.vertex_groups ) > 0 and not hasSkin:
                raise RuntimeError(
                    'Mesh "' + obj.name + '" is weighted to vertex groups that do not match any bone '
                    'in the exported skeleton. If you are exporting a custom skeleton, clear the '
                    'reference model, since it overrides the skeleton in the scene.' )

            materials = [ slot.material for slot in obj.material_slots ]

            primWorkingSets: Dict[int, imPrimitiveWorkingSet] = dict()
            triCount = len( triangles )

            for i, tri in enumerate( triangles ):
                if self.plugin.updateUI(): self.updateSubProgress( 'Processing faces', i, triCount )

                matId = tri.material_index
                material = materials[matId] if matId < len( materials ) else None
                if material is not None:
                    self.processMaterial( material )

                if matId not in primWorkingSets:
                    prim = imPrimitive( obj.name, self.getMaterialName( material ) )
                    primWorkingSets[matId] = imPrimitiveWorkingSet( prim, [prim] )

                workingSet = primWorkingSets[matId]
                if len( workingSet.current.positions ) + 3 > self.MAX_INDEX_COUNT:
                    # split before overflowing the index buffer rather than after
                    prim = imPrimitive( obj.name, self.getMaterialName( material ) )
                    workingSet.current = prim
                    workingSet.primitives.append( prim )

                tempMesh = workingSet.current

                for j in range( 3 ):
                    vertIdx = tri.vertices[j]
                    loopIdx = tri.loops[j]
                    vertex = mesh.vertices[vertIdx]

                    # positions go out in blender world space, transformMtx does the
                    # z up to y up turn and the scale, the reverse of the importer
                    pos = self.convertPoint3ToNclVec4( worldMtx @ vertex.co, 1 )
                    pos = self.transformMtx * pos
                    tempMesh.positions.append( NclVec3( pos[0], pos[1], pos[2] ) )

                    rawNrm = loopNormals[loopIdx] if loopNormals is not None else tuple( vertex.normal )
                    nrm = normalMtx @ mathutils.Vector( rawNrm )
                    # w must be 0 for direction vectors or the translation leaks in
                    nrm = self.convertPoint3ToNclVec4( nrm, 0 )
                    nrm = nclNormalize( self.transformMtxNormal * nrm )
                    tempMesh.normals.append( NclVec3( nrm[0], nrm[1], nrm[2] ) )

                    for slot, data in uvLayers.items():
                        uv = data[loopIdx].uv
                        converted = self.convertPoint3ToNclVec3UV( ( uv[0], uv[1], 0 ) )
                        if slot == 'UVPrimary':     tempMesh.uvPrimary.append( converted )
                        elif slot == 'UVSecondary': tempMesh.uvSecondary.append( converted )
                        elif slot == 'UVUnique':    tempMesh.uvUnique.append( converted )
                        elif slot == 'UVExtend':    tempMesh.uvExtend.append( converted )

                    if colorLayer is not None:
                        try:
                            idx = loopIdx if colorLayer.domain == 'CORNER' else vertIdx
                            c = colorLayer.data[idx].color
                            tempMesh.colors.append( ( c[0], c[1], c[2], c[3] ) )
                        except Exception:
                            tempMesh.colors.append( ( 127.0/255.0, 127.0/255.0, 127.0/255.0, 1.0 ) )

                    if hasSkin:
                        tempMesh.weights.append( self._buildVertexWeight( vertex, boneIndexByGroup ) )
                    elif needsWeights:
                        tempMesh.weights.append( self._getFallbackWeight() )

            self.generatePrimitives( editorNode, attribs, primWorkingSets )
        finally:
            cleanup()