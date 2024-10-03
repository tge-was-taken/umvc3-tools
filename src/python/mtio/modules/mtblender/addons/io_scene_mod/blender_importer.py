__package__ = 'modules.mtblender.addons.io_scene_mod'

from ....mtlib import *

class BlenderArrayProxy(EditorArrayProxy):
    def __init__(self) -> None:
        self.array = []

    def append(self,value):
        self.array.append(value)

    def __len__(self):
        return len(self.array)

    def unwrap(self):
        return self.array

    def __getitem__(self, key):
        return self.array[key]

    def __setitem__(self, key, value):
        self.array[key] = value

class BlenderCustomAttributeProxy(EditorCustomAttributeProxy):
    # yet another guid wasted
    # not sure if necessary
    SUFFIX = 'f4515ae7-57e2-4ca2-8346-27cf689efe7a'

    def __init__(self, attribs) -> None:
        super().__init__(attribs)

    def getCustomAttribute(self, name: str) -> Any:
        return getattr(self._ctx, name+self.SUFFIX)

    def setCustomAttribute(self, name: str, value: Any):
        return setattr(self._ctx, name+self.SUFFIX, value)

class BlenderLayerProxy(EditorLayerProxy):
    def __init__(self, layer) -> None:
        self.layer = layer

    def addNode(self,obj):
        self.layer.objects.link(obj)

