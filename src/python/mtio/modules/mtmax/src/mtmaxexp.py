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
            self.field03 = 0
            self.field04 = 0

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
        return rt.classOf( node ) in [rt.Editable_mesh, rt.Editable_poly]

    def _isGroupNode( self, node ):
        '''Returns if the node represents a group'''

        # group nodes may have group attrib data
        if hasattr(node, 'mtModelGroupAttributes'):
            return True
        
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
        return rt.classOf( node ) == rt.BoneGeometry
    
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
            id=attribs.id, 
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
                
    def _convertTextureToTEX( self, inPath, outPath, origPath, forcedFormat ):
        # TODO this code is almost the same as the code in mttexconv
        basePath, baseName, exts = util.splitPath( inPath )
        inExt = exts[len(exts) - 1]
        
        inDDSBasePath = basePath
        inDDSPath = os.path.join( basePath, baseName )
        if len(exts) > 1:
            for i in range(0, len(exts) - 1):
                inDDSPath += '.' + exts[i]
        inDDSPath += '.DDS'
        
        if outPath == None:
            outPath = os.path.join( basePath, baseName )
            if len(exts) > 1:
                for i in range(0, len(exts) - 1):
                    outPath += '.' + exts[i]
            
            outExt = 'tex'
            if inExt == 'tex':
                outExt = 'dds'
            outPath += '.' + outExt
                
        outBasePath, outBaseName, outExts = util.splitPath( outPath )

        
        outExt = outExts[len(outExts) - 1]
        
        origTex = None
        if origPath != None and origPath != '':
            origTex = rTextureData()
            origTex.loadBinaryFile( origPath )
            
        # detect format from name
        fmt = forcedFormat
        if fmt == '' or fmt == None:
            if origTex != None:
                fmt = origTex.header.fmt.surfaceFmt
            else:
                fmt = rTextureSurfaceFmt.getFormatFromTextureName( baseName, True )
                if fmt == None:
                    # not detected, fallback
                    fmt = rTextureSurfaceFmt.BM_OPA
        
        convert = True
        if inExt.lower() == 'dds':
            # check if DDS format matches
            fmtDDS = rTextureSurfaceFmt.getDDSFormat( fmt )
            dds = DDSFile.fromFile( inPath )
            if dds.header.ddspf.dwFourCC == fmtDDS:
                # don't need to convert to proper format
                convert = False
                
        if convert:  
            # convert file to DDS with texconv
            fmtDDS = rTextureSurfaceFmt.getDDSFormat( fmt )
            fmtDDSName = ''
            if fmtDDS == DDS_FOURCC_DXT1:
                fmtDDSName = 'DXT1'
            elif fmtDDS == DDS_FOURCC_DXT2:
                fmtDDSName = 'DXT2'
            elif fmtDDS == DDS_FOURCC_DXT3:
                fmtDDSName = 'DXT3'
            elif fmtDDS == DDS_FOURCC_DXT4:
                fmtDDSName = 'DXT4'
            elif fmtDDS == DDS_FOURCC_DXT5:
                fmtDDSName = 'DXT5'
            else:
                raise Exception("Unhandled dds format: " + str(fmtDDS))
            
            maxlog.info( 'converting input {} to DDS {}'.format(inPath, inDDSPath))
            maxlog.debug( 'DDS format: {}'.format( fmtDDSName ) )
            maxlog.debug( '\ntexconv start')
            texconv.texconv( inPath, outPath=inDDSBasePath, fileType='DDS', featureLevel=9.1, pow2=True, fmt=fmtDDSName, overwrite=True, srgb=True )
            maxlog.debug( 'texconv end\n')
        
        maxlog.info('converting DDS {} to TEX {}'.format( inDDSPath, outPath ))
        maxlog.debug('TEX format: {}'.format(fmt))
        dds = DDSFile.fromFile( inDDSPath )
        tex = rTextureData.fromDDS( dds )
        tex.header.fmt.surfaceFmt = fmt
        
        # copy faces from original cubemap if needed
        if origTex != None: 
            for face in origTex.faces:
                tex.faces.append( face )
        
        try:
            tex.saveBinaryFile( outPath )
        except PermissionError as e:
            maxlog.error( f"unable to save tex file, make sure you have write permissions to {outPath}" )
            
    def _processTextureMap( self, textureMap ):
        if textureMap != None and not textureMap in self._textureMapCache:
            # add to cache
            self._textureMapCache[textureMap] = True
            
            maxlog.info(f'processing texture: {textureMap.filename}')
            if os.path.exists(textureMap.filename):
                relPath = self._getTextureMapRelPathOrDefault( textureMap, None )
                fullPath = mtmaxconfig.exportRoot + '/' + relPath
                
                if self.outPath.hash != None:
                    texPath = fullPath + '.241f5deb.tex'
                else:
                    texPath = fullPath + '.tex'
                if not os.path.exists(texPath):
                    maxlog.info('converting texture to TEX')
                    self._convertTextureToTEX( textureMap.filename, texPath, None, None )
                else:
                    maxlog.info(f'skipping texture conversion because {texPath} already exists')
            else:
                maxlog.info(f'skipping texture conversion because {textureMap.filename} does not exist')
     
    def _getTextureMapRelPathOrDefault( self, textureMap, default ):
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
        print(result)
        return result
                
    def _getMaterialTextureMapRelPathOrDefault( self, material, textureMapName, default ):
        if not hasattr(material, textureMapName) or getattr(material, textureMapName) == None: return default
        return self._getTextureMapRelPathOrDefault( getattr(material, textureMapName), default )
     
    def _processMaterial( self, material ):
        if material not in self._materialCache:
            # add to cache
            self._materialCache[material] = True
            
            maxlog.info(f'processing material: {material.name}')
            
            if mtmaxconfig.exportGenerateMrl:
                self.mrl.materials.append(
                    imMaterialInfo.createDefault( material.name, 
                        normalMap=self._getMaterialTextureMapRelPathOrDefault( material, 'norm_map', imMaterialInfo.DEFAULT_NORMAL_MAP ),
                        albedoMap=self._getMaterialTextureMapRelPathOrDefault( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP ),
                        specularMap=self._getMaterialTextureMapRelPathOrDefault( material, 'specular_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
                        )
                    )
            
            if mtmaxconfig.exportTexturesToTex:
                if hasattr(material, 'base_color_map'): self._processTextureMap( material.base_color_map )
                if hasattr(material, 'specular_map'): self._processTextureMap( material.specular_map )
                if hasattr(material, 'glossiness_map' ): self._processTextureMap( material.glossiness_map )
                if hasattr(material, 'ao_map' ): self._processTextureMap( material.ao_map )
                if hasattr(material, 'norm_map' ): self._processTextureMap( material.norm_map )
                if hasattr(material, 'emit_color_map' ): self._processTextureMap( material.emit_color_map )
                if hasattr(material, 'opacity_map' ): self._processTextureMap( material.opacity_map )
                if hasattr(material, 'displacement_map' ): self._processTextureMap( material.displacement_map )
                
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
            rt.execute('max modify mode')
            rt.select( maxNode )
            maxSkin = rt.modPanel.getCurrentObject()
            hasSkin = rt.isKindOf( maxSkin, rt.Skin )
            if hasSkin:
                # fix unrigged vertices
                maxSkin.weightAllVertices = False
                maxSkin.weightAllVertices = True
                rt.skinOps.removeZeroWeights( maxSkin )
        else:
            hasSkin = False

        if mtmaxconfig.exportNormals:
            maxlog.debug('adding temporary edit normals modifier to get the proper vertex normals')
            editNormalsMod = rt.Edit_Normals()
            rt.addModifier( maxNode, editNormalsMod )
        
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
                tempMesh.positions.append( pos )
                
                if mtmaxconfig.exportNormals:
                    temp = editNormalsMod.GetNormal( editNormalsMod.GetNormalId( i + 1, j + 1 ) )
                    if temp == None:
                        # TODO figure out why this happens
                        # my guess is that it only returns normals that have been explicitly set with the modifier
                        temp = rt.getNormal( maxMesh, vertIdx )
                    nrm = self._convertMaxPoint3ToNclVec4( temp )
                else:
                    nrm = self._convertMaxPoint3ToNclVec4( rt.getNormal( maxMesh, vertIdx ) )
                nrm = nrm * self.transformMtx # needed with reference model
                tempMesh.normals.append( nrm )
                
                tempMesh.uvs.append( self._convertMaxPoint3ToNclVec3UV( rt.getTVert( maxMesh, tvertIdx ) ) )

                if hasSkin:
                    weightCount = rt.skinOps.getVertexWeightCount( maxSkin, vertIdx )
                    weight = imVertexWeight()
                    for k in range( 0, weightCount ):
                        boneId = rt.skinops.getVertexWeightBoneId( maxSkin, vertIdx, k + 1 )
                        boneWeight = rt.skinOps.getVertexWeight( maxSkin, vertIdx, k + 1 )
                        boneName = rt.skinOps.getBoneName( maxSkin, boneId, 0 )
                        jointIdx = self.jointIdxByName[ boneName ]
                        weight.weights.append( boneWeight )
                        weight.indices.append( jointIdx )
                    tempMesh.weights.append( weight )
                else:
                    # TODO is this correct?
                    weight = imVertexWeight()
                    weight.weights.append( 1 )
                    weight.indices.append( 2 )
                    tempMesh.weights.append( weight )

        # remove temporary modifiers
        if mtmaxconfig.exportNormals:
            maxlog.debug('delete temporary edit normals modifier')
            rt.deleteModifier( maxNode, editNormalsMod )

        # create optimized primitives
        for tempMesh in tempMeshes.values():
            prim: imPrimitive = tempMesh
            maxlog.info(f'processing submesh with material {prim.materialName}')

            # copy over attribs
            if attribs.flags != None: prim.flags = attribs.flags
            if attribs.groupId != None: prim.group = self.model.getGroupById(attribs.groupId)
            if attribs.lodIndex != None: prim.lodIndex = attribs.lodIndex
            if attribs.renderFlags != None: prim.renderFlags = attribs.renderFlags
            if attribs.id != None: prim.id = attribs.id
            if attribs.field2c != None: prim.field2c = attribs.field2c

            prim.makeIndexed()
            prim.generateTangents()
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