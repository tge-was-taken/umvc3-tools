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
        obj.data.materials.append( self._materialForPrimitive( primitive.indices.getMaterialIndex(), shaderInfo.name, context,
                                                                mt_exact.receives_shadows( getattr( primitive, 'flags', 0xffff ) ) ) )
        if self._wantsExact( context ) and context.scene.get( 'mt_exact_outlines' ):
            # the game's outline pass; the IASkinBridge meshes exist only for it
            # (off for now: the stencil test it relies on isn't reproduced yet)
            try:
                mt_exact.add_outline( obj, shaderInfo.name, context, self.logger, outline_only=shaderInfo.name.startswith( 'IASkinBridge' ) )
            except Exception as e:
                self.logger.warn( f'could not add the game outline to {mesh_name}: {e}' )
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
<<<<<<< Updated upstream
=======

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
>>>>>>> Stashed changes
        
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


    # ------------------------------------------------------------------
    # MT shading
    # ------------------------------------------------------------------
    #
    # Rebuilt from the game's compiled shaders (root.spkg) and shader database
    # (UserShaderPackage.mfx), see modules/mt_shading.py. The mrl flags pick the same
    # building blocks the game's shader system does, the cbuffer values go onto sockets
    # named after the real shader constants, and the lighting comes from scene properties
    # that a stage's sdl can fill in. Works in Eevee and Cycles.

    def _wantsToonShading( self, context ):
        try:
            return bool( context.scene.sub_scene_properties.import_toon_shading )
        except Exception:
            return False

    def decodeYUVTexture( self, image, ddsPath ):
        try:
            png = os.path.splitext( ddsPath )[0] + '_rgb.png'
            decoded = mt_shading.decode_yuv_image( image, png )
            try:
                decoded['mt_raw_image'] = image.name
            except Exception:
                pass
            self.logger.info( f'decoded YUV (format 42) texture {os.path.basename( ddsPath )}' )
            return decoded
        except Exception as e:
            self.logger.warn( f'could not decode YUV texture {ddsPath}: {e}' )
            return image

    def tagTextureFormat( self, image, fmt, texPath ):
        try:
            if image is not None:
                image['mt_tex_format'] = int( fmt )
                image['mt_tex_path'] = str( texPath )
        except Exception:
            pass

    def _mtTexNode( self, nodes, image, label, x, y, non_color=True, extend=False ):
        tex = nodes.new( 'ShaderNodeTexImage' )
        tex.image = image
        tex.label = label
        tex.location = ( x, y )
        if non_color:
            try:
                image.colorspace_settings.name = 'Non-Color'
            except Exception:
                pass
        if extend:
            tex.extension = 'EXTEND'
            tex.interpolation = 'Linear'
        return tex

    def _mtUV( self, bpy_material, nodes, tex, material, slot ):
        try:
            self._attachUVChannel( bpy_material, nodes, tex, material, slot )
        except Exception as e:
            self.logger.debug( f'uv for {slot}: {e}' )

    def _mtRamp( self, nodes, links, image, label, coords, uv, x, y ):
        '''Samples a toon ramp once per colour channel, each at its own u (they only differ
        when coloured scene lights hit the surface) and puts r, g and b back together.'''
        comb = nodes.new( 'ShaderNodeCombineColor' )
        comb.location = ( x + 300, y )
        for i, suffix in enumerate( ( '', ' G', ' B' ) ):
            tex = self._mtTexNode( nodes, image, label, x, y - i * 90, extend=True )
            tex.hide = True
            links.new( coords.outputs[uv + suffix], tex.inputs['Vector'] )
            sep = nodes.new( 'ShaderNodeSeparateColor' )
            sep.location = ( x + 150, y - i * 90 )
            sep.hide = True
            links.new( tex.outputs['Color'], sep.inputs['Color'] )
            links.new( sep.outputs[i], comb.inputs[i] )
        return comb.outputs['Color']

    # ------------------------------------------------------------------------------------
    # exact mode: the game's own pixel shaders compiled to nodes (see mt_exact)
    # ------------------------------------------------------------------------------------
    DEFAULT_GAME_DIRS = (
        r'C:\Program Files (x86)\Steam\steamapps\common\ULTIMATE MARVEL VS. CAPCOM 3',
        r'C:\Steam\steamapps\common\ULTIMATE MARVEL VS. CAPCOM 3',
        r'D:\SteamLibrary\steamapps\common\ULTIMATE MARVEL VS. CAPCOM 3',
    )

    def _storeTangentFrame( self, mesh ):
        if 'mt_tangent' not in mesh.attributes or 'UVPrimary' not in mesh.uv_layers:
            return
        try:
            mesh.calc_tangents( uvmap='UVPrimary' )
        except Exception as e:
            self.logger.debug( f'no tangent frame for {mesh.name}: {e}' )
            return
        gt = mesh.attributes['mt_tangent'].data
        gs = mesh.attributes['mt_tangent_sign'].data
        coef, sign = [], []
        for l in mesh.loops:
            t = mathutils.Vector( gt[l.vertex_index].vector )
            if t.length > 1e-8:
                t.normalize()
            coef.extend( ( t.dot( l.tangent ), t.dot( l.bitangent ), t.dot( l.normal ) ) )
            sign.append( 1.0 if gs[l.vertex_index].value >= 0 else -1.0 )
        try:
            a = mesh.attributes.new( name='mt_tan_coef', type='FLOAT_VECTOR', domain='CORNER' )
            a.data.foreach_set( 'vector', coef )
            a = mesh.attributes.new( name='mt_tan_sign', type='FLOAT', domain='CORNER' )
            a.data.foreach_set( 'value', sign )
        except Exception as e:
            self.logger.debug( f'could not store the tangent frame for {mesh.name}: {e}' )
        try:
            mesh.free_tangents()
        except Exception:
            pass

    def _wantsExact( self, context ):
        try:
            mip = context.scene.sub_scene_properties
            return bool( mip.import_toon_shading and mip.import_exact_shading and context.scene.get( 'mt_game_native_dir' ) )
        except Exception:
            return False

    def _setupExact( self, modFilePath, context ):
        mip = context.scene.sub_scene_properties
        if not getattr( mip, 'import_exact_shading', False ):
            return
        from ..mtlib import mtshaders
        hint = bpy.path.abspath( getattr( mip, 'game_native_dir', '' ) or '' )
        native = mtshaders.ShaderDB.find_native( hint, modFilePath, *self.DEFAULT_GAME_DIRS )
        if native is None:
            self.logger.warn( 'game shaders not found (set the game folder in the import panel), using the approximate MT shading' )
            context.scene['mt_game_native_dir'] = ''
            return
        context.scene['mt_game_native_dir'] = native
        self.logger.info( f'using the game shaders from {native}' )
        scene = context.scene
        try:
            mt_exact.ensure_game_camera( scene, getattr( mip, 'model_scale', 1.0 ) or 1.0 )
        except Exception as e:
            self.logger.warn( f'could not add the game camera: {e}' )
        if 'mt_outline_push' not in scene.keys():
            scene['mt_outline_push'] = 60.0
        if 'mt_outenc' not in scene.keys():
            scene['mt_outenc'] = 1
        if not scene.get( 'mt_exact_defaults' ):
            # first exact import in this scene: start from what the game used and show it in
            # the rim / ambient panel values that drive those constants
            try:
                mt_exact.ensure_renderer_props( scene )
                mt_exact.sync_lighting_from_constants( scene )
                scene['mt_exact_defaults'] = 1
            except Exception as e:
                self.logger.warn( f'could not set the game renderer defaults: {e}' )

    def _rememberForExact( self, bpy_material, material, context ):
        if not self._wantsExact( context ):
            return
        images = {}
        for cmd in material.cmds:
            if cmd.type != 'texture' or not cmd.data:
                continue
            try:
                img = self.loadTextureSlot( material, cmd.name, context )
            except Exception:
                img = None
            if img is not None and img.get( 'mt_raw_image' ) and img['mt_raw_image'] in bpy.data.images:
                raw = bpy.data.images[img['mt_raw_image']]
                raw['mt_tex_format'] = img.get( 'mt_tex_format', 42 )
                img = raw
            if img is not None:
                # the game path, so an export writes the texture back where it came from
                img['mt_tex_path'] = cmd.data
                images[cmd.name] = img
        self._exactInfo[bpy_material.name] = ( material, images )
        try:
            bpy_material['mt_mrl_path'] = getattr( self, 'mrlPath', '' ) or ''
        except Exception:
            pass

    def _materialForPrimitive( self, matIndex, ia, context, receive=True ):
        base = self.editorMaterialArray[matIndex].unwrap()
        if not self._wantsExact( context ) or base.name not in self._exactInfo:
            return base
        key = ( matIndex, ia, receive )
        if key in self._exactMaterials:
            return self._exactMaterials[key]
        material, images = self._exactInfo[base.name]
        # one blender material per vertex layout, the game picks a different program for each
        used = [ k for k in self._exactMaterials if k[0] == matIndex ]
        mat = base if not used else base.copy()
        if used:
            mat.name = f'{base.name}@{ia}' + ( '' if receive else '@noshadow' )
        try:
            prog = mt_exact.build_exact_material( mat, material, ia, images, context, self.logger, receive=receive )
        except Exception as e:
            prog = None
            self.logger.warn( f'could not compile the game shader for {mat.name}: {e}' )
            self.logger.exception( e )
        if prog is None and used:
            bpy.data.materials.remove( mat )
            mat = base
        self._exactMaterials[key] = mat
        return mat

    def _buildMTMaterial( self, bpy_material, material, context, images ):
        '''Replaces the material's graph with the MT shading graph.'''
        nodes = bpy_material.node_tree.nodes
        links = bpy_material.node_tree.links
        for n in list( nodes ):
            nodes.remove( n )
        out = nodes.new( 'ShaderNodeOutputMaterial' )
        out.location = ( 700, 200 )

        variant = material.getShaderVariant()
        coords = nodes.new( 'ShaderNodeGroup' )
        coords.node_tree = mt_shading.get_coords_group()
        coords.label = coords.name = 'MT Toon Coords'
        coords.location = ( -500, -500 )
        group = nodes.new( 'ShaderNodeGroup' )
        group.node_tree = mt_shading.get_character_group()
        group.label = group.name = 'MT Character'
        group.location = ( 300, 200 )
        group.width = 260
        G = group.inputs
        links.new( group.outputs['Shader'], out.inputs['Surface'] )

        def setv( name, value ):
            sock = G.get( name ) or coords.inputs.get( name )
            if sock is not None and value is not None:
                try:
                    sock.default_value = value
                except Exception:
                    try:
                        sock.default_value = ( value[0], value[1], value[2], 1.0 )
                    except Exception:
                        pass

        geo = nodes.new( 'ShaderNodeNewGeometry' )
        geo.location = ( -1300, -300 )
        links.new( geo.outputs['Normal'], coords.inputs['Vertex Normal'] )

        # --- normal: alpha is X, green is Y (flipped for blender's uv), z rebuilt
        normal_sock = geo.outputs['Normal']
        if images.get( 'tNormalMap' ) is not None:
            tex = self._mtTexNode( nodes, images['tNormalMap'], 'tNormalMap', -1300, -100 )
            self._mtUV( bpy_material, nodes, tex, material, 'tNormalMap' )
            sep = nodes.new( 'ShaderNodeSeparateColor' ); sep.location = ( -1050, -100 )
            links.new( tex.outputs['Color'], sep.inputs['Color'] )
            def m( op, a, b=None, loc=( -900, -100 ) ):
                n = nodes.new( 'ShaderNodeMath' ); n.operation = op; n.location = loc
                for i, v in enumerate( ( a, b ) ):
                    if v is None: continue
                    if isinstance( v, bpy.types.NodeSocket ): links.new( v, n.inputs[i] )
                    else: n.inputs[i].default_value = v
                return n.outputs[0]
            x = m( 'MULTIPLY_ADD', tex.outputs['Alpha'], 2.0 ); x.node.inputs[2].default_value = -0.996078
            y = m( 'MULTIPLY_ADD', sep.outputs['Green'], 2.0 ); y.node.inputs[2].default_value = -0.996078
            y = m( 'MULTIPLY', y, -1.0 )
            zz = m( 'SQRT', m( 'MAXIMUM', m( 'SUBTRACT', m( 'SUBTRACT', 1.0, m( 'MULTIPLY', x, x ) ), m( 'MULTIPLY', y, y ) ), 0.0001 ) )
            comb = nodes.new( 'ShaderNodeCombineXYZ' ); comb.location = ( -700, -100 )
            for i, c in enumerate( ( x, y, zz ) ):
                links.new( m( 'MULTIPLY_ADD', c, 0.5 ), comb.inputs[i] )
                comb.inputs[i].links[0].from_node.inputs[2].default_value = 0.5
            nmap = nodes.new( 'ShaderNodeNormalMap' ); nmap.location = ( -550, -100 )
            try:
                nmap.uv_map = material.getUVChannelForSlot( 'tNormalMap' )
            except Exception:
                pass
            links.new( comb.outputs[0], nmap.inputs['Color'] )
            normal_sock = nmap.outputs['Normal']
        links.new( normal_sock, coords.inputs['Normal'] )
        links.new( normal_sock, G['Normal'] )
        links.new( coords.outputs['Shading Normal'], G['Shading Normal'] )
        for name in ( 'Lambert Light', 'Light Color', 'Ambient Light', 'World Light', 'Scene Lights' ):
            links.new( coords.outputs[name], G[name] )

        # --- albedo
        if images.get( 'tAlbedoMap' ) is not None:
            tex = self._mtTexNode( nodes, images['tAlbedoMap'], 'tAlbedoMap', -700, 500 )
            self._mtUV( bpy_material, nodes, tex, material, 'tAlbedoMap' )
            links.new( tex.outputs['Color'], G['Albedo'] )
            links.new( tex.outputs['Alpha'], G['Alpha'] )
        setv( 'Use Alpha', 1.0 if material.isAlphaBlended() or variant['alpha_test'] else 0.0 )

        # --- specular mask: green channel, matcap uv for FUVViewNormal
        if images.get( 'tSpecularMap' ) is not None:
            tex = self._mtTexNode( nodes, images['tSpecularMap'], 'tSpecularMap', -700, 250 )
            if variant['spec_view_uv']:
                links.new( coords.outputs['View UV'], tex.inputs['Vector'] )
            else:
                self._mtUV( bpy_material, nodes, tex, material, 'tSpecularMap' )
            sep = nodes.new( 'ShaderNodeSeparateColor' ); sep.location = ( -450, 250 )
            links.new( tex.outputs['Color'], sep.inputs['Color'] )
            links.new( sep.outputs['Green'], G['Specular Mask'] )

        # --- toon ramps, sampled at the u the coords group works out
        toon = variant['toon'] and images.get( 'tToonMap' ) is not None
        if toon:
            img = images['tToonMap']
            if variant['toon_high']:
                tf = material.getConstant( 'fToonFactor' )
                if tf is not None:
                    try:
                        img = mt_shading.bake_toon_high_ramp( img, tf )
                    except Exception as e:
                        self.logger.warn( f'could not bake the FToonShaderHigh ramp: {e}' )
            links.new( self._mtRamp( nodes, links, img, 'tToonMap', coords, 'Toon UV', -250, -350 ), G['Toon Ramp'] )
        if images.get( 'tToonRevMap' ) is not None:
            links.new( self._mtRamp( nodes, links, images['tToonRevMap'], 'tToonRevMap', coords, 'Rev UV', -250, -900 ),
                       G['Toon Rev Ramp'] )
        else:
            setv( 'Rim', 0.0 )

        # --- sphere map reflection
        if images.get( 'tSphereMap' ) is not None:
            tex = self._mtTexNode( nodes, images['tSphereMap'], 'tSphereMap', -250, 0, extend=True )
            links.new( coords.outputs['View UV'], tex.inputs['Vector'] )
            links.new( tex.outputs['Color'], G['Reflection'] )

        # --- vertex occlusion (stored as 1 - occlusion)
        occ = nodes.new( 'ShaderNodeAttribute' )
        occ.attribute_type = 'GEOMETRY'
        occ.attribute_name = self.OCCLUSION_ATTRIBUTE
        occ.location = ( -250, 650 )
        inv = nodes.new( 'ShaderNodeMath' ); inv.operation = 'SUBTRACT'; inv.location = ( 0, 650 )
        inv.inputs[0].default_value = 1.0
        links.new( occ.outputs['Fac'], inv.inputs[1] )
        links.new( inv.outputs[0], G['Occlusion'] )

        # --- mrl values and switches
        hl = material.getHalfLambert() or ( 0.5, 0.5 )
        # plain FToonLightCalc samples at N.L, which is the same formula with spread 1
        setv( 'fHalfLambertRevise', hl[0] if variant['half'] else 1.0 )
        setv( 'fHalfLambertReviseRev', hl[1] if variant['rev_half'] else 1.0 )
        setv( 'Uroko', 1.0 if variant['uroko'] else 0.0 )
        setv( 'fUrokoFactor', material.getConstant( 'fUrokoFactor', 1.0 ) )
        for name in ( 'fAlbedoColor', 'fDiffuseColor', 'fSpecularColor', 'fShininess', 'fReflectiveColor',
                      'fFresnelSchlick', 'fFresnelLegacyFactor', 'fFresnelLegacyBias',
                      'fDiffuseColorCorectValue', 'fTransparency' ):
            setv( name, material.getConstant( name ) )
        setv( 'Toon', 1.0 if toon else 0.0 )
        setv( 'Color Correct', 1.0 if variant['color_correct'] else 0.0 )
        setv( 'Specular', float( variant['specular'] ) )
        setv( 'Rim', 1.0 if ( variant['rim'] and images.get( 'tToonRevMap' ) is not None ) else 0.0 )
        setv( 'Fresnel', float( variant['fresnel'] ) )

        # cast shadows so scene lights shadow the character (turn shadows off on a light
        # for the game's look, the game has no self shadowing)
        try:
            bpy_material.shadow_method = 'HASHED' if material.isAlphaBlended() or variant['alpha_test'] else 'OPAQUE'
        except Exception:
            pass
        bpy_material['mt_variant'] = ', '.join( k for k, v in variant.items() if v is True )
        self.logger.info( f'{bpy_material.name}: MT shading ({bpy_material["mt_variant"]})' )

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

            # Opt in. With it off an import is plain Principled, which is what rigging and
            # export work wants: textures as authored, nothing to undo.
            mt_shaded = False
            if self._wantsToonShading( context ):
                try:
                    images = {
                        'tAlbedoMap':  albedo_map,
                        'tSpecularMap': specular_map,
                        'tNormalMap':  normal_map,
                        'tToonMap':    toon_nodes['tToonMap'].image if 'tToonMap' in toon_nodes else None,
                        'tToonRevMap': toon_nodes['tToonRevMap'].image if 'tToonRevMap' in toon_nodes else None,
                        'tSphereMap':  self.loadTextureSlot( material, 'tSphereMap', context ),
                    }
                    self._buildMTMaterial( bpy_material, material, context, images )
                    mt_shaded = True
                    self._rememberForExact( bpy_material, material, context )
                except Exception as e:
                    self.logger.warn( f'could not build MT shading for {materialName}: {e}' )
                    self.logger.exception( e )

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

    # ------------------------------------------------------------------
    # Ink outline
    # ------------------------------------------------------------------
    #
    # The shader package carries VS_MaterialOutline / PS_MaterialOutline / TMaterialOutline
    # plus maskOutlineGeometry, so the game draws the contour as a geometry pass rather
    # than only as a screen space filter. None of the mrls reference outlines, which fits:
    # it is driven globally by the uOutlineFilter units in the stage sdl.
    #
    # The blender equivalent of that pass is an inverted hull. A Solidify modifier pushes
    # a shell outwards with flipped normals, and the outline material culls backfaces so
    # only the shell's inside shows, which reads as a line around the silhouette.

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
        self._exactInfo = {}
        self._exactMaterials = {}
        if self._wantsToonShading( context ):
            try:
                mip = context.scene.sub_scene_properties
                mt_shading.ensure_scene_lighting( context.scene, getattr( mip, 'model_scale', 1.0 ) )
                mt_shading.set_view_transform_standard( context.scene )
            except Exception as e:
                self.logger.warn( f'could not set up MT lighting: {e}' )
            self._setupExact( modFilePath, context )
        super().importModel(modFilePath, context)
        try:
            made = mt_exact.split_outlines( list( getattr( self, 'importedMeshObjects', [] ) ) )
            self.importedMeshObjects = list( getattr( self, 'importedMeshObjects', [] ) ) + made
        except Exception as e:
            self.logger.warn( f'could not move the outlines to their own objects: {e}' )
        try:
            # every face expression is in the file, one group each; the game shows one
            n = mt_exact.apply_face_group( context.scene, getattr( self, 'importedMeshObjects', [] ) )
            if n:
                self.logger.info( f'hid {n} primitives of the other face expressions / unused groups' )
        except Exception as e:
            self.logger.warn( f'could not pick the face expression: {e}' )
        if self._wantsExact( context ):
            try:
                mt_exact.link_scene_drivers( context.scene )
            except Exception as e:
                self.logger.warn( f'could not link the game shader constants to the scene: {e}' )

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