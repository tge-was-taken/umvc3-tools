import copy
from ..mtlib import *
from ..mtlib.base_importer import *
from . import blender_plugin
from .blender_plugin import *
from . import mt_shading
from . import mt_exact
import os
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
    # Stored inverted (1 - occlusion) so anything without the attribute, a new mesh or
    # verts joined in from elsewhere, reads 0 and stays fully lit instead of going black.
    OCCLUSION_ATTRIBUTE = 'mt_ao_darken'

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

    # Import functions
    def importPrimitive( self, primitive, envelopeIndex, indexStream, vertexStream, context ):
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
        # collected so the outline pass knows exactly what this import made, rather
        # than guessing from the selection
        if not hasattr( self, 'importedMeshObjects' ):
            self.importedMeshObjects = []
        self.importedMeshObjects.append( obj )
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

        # Stage formats (IANonSkinBC/BCA/TBNL) carry baked per vertex colour and alpha.
        # Store it as a POINT domain byte colour so the exporter can read it straight
        # back per vertex, no corner mapping needed.
        if len( vertexData.colorArray ) == len( verts ):
            try:
                layer = mesh.color_attributes.new( name='VertexColor', type='BYTE_COLOR', domain='POINT' )
                for i, c in enumerate( vertexData.colorArray ):
                    layer.data[i].color = ( c[0], c[1], c[2], c[3] )
            except Exception as e:
                self.logger.debug( 'could not create vertex colour layer: ' + str( e ) )

        # Per vertex occlusion. The character shaders multiply the lit diffuse by it, so
        # it goes on the mesh as a float attribute the MT Character group reads, and the
        # exporter writes it back instead of a flat 1.
        occ = vertexData.occlusionArray or []
        if len( occ ) == len( verts ):
            try:
                attr = mesh.attributes.new( name=self.OCCLUSION_ATTRIBUTE, type='FLOAT', domain='POINT' )
                attr.data.foreach_set( 'value', [ 1.0 - float( v ) for v in occ ] )
            except Exception as e:
                self.logger.debug( 'could not create occlusion attribute: ' + str( e ) )
        
        tan = vertexData.tangentArray or []
        if len( tan ) == len( verts ):
            try:
                attr = mesh.attributes.new( name='mt_tangent', type='FLOAT_VECTOR', domain='POINT' )
                attr.data.foreach_set( 'vector', [ c for t in tan for c in t[:3] ] )
                attr = mesh.attributes.new( name='mt_tangent_sign', type='FLOAT', domain='POINT' )
                attr.data.foreach_set( 'value', [ float( t[3] ) for t in tan ] )
            except Exception as e:
                self.logger.debug( 'could not create tangent attributes: ' + str( e ) )

        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties

        # apply weights
        if len(vertexData.jointArray) > 0 and mip.import_weights:
            self.importWeights(obj, primitive, vertexData)
        elif len(vertexData.jointArray) == 0:
            self.logger.debug(f'primitive {obj.name} has no vertex weights')
        

        if mip.import_normals:
            # Adapted from https://github.com/Pherakki/BlenderToolsForGFS/blob/223c88d8bf1eaa7dd1bd01fe18edb2fd668e38fa/src/BlenderIO/Import/ImportModel.py#L241
            # Assign normals
            # Works thanks to this stackexchange answer https://blender.stackexchange.com/a/75957
            # which a few of these comments below are also taken from
            # Do this LAST because it can remove some loops
            # create_normals_split and use_auto_smooth were removed in 4.1, custom
            # normals work without them there
            if hasattr( mesh, 'create_normals_split' ):
                mesh.create_normals_split()
            for face in mesh.polygons:
                face.use_smooth = True  # loop normals have effect only if smooth shading ?

            # the game's outline vertex shader pushes each vertex along its own stored normal;
            # keep it per vertex for the outline hull (Blender's normals follow the winding,
            # which the outline-only bridge strips don't keep consistent)
            try:
                gn = mesh.attributes.new( name='mt_game_normal', type='FLOAT_VECTOR', domain='POINT' )
                gn.data.foreach_set( 'vector', [ c for n in vertexData.normalArray for c in tuple( n )[:3] ] )
            except Exception:
                pass
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

            if hasattr( mesh, 'use_auto_smooth' ):
                mesh.use_auto_smooth = True

        # The game's tangent frame, expressed in Blender's own (MikkTSpace) frame per face
        # corner. Both frames follow the surface when the mesh deforms, so the shader can
        # rebuild the game tangent from these coefficients in any pose (exact in the bind pose).
        self._storeTangentFrame( mesh )
        
        obj['mt_group'] = int( primitive.indices.getGroupId() )
        # IASkinBridge primitives are only ever drawn by the outline pass
        obj['mt_bridge'] = bool( shaderInfo.name.startswith( 'IASkinBridge' ) )
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
        # share one image per file, materials reuse the same textures a lot
        return bpy.data.images.load(filepath=filename, check_existing=True)

    def createDummy( self, name, pos ):
        blendGroup = bpy.data.objects.new(name, None)
        #blendGroup.location = group.boundingSphere[0], group.boundingSphere[1], group.boundingSphere[2]
        return BlenderNodeProxy(blendGroup)

    def parentGroupToArmature( self, editorGroup ):
        if self.armatureObj is None:
            return
        obj = editorGroup.unwrap()
        obj.parent = self.armatureObj
        obj.matrix_parent_inverse = self.armatureObj.matrix_world.inverted()

    def importSkeleton( self, context ):
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

        super().importSkeleton(context)

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

    def createBone( self, joint: rModelJoint, name, tfm, parentBone, context ):
        assertBlenderMode('EDIT')
        mip:UMVC3ModelImportProperties = context.scene.sub_scene_properties
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

        if mip.inherit_scale == False:
            bpy_bone.inherit_scale = "NONE"    

        return BlenderEditBoneProxy(bpy_bone, tfm)

    def setSkeletonAttributes( self, rootBone ):
        assertBlenderMode('OBJECT')

        # if self.config.lukasCompat and rootBone is not None:
        #     self.setUserProp( rootBone, 'LMTBone', 255 )

        for i, joint in enumerate( self.model.joints ):
            editorBone = self.editorBoneArray[ i ]
            # for compat. with Lukas' Mt Framework animation importing script  
            self.setInheritanceFlags( editorBone, (1,2,3,4,5,6) )
            self.setUserProp( editorBone, 'LMTBone', joint.id )        
            self.setJointCustomAttributes( joint, editorBone )
    
    # Material functions
    def _attachUVChannel( self, bpy_material, nodes, tex_node, material, slot ):
        '''The mrl says which uv channel feeds each texture slot. Without an explicit
        UV Map node blender falls back to whichever layer happens to be active, which
        is wrong for anything not using the primary channel.'''
        try:
            channel = material.getUVChannelForSlot( slot )
        except Exception:
            channel = 'UVPrimary'
        uv = nodes.new( 'ShaderNodeUVMap' )
        uv.uv_map = channel
        uv.location.x = tex_node.location.x - 200
        uv.location.y = tex_node.location.y
        uv.label = slot + ' -> ' + channel
        bpy_material.node_tree.links.new( uv.outputs['UV'], tex_node.inputs['Vector'] )

        try:
            anim = material.getUVAnimation()
        except Exception:
            anim = None
        if anim is not None and anim['channel'] == channel and any( anim['direction'] ):
            self._attachUVScroll( bpy_material, nodes, uv, tex_node, anim )
        return uv

    UV_SCROLL_REFERENCE_RATE = 240.0    # Dante's gauntlet, the one we have seen moving
    UV_SCROLL_BASE_SPEED     = 0.004    # uv units per frame at that rate

    def _attachUVScroll( self, bpy_material, nodes, uv_node, tex_node, anim ):
        try:
            links = bpy_material.node_tree.links
            mapping = nodes.new( 'ShaderNodeMapping' )
            mapping.location.x = uv_node.location.x + 100
            mapping.location.y = uv_node.location.y - 120
            mapping.label = 'UV scroll'
            links.new( uv_node.outputs['UV'], mapping.inputs['Vector'] )
            links.new( mapping.outputs['Vector'], tex_node.inputs['Vector'] )

            rate = anim['rate'] if anim['rate'] else self.UV_SCROLL_REFERENCE_RATE
            speed = self.UV_SCROLL_BASE_SPEED * ( self.UV_SCROLL_REFERENCE_RATE / float( rate ) )

            u, v = anim['direction']
            bpy_material['UVScrollSpeed'] = speed
            bpy_material['UVScrollU']     = float( u )
            bpy_material['UVScrollV']     = float( v )
            bpy_material['UVScrollRate']  = int( anim['rate'] )

            # one driver per axis, so a material can scroll diagonally if it wants to
            for axis, prop in ( ( 0, 'UVScrollU' ), ( 1, 'UVScrollV' ) ):
                drv = mapping.inputs['Location'].driver_add( 'default_value', axis ).driver
                drv.type = 'SCRIPTED'
                a = drv.variables.new(); a.name = 'spd'
                a.targets[0].id_type = 'MATERIAL'
                a.targets[0].id = bpy_material
                a.targets[0].data_path = '["UVScrollSpeed"]'
                b = drv.variables.new(); b.name = 'dir'
                b.targets[0].id_type = 'MATERIAL'
                b.targets[0].id = bpy_material
                b.targets[0].data_path = '["%s"]' % prop
                drv.expression = 'frame * spd * dir'

            self.logger.info(
                f"uv scroll on {bpy_material.name}: channel {anim['channel']}, "
                f"vector ({u:+.0f}, {v:+.0f}), rate {anim['rate']}" )
        except Exception as e:
            self.logger.debug( 'could not set up uv scroll: ' + str( e ) )

    MT_GROUP_NAME = 'MT Character'

    MT_GROUP_INPUTS = (
        # ( name, type, default, min, max )
        ( 'Albedo',            'NodeSocketColor', ( 0.8, 0.8, 0.8, 1.0 ), None, None ),
        ( 'Alpha',             'NodeSocketFloat', 1.0, 0.0, 1.0 ),
        ( 'Normal',            'NodeSocketVector', ( 0.0, 0.0, 1.0 ), None, None ),
        ( 'Specular Mask',     'NodeSocketFloat', 1.0, 0.0, 1.0 ),
        ( 'Toon Ramp',         'NodeSocketColor', ( 1.0, 1.0, 1.0, 1.0 ), None, None ),
        ( 'Toon Rev Ramp',     'NodeSocketColor', ( 0.0, 0.0, 0.0, 1.0 ), None, None ),
        ( 'HalfLambert Bias',  'NodeSocketFloat', 0.5, 0.0, 1.0 ),
        ( 'HalfLambert Scale', 'NodeSocketFloat', 0.5, 0.0, 2.0 ),
        ( 'Shadow Floor',      'NodeSocketFloat', 0.2, 0.0, 1.0 ),
        ( 'Diffuse Tint',      'NodeSocketColor', ( 1.0, 1.0, 1.0, 1.0 ), None, None ),
        ( 'Specular Tint',     'NodeSocketColor', ( 1.0, 1.0, 1.0, 1.0 ), None, None ),
        ( 'Specular Power',    'NodeSocketFloat', 10.0, 1.0, 256.0 ),
        ( 'Rim Light',         'NodeSocketFloat', 0.0, 0.0, 4.0 ),
        # driven by the mrl feature flags, so a flag switches behaviour instead of
        # only appearing as text in the reference panel
        ( 'Use Toon Ramp',     'NodeSocketFloat', 1.0, 0.0, 1.0 ),
        ( 'Fresnel',           'NodeSocketFloat', 0.0, 0.0, 4.0 ),
        ( 'Specular Amount',   'NodeSocketFloat', 1.0, 0.0, 4.0 ),
        ( 'Rim Colour',        'NodeSocketColor', ( 1.0, 1.0, 1.0, 1.0 ), None, None ),
    )

    def _groupInterfaceNew( self, group, name, socket_type, in_out ):
        """4.0 replaced group.inputs/outputs with group.interface."""
        if hasattr( group, 'interface' ):
            return group.interface.new_socket( name=name, in_out=in_out,
                                               socket_type=socket_type )
        coll = group.inputs if in_out == 'INPUT' else group.outputs
        return coll.new( socket_type, name )

    def _getOrBuildMTGroup( self ):
        existing = bpy.data.node_groups.get( self.MT_GROUP_NAME )
        if existing is not None:
            # never clobber a group the user may have edited
            return existing

        group = bpy.data.node_groups.new( self.MT_GROUP_NAME, 'ShaderNodeTree' )
        n = group.nodes

        gin = n.new( 'NodeGroupInput' )
        gin.location = ( -1200, 0 )
        gout = n.new( 'NodeGroupOutput' )
        gout.location = ( 900, 0 )

        for name, stype, default, lo, hi in self.MT_GROUP_INPUTS:
            sock = self._groupInterfaceNew( group, name, stype, 'INPUT' )
            try:
                sock.default_value = default
                if lo is not None: sock.min_value = lo
                if hi is not None: sock.max_value = hi
            except Exception:
                pass
        self._groupInterfaceNew( group, 'Shader', 'NodeSocketShader', 'OUTPUT' )

        L = group.links
        I = gin.outputs

        # --- the lambert term -------------------------------------------------
        # A plain diffuse lobe converted to a scalar. This is what MT feeds into its
        # ramp lookup; there is no way to get a raw NdotL in Eevee's node graph.
        diff = n.new( 'ShaderNodeBsdfDiffuse' )
        diff.location = ( -1000, -200 )
        diff.inputs['Color'].default_value = ( 1, 1, 1, 1 )
        L.new( I['Normal'], diff.inputs['Normal'] )

        s2rgb = n.new( 'ShaderNodeShaderToRGB' )
        s2rgb.location = ( -820, -200 )
        L.new( diff.outputs['BSDF'], s2rgb.inputs['Shader'] )

        # half lambert: NdotL * scale + bias, mapped onto the ramp's u axis
        hl_end = n.new( 'ShaderNodeMath' )
        hl_end.operation = 'ADD'
        hl_end.location = ( -820, -420 )
        hl_end.label = 'bias + scale'
        L.new( I['HalfLambert Bias'], hl_end.inputs[0] )
        L.new( I['HalfLambert Scale'], hl_end.inputs[1] )

        lookup = n.new( 'ShaderNodeMapRange' )
        lookup.location = ( -620, -200 )
        lookup.label = 'half lambert'
        lookup.clamp = True
        L.new( s2rgb.outputs['Color'], lookup.inputs['Value'] )
        L.new( I['HalfLambert Bias'], lookup.inputs['To Min'] )
        L.new( hl_end.outputs[0], lookup.inputs['To Max'] )

        # --- ramp, lifted off black ------------------------------------------
        # The ramps are flat black below u = 0.5 and the game never lets a surface go
        # fully dark, so the floor keeps albedo readable in shadow.
        floor = n.new( 'ShaderNodeMapRange' )
        floor.location = ( -400, -200 )
        floor.label = 'shadow floor'
        floor.clamp = True
        L.new( I['Toon Ramp'], floor.inputs['Value'] )
        L.new( I['Shadow Floor'], floor.inputs['To Min'] )
        floor.inputs['To Max'].default_value = 1.0

        # --- diffuse ----------------------------------------------------------
        tinted = n.new( 'ShaderNodeMixRGB' )
        tinted.blend_type = 'MULTIPLY'
        tinted.location = ( -200, 100 )
        tinted.label = 'albedo x tint'
        tinted.inputs['Fac'].default_value = 1.0
        L.new( I['Albedo'], tinted.inputs['Color1'] )
        L.new( I['Diffuse Tint'], tinted.inputs['Color2'] )

        # With Use Toon Ramp at 0 the lookup is bypassed and the plain lambert term is
        # used instead, so the same group covers a non toon material.
        lighting = n.new( 'ShaderNodeMixRGB' )
        lighting.blend_type = 'MIX'
        lighting.location = ( -200, -200 )
        lighting.label = 'lambert or ramp'
        L.new( I['Use Toon Ramp'], lighting.inputs['Fac'] )
        L.new( s2rgb.outputs['Color'], lighting.inputs['Color1'] )
        L.new( floor.outputs['Result'], lighting.inputs['Color2'] )

        shaded = n.new( 'ShaderNodeMixRGB' )
        shaded.blend_type = 'MULTIPLY'
        shaded.location = ( 0, 0 )
        shaded.label = 'x lighting'
        shaded.inputs['Fac'].default_value = 1.0
        L.new( tinted.outputs['Color'], shaded.inputs['Color1'] )
        L.new( lighting.outputs['Color'], shaded.inputs['Color2'] )

        # --- rim light --------------------------------------------------------
        # FCalcRimLight is set on most character materials. A fresnel term is the
        # closest thing blender has and it reads correctly at silhouette edges.
        fres = n.new( 'ShaderNodeFresnel' )
        fres.location = ( -400, -600 )
        fres.inputs['IOR'].default_value = 1.45
        L.new( I['Normal'], fres.inputs['Normal'] )

        rim_total = n.new( 'ShaderNodeMath' )
        rim_total.operation = 'ADD'
        rim_total.location = ( -380, -700 )
        rim_total.label = 'rim + fresnel'
        L.new( I['Rim Light'], rim_total.inputs[0] )
        L.new( I['Fresnel'], rim_total.inputs[1] )

        rim_amt = n.new( 'ShaderNodeMath' )
        rim_amt.operation = 'MULTIPLY'
        rim_amt.location = ( -200, -600 )
        rim_amt.label = 'rim strength'
        L.new( fres.outputs['Fac'], rim_amt.inputs[0] )
        L.new( rim_total.outputs[0], rim_amt.inputs[1] )

        rim_col = n.new( 'ShaderNodeMixRGB' )
        rim_col.blend_type = 'MULTIPLY'
        rim_col.location = ( 0, -600 )
        rim_col.inputs['Fac'].default_value = 1.0
        L.new( I['Rim Colour'], rim_col.inputs['Color1'] )
        rim_col.inputs['Color2'].default_value = ( 1, 1, 1, 1 )

        rim_scaled = n.new( 'ShaderNodeMixRGB' )
        rim_scaled.blend_type = 'MULTIPLY'
        rim_scaled.location = ( 180, -600 )
        rim_scaled.label = 'rim'
        L.new( rim_amt.outputs[0], rim_scaled.inputs['Fac'] )
        rim_scaled.inputs['Color1'].default_value = ( 0, 0, 0, 1 )
        L.new( rim_col.outputs['Color'], rim_scaled.inputs['Color2'] )

        # --- specular ---------------------------------------------------------
        # FSpecularMaskToon: a glossy lobe gated by the specular map, tinted by
        # CBMaterial[4..6]. Power comes in as an exponent, blender wants roughness.
        rough = n.new( 'ShaderNodeMath' )
        rough.operation = 'DIVIDE'
        rough.location = ( -820, -800 )
        rough.inputs[0].default_value = 2.0
        pow_plus = n.new( 'ShaderNodeMath' )
        pow_plus.operation = 'ADD'
        pow_plus.location = ( -1000, -800 )
        L.new( I['Specular Power'], pow_plus.inputs[0] )
        pow_plus.inputs[1].default_value = 2.0
        L.new( pow_plus.outputs[0], rough.inputs[1] )

        rough_sqrt = n.new( 'ShaderNodeMath' )
        rough_sqrt.operation = 'SQRT'
        rough_sqrt.location = ( -620, -800 )
        rough_sqrt.label = 'exponent to roughness'
        L.new( rough.outputs[0], rough_sqrt.inputs[0] )

        gloss = n.new( 'ShaderNodeBsdfGlossy' )
        gloss.location = ( -400, -820 )
        L.new( I['Specular Tint'], gloss.inputs['Color'] )
        L.new( rough_sqrt.outputs[0], gloss.inputs['Roughness'] )
        L.new( I['Normal'], gloss.inputs['Normal'] )

        gloss_rgb = n.new( 'ShaderNodeShaderToRGB' )
        gloss_rgb.location = ( -200, -820 )
        L.new( gloss.outputs['BSDF'], gloss_rgb.inputs['Shader'] )

        spec_masked = n.new( 'ShaderNodeMixRGB' )
        spec_masked.blend_type = 'MULTIPLY'
        spec_masked.location = ( 0, -820 )
        spec_masked.label = 'x specular mask'
        spec_masked.inputs['Fac'].default_value = 1.0
        L.new( gloss_rgb.outputs['Color'], spec_masked.inputs['Color1'] )
        L.new( I['Specular Mask'], spec_masked.inputs['Color2'] )

        spec_amt = n.new( 'ShaderNodeMixRGB' )
        spec_amt.blend_type = 'MULTIPLY'
        spec_amt.location = ( 130, -820 )
        spec_amt.label = 'x specular amount'
        spec_amt.inputs['Fac'].default_value = 1.0
        L.new( spec_masked.outputs['Color'], spec_amt.inputs['Color1'] )
        L.new( I['Specular Amount'], spec_amt.inputs['Color2'] )

        # --- combine ----------------------------------------------------------
        plus_spec = n.new( 'ShaderNodeMixRGB' )
        plus_spec.blend_type = 'ADD'
        plus_spec.location = ( 260, -200 )
        plus_spec.inputs['Fac'].default_value = 1.0
        L.new( shaded.outputs['Color'], plus_spec.inputs['Color1'] )
        L.new( spec_amt.outputs['Color'], plus_spec.inputs['Color2'] )

        plus_rim = n.new( 'ShaderNodeMixRGB' )
        plus_rim.blend_type = 'ADD'
        plus_rim.location = ( 440, -200 )
        plus_rim.inputs['Fac'].default_value = 1.0
        L.new( plus_spec.outputs['Color'], plus_rim.inputs['Color1'] )
        L.new( rim_scaled.outputs['Color'], plus_rim.inputs['Color2'] )

        emit = n.new( 'ShaderNodeEmission' )
        emit.location = ( 620, -100 )
        L.new( plus_rim.outputs['Color'], emit.inputs['Color'] )

        # alpha, so one group covers both BSSolid and BSBlendAlpha materials
        trans = n.new( 'ShaderNodeBsdfTransparent' )
        trans.location = ( 620, -320 )
        blend = n.new( 'ShaderNodeMixShader' )
        blend.location = ( 760, -200 )
        L.new( I['Alpha'], blend.inputs['Fac'] )
        L.new( trans.outputs['BSDF'], blend.inputs[1] )
        L.new( emit.outputs['Emission'], blend.inputs[2] )
        L.new( blend.outputs['Shader'], gout.inputs['Shader'] )

        self.logger.info( f'built the {self.MT_GROUP_NAME} node group' )
        return group

    def _wantsToonShading( self, context ):
        try:
            return bool( context.scene.sub_scene_properties.import_toon_shading )
        except Exception:
            return False

    def _buildMTShader( self, bpy_material, nodes, principled, albedo_tex, ramp_tex, material,
                        normal_out=None, spec_out=None, rev_tex=None, useToonRamp=True ):
        """Drop in an MT Character group and feed it. The per material graph is just
        textures, the group, and the output; everything else lives in the group."""
        try:
            links = bpy_material.node_tree.links
            out = nodes.get( 'Material Output' )
            if out is None:
                for nd in nodes:
                    if nd.bl_idname == 'ShaderNodeOutputMaterial':
                        out = nd
                        break
            if out is None:
                return

            group = self._getOrBuildMTGroup()
            inst = nodes.new( 'ShaderNodeGroup' )
            inst.node_tree = group
            inst.name = 'MT Character'
            inst.label = 'MT Character'
            inst.location = ( 100, 300 )
            inst.width = 240

            def setv( name, value ):
                sock = inst.inputs.get( name )
                if sock is not None:
                    try:
                        sock.default_value = value
                    except Exception:
                        pass

            def link( name, socket ):
                sock = inst.inputs.get( name )
                if sock is not None and socket is not None:
                    links.new( socket, sock )

            # textures
            if albedo_tex is not None:
                link( 'Albedo', albedo_tex.outputs['Color'] )
                if material.isAlphaBlended():
                    link( 'Alpha', albedo_tex.outputs['Alpha'] )
                else:
                    setv( 'Alpha', 1.0 )
            if ramp_tex is not None and useToonRamp:
                # sampled by the group, so give it the u coordinate it expects
                self._wireRampLookup( bpy_material, nodes, inst, ramp_tex )
                link( 'Toon Ramp', ramp_tex.outputs['Color'] )
            if rev_tex is not None:
                link( 'Toon Rev Ramp', rev_tex.outputs['Color'] )
            if normal_out is not None:
                link( 'Normal', normal_out )
            if spec_out is not None:
                link( 'Specular Mask', spec_out )

            # mrl numbers
            hl = material.getHalfLambert() or ( 0.5, 0.5 )
            setv( 'HalfLambert Bias',  float( hl[0] ) )
            setv( 'HalfLambert Scale', float( hl[1] ) )

            factor = self._diffuseFactor( material )
            setv( 'Diffuse Tint', ( factor[0], factor[1], factor[2], 1.0 ) )

            spec = material.getSpecularTint()
            if spec is not None:
                setv( 'Specular Tint', ( spec[0], spec[1], spec[2], 1.0 ) )
            power = material.getSpecularPower()
            if power:
                setv( 'Specular Power', float( power ) )

            # Feature flags become behaviour rather than text. Each of these is present
            # on a material only when the shader uses it.
            setv( 'Rim Light',       1.0 if material.hasFlag( 'FCalcRimLight' ) else 0.0 )
            setv( 'Fresnel',         0.5 if material.hasFlag( 'FFresnel' ) else 0.0 )
            setv( 'Specular Amount', 1.0 if material.hasFlag( 'FSpecular' ) else 0.0 )
            # the ramp only drives shading when the user asked for it, otherwise the
            # group falls back to a plain lambert and stays useful
            setv( 'Use Toon Ramp',   1.0 if useToonRamp else 0.0 )

            links.new( inst.outputs['Shader'], out.inputs['Surface'] )

            # the ramp is the whole lighting model, blender's own shadowing double counts
            try:
                bpy_material.shadow_method = 'NONE'
            except Exception:
                pass

            # Nothing feeds it any more, so leave it out of the graph rather than
            # parking a dead node next to every material.
            try:
                if principled is not None:
                    nodes.remove( principled )
            except Exception:
                pass
            self.logger.info( f'{bpy_material.name}: MT Character group, '
                              f'bias {hl[0]:.3f} scale {hl[1]:.3f}' )
        except Exception as e:
            self.logger.warn( 'could not build the MT shader: ' + str( e ) )

    def _wireRampLookup( self, bpy_material, nodes, inst, ramp_tex ):
        """The ramp is a 512x1 lookup, so it needs the half lambert value as its u.
        That value is computed inside the group, so mirror the same maths outside to
        drive the texture. Cheap, and keeps the group's inputs plain colours."""
        try:
            links = bpy_material.node_tree.links
            diff = nodes.new( 'ShaderNodeBsdfDiffuse' )
            diff.location = ( -1500, -300 )
            diff.inputs['Color'].default_value = ( 1, 1, 1, 1 )
            s2 = nodes.new( 'ShaderNodeShaderToRGB' )
            s2.location = ( -1320, -300 )
            links.new( diff.outputs['BSDF'], s2.inputs['Shader'] )

            rng = nodes.new( 'ShaderNodeMapRange' )
            rng.location = ( -1140, -300 )
            rng.label = 'half lambert'
            rng.clamp = True
            links.new( s2.outputs['Color'], rng.inputs['Value'] )
            bias = inst.inputs['HalfLambert Bias'].default_value
            scale = inst.inputs['HalfLambert Scale'].default_value
            rng.inputs['To Min'].default_value = max( 0.0, min( 1.0, bias ) )
            rng.inputs['To Max'].default_value = max( 0.0, min( 1.0, bias + scale ) )

            comb = nodes.new( 'ShaderNodeCombineXYZ' )
            comb.location = ( -940, -300 )
            links.new( rng.outputs['Result'], comb.inputs['X'] )
            comb.inputs['Y'].default_value = 0.5
            ramp_tex.location = ( -760, -300 )
            links.new( comb.outputs['Vector'], ramp_tex.inputs['Vector'] )
        except Exception as e:
            self.logger.debug( 'could not wire the ramp lookup: ' + str( e ) )

    def _diffuseFactor( self, material ):
        """CBMaterial[0..2] tints the albedo and CBDiffuseColorCorect scales it, a flat
        1.22 on every material seen that has it. Both belong on the plain Principled
        path as much as the toon one, so they live here rather than inside either."""
        factor = [ 1.0, 1.0, 1.0 ]
        tint = material.getDiffuseTint()
        if tint is not None:
            factor = [ tint[0], tint[1], tint[2] ]
        boost = material.getDiffuseColorCorrect()
        if boost is not None:
            factor = [ c * boost for c in factor ]
        return factor

    def _applyMaterialState( self, bpy_material, material ):
        '''Blend and raster state map straight onto blender material settings and
        matter more visually than people expect.'''
        try:
            if material.isDoubleSided():
                bpy_material.use_backface_culling = False
            else:
                bpy_material.use_backface_culling = True

            if material.isAlphaBlended():
                bpy_material.blend_method = 'BLEND'
                if hasattr( bpy_material, 'shadow_method' ):
                    bpy_material.shadow_method = 'HASHED'
                bpy_material.show_transparent_back = False
            else:
                bpy_material.blend_method = 'OPAQUE'
        except Exception as e:
            self.logger.debug( 'could not apply material state: ' + str( e ) )
    def convertMaterial( self, material: imMaterialInfo, context, materialName: str ):
        bpy_material = bpy.data.materials.new(name=materialName)
        bpy_material.use_nodes = True
        if material is not None and not hasattr( material, 'getUVChannelForSlot' ):
            self.logger.warn(
                f"material '{materialName}' has no mrl entry, importing untextured" )
            material = None

        if material is not None:
            nodes = bpy_material.node_tree.nodes
            principled_bsdf = nodes.get("Principled BSDF") or nodes.new("ShaderNodeBsdfPrincipled")

            albedo_tex = None
            metalness_tex = None
            normal_map_node = None
            albedo_map = self.loadTextureSlot(material, "tAlbedoMap", context)
            if albedo_map:
                albedo_tex = nodes.new("ShaderNodeTexImage")
                albedo_tex.image = albedo_map
                albedo_tex.location.x = -900
                albedo_tex.location.y = 300
                bpy_material.node_tree.links.new(albedo_tex.outputs["Color"], principled_bsdf.inputs["Base Color"])
                self._attachUVChannel( bpy_material, nodes, albedo_tex, material, 'tAlbedoMap' )

                # the albedo alpha channel is the transparency source when the
                # blend state composites rather than writing opaque
                if material.isAlphaBlended():
                    bpy_material.node_tree.links.new(albedo_tex.outputs["Alpha"], principled_bsdf.inputs["Alpha"])

            specular_map = self.loadTextureSlot(material, "tSpecularMap", context)
            if specular_map:
                metalness_tex = nodes.new("ShaderNodeTexImage")
                metalness_tex.image = specular_map
                metalness_tex.location.x = -900
                metalness_tex.location.y = 0


                #Specular Maps are sensitive in Marvel 3 so we have to compensate for that to get closer to the desired lighting.
                metalness_tex_power = nodes.new("ShaderNodeMath")
                metalness_tex_power.operation = 'POWER'
                metalness_tex_power.inputs[1].default_value  = 0.250

                metalness_tex_power.location.x = -300
                metalness_tex_power.location.y = 0

                bpy_material.node_tree.links.new(metalness_tex.outputs["Color"], metalness_tex_power.inputs[0])

                #Sets the Color Space to Non-Color so the material displays properly.
                metalness_tex.image.colorspace_settings.name = 'Non-Color'                
                bpy_material.node_tree.links.new(metalness_tex_power.outputs["Value"], principled_bsdf.inputs["Roughness"])
                self._attachUVChannel( bpy_material, nodes, metalness_tex, material, 'tSpecularMap' )

            normal_map = self.loadTextureSlot(material, "tNormalMap", context)
            if normal_map:
                normal_map_node = nodes.new("ShaderNodeNormalMap")
                normal_map_node.location.x = -200
                normal_map_node.location.y = -100

                normal_map_tex = nodes.new("ShaderNodeTexImage")
                normal_map_tex.location.x = -900
                normal_map_tex.location.y = -300

                normal_map_separate_color = nodes.new("ShaderNodeSeparateColor")
                normal_map_separate_color.location.x = -650
                normal_map_separate_color.location.y = -300

                normal_map_invert = nodes.new("ShaderNodeInvert")
                normal_map_invert.location.x = -650
                normal_map_invert.location.y = -500

                normal_map_combine = nodes.new("ShaderNodeCombineColor")
                normal_map_combine.location.x = -400
                normal_map_combine.location.y = -200

                # Swap the red and alpha channels of the normal map
                # normal_map_pixels = np.array(normal_map.pixels)
                # normal_map_pixels = normal_map_pixels.reshape(-1, 4)
                # normal_map_pixels[:, 0], normal_map_pixels[:, 3] = normal_map_pixels[:, 3], normal_map_pixels[:, 0]
                # normal_map_pixels = normal_map_pixels.flatten()
                # normal_map.pixels = normal_map_pixels

                #Sets the Color Space to Non-Color so the material displays properly.
                normal_map_tex.image = normal_map
                normal_map_tex.image.colorspace_settings.name = 'Non-Color' 
                bpy_material.node_tree.links.new(normal_map_tex.outputs["Color"], normal_map_separate_color.inputs["Color"])
                bpy_material.node_tree.links.new(normal_map_separate_color.outputs["Green"], normal_map_invert.inputs["Color"])

                bpy_material.node_tree.links.new(normal_map_tex.outputs["Alpha"], normal_map_combine.inputs["Red"])
                bpy_material.node_tree.links.new(normal_map_invert.outputs["Color"], normal_map_combine.inputs["Green"])
                bpy_material.node_tree.links.new(normal_map_separate_color.outputs["Blue"], normal_map_combine.inputs["Blue"])

                bpy_material.node_tree.links.new(normal_map_combine.outputs["Color"], normal_map_node.inputs["Color"])

                bpy_material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
                self._attachUVChannel( bpy_material, nodes, normal_map_tex, material, 'tNormalMap' )

                # normal_map_tex.image.colorspace_settings.name = 'Non-Color'                
                # bpy_material.node_tree.links.new(normal_map_tex.outputs["Color"], normal_map_node.inputs["Color"])
                # bpy_material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
            
            # A second albedo layered over the first, on its own uv channel.
            # Dante uses it on two materials. Mixed rather than replacing, which is
            # the sane default without knowing the shader's exact blend.
            blend_map = self.loadTextureSlot( material, 'tAlbedoBlendMap', context )
            if blend_map and albedo_map:
                blend_tex = nodes.new( 'ShaderNodeTexImage' )
                blend_tex.image = blend_map
                blend_tex.location.x = -900
                blend_tex.location.y = 600
                blend_tex.label = 'tAlbedoBlendMap'
                self._attachUVChannel( bpy_material, nodes, blend_tex, material, 'tAlbedoBlendMap' )

                try:
                    links = bpy_material.node_tree.links
                    mix = nodes.new( 'ShaderNodeMixRGB' )
                    mix.blend_type = 'MIX'
                    mix.location.x = -600
                    mix.location.y = 450
                    links.new( albedo_tex.outputs['Color'], mix.inputs['Color1'] )
                    links.new( blend_tex.outputs['Color'], mix.inputs['Color2'] )
                    links.new( blend_tex.outputs['Alpha'], mix.inputs['Fac'] )
                    links.new( mix.outputs['Color'], principled_bsdf.inputs['Base Color'] )
                except Exception as e:
                    self.logger.debug( 'could not wire tAlbedoBlendMap: ' + str( e ) )

            toon_nodes = {}
            for slot, yoff in ( ( 'tToonMap', 1200 ), ( 'tToonRevMap', 1000 ) ):
                toon_img = self.loadTextureSlot( material, slot, context )
                if toon_img:
                    toon_tex = nodes.new( 'ShaderNodeTexImage' )
                    toon_tex.image = toon_img
                    toon_tex.location.x = -400
                    toon_tex.location.y = yoff
                    toon_tex.label = slot
                    # a lookup ramp, not a colour texture
                    try:
                        toon_tex.image.colorspace_settings.name = 'Non-Color'
                        toon_tex.extension = 'EXTEND'
                        toon_tex.interpolation = 'Linear'
                    except Exception:
                        pass
                    toon_nodes[slot] = toon_tex

            # The MT group is always built, because Principled cannot represent this
            # material model at all. The toggle only decides whether the toon ramp
            # drives the lighting or the group falls back to a plain lambert.
            # Opt in only. With the Rendering options off an import is plain Principled,
            # which is what rigging and export work wants: textures as authored, no
            # tint, no brightness lift, nothing to undo.
            if self._wantsToonShading( context ):
                self._buildMTShader(
                    bpy_material, nodes, principled_bsdf, albedo_tex,
                    toon_nodes.get( 'tToonMap' ), material,
                    normal_out  = normal_map_node.outputs['Normal'] if normal_map_node else None,
                    spec_out    = metalness_tex.outputs['Color'] if metalness_tex else None,
                    rev_tex     = toon_nodes.get( 'tToonRevMap' ),
                    useToonRamp = True )

            # CBHalfLambert drives the toon ramp lookup and varies per material,
            # 7 distinct pairs across Dante's 25. Stash it so it isn't lost.
            hl = material.getHalfLambert()
            if hl is not None:
                bpy_material['CBHalfLambert'] = [ hl[0], hl[1] ]

            #Light Maps. tOcclusionMap
            # Specular tint and power go to the MT group as inputs, so the old
            # principled specular block is gone; it also ran after the group had
            # already removed that node.
            self._applyMaterialState( bpy_material, material )

            light_map = self.loadTextureSlot(material, "tOcclusionMap", context)
            if light_map and not mt_shaded:
                light_map_tex = nodes.new("ShaderNodeTexImage")   
                light_map_tex.image = light_map
                #Not sure how to properly apply the light map to the Blender scene so we'll just put the texture in the shading tab separate from the rest.
                light_map_tex.location.x = -400
                light_map_tex.location.y = 800             

                #Attempt to create a UV Map Node & attach it.
                light_map_UVMap = nodes.new("ShaderNodeUVMap")
                # was hardcoded to UVUnique; the mrl names the channel per slot
                try:
                    light_map_UVMap.uv_map = material.getUVChannelForSlot( 'tOcclusionMap' )
                except Exception:
                    light_map_UVMap.uv_map = "UVUnique"
                light_map_UVMap.location.x = -550
                light_map_UVMap.location.y = 800
                bpy_material.node_tree.links.new(light_map_UVMap.outputs["UV"], light_map_tex.inputs["Vector"])

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

        # #Because Object Mode Bone properties are not accessible in a script, 
        # #I'm adding these MT Attributes to the respective Pose bone instead.
        bone = self.armatureObj.pose.bones[obj.getName()]

        # bone = self.armature.bones.get(obj.getName())
        return BlenderCustomAttributeSetProxy(bone)

    OUTLINE_MATERIAL_NAME = 'MT Outline'

    def _getOrBuildOutlineMaterial( self ):
        mat = bpy.data.materials.get( self.OUTLINE_MATERIAL_NAME )
        if mat is not None:
            return mat
        mat = bpy.data.materials.new( name=self.OUTLINE_MATERIAL_NAME )
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        for n in list( nodes ):
            if n.bl_idname != 'ShaderNodeOutputMaterial':
                nodes.remove( n )
        out = nodes[0]
        emit = nodes.new( 'ShaderNodeEmission' )
        emit.location = ( -200, 0 )
        emit.inputs['Color'].default_value = ( 0.0, 0.0, 0.0, 1.0 )
        emit.inputs['Strength'].default_value = 1.0
        links.new( emit.outputs['Emission'], out.inputs['Surface'] )
        # showing only the inside of the shell is what makes it a line and not a blob
        mat.use_backface_culling = True
        try:
            mat.shadow_method = 'NONE'
        except Exception:
            pass
        self.logger.info( f'built the {self.OUTLINE_MATERIAL_NAME} material' )
        return mat

    def _addOutline( self, obj, thickness ):
        try:
            if obj is None or obj.type != 'MESH':
                return
            if any( m.type == 'SOLIDIFY' and m.name == 'MT Outline' for m in obj.modifiers ):
                return

            mat = self._getOrBuildOutlineMaterial()
            if mat.name not in [ s.name for s in obj.data.materials if s ]:
                obj.data.materials.append( mat )
            slot = len( obj.data.materials ) - 1

            mod = obj.modifiers.new( name='MT Outline', type='SOLIDIFY' )
            mod.thickness = float( thickness )
            mod.offset = 1.0
            mod.use_flip_normals = True
            mod.use_rim = False
            mod.material_offset = slot
            mod.material_offset_rim = slot
            # a uniform shell reads better than one that thins at tight corners
            mod.use_even_offset = True
            mod.thickness_clamp = 0.0
        except Exception as e:
            self.logger.debug( f'could not add an outline to {getattr(obj,"name","?")}: {e}' )

    def importModel(self, modFilePath, context):
        super().importModel(modFilePath, context)

        try:
            mip = context.scene.sub_scene_properties
            if getattr( mip, 'import_outline', False ):
                thickness = float( getattr( mip, 'outline_thickness', 0.45 ) )
                count = 0
                for obj in getattr( self, 'importedMeshObjects', [] ):
                    self._addOutline( obj, thickness )
                    count += 1
                if count == 0:
                    # fall back to whatever this import just created
                    for obj in bpy.context.selected_objects:
                        if obj.type == 'MESH':
                            self._addOutline( obj, thickness )
                            count += 1
                self.logger.info( f'ink outline added to {count} meshes at {thickness} units' )
        except Exception as e:
            self.logger.debug( 'could not add outlines: ' + str( e ) )