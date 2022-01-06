import os
from posixpath import relpath, split
import sys
from typing import List, Tuple

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
import mtmaxutil
from mtlib import texconv
import maxlog
import shutil
from mtlib import textureutil

def _tryParseInt(input, base=10, default=None):
    try:
        return int(str(input), base=base)
    except Exception:
        return default

class MtGroupAttribData(object):
    '''Wrapper for group custom attribute data'''
    def __init__( self, maxNode ):
        attribs = maxNode.mtModelGroupAttributes if hasattr(maxNode, 'mtModelGroupAttributes') else None
        if attribs != None:
            self.id = _tryParseInt(attribs.id)
            self.field04 = _tryParseInt(attribs.field04)
            self.field08 = _tryParseInt(attribs.field08)
            self.field0c = _tryParseInt(attribs.field0c)
            self.bsphere = attribs.bsphere
        else:
            self.id = None
            self.field04 = None
            self.field08 = None
            self.field0c = None
            self.bsphere = None

class MtPrimitiveAttribData(object):
    '''Wrapper for primitive custom attribute data'''
    def __init__( self, maxNode ):
        attribs = maxNode.mtPrimitiveAttributes if hasattr(maxNode, 'mtPrimitiveAttributes') else None
        if attribs != None:
            self.flags = _tryParseInt(attribs.flags.strip(), base=0)
            if attribs.groupId == "inherit":
                if maxNode.parent != None:
                    self.groupId = MtGroupAttribData(maxNode.parent).id
                else:
                    # invalid
                    self.groupId = None
            else:
                self.groupId = _tryParseInt(attribs.groupId.strip(), base=0)
            self.lodIndex = _tryParseInt(attribs.lodIndex)
            self.renderFlags = _tryParseInt(attribs.renderFlags, base=0)
            self.id = _tryParseInt(attribs.id)
            self.field2c = _tryParseInt(attribs.field2c)
        else:
            self.flags = None
            self.groupId = None
            self.lodIndex = None
            self.renderFlags = None
            self.id = None
            self.field2c = None
            
            if maxNode.parent != None:
                # even if no attribs are set, we should still inherit the group id if the mesh is parented to a group
                self.groupId = MtGroupAttribData(maxNode.parent).id

class MtJointAttribData(object):
    '''Wrapper for joint custom attribute data'''
    def __init__( self, maxNode, jointMeta ):
        attribs = maxNode.mtJointAttributes if hasattr(maxNode, 'mtJointAttributes') else None
        if attribs != None:
            # grab attributes from custom attributes on node
            self.id = _tryParseInt(attribs.id)
            self.symmetryNode = rt.getNodeByName( attribs.symmetryName )
            self.field03 = _tryParseInt(attribs.field03)
            self.field04 = _tryParseInt(attribs.field04)
        elif jointMeta != None:
            # grab attributes from joint metadata
            self.id = jointMeta.id
            self.symmetryNode = None # TODO try to guess symmetry from names?
            self.field03 = None
            self.field04 = None
        else:
            self.id = None
            self.symmetryNode = None
            self.field03 = None
            self.field04 = None

