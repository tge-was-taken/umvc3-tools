import copy
from .mtlib import *
from .mtlib.base_importer import *
from . import blender_plugin
from .blender_plugin import *
import bpy
import mathutils
import array
import yaml
import numpy as np

def assertBlenderMode(expectedMode:str):
    try:
        bpy.context.object.mode == expectedMode
    except AttributeError:
        return expectedMode == 'OBJECT'

class BlenderModelImporter(ModelImporterBase):
    def __init__(self):
        super().__init__(blender_plugin.plugin)
        self.armature = None
        self.armatureObj = None

    def setUserProp(self, obj: EditorNodeProxy, key: str, value: Any):
        assertBlenderMode('OBJECT')
        bone = self.armature.bones.get(obj.getName())
        bone[key] = value

    def setInheritanceFlags( self, bone, flags ):
        self.logger.debug(f'setInheritanceFlags({bone},{flags})')

    def normalize( self, vector ):
        length = vector.length
        if length == 0:
            return mathutils.Vector((0, 0, 0))
        return vector / length

    def transformPoint( self, point, matrix ):
        return matrix @ point

    # Progress functions
    def updateProgress( self, what, value, count = 0 ):
        self.logger.debug(f'updateProgress({what},{value},{count})')
        
    def updateSubProgress( self, what, value, count = 0 ):
        self.logger.debug(f'updateSubProgress({what},{value},{count})')

    # Layer functions
    def newLayerFromName( self, name ):
        self.logger.debug(f'newLayerFromName({name})')
        layer = bpy.data.collections.new(name)
        if layer is None: return None
        bpy.context.scene.collection.children.link(layer)
        return BlenderLayerProxy(layer)
        
    def getLayerFromName( self, name ):
        self.logger.debug(f'getLayerFromName({name})')
        layer = bpy.data.collections.get(name)
        if layer is None: return None
        return BlenderLayerProxy(layer)

    # Convert functions
    def convertNclVec3ToPoint3( self, value ):
        return mathutils.Vector((value[0], value[1], value[2]))

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
        
    def convertNclMat43ToMatrix( self, value ):
        matrix = mathutils.Matrix(( 
            self.convertNclVec3ToPoint3( value[0] ), 
            self.convertNclVec3ToPoint3( value[1] ), 
            self.convertNclVec3ToPoint3( value[2] ), 
            self.convertNclVec3ToPoint3( value[3] ) 
        ))
        matrix.transpose()
        return matrix

    # Import functions
    def importPrimitive( self, primitive, envelopeIndex, indexStream, vertexStream ):
        def setUVMap(mesh, faces,array,name):
            if len(array) > 0:
                uvs = []
                for f in faces:
                    for fi in f:
                        uv = array[fi]
                        uvs.append(uv[0])
                        uvs.append(uv[1])
                layer = mesh.uv_layers.new(name=name)
                layer.data.foreach_set("uv", uvs)

        shaderInfo: ShaderObjectInfo = mvc3shaderdb.shaderObjectsByHash[ primitive.vertexShader.getHash() ]
        self.logger.debug( f'shader {shaderInfo.name} ({hex(shaderInfo.hash)})')

        # read vertices
        vertexData = self.decodeVertices( primitive, shaderInfo, 
            vertexStream )

        # read faces
        faceArray = self.decodeFaces( primitive, indexStream )
        
        # build mesh object
        self.logger.debug('creating mesh')
        mesh_name = self.metadata.getPrimitiveName(primitive.id)
        verts = [(v[0], v[1], v[2]) for v in vertexData.vertexArray]
        faces = [(int(f[0]), int(f[1]), int(f[2])) for f in faceArray]
        
        mesh = bpy.data.meshes.new(mesh_name+'.mesh')
        obj = bpy.data.objects.new(mesh_name, mesh)
        obj.data.materials.append(self.editorMaterialArray[primitive.indices.getMaterialIndex()].unwrap())
        self.setPrimitiveCustomAttributes( primitive, shaderInfo, BlenderNodeProxy(obj), envelopeIndex )
        if self.layer != None:
            # add to layer
            self.layer.unwrap().objects.link(obj)
        else:
            # add to scene
            bpy.context.scene.collection.objects.link(obj)

        mesh.from_pydata(verts, [], faces)
        setUVMap(mesh, faces, vertexData.uvPrimaryArray, 'UVPrimary')
        setUVMap(mesh, faces, vertexData.uvSecondaryArray, 'UVSecondary')
        setUVMap(mesh, faces, vertexData.uvExtendArray, 'UVExtend')
        setUVMap(mesh, faces, vertexData.uvUniqueArray, 'UVUnique')

        #if colors is not None:
        #    mesh.vertex_colors.new(name="KF_COLOR")
        #    mesh.vertex_colors["KF_COLOR"].data.foreach_set("color", colors)

        # apply weights
        if len(vertexData.jointArray) > 0 and self.config.importWeights:
            self.importWeights(obj, primitive, vertexData)
        elif len(vertexData.jointArray) == 0:
            self.logger.debug(f'primitive {obj.name} has no vertex weights')
        
        if self.config.importNormals:
            # Adapted from https://github.com/Pherakki/BlenderToolsForGFS/blob/223c88d8bf1eaa7dd1bd01fe18edb2fd668e38fa/src/BlenderIO/Import/ImportModel.py#L241
            # Assign normals
            # Works thanks to this stackexchange answer https://blender.stackexchange.com/a/75957
            # which a few of these comments below are also taken from
            # Do this LAST because it can remove some loops
            mesh.create_normals_split()
            for face in mesh.polygons:
                face.use_smooth = True  # loop normals have effect only if smooth shading ?

            # Set loop normals
            loop_normals = [mathutils.Vector(vertexData.normalArray[loop.vertex_index]) for loop in mesh.loops]
            mesh.loops.foreach_set("normal", [subitem for item in loop_normals for subitem in item])

            mesh.validate(clean_customdata=False)  # important to not remove loop normals here!
            mesh.update()

            clnors = array.array('f', [0.0] * (len(mesh.loops) * 3))
            mesh.loops.foreach_get("normal", clnors)

            mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
            # This line is pretty smart (came from the stackoverflow answer)
            # 1. Creates three copies of the same iterator over clnors
            # 2. Splats those three copies into a zip
            # 3. Each iteration of the zip now calls the iterator three times, meaning that three consecutive elements
            #    are popped off
            # 4. Turn that triplet into a tuple
            # In this way, a flat list is iterated over in triplets without wasting memory by copying the whole list
            mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))

            mesh.use_auto_smooth = True
        
        # parent to group
        if primitive.indices.getGroupId() in self.editorGroupLookup:
            group = self.editorGroupLookup[primitive.indices.getGroupId()].unwrap()
            obj.parent = group
        
        mesh.validate(verbose=True, clean_customdata=False)
        
        mesh.update()
        mesh.update()

    def importWeights( self, editorObj, primitive, vertexData: DecodedVertexData ):
        self.logger.info( 'importing mesh weights' )

        bpy.context.view_layer.objects.active = self.armatureObj
        bpy.ops.object.mode_set(mode='EDIT')
        
        weightData = self.preprocessWeights( primitive, vertexData )

        # add used bones to skin modifier
        vertexGroupMap = dict()
        for i, editorBone in enumerate( weightData.usedBones ):
            vertexGroupMap[i] = editorObj.vertex_groups.new(name=editorBone.getName())

        # set vertex weights
        for j in range( 0, primitive.vertexCount ):
            newMaxVtxJointArray = weightData.jointArray[j]
            newMaxVtxWeightArray = weightData.weightArray[j]
            assert len( newMaxVtxJointArray ) > 0 
            assert len( newMaxVtxWeightArray ) > 0
            assert len( newMaxVtxJointArray ) == len( newMaxVtxWeightArray )
            for k in range( 0, len( newMaxVtxJointArray )):
                vertexGroup = vertexGroupMap[newMaxVtxJointArray[k]]
                vertexGroup.add([j], newMaxVtxWeightArray[k], 'REPLACE')

        modifier = editorObj.modifiers.new('Armature', 'ARMATURE')
        modifier.object = self.armatureObj

        bpy.ops.object.mode_set(mode='OBJECT')

    # Create functions
    def createArray( self ):
        return BlenderArrayProxy()
          
    def createPoint3( self, x, y, z ):
        return mathutils.Vector((x, y, z))
    
    def createPoint2( self, x, y ):
        return mathutils.Vector((x, y))
        
    def createTexture( self, filename ):
        return bpy.data.images.load(filepath=filename)

    def createDummy( self, name, pos ):
        blendGroup = bpy.data.objects.new(name, None)
        #blendGroup.location = group.boundingSphere[0], group.boundingSphere[1], group.boundingSphere[2]
        return BlenderNodeProxy(blendGroup)

    def importSkeleton( self ):
        # Create armature
        self.armature = bpy.data.armatures.new('Armature')
        self.armatureObj = bpy.data.objects.new('Armature', self.armature)
        if self.layer != None:
            self.layer.unwrap().objects.link(self.armatureObj)
        else:
            bpy.context.scene.collection.objects.link(self.armatureObj)

        bpy.context.view_layer.objects.active = self.armatureObj
        
        # Bones can only be created in edit mode
        bpy.ops.object.mode_set(mode='EDIT',toggle=False)

        super().importSkeleton()

        def findNextBone(bone):
            nextBone = None
            for otherBone in self.editorBoneArray:
                otherBone = otherBone.unwrap()
                if otherBone.parent is not None and otherBone.parent == bone:
                    nextBone = otherBone
                    break     
            return nextBone

        for bone in self.editorBoneArray:
            bone = bone.unwrap()
            nextBone = findNextBone(bone)
            tailDir = (bone.tail - bone.head).normalized()
            assert(tailDir.magnitude > 0)
            length = 0 # whichever length you prefer, they're formally 0 length but blender deletes those automagically 
            if nextBone is not None:
                length = (nextBone.head - bone.head).length
            length = max(length, 0.5)
            bone.tail = bone.head + (tailDir * length)

        # Ensure we're in object mode because after this we'll be adding
        # attributes to the object mode bone data
        bpy.ops.object.mode_set(mode='OBJECT',toggle=False)

    def createBone( self, joint: rModelJoint, name, tfm, parentBone ):
        assertBlenderMode('EDIT')
        
        def vec_roll_to_mat3(vec, roll):
            #port of the updated C function from armature.c
            #https://developer.blender.org/T39470
            #note that C accesses columns first, so all matrix indices are swapped compared to the C version

            nor = vec.normalized()
            THETA_THRESHOLD_NEGY = 1.0e-9
            THETA_THRESHOLD_NEGY_CLOSE = 1.0e-5

            #create a 3x3 matrix
            bMatrix = mathutils.Matrix().to_3x3()

            theta = 1.0 + nor[1]

            if (theta > THETA_THRESHOLD_NEGY_CLOSE) or ((nor[0] or nor[2]) and theta > THETA_THRESHOLD_NEGY):

                bMatrix[1][0] = -nor[0]
                bMatrix[0][1] = nor[0]
                bMatrix[1][1] = nor[1]
                bMatrix[2][1] = nor[2]
                bMatrix[1][2] = -nor[2]
                if theta > THETA_THRESHOLD_NEGY_CLOSE:
                    #If nor is far enough from -Y, apply the general case.
                    bMatrix[0][0] = 1 - nor[0] * nor[0] / theta
                    bMatrix[2][2] = 1 - nor[2] * nor[2] / theta
                    bMatrix[0][2] = bMatrix[2][0] = -nor[0] * nor[2] / theta

                else:
                    #If nor is too close to -Y, apply the special case.
                    theta = nor[0] * nor[0] + nor[2] * nor[2]
                    bMatrix[0][0] = (nor[0] + nor[2]) * (nor[0] - nor[2]) / -theta
                    bMatrix[2][2] = -bMatrix[0][0]
                    bMatrix[0][2] = bMatrix[2][0] = 2.0 * nor[0] * nor[2] / theta

            else:
                #If nor is -Y, simple symmetry by Z axis.
                bMatrix = mathutils.Matrix().to_3x3()
                bMatrix[0][0] = bMatrix[1][1] = -1.0

            #Make Roll matrix
            rMatrix = mathutils.Matrix.Rotation(roll, 3, nor)

            #Combine and output result
            mat = rMatrix @ bMatrix
            return mat

        def mat3_to_vec_roll(mat):
            """
            Code from
            https://blender.stackexchange.com/a/38337
            https://blender.stackexchange.com/a/90240
            """
            vec = mat.col[1]
            vecmat = vec_roll_to_mat3(mat.col[1], 0)
            try:
                vecmatinv = vecmat.inverted()
            except:
                vecmatinv = vecmat
            rollmat = vecmatinv @ mat
            roll = math.atan2(rollmat[0][2], rollmat[2][2])
            return vec, roll

        self.logger.debug(f'createBone({name},{tfm},{parentBone})')
        matrix = self.convertNclMat44ToMatrix(tfm)
        # This matrix fixes the direction of the tail
        tailRotationMatrix = mathutils.Matrix(((0.0, 1.0, 0.0, 0.0),
            (-1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0)))
        matrix = matrix @ tailRotationMatrix

        # Copied from https://github.com/Pherakki/BlenderToolsForGFS/blob/223c88d8bf1eaa7dd1bd01fe18edb2fd668e38fa/src/BlenderIO/Import/Utils/BoneConstruction.py#L6
        bpy_bone = self.armature.edit_bones.new(name)
        
        tail, roll = mat3_to_vec_roll(matrix.to_3x3())
        pos_vector = matrix.to_translation()
        bpy_bone.head = pos_vector
        bpy_bone.tail = pos_vector + tail
        bpy_bone.roll = roll
        
        # Head/tail/roll sets correctly in Blender 2.83, but not in
        # Blender 3.4?!
        # So here we'll just manually set the matrix because... I have no idea
        # why Blender sets the matrix_local incorrectly later
        # Can't just set the matrix because that prevents the head/tail being set,
        # so set the head/tail first and then align the roll by setting the matrix
        # I feel *extremely* uncomfortable about the fact that two different
        # roll values are required in two versions of Blender to get the same
        # matrix - need to find out why.
        
        bpy_bone.matrix = matrix
        if parentBone:
            bpy_bone.parent = parentBone.unwrap()

        return BlenderEditBoneProxy(bpy_bone, tfm)

    def setSkeletonAttributes( self, rootBone ):
        assertBlenderMode('OBJECT')

        if self.config.lukasCompat and rootBone is not None:
            self.setUserProp( rootBone, 'LMTBone', 255 )

        for i, joint in enumerate( self.model.joints ):
            editorBone = self.editorBoneArray[ i ]
            # for compat. with Lukas' Mt Framework animation importing script  
            self.setInheritanceFlags( editorBone, (1,2,3,4,5,6) )
            self.setUserProp( editorBone, 'LMTBone', joint.id )        
            self.setJointCustomAttributes( joint, editorBone )
    
    # Material functions
    def convertMaterial( self, material: imMaterialInfo, materialName: str ):
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

                # Swap the red and alpha channels of the normal map
                # normal_map_pixels = np.array(normal_map.pixels)
                # normal_map_pixels = normal_map_pixels.reshape(-1, 4)
                # normal_map_pixels[:, 0], normal_map_pixels[:, 3] = normal_map_pixels[:, 3], normal_map_pixels[:, 0]
                # normal_map_pixels = normal_map_pixels.flatten()
                # normal_map.pixels = normal_map_pixels

                normal_map_tex.image = normal_map
                bpy_material.node_tree.links.new(normal_map_tex.outputs["Color"], normal_map_node.inputs["Color"])
                bpy_material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])

            # normal_map = self.loadTextureSlot(material, "tNormalMap")
            # if normal_map:
            #     normal_map_node = nodes.new("ShaderNodeSeparateRGB")
            #     normal_map_tex = nodes.new("ShaderNodeTexImage")
            #     normal_map_tex.image = normal_map
            #     bpy_material.node_tree.links.new(normal_map_tex.outputs["Color"], normal_map_node.inputs["Image"])
                
            #     # separate the RGB and Alpha channels
            #     normal_map_r = nodes.new("ShaderNodeSeparateRGB")
            #     normal_map_a = nodes.new("ShaderNodeSeparateRGB")
            #     bpy_material.node_tree.links.new(normal_map_node.outputs["Image"], normal_map_r.inputs["Image"])
            #     bpy_material.node_tree.links.new(normal_map_node.outputs["Image"], normal_map_a.inputs["Image"])
            #     normal_map_r_out = normal_map_r.outputs["R"]
            #     normal_map_a_out = normal_map_a.outputs["A"]
                
            #     # swap the RGB and Alpha channels
            #     normal_map_rgb = nodes.new("ShaderNodeCombineRGB")
            #     normal_map_rgb.inputs["R"].default_value = normal_map_a_out.default_value
            #     normal_map_rgb.inputs["G"].default_value = normal_map_r_out.default_value
            #     normal_map_rgb.inputs["B"].default_value = normal_map_r_out.default_value
            #     bpy_material.node_tree.links.new(normal_map_r_out, normal_map_rgb.inputs["G"])
            #     bpy_material.node_tree.links.new(normal_map_a_out, normal_map_rgb.inputs["R"])
                
            #     # connect the swapped RGB and Alpha channels to the normal map node
            #     normal_map_node = nodes.new("ShaderNodeNormalMap")
            #     bpy_material.node_tree.links.new(normal_map_rgb.outputs["Image"], normal_map_node.inputs["Color"])
            #     bpy_material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])

        return BlenderMaterialProxy(bpy_material)

    # Attribute functions
    def createGroupCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        return BlenderCustomAttributeSetProxy(obj.unwrap())

    def createMaterialCustomAttribute( self, obj )-> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        return BlenderCustomAttributeSetProxy(obj.unwrap())

    def createPrimitiveCustomAttribute( self, obj ) -> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        return BlenderCustomAttributeSetProxy(obj.unwrap())

    def createJointCustomAttribute( self, obj ) -> EditorCustomAttributeSetProxy:
        assertBlenderMode('OBJECT')
        bone = self.armature.bones.get(obj.getName())
        return BlenderCustomAttributeSetProxy(bone)

    def importModel(self, modFilePath):
        super().importModel(modFilePath)