class BlenderModelImporter(ModelImporterBase):
    def __init__(self):
        super().__init__()

    # Misc functions
    def timeStamp():
        return bpy.context.scene.frame_start

    def disableSceneRedraw():
        bpy.ops.view3d.zoom(center=False, delta=-1)

    def enableSceneRedraw():
        bpy.ops.view3d.zoom(center=False, delta=1)

    def isDebugEnv():
        return True # TODO

    def getIndexBase( self ):
        return 0

    def setUserProp(self, obj, key, value):
        obj[key+BlenderCustomAttributeProxy.SUFFIX] = value

    def setInheritanceFlags( self, bone, flags ):
        pass

    def updateUI( self ):
        pass # TODO

    def normalize( self, value ):
        pass # TODO

    # Progress functions
    def updateProgress( self, what, value, count = 0 ):
        pass

    def updateSubProgress( self, what, value, count = 0 ):
        pass

    # Layer functions
    def newLayerFromName(name):
        return BlenderLayerProxy(bpy.data.scenes[0].view_layers.new(name))

    def getLayerFromName(name):
        return BlenderLayerProxy(bpy.data.scenes[0].view_layers.get(name))

    # Convert functions
    def convertNclVec3ToPoint3( self, nclVec3 ):
        return bpy.mathutils.Vector((nclVec3[0], nclVec3[1], nclVec3[2]))
        
    def convertNclMat44ToMatrix( self, nclMtx ):
        return bpy.mathutils.Matrix( self.convertNclVec3ToPoint3( nclMtx[0] ), 
                           self.convertNclVec3ToPoint3( nclMtx[1] ), 
                           self.convertNclVec3ToPoint3( nclMtx[2] ), 
                           self.convertNclVec3ToPoint3( nclMtx[3] ) )
        
    def convertNclMat43ToMatrix( self, nclMtx ):
        return bpy.mathutils.Matrix( self.convertNclVec3ToPoint3( nclMtx[0] ), 
                           self.convertNclVec3ToPoint3( nclMtx[1] ), 
                           self.convertNclVec3ToPoint3( nclMtx[2] ), 
                           self.convertNclVec3ToPoint3( nclMtx[3] ) )

    # Import functions
    def importPrimitive( self, primitive, envelopeIndex, indexStream, vertexStream ):
        shaderInfo: ShaderObjectInfo = mvc3shaderdb.shaderObjectsByHash[ primitive.vertexShader.getHash() ]
        self.log.debug( f'shader {shaderInfo.name} ({hex(shaderInfo.hash)})')

        # read vertices
        vertexData = self.decodeVertices( primitive, shaderInfo, 
            vertexStream )

        # read faces
        faceArray = self.decodeFaces( primitive, indexStream )
        
        # build mesh object
        self.log.debug('creating mesh')
        has_uvs = len(vertexData.uvPrimaryArray) > 0
        mesh_name = self.metadata.getPrimitiveName(primitive.id)
        verts = [(v[0], v[1], v[2]) for v in vertexData.vertexArray]
        faces = [(f[0], f[1], f[2]) for f in faceArray]
        
        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        
        if has_uvs:
            # TODO other uv maps
            uv_layer = mesh.uv_layers.new(name='UVMap')
            for i, uv in enumerate(vertexData.uvPrimaryArray):
                uv_layer.data[i].uv = (uv[0], uv[1])
        
        if self.config.importNormals:
            normals = [(n[0], n[1], n[2]) for n in vertexData.normalArray]
            mesh.create_normals_split()
            mesh.normals_split_custom_set(normals)
            mesh.use_auto_smooth = True
        
        obj = bpy.data.objects.new(mesh_name, mesh)
        obj.data.materials.append(self.editorMaterialArray[primitive.indices.getMaterialIndex()])
        
        # parent to group
        if primitive.indices.getGroupId() in self.editorGroupLookup:
            group = self.editorGroupLookup[primitive.indices.getGroupId()]
            obj.parent = group
        
        # apply weights
        if len(vertexData.jointArray) > 0 and self.config.importWeights:
            self.importWeights(obj, primitive, vertexData)
        elif len(vertexData.jointArray) == 0:
            self.log.debug(f'primitive {obj.name} has no vertex weights')
        
        if self.layer != None:
            # add to layer
            self.layer.addNode( mesh )
        else:
            # add to scene
            bpy.context.scene.collection.objects.link(obj)

    def importWeights( self, editorObj, primitive, vertexData: DecodedVertexData ):
        self.log.info( 'importing mesh weights' )
        
        weightData = self.preprocessWeights( primitive, vertexData )
        
        # add used bones to skin modifier
        for i, maxBone in enumerate( weightData.usedBones ):
            editorObj.vertex_groups.new(name=maxBone.name)

        # set vertex weights
        blenderVertexGroups = list(editorObj.vertex_groups)
        for j in range( 0, primitive.vertexCount ):
            newMaxVtxJointArray = weightData.jointArray[j]
            newMaxVtxWeightArray = weightData.weightArray[j]
            assert len( newMaxVtxJointArray ) > 0 
            assert len( newMaxVtxWeightArray ) > 0
            for k in range( 0, len( newMaxVtxJointArray )):
                blenderVertexGroups[newMaxVtxJointArray[k]].add((j,), newMaxVtxWeightArray[k], 'REPLACE')

    # Create functions
    def createArray( self ):
        return BlenderArrayProxy()
    
    def createPoint3( self, x, y, z ):
        return bpy.mathutils.Vector((x, y, z))
    
    def createPoint2( self, x, y ):
        return bpy.mathutils.Vector((x, y, 0))

    def createTexture( self, filename ):
        return bpy.data.images.load(filepath=filename)

    def createDummy( self, name, pos ):
        maxGroup = bpy.data.objects.new(name, None)
        #maxGroup.location = group.boundingSphere[0], group.boundingSphere[1], group.boundingSphere[2]
        return maxGroup

    def createBone( self, name, tfm, parentBone ):
        armature = bpy.data.armatures.new(name + 'Armature')
        obj = bpy.data.objects.new(name, armature)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bone = armature.edit_bones.new(name)
        bone.head = tfm.translation
        bone.tail = tfm.translation + 0.01 * tfm.to_scale_packing().normalized()
        bone.align_roll(tfm.to_3x3().to_quaternion().to_euler().z)
        bone.width = 0.001
        bone.length = 0.001
        bone.use_deform = False
        bone.show_wire = True
        bone.show_axes = False
        bone.color = (1, 1, 0)
        if parentBone:
            bone.parent = parentBone
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.layer:
            self.layer.objects.link(obj)
        return obj

    # Material functions
    def convertMaterial( self, material: imMaterialInfo, materialName: str ):
        self.convertMaterial_PhysicalMaterial( material, materialName )

    def convertMaterial_PhysicalMaterial( self, material: imMaterialInfo, materialName: str ):
        bpy_material = bpy.data.materials.new(name=materialName)
        bpy_material.use_nodes = True

        if material is not None:
            nodes = bpy_material.node_tree.nodes
            principled_bsdf = nodes.get("Principled BSDF") or nodes.new("ShaderNodeBsdfPrincipled")

            albedo_map = self.loadTextureSlot(material, "tAlbedoMap")
            if albedo_map:
                albedo_tex = nodes.new("ShaderNodeTexImage")
                albedo_tex.image = albedo_map
                bpy_material.node_tree.links.new(albedo_tex.outputs["Color"], principled_bsdf.inputs["Base Color"])

            specular_map = self.loadTextureSlot(material, "tSpecularMap")
            if specular_map:
                metalness_tex = nodes.new("ShaderNodeTexImage")
                metalness_tex.image = specular_map
                bpy_material.node_tree.links.new(metalness_tex.outputs["Color"], principled_bsdf.inputs["Metallic"])

            normal_map = self.loadTextureSlot(material, "tNormalMap")
            if normal_map:
                normal_map_node = nodes.new("ShaderNodeNormalMap")
                normal_map_tex = nodes.new("ShaderNodeTexImage")
                normal_map_tex.image = normal_map
                bpy_material.node_tree.links.new(normal_map_tex.outputs["Color"], normal_map_node.inputs["Color"])
                bpy_material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])

        return bpy_material

    def convertMaterial_PBRSpecGloss( self, material: imMaterialInfo, materialName: str ):
        editorMaterial = bpy.data.materials.new(materialName)
        editorMaterial.use_nodes = True
        principled = editorMaterial.node_tree.nodes.get("Principled BSDF")
        if not principled:
            principled = editorMaterial.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
            principled.location = 0,0
            editorMaterial.node_tree.links.new(principled.outputs[0], editorMaterial.node_tree.nodes['Material Output'].inputs[0])

        if material != None:
            principled.inputs[0].default_value = (1,1,1,1)
            principled.inputs[4].default_value = 1
            #load albedo map
            albedo_tex = self.loadTextureSlot( material, 'tAlbedoMap' )
            if albedo_tex:
                principled.inputs[0].default_value = (0,0,0,1)
                albedo_tex_node = editorMaterial.node_tree.nodes.new("ShaderNodeTexImage")
                albedo_tex_node.image = bpy.data.images.load(albedo_tex)
                editorMaterial.node_tree.links.new(albedo_tex_node.outputs[0], principled.inputs[0])
            
            #load specular map
            spec_tex = self.loadTextureSlot( material, 'tSpecularMap' )
            if spec_tex:
                principled.inputs[4].default_value = 0
                spec_tex_node = editorMaterial.node_tree.nodes.new("ShaderNodeTexImage")
                spec_tex_node.image = bpy.data.images.load(spec_tex)
                editorMaterial.node_tree.links.new(spec_tex_node.outputs[0], principled.inputs[4])

            #load normal map
            norm_tex = self.loadTextureSlot( material, 'tNormalMap' )
            if norm_tex:
                norm_tex_node = editorMaterial.node_tree.nodes.new("ShaderNodeTexImage")
                norm_tex_node.image = bpy.data.images.load(norm_tex)
                norm_map_node = editorMaterial.node_tree.nodes.new("ShaderNodeNormalMap")
                editorMaterial.node_tree.links.new(norm_tex_node.outputs[0], norm_map_node.inputs[1])
                editorMaterial.node_tree.links.new(norm_map_node.outputs[0], principled.inputs[17])

        return editorMaterial

    # Attribute functions
    def createGroupCustomAttribute( self, obj )-> EditorCustomAttributeProxy:
        return BlenderCustomAttributeProxy(obj)

    def createMaterialCustomAttribute( self, obj )-> EditorCustomAttributeProxy:
        return BlenderCustomAttributeProxy(obj)

    def createPrimitiveCustomAttribute( self, obj ) -> EditorCustomAttributeProxy:
        return BlenderCustomAttributeProxy(obj)

    def createJointCustomAttribute( self, obj ) -> EditorCustomAttributeProxy:
        return BlenderCustomAttributeProxy(obj)