class MtModelExporter(object):
    '''Model scene exporter interface'''

    def __init__( self ):
        self.model = None
        self.maxNodeToJointMap = None
        self.jointToMaxNodeMap = None
        self.jointIdxByName = None
        self.ref = None
        self._textureMapCache = dict()
        self._materialCache = dict()
        self.transformMtx = None
        
    def _convertMaxPoint3ToNclVec3( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], v[1], v[2]))

    def _convertMaxPoint3ToNclVec3UV( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], 1 - v[1], v[2]))
        
    def _convertMaxPoint3ToNclVec4( self, v: rt.Point3, w = 1 ) -> NclVec3:
        return NclVec4((v[0], v[1], v[2], w))
    
    def _convertMaxMatrix3ToNclMat43( self, v: rt.Matrix3 ) -> NclMat43:
        return nclCreateMat43((self._convertMaxPoint3ToNclVec3(v[0]), 
                               self._convertMaxPoint3ToNclVec3(v[1]), 
                               self._convertMaxPoint3ToNclVec3(v[2]), 
                               self._convertMaxPoint3ToNclVec3(v[3])))
        
    def _convertMaxMatrix3ToNclMat44( self, v: rt.Matrix3 ):
        return nclCreateMat44((self._convertMaxPoint3ToNclVec4(v[0], 0), 
                               self._convertMaxPoint3ToNclVec4(v[1], 0), 
                               self._convertMaxPoint3ToNclVec4(v[2], 0), 
                               self._convertMaxPoint3ToNclVec4(v[3], 1)))

    def _shouldExportNode( self, node ):
        '''Returns if the node should be included in the export'''
        return not node.isHidden

    def _isMeshNode( self, node ):
        '''Returns if the node is a mesh'''

        # node is considered a mesh of it is an editable mesh or editable poly
        # TODO: investigate other possible types
        return rt.classOf( node ) in [rt.Editable_mesh, rt.Editable_poly, rt.PolyMeshObject]

    def _isGroupNode( self, node ):
        '''Returns if the node represents a group'''

        # group nodes may have group attrib data
        if hasattr(node, 'mtModelGroupAttributes'):
            return True
        
        if len(node.children) == 0:
            return False
        
        # group nodes should be parented to meshes
        # this doesn't allow empty groups, however the previous clause 
        # should cover that
        for child in node.children:
            if not self._isMeshNode( child ):
                return False

        return True

    def _isBoneNode( self, node ):
        '''Returns if the node is a bone'''

        # node is considered a bone node of it's bone geometry (helper)
        # TODO: investigate otehr possible types (Biped, ...?)
        return rt.classOf( node ) in [rt.BoneGeometry, rt.Dummy]
    
    def _getObjects( self ):
        # return a list of scene objects as opposed to enumerating directly to prevent crashes
        return list( rt.objects )

    def _processBone( self, maxNode ): 
        assert( self._isBoneNode( maxNode ) )

        if maxNode in self.maxNodeToJointMap:
            # prevent recursion
            return self.maxNodeToJointMap[maxNode]

        maxlog.info(f'processing bone: {maxNode.name}')
        jointMeta = self.metadata.getJointByName( maxNode.name )
        attribs = MtJointAttribData( maxNode, jointMeta )
        worldMtx = self._convertMaxMatrix3ToNclMat44( maxNode.transform )
        parentWorldMtx = self._convertMaxMatrix3ToNclMat44( maxNode.parent.transform ) if maxNode.parent != None else nclCreateMat44()
        localMtx = nclMultiply( nclInverse( parentWorldMtx ), worldMtx )
        if maxNode.parent == None:
            localMtx *= self.transformMtx
        
        joint = imJoint(
            name=maxNode.name, 
            id=attribs.id if attribs.id != None else len(self.model.joints), 
            #worldMtx=self._convertMaxMatrix3ToNclMat44( maxNode.transform ),
            localMtx=localMtx,
            parent=self.maxNodeToJointMap[ maxNode.parent ] if maxNode.parent != None else None, # must be specified here to not infere with matrix calculations
            field03=attribs.field03,
            field04=attribs.field04,
            length=None,        # TODO copy from attribs (?)
            invBindMtx=None,    # TODO copy from attribs (?)
            offset=None,        # TODO copy from attribs (?)
            symmetry=None,      # need to create current joint first to resolve self and forward references
        )
        maxlog.debug(joint)

        self.maxNodeToJointMap[maxNode] = joint
        self.jointToMaxNodeMap[joint] = maxNode
        self.model.joints.append( joint )
        self.jointIdxByName[ joint.name ] = len( self.model.joints ) - 1
    
    def _processBones( self ):
        if not mtmaxconfig.exportSkeleton:
            maxlog.info('processing bones skipped because it has been disabled through the config')
            return
        
        maxlog.info('processing bones')
        
        # convert all joints first
        # so we can reference them when building the primitives
        self.maxNodeToJointMap = dict()
        self.jointToMaxNodeMap = dict()
        self.jointIdxByName = dict()
        
        if self.ref != None and mtmaxconfig.exportUseRefJoints:
            # copy over original joints
            maxlog.info('copying bones from reference model')
            for i, refJoint in enumerate(self.ref.joints):
                joint = imJoint(
                    name=self.metadata.getJointName(refJoint.id),
                    id=refJoint.id,
                    localMtx=self.ref.jointLocalMtx[i],
                    invBindMtx=self.ref.jointInvBindMtx[i],
                    parent=self.model.joints[refJoint.parentIndex] if refJoint.parentIndex != 255 else None,
                    symmetry=None, # resolve later
                    field03=refJoint.field03,
                    field04=refJoint.field04,
                    length=refJoint.length,
                    offset=refJoint.offset,
                )

                self.jointIdxByName[joint.name] = i
                self.model.joints.append(joint)

            for i, joint in enumerate(self.model.joints):
                refJoint = self.ref.joints[i]
                joint.symmetry = self.model.joints[refJoint.symmetryIndex] if refJoint.symmetryIndex != 255 else None
        else:
            # process all bones in the scene
            for maxNode in self._getObjects():
                if not self._shouldExportNode( maxNode ) or not self._isBoneNode( maxNode ):
                    continue

                self._processBone( maxNode )

            # resolve references
            for joint in self.model.joints:
                maxNode = self.jointToMaxNodeMap[joint]
                jointMeta = self.metadata.getJointByName( maxNode.name )
                attribs = MtJointAttribData( maxNode, jointMeta )
                joint.symmetry = self._processBone( attribs.symmetryNode ) if attribs.symmetryNode != None else None
                
    def _convertTextureToTEX( self, inPath, outPath):
        try:
            textureutil.convertTexture( inPath, outPath )
        except PermissionError as e:
            maxlog.error( f"unable to save tex file, make sure you have write permissions to {outPath}" )
            
    def _exportTextureMap( self, textureMap ):
        if textureMap != None and not textureMap in self._textureMapCache:
            # add to cache
            self._textureMapCache[textureMap] = True
            
            if rt.classOf( textureMap ) in [rt.Bitmap, rt.Bitmaptexture]:
                maxlog.info(f'processing texture: {textureMap.filename}')
                if os.path.exists(textureMap.filename):
                    relPath = self._getTextureMapResourcePathOrDefault( textureMap, None )
                    fullPath = mtmaxconfig.exportRoot + '/' + relPath
                    
                    if self.outPath.hash != None:
                        texPath = fullPath + '.241f5deb.tex'
                    else:
                        texPath = fullPath + '.tex'
                    if mtmaxconfig.exportOverwriteTextures or not os.path.exists(texPath):
                        maxlog.info('converting texture to TEX')
                        self._convertTextureToTEX( textureMap.filename, texPath )
                    else:
                        maxlog.info(f'skipping texture conversion because {texPath} already exists')
                else:
                    maxlog.info(f'skipping texture conversion because {textureMap.filename} does not exist')
            elif rt.classOf( textureMap ) == rt.Normal_Bump:
                self._exportTextureMapSafe( textureMap, 'normal_map' )
                self._exportTextureMapSafe( textureMap, 'bump_map' )
            else:
                maxlog.warn(f'unknown texture map type: {rt.classOf( textureMap )}')
                
    def _exportTextureMapSafe( self, material, textureMapName ):
        materialName = getattr(material, "name", None)
        if hasattr( material, textureMapName ):
            if getattr( material, textureMapName, None ) != None:
                self._exportTextureMap( getattr( material, textureMapName ) )
            else:
                maxlog.debug( f'material "{materialName}" texture map "{textureMapName}" not exported because it has not been assigned')
        else:
            maxlog.debug( f'material "{materialName}" texture map "{textureMapName}" not exported because it does not exist on the material')
            
     
    def _getTextureMapResourcePathOrDefault( self, textureMap, default ):
        if textureMap == None: return default
        path = util.ResourcePath( textureMap.filename, rootPath=mtmaxconfig.exportRoot )
        if self.outPath.relBasePath != None:
            # take the relative directory path of the model and append the name of the texture
            result = self.outPath.relBasePath + '/' + path.baseName
        else:
            # because the model output path is not relative to the root, we put the texture at the root
            # the user will likely have to fix this
            result = path.baseName
        result = result.replace('/', '\\')
        return result
    
    def _getTextureMapResourcePathOrDefaultSafe( self, material, textureMap, default ):
        return self._getTextureMapResourcePathOrDefault( getattr( material, textureMap, None ), default )
    
    def _copyUsedDefaultTexturesToOutput( self, material ):
        for map in material.iterTextures():
            if imMaterialInfo.isDefaultTextureMap( map ):
                # make sure to export the default textures whenever they are used
                defaultMapTexPath = os.path.join( util.getResourceDir(), 'textures', map + ".tex" )
                
                # always expected to be at the root
                defaultMapTexExportPath = os.path.join( mtmaxconfig.exportRoot, map + '.tex' ) if self.outPath.hash == None else \
                                            os.path.join( mtmaxconfig.exportRoot, map + '.241f5deb.tex' )

                shutil.copy( defaultMapTexPath, defaultMapTexExportPath )
    
    def _processMaterial_PBRSpecGloss( self, material ):
        assert rt.classOf( material ) == rt.PBRSpecGloss
        
        materialInstance = None
        if mtmaxconfig.exportGenerateMrl:
            # create material instance
            normalMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'norm_map', imMaterialInfo.DEFAULT_NORMAL_MAP )
            albedoMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP )
            specularMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'specular_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
            materialInstance = imMaterialInfo.createDefault( material.name, 
                normalMap=normalMap,
                albedoMap=albedoMap,
                specularMap=specularMap,
            )

        if mtmaxconfig.exportTexturesToTex:
            self._exportTextureMapSafe( material, 'base_color_map' )
            self._exportTextureMapSafe( material, 'specular_map' )
            self._exportTextureMapSafe( material, 'glossiness_map' )
            self._exportTextureMapSafe( material, 'ao_map' )
            self._exportTextureMapSafe( material, 'norm_map' )
            self._exportTextureMapSafe( material, 'emit_color_map' )
            self._exportTextureMapSafe( material, 'opacity_map' )
            self._exportTextureMapSafe( material, 'displacement_map' )
            
        return materialInstance
    
    def _processMaterial_PhysicalMaterial( self, material ):
        assert rt.classOf( material ) == rt.PhysicalMaterial
        
        materialInstance = None
        if mtmaxconfig.exportGenerateMrl:
            # create material instance
            if getattr( material, 'bump_map', None ) != None and rt.classOf( material.bump_map ) == rt.Normal_Bump:
                normalMap = self._getTextureMapResourcePathOrDefaultSafe( material.bump_map, 'normal', imMaterialInfo.DEFAULT_NORMAL_MAP )
            else:
                # TODO handle different normal map assignments?
                normalMap = imMaterialInfo.DEFAULT_NORMAL_MAP
            
            albedoMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP )
            # TODO is metalness correct for specular?
            specularMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'metalness_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
            materialInstance = imMaterialInfo.createDefault( material.name, 
                normalMap=normalMap,
                albedoMap=albedoMap,
                specularMap=specularMap,
            )

        if mtmaxconfig.exportTexturesToTex:
            self._exportTextureMapSafe( material, 'base_weight_map' )
            self._exportTextureMapSafe( material, 'base_color_map' )
            self._exportTextureMapSafe( material, 'reflectivity_map' )
            self._exportTextureMapSafe( material, 'refl_color_map' )
            self._exportTextureMapSafe( material, 'metalness_map' )
            self._exportTextureMapSafe( material, 'diff_rough_map' )
            self._exportTextureMapSafe( material, 'anisotropy_map' )
            self._exportTextureMapSafe( material, 'aniso_angle_map' )
            self._exportTextureMapSafe( material, 'transparency_map' )
            self._exportTextureMapSafe( material, 'trans_color_map' )
            self._exportTextureMapSafe( material, 'trans_rough_map' )
            self._exportTextureMapSafe( material, 'trans_ior_map' )
            self._exportTextureMapSafe( material, 'scattering_map' )
            self._exportTextureMapSafe( material, 'sss_color_map' )
            self._exportTextureMapSafe( material, 'sss_scale_map' )
            self._exportTextureMapSafe( material, 'emission_map' )
            self._exportTextureMapSafe( material, 'emit_color_map' )
            self._exportTextureMapSafe( material, 'coat_map' )
            self._exportTextureMapSafe( material, 'coat_color_map' )
            self._exportTextureMapSafe( material, 'bump_map' )
            self._exportTextureMapSafe( material, 'coat_rough_map' )
            self._exportTextureMapSafe( material, 'displacement_map' )
            self._exportTextureMapSafe( material, 'cutout_map' )
            
        return materialInstance
     
    def _processMaterial( self, material ):
        if material not in self._materialCache:
            # add to cache
            self._materialCache[material] = True
            
            maxlog.info(f'processing material: {material.name}')
            materialInstance = None
            if rt.classOf( material ) == rt.PBRSpecGloss:
                materialInstance = self._processMaterial_PBRSpecGloss( material )
            elif rt.classOf( material ) == rt.PhysicalMaterial:
                materialInstance = self._processMaterial_PhysicalMaterial( material )
            else:
                maxlog.error( f"unsupported material type: {rt.classOf( material )}" )
                return
            
            if materialInstance != None:
                self._copyUsedDefaultTexturesToOutput( materialInstance )
                self.mrl.materials.append( materialInstance )
                
    def _getMaterialName( self, material ):
        if material == None:
            return 'default_material'
        else:
            return material.name
            
    def _processMesh( self, maxNode ):
        maxlog.info(f'processing mesh: {maxNode.name}')
        attribs = MtPrimitiveAttribData(maxNode)
            
        if mtmaxconfig.exportWeights:
            maxlog.debug('getting skin modifier')
            maxSkin = maxNode.modifiers[rt.Name('Skin')]
            hasSkin = maxSkin != None
            if hasSkin:
                # fix unrigged vertices
                maxSkin.weightAllVertices = False
                maxSkin.weightAllVertices = True
                # node arg is ignored
                #rt.skinOps.removeZeroWeights( maxSkin, node=maxNode )
        else:
            hasSkin = False

        editNormalsMod = maxNode.modifiers[rt.Name('Edit_Normals')]
        
        # collect all vertex data per material
        maxlog.debug('collecting vertex data')
        maxMesh = rt.snapshotAsMesh( maxNode )
        faceCount = rt.getNumFaces( maxMesh )
        tempMeshes = dict()

        for i in range( 0, faceCount ):
            face = rt.getFace( maxMesh, i + 1 )
            tvFace = rt.getTVFace( maxMesh, i + 1 )
            matId = rt.getFaceMatID( maxMesh, i + 1 ) 
            material = maxNode.material[matId-1] if rt.classOf(maxNode.material) == rt.Multimaterial else maxNode.material
            
            for j in range( 0, 3 ):
                vertIdx = face[j]
                tvertIdx = tvFace[j]

                if matId not in tempMeshes:
                    # create temporary mesh for this material
                    tempMeshes[matId] = imPrimitive(
                        maxNode.name,
                        self._getMaterialName( material ),
                    )

                tempMesh = tempMeshes[matId]
                if material != None:
                    self._processMaterial( material )
                
                pos = self._convertMaxPoint3ToNclVec4( rt.getVert( maxMesh, vertIdx ) )
                pos = pos * self.transformMtx # needed with reference model
                pos = NclVec3( pos[0], pos[1], pos[2] )
                tempMesh.positions.append( pos )
                
                if editNormalsMod != None:
                    temp = editNormalsMod.GetNormal( editNormalsMod.GetNormalId( i + 1, j + 1 ) )
                    if temp == None:
                        # TODO figure out why this happens
                        # my guess is that it only returns normals that have been explicitly set with the modifier
                        temp = rt.getNormal( maxMesh, vertIdx )
                    nrm = self._convertMaxPoint3ToNclVec4( temp )
                else:
                    nrm = self._convertMaxPoint3ToNclVec4( rt.getNormal( maxMesh, vertIdx ) )
                nrm = nclNormalize( nrm * self.transformMtxNormal )
                nrm = NclVec3( nrm[0], nrm[1], nrm[2] )
                tempMesh.normals.append( nrm )
                
                tempMesh.uvs.append( self._convertMaxPoint3ToNclVec3UV( rt.getTVert( maxMesh, tvertIdx ) ) )

                if hasSkin:
                    weightCount = rt.skinOps.getVertexWeightCount( maxSkin, vertIdx, node=maxNode )
                    weight = imVertexWeight()
                    for k in range( 0, weightCount ):
                        boneId = rt.skinops.getVertexWeightBoneId( maxSkin, vertIdx, k + 1, node=maxNode )
                        boneWeight = rt.skinOps.getVertexWeight( maxSkin, vertIdx, k + 1, node=maxNode )
                        boneName = rt.skinOps.getBoneName( maxSkin, boneId, 0, node=maxNode )
                        if boneName not in self.jointIdxByName:
                            raise RuntimeError(f'mesh "{maxNode.name}" references bone "{boneName}" that does not exist in the skeleton' )
                            
                        jointIdx = self.jointIdxByName[ boneName ]
                        weight.weights.append( boneWeight )
                        weight.indices.append( jointIdx )
                    if tempMesh.weights == None:
                        tempMesh.weights = []
                    tempMesh.weights.append( weight )
                else:
                    # TODO fix this hack
                    weight = imVertexWeight()
                    weight.weights.append( 1 )
                    weight.indices.append( 2 )
                    if tempMesh.weights == None:
                        tempMesh.weights = []
                    tempMesh.weights.append( weight )

        # create optimized primitives
        for tempMesh in tempMeshes.values():
            prim: imPrimitive = tempMesh
            maxlog.info(f'processing submesh with material {prim.materialName}')

            # copy over attribs
            if attribs.flags != None: prim.flags = attribs.flags
            if attribs.groupId != None: 
                group = self.model.getGroupById(attribs.groupId)
                if group == None:
                    # add group
                    group = imGroup(self.metadata.getGroupName(attribs.groupId), attribs.groupId, 0, 0, 0, boundingSphere=NclVec4())
                    self.model.groups.append(group)
                prim.group = group
                    
            if attribs.lodIndex != None: prim.lodIndex = attribs.lodIndex
            if attribs.renderFlags != None: prim.renderFlags = attribs.renderFlags
            if attribs.id != None: prim.id = attribs.id
            if attribs.field2c != None: prim.field2c = attribs.field2c

            prim.generateTangents()
            prim.makeIndexed()
            self.model.primitives.append( prim )
        
    def _processMeshes( self ):
        if not mtmaxconfig.exportPrimitives:
            maxlog.info('exporting meshes skipped because it has been disabled through the config')
            return
        
        # convert meshes
        maxlog.info('processing meshes')
        for maxNode in self._getObjects():
            if not self._shouldExportNode( maxNode ) or not self._isMeshNode( maxNode ):
                continue
            
            mtmaxutil.updateUI()
            self._processMesh( maxNode )

    def _processGroups( self ):
        if not mtmaxconfig.exportGroups:
            maxlog.info('exporting groups skipped because it has been disabled through the config')
            return
        
        maxlog.info('processing groups')
        if self.ref != None and mtmaxconfig.exportUseRefGroups:
            maxlog.info('copying groups from reference model')
            for i, refGroup in enumerate(self.ref.groups):
                group = imGroup(
                    name=self.metadata.getGroupName(refGroup.id),
                    id=refGroup.id,
                    field04=refGroup.field04,
                    field08=refGroup.field08,
                    field0c=refGroup.field0c,
                    boundingSphere=refGroup.boundingSphere,
                )
                #maxlog.debug(str(group))
                self.model.groups.append(group)
        else:
            # process all groups in the scene
            for maxNode in self._getObjects():
                if not self._shouldExportNode( maxNode ) or not self._isGroupNode( maxNode ):
                    continue
                
                maxlog.info(f'processing group node {maxNode}')
                attribs = MtGroupAttribData(maxNode)
                group = imGroup(
                    name=maxNode.name,
                    id=attribs.id,
                    field04=attribs.field04 if attribs.field04 != None else 0,
                    field08=attribs.field08 if attribs.field08 != None else 0,
                    field0c=attribs.field0c if attribs.field0c != None else 0,
                    #TODO fix this
                    #boundingSphere=attribs.bsphere if attribs.bsphere != None else None,
                )
                #maxlog.debug(str(group))

    def _processPml( self ):
        if not mtmaxconfig.exportPml:
            maxlog.info('exporting pml skipped because it has been disabled through the config')
            return
        
        maxlog.info('processing pml')
        if self.ref != None and mtmaxconfig.exportUseRefPml:
            maxlog.info('copying pml from reference model')
            for i, refPml in enumerate(self.ref.primitiveJointLinks):
                pml = imPrimitiveJointLink(
                    name='pml_'+str(i),
                    joint=self.model.joints[refPml.jointIndex],
                    field04=refPml.field04,
                    field08=refPml.field08,
                    field0c=refPml.field0c,
                    boundingSphere=refPml.boundingSphere,
                    min=refPml.min,
                    max=refPml.max,
                    localMtx=refPml.localMtx,
                    field80=refPml.field80
                )
                #maxlog.debug(str(pml))
                self.model.primitiveJointLinks.append(pml)
        else:
            # TODO: represent these in the scene
            maxlog.debug("exporting pml from scene not implemented")
    
    def _writeBinaries( self ):
        maxlog.debug('converting intermediate model to binary model format')
        binMod = self.model.toBinaryModel()
        
        maxlog.debug('writing binary model')
        stream = NclBitStream()
        binMod.write( stream )
        try:
            util.saveByteArrayToFile( self.outPath.fullPath, stream.getBuffer() )
        except PermissionError as e:
            maxlog.error( f"unable to save mod file, make sure you have write permissions to {self.outPath.fullPath}" )
        
        if self.outPath.hash != None:
            mrlExportPath = self.outPath.basePath + '/' + self.outPath.baseName + '.2749c8a8.mrl' 
        else:
            mrlExportPath = self.outPath.basePath + '/' + self.outPath.baseName + '.mrl'
            
        if mtmaxconfig.exportGenerateMrl:
            mrlYmlExportPath = mrlExportPath + ".yml"
            maxlog.info(f"writing generated mrl yml to {mrlYmlExportPath}")
            self.mrl.updateTextureList()
            try:
                self.mrl.saveYamlFile( mrlYmlExportPath )
            except PermissionError as e:
                maxlog.error( f"unable to save mrl yml file, make sure you have write permissions to {mrlYmlExportPath}" )
            
        if mtmaxconfig.exportGenerateMrl or (mtmaxconfig.exportExistingMrlYml and self.mrl != None):
            maxlog.info(f'exporting mrl yml to {mrlExportPath}')
            
            try:
                self.mrl.saveBinaryFile( mrlExportPath )
            except PermissionError as e:
                maxlog.error( f"unable to save mrl file, make sure you have write permissions to {mrlExportPath}" )
    
    def _calcTransformMtx( self ):
        mtx = nclCreateMat44()
        if mtmaxconfig.flipUpAxis:
            #mtx *= nclCreateMat44((NclVec4((1,  0,  0, 0)),  # x=x
            #                       NclVec4((0,  1, 0, 0)),  # y=-z
            #                       NclVec4((0,  0,  1, 0)),  # z=y
            #                       NclVec4((0,  0,  0, 1))))
            
            #mtx *= util.Z_TO_Y_UP_MATRIX
            mtx *= util.Y_TO_Z_UP_MATRIX # why? should be z to y up. needed with reference model
        if mtmaxconfig.scale != 1:
            mtx *= nclScale( mtmaxconfig.scale )
        return mtx
    
    def exportModel( self, path ):
        maxlog.info(f'exporting to {path}')
        
        # start building intermediate model data for conversion
        self.model = imModel()
        self.outPath = util.ResourcePath(path, rootPath=mtmaxconfig.exportRoot)
        self.metadata = ModelMetadata()
        self.mrl = None
        self.transformMtx = self._calcTransformMtx()
        self.transformMtxNormal = nclTranspose( nclInverse( self.transformMtx ) )

        if os.path.exists( mtmaxconfig.exportMetadataPath ):
            maxlog.info(f'loading metadata file from {mtmaxconfig.exportMetadataPath}')
            self.metadata.loadFile( mtmaxconfig.exportMetadataPath )

        if os.path.exists( mtmaxconfig.exportRefPath ):
            maxlog.info(f'loading reference model from {mtmaxconfig.exportRefPath}')
            self.ref = rModelData()
            self.ref.read( NclBitStream( util.loadIntoByteArray( mtmaxconfig.exportRefPath ) ) )
            
        if os.path.exists( mtmaxconfig.exportMrlYmlPath ):
            maxlog.info(f'loading mrl yml from {mtmaxconfig.exportMrlYmlPath}')
            self.mrl = imMaterialLib()
            self.mrl.loadYamlFile( mtmaxconfig.exportMrlYmlPath )
        elif mtmaxconfig.exportGenerateMrl:
            maxlog.info(f'generating new mrl')
            self.mrl = imMaterialLib()
            
        maxlog.debug('creating output directories')
        if not os.path.exists( mtmaxconfig.exportRoot ):
            os.makedirs( mtmaxconfig.exportRoot )
        if not os.path.exists( os.path.dirname( mtmaxconfig.exportFilePath ) ):
            os.makedirs( mtmaxconfig.exportFilePath )

        maxlog.info('processing scene')
        if self.ref != None and mtmaxconfig.exportUseRefBounds:
            # copy over header values
            maxlog.debug('copying over header values from reference model')
            self.model.field90 = self.ref.header.field90
            self.model.field94 = self.ref.header.field94
            self.model.field98 = self.ref.header.field98
            self.model.field9c = self.ref.header.field9c
            self.model.center = self.ref.header.center
            self.model.max = self.ref.header.max
            self.model.min = self.ref.header.min
            self.model.radius = self.ref.header.radius
        
        self._processBones()
        self._processGroups()
        self._processMeshes()
        self._processPml()
        
        maxlog.info('writing files')
        self._writeBinaries()
        
        maxlog.info('export completed successfully')