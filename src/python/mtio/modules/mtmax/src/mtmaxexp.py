import os
from posixpath import relpath, split
import sys
from typing import List, Tuple
from copy import deepcopy

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
import mtmaxutil
from mtlib import texconv
import mtmaxlog
import shutil
from mtlib import textureutil
from mtlib import util
import mtmaxver
from mtmax.src import MtMaxModelExportRollout

def _tryParseInt(input, base=10, default=None):
    try:
        return int(str(input).strip(), base=base)
    except Exception:
        return default
    
def _tryParseFloat(input, default=None):
    try:
        return float(str(input).strip())
    except Exception:
        return default
    
def _updateProgress( what, value, count = 0 ):
    rollout = MtMaxModelExportRollout.getMxsVar()
    rollout.pbExport.value = value if count == 0 else (value/count) * 100
    rollout.lblExportProgressCategory.text = what
    
def _updateSubProgress( what, value, count = 0 ):
    rollout = MtMaxModelExportRollout.getMxsVar()
    rollout.pbExportSub.value = value if count == 0 else (value/count) * 100
    rollout.lblExportProgressSubCategory.text = what
    
def _progressCallback( what, i, count ):
    if mtmaxutil.updateUI():
        mtmaxlog.info( what + f' {i}/{count}' )
        _updateSubProgress( what, i, count )

class MtGroupAttribData(object):
    '''Wrapper for group custom attribute data'''
    def __init__( self, maxNode ):
        attribs = maxNode.MtMaxGroupAttributes if hasattr(maxNode, 'MtMaxGroupAttributes') else None
        if attribs != None:
            self.id = _tryParseInt(attribs.id)
            self.field04 = _tryParseInt(attribs.field04)
            self.field08 = _tryParseInt(attribs.field08)
            self.field0c = _tryParseInt(attribs.field0c)
            self.bsphere = NclVec4(attribs.bsphere[0], attribs.bsphere[1], attribs.bsphere[2], attribs.bsphere[3])
            self.index = _tryParseInt(getattr(attribs, 'index', None))
        else:
            self.id = None
            self.field04 = None
            self.field08 = None
            self.field0c = None
            self.bsphere = None
            self.index = None

class MtPrimitiveAttribData(object):
    '''Wrapper for primitive custom attribute data'''
    def __init__( self, maxNode ):
        attribs = maxNode.MtPrimitiveAttributes if hasattr(maxNode, 'MtPrimitiveAttributes') else None
        if attribs != None:
            self.flags = _tryParseInt(attribs.flags, base=0)
            if attribs.groupId == "inherit":
                if maxNode.parent != None:
                    self.groupId = MtGroupAttribData(maxNode.parent).id
                else:
                    # invalid
                    self.groupId = None
            else:
                self.groupId = _tryParseInt(attribs.groupId, base=0)
            self.lodIndex = _tryParseInt(attribs.lodIndex)
            self.renderFlags = _tryParseInt(attribs.renderFlags, base=0)
            self.id = _tryParseInt(attribs.id)
            self.field2c = _tryParseInt(attribs.field2c)
            self.primitiveJointLinkCount = _tryParseInt(getattr(attribs, 'primitiveJointLinkCount', None))
            self.primitiveJointLinkIndex = _tryParseInt(getattr(attribs, 'primitiveJointLinkIndex', None))
            self.index = _tryParseInt(getattr(attribs, 'index', None))
            self.vertexShader = attribs.shaderName
        else:
            self.flags = None
            self.groupId = None
            self.lodIndex = None
            self.renderFlags = None
            self.id = None
            self.field2c = None
            self.primitiveJointLinkCount = None
            self.primitiveJointLinkIndex = None
            self.index = None
            self.vertexShader = None
            
            if maxNode.parent != None:
                # even if no attribs are set, we should still inherit the group id if the mesh is parented to a group
                self.groupId = MtGroupAttribData(maxNode.parent).id

class MtJointAttribData(object):
    '''Wrapper for joint custom attribute data'''
    def __init__( self, maxNode, jointMeta ):
        name: str = maxNode.name
        attribs = maxNode.MtMaxJointAttributes if hasattr(maxNode, 'MtMaxJointAttributes') else None
        if attribs != None:
            # grab attributes from custom attributes on node
            self.id = _tryParseInt(attribs.id)
            self.symmetryNode = rt.getNodeByName( attribs.symmetryName )
            # auto detect if symmetry node is not found and symmetry name is set to 'auto'
            if self.symmetryNode == None and attribs.symmetryName == "auto":
                self.symmetryNode = self._detectSymmetryNode( name )
            self.field03 = _tryParseInt(attribs.field03)
            self.field04 = _tryParseFloat(attribs.field04)
            self.length = _tryParseFloat(attribs.length)
            self.offsetX = _tryParseFloat(attribs.offsetX)
            self.offsetY = _tryParseFloat(attribs.offsetY)
            self.offsetZ = _tryParseFloat(attribs.offsetZ)
            self.index = _tryParseInt(getattr(attribs, 'index', None))
        else:
            if jointMeta != None:
                self.id = jointMeta.id
            else:
                self.id = None
                
            self.symmetryNode = self._detectSymmetryNode( name )
            self.field03 = None
            self.field04 = None
            self.length = None
            self.offsetX = None
            self.offsetY = None
            self.offsetZ = None
            self.index = None
            
    def _detectSymmetryNode( self, name: str ):
        return rt.getNodeByName( util.replaceSuffix( name, "_l", "_r" ) ) if name.endswith("_l") else \
               rt.getNodeByName( util.replaceSuffix( name, "_r", "_l" ) ) if name.endswith("_r") else \
               rt.getNodeByName( util.replaceSuffix( name, "_L", "_R" ) ) if name.endswith("_L") else \
               rt.getNodeByName( util.replaceSuffix( name, "_R", "_L" ) ) if name.endswith("_R") else \
               rt.getNodeByName( util.replaceSuffix( name, "L", "R" ) ) if name.endswith("L") else \
               rt.getNodeByName( util.replaceSuffix( name, "R", "L" ) ) if name.endswith("R") else \
               None

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
        self._transformMtx = None
        self._processedNodes = set()
        self._refPrimitiveJointLinks = []
        
    def _convertMaxPoint3ToNclVec3( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], v[1], v[2]))

    def _convertMaxPoint3ToNclVec3UV( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], 1 - v[1], v[2]))
        
    def _convertMaxPoint3ToNclVec4( self, v: rt.Point3, w ) -> NclVec3:
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
    
    '''
    Table of node types
    Modifier                    classOf                                                 superClassOf
    Bone                        BoneGeometry                                            GeometryClass
    Editable Mesh / Edit Mesh   Editable_mesh                                           GeometryClass
    Editable Poly / Edit Poly   PolyMeshObject, Editable_poly                           GeometryClass
    Biped Object                Biped_Object                                            GeometryClass
    Line                        line                                                    shape
    Dummy (Group)               Dummy                                                   helper
    Dummy (Bone)                Dummy                                                   helper
    '''

    def _isMeshNode( self, node ):
        '''Returns if the node is a mesh'''

        # node is considered a mesh of it is an editable mesh or editable poly
        # TODO: investigate other possible types
        return rt.classOf( node ) in [rt.Editable_mesh, rt.Editable_poly, rt.PolyMeshObject]

    def _isGroupNode( self, node ):
        '''Returns if the node represents a group'''
        
        # Groups have the same types as bones (Dummy), so we must
        # take extra care to disambiguate
        
        # groups should be a dummy node
        if rt.classOf( node ) not in [rt.Dummy]:
            return False
        
        # definitely not a group if it has joint attributes
        if hasattr( node, 'MtMaxJointAttributes' ):
            return False

        # definitely a group if it has group attributes
        if hasattr( node, 'MtMaxGroupAttributes' ):
            return True
        
        # a group should not be parented to anything
        if node.parent != None:
            return False
        
        # we can't determine the type based on the children if there are none
        # so assume it's not a group
        if len(node.children) == 0:
            return False
        
        # only meshes should be parented to groups
        # this doesn't allow empty groups, however the previous clauses 
        # should cover those
        for child in node.children:
            if not self._isMeshNode( child ):
                return False

        return True

    def _isBoneNode( self, node ):
        '''Returns if the node is a bone'''

        # node is considered a bone node of it's bone geometry (helper)
        return rt.classOf( node ) in [rt.BoneGeometry, rt.Dummy, rt.Biped_Object] and not self._isGroupNode( node )
    
    def _isSplineNode( self, node ):
        '''Return sif the node is spline shape'''
        
        return rt.superClassOf( node ) in [rt.shape]
    
    def _getObjects( self ):
        # return a list of scene objects as opposed to enumerating directly to prevent crashes
        temp = list(rt.objects)
        objects = []
        for o in temp:
            if not o in self._processedNodes:
                objects.append( o )
        return objects
    
    def _getNodeWorldMtx( self, maxNode ):
        worldMtx = self._convertMaxMatrix3ToNclMat44( maxNode.transform )
        if mtmaxconfig.exportBakeScale:
            worldMtx[3] *= NclVec4((mtmaxconfig.exportScale, mtmaxconfig.exportScale, mtmaxconfig.exportScale, 1))
        return worldMtx
    
    def _getNodeLocalMtx( self, maxNode ):
        worldMtx = self._convertMaxMatrix3ToNclMat44( maxNode.transform )
        parentWorldMtx = self._convertMaxMatrix3ToNclMat44( maxNode.parent.transform ) if maxNode.parent != None else nclCreateMat44()
        localMtx = nclMultiply( worldMtx, nclInverse( parentWorldMtx ) )
        if mtmaxconfig.exportBakeScale:
            localMtx[3] *= NclVec4((mtmaxconfig.exportScale, mtmaxconfig.exportScale, mtmaxconfig.exportScale, 1))
            if maxNode.parent == None:
                localMtx = self._transformMtxNoScale * localMtx
        else:
            if maxNode.parent == None:
                localMtx = self._transformMtx * localMtx
        return localMtx

    def _processBone( self, maxNode ): 
        assert( self._isBoneNode( maxNode ) )

        if maxNode in self.maxNodeToJointMap:
            # prevent recursion
            return self.maxNodeToJointMap[maxNode]

        mtmaxlog.info(f'processing bone: {maxNode.name}')
        jointMeta = self.metadata.getJointByName( maxNode.name )
        attribs = MtJointAttribData( maxNode, jointMeta )
        localMtx = self._getNodeLocalMtx( maxNode )
        
        joint = imJoint(
            name=maxNode.name, 
            id=attribs.id if attribs.id != None else len(self.model.joints) + 1, 
            localMtx=localMtx,
            parent=self._processBone( maxNode.parent ) if maxNode.parent != None else None, # must be specified here to not infere with matrix calculations
            field03=attribs.field03,
            field04=attribs.field04,
            length=None,        # TODO copy from attribs (?)
            invBindMtx=None,    # TODO copy from attribs (?)
            offset=None,        # TODO copy from attribs (?)
            symmetry=None,      # need to create current joint first to resolve self and forward references
            index=attribs.index,
        )
        
        self.maxNodeToJointMap[maxNode] = joint
        self.jointToMaxNodeMap[joint] = maxNode
        self.model.joints.append( joint )
        self.jointIdxByName[ joint.name ] = len( self.model.joints ) - 1
        
    def _iterBoneNodes( self ):
        # process all bones in the scene
        for maxNode in self._getObjects():
            if not self._shouldExportNode( maxNode ) or not self._isBoneNode( maxNode ):
                continue

            yield maxNode
    
    def _processBones( self ):
        if not mtmaxconfig.exportSkeleton:
            mtmaxlog.info('processing bones skipped because it has been disabled through the config')
            return
        
        mtmaxlog.info('processing bones')
        
        # convert all joints first
        # so we can reference them when building the primitives
        self.maxNodeToJointMap = dict()
        self.jointToMaxNodeMap = dict()
        self.jointIdxByName = dict()
        
        if self.ref != None and mtmaxconfig.exportUseRefJoints:
            # copy over original joints
            mtmaxlog.info('copying bones from reference model')
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
            boneNodes = list(self._iterBoneNodes())
            for i, maxNode in enumerate( boneNodes ):
                _updateProgress( 'Processing bones', i, len(boneNodes) )
                self._processBone( maxNode )
                self._processedNodes.add( maxNode )

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
            raise RuntimeError( f"unable to save tex file, make sure you have write permissions to {outPath}" )
            
    def _exportTextureMap( self, textureMap ):
        if textureMap != None and not textureMap in self._textureMapCache:
            # add to cache
            self._textureMapCache[textureMap] = True
            
            if rt.classOf( textureMap ) in [rt.Bitmap, rt.Bitmaptexture]:
                mtmaxlog.info(f'processing texture: {textureMap.filename}')
                if os.path.exists(textureMap.filename):
                    relPath = self._getTextureMapResourcePathOrDefault( textureMap, None )
                    fullPath = mtmaxconfig.exportRoot + '/' + relPath
                    
                    if self.outPath.hash != None:
                        texPath = fullPath + '.241f5deb.tex'
                    else:
                        texPath = fullPath + '.tex'
                    if mtmaxconfig.exportOverwriteTextures or not os.path.exists(texPath):
                        mtmaxlog.info('converting texture to TEX')
                        self._convertTextureToTEX( textureMap.filename, texPath )
                    else:
                        mtmaxlog.info(f'skipping texture conversion because {texPath} already exists')
                else:
                    mtmaxlog.info(f'skipping texture conversion because {textureMap.filename} does not exist')
            elif rt.classOf( textureMap ) == rt.Normal_Bump:
                self._exportTextureMapSafe( textureMap, 'normal_map' )
                self._exportTextureMapSafe( textureMap, 'bump_map' )
            else:
                mtmaxlog.warn(f'unknown texture map type: {rt.classOf( textureMap )}')
                
    def _exportTextureMapSafe( self, material, textureMapName ):
        materialName = getattr(material, "name", None)
        if hasattr( material, textureMapName ):
            if getattr( material, textureMapName, None ) != None:
                self._exportTextureMap( getattr( material, textureMapName ) )
            else:
                mtmaxlog.debug( f'material "{materialName}" texture map "{textureMapName}" not exported because it has not been assigned')
        else:
            mtmaxlog.debug( f'material "{materialName}" texture map "{textureMapName}" not exported because it does not exist on the material')
            
    def _getTextureMapResourcePathInternal( self, name ):
        if self.outPath.relBasePath != None:
            # take the relative directory path of the model and append the name of the texture
            result = self.outPath.relBasePath + '\\' + name
        else:
            # because the model output path is not relative to the root, we put the texture at the root
            # the user will likely have to fix this
            result = name
        return result
            
    def _getTextureMapResourcePathOrDefault( self, textureMap, default ):
        if textureMap == None: return self._getTextureMapResourcePathInternal( default )
        path = util.ResourcePath( textureMap.filename, rootPath=mtmaxconfig.exportRoot )
        result = self._getTextureMapResourcePathInternal( path.baseName )
        result = result.replace('/', '\\')
        return result
    
    def _getTextureMapResourcePathOrDefaultSafe( self, material, textureMap, default ):
        return self._getTextureMapResourcePathOrDefault( getattr( material, textureMap, None ), default )
    
    def _copyUsedDefaultTexturesToOutput( self, material ):
        for map in material.iterTextures():
            if imMaterialInfo.isDefaultTextureMap( map ):
                # make sure to export the default textures whenever they are used
                defaultMapTexPath = os.path.join( util.getResourceDir(), 'textures', os.path.basename( map ) + ".tex" )
                
                if map[0] != '\\':
                    # add separator if it's somehow missing
                    map = '\\' + map
                    
                defaultMapTexExportPath = mtmaxconfig.exportRoot + map + '.tex' if self.outPath.hash == None else \
                                          mtmaxconfig.exportRoot + map + '.241f5deb.tex'

                shutil.copy( defaultMapTexPath, defaultMapTexExportPath )
    
    def _processMaterial_PBRSpecGloss( self, material ):
        assert rt.classOf( material ) == rt.PBRSpecGloss
        
        materialInstance = None
        if mtmaxconfig.exportGenerateMrl:
            # create material instance
            normalMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'norm_map', imMaterialInfo.DEFAULT_NORMAL_MAP )
            albedoMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP )
            specularMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'specular_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
            materialInstance = imMaterialInfo.createFromTemplate( 
                mtmaxconfig.exportMaterialPreset,
                material.name, 
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
                normalMap = self._getTextureMapResourcePathInternal( imMaterialInfo.DEFAULT_NORMAL_MAP )
            
            albedoMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP )
            # TODO is metalness correct for specular?
            specularMap = self._getTextureMapResourcePathOrDefaultSafe( material, 'metalness_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
            materialInstance = imMaterialInfo.createFromTemplate( 
                mtmaxconfig.exportMaterialPreset,
                material.name, 
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
            
            mtmaxlog.info(f'processing material: {material.name}')
            materialInstance = None
            if hasattr( rt, 'PBRSpecGloss' ) and rt.classOf( material ) == rt.PBRSpecGloss:
                materialInstance = self._processMaterial_PBRSpecGloss( material )
            elif rt.classOf( material ) == rt.PhysicalMaterial:
                materialInstance = self._processMaterial_PhysicalMaterial( material )
            else:
                mtmaxlog.error( f"unsupported material type: {rt.classOf( material )}" )
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
        mtmaxlog.info(f'processing mesh: {maxNode.name}')
        attribs = MtPrimitiveAttribData(maxNode)
            
        if mtmaxconfig.exportWeights:
            mtmaxlog.debug('getting skin modifier')
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

        removeEditNormals = False
        editNormalsMod = maxNode.modifiers[rt.Name('Edit_Normals')]
        if editNormalsMod == None:
            if mtmaxconfig.exportNormals:
                mtmaxlog.debug('adding temporary edit normals modifier to get the proper vertex normals')
                editNormalsMod = rt.Edit_Normals()
                rt.select( maxNode )
                rt.modPanel.addModToSelection( editNormalsMod, ui=False )
                removeEditNormals = True
        
        # collect all vertex data per material
        mtmaxlog.debug('collecting vertex data')
        maxMesh = rt.snapshotAsMesh( maxNode )
        faceCount = rt.getNumFaces( maxMesh )
        hasUVs = rt.getNumTVerts( maxMesh ) > 0
        
        primWorkingSets: Dict[int, imPrimitiveWorkingSet] = dict()

        for i in range( 0, faceCount ):
            if mtmaxutil.updateUI(): _updateSubProgress( 'Processing faces', i, faceCount )
            
            face = rt.getFace( maxMesh, i + 1 )
            tvFace = rt.getTVFace( maxMesh, i + 1 ) if hasUVs else None
            matId = rt.getFaceMatID( maxMesh, i + 1 ) 
            material = maxNode.material[matId-1] if rt.classOf(maxNode.material) == rt.Multimaterial else maxNode.material
            

            if matId not in primWorkingSets:
                # create temporary mesh for this material
                prim = imPrimitive(
                    maxNode.name,
                    self._getMaterialName( material ),
                )
                primWorkingSets[matId] = imPrimitiveWorkingSet(prim, [prim])
            
            workingSet = primWorkingSets[matId]
            
            # Max Vertex count 26758, Index count 63762
            if len( workingSet.current.positions ) >= 63762:
                prim = imPrimitive(
                    maxNode.name,
                    self._getMaterialName( material ),
                )
                workingSet.current = prim
                workingSet.primitives.append( prim )
            
            for j in range( 0, 3 ):
                vertIdx = face[j]
                tvertIdx = tvFace[j] if hasUVs else None               
                tempMesh = workingSet.current
                                    
                if material != None:
                    self._processMaterial( material )
                
                pos = self._convertMaxPoint3ToNclVec4( rt.getVert( maxMesh, vertIdx ), 1 )
                pos = self._transformMtx * pos  # needed with reference model
                pos = NclVec3( pos[0], pos[1], pos[2] )
                tempMesh.positions.append( pos )
                
                # NOTE w MUST be 0 for normal vectors otherwise the results will be wrong!
                if editNormalsMod != None:
                    normalId = editNormalsMod.GetNormalId( i + 1, j + 1 )
                    temp = editNormalsMod.GetNormal( normalId )
                    if temp == None:
                        # TODO figure out why this happens
                        # my guess is that it only returns normals that have been explicitly set with the modifier
                        temp = rt.getNormal( maxMesh, vertIdx )
                    nrm = self._convertMaxPoint3ToNclVec4( temp, 0 )
                else:
                    nrm = self._convertMaxPoint3ToNclVec4( rt.getNormal( maxMesh, vertIdx ), 0 )
                nrm = nclNormalize( self._transformMtxNormal * nrm )
                nrm = NclVec3( nrm[0], nrm[1], nrm[2] )
                tempMesh.normals.append( nrm )
                
                # TODO other uv channels
                if hasUVs:
                    tempMesh.uvPrimary.append( self._convertMaxPoint3ToNclVec3UV( rt.getTVert( maxMesh, tvertIdx ) ) )
                else:
                    # TODO maybe omit the uvs entirely?
                    tempMesh.uvPrimary.append( NclVec3( 0, 0, 0 ) )

                if hasSkin:
                    weightCount = rt.skinOps.getVertexWeightCount( maxSkin, vertIdx, node=maxNode )
                    weight = imVertexWeight()
                    for k in range( 0, weightCount ):
                        boneId = rt.skinops.getVertexWeightBoneId( maxSkin, vertIdx, k + 1, node=maxNode )
                        boneWeight = rt.skinOps.getVertexWeight( maxSkin, vertIdx, k + 1, node=maxNode )
                        if boneWeight < 0.001:
                            # ignore empty weights
                            continue
                            
                        boneName = rt.skinOps.getBoneName( maxSkin, boneId, 0, node=maxNode )
                        if boneName not in self.jointIdxByName:
                            raise RuntimeError(
f'''Mesh "{maxNode.name}" skin modifier references bone "{boneName}" that does not exist in the skeleton.
Verify that the metadata matches the model you are exporting and, in case you are exporting a custom skeleton,
don't have an reference/original model specified as it will override the skeleton in the scene.''' )
                            
                        jointIdx = self.jointIdxByName[ boneName ]
                        weight.weights.append( boneWeight )
                        weight.indices.append( jointIdx )
                    if tempMesh.weights == None:
                        tempMesh.weights = []
                    tempMesh.weights.append( weight )
                else:
                    if len( self.model.joints ) > 0:
                        # assume character model, which need weights for every vertex
                        if len(self.model.joints) < 3:
                            rootIndex = 0
                        else:
                            # works better for characters
                            rootIndex = 2
                    
                        # TODO fix this hack
                        weight = imVertexWeight()
                        weight.weights.append( 1 )
                        weight.indices.append( rootIndex )
                        if tempMesh.weights == None:
                            tempMesh.weights = []
                        tempMesh.weights.append( weight )

        # create optimized primitives
        for i, primWorkingSet in enumerate(primWorkingSets.values()):
            primWorkingSet: imPrimitiveWorkingSet
            
            for prim in primWorkingSet.primitives:
                prim: imPrimitive
                if mtmaxutil.updateUI(): _updateProgress( "Optimizing submesh", i, len(primWorkingSets) )
                mtmaxlog.info(f'processing submesh with material {prim.materialName}')

                # copy over attribs
                if attribs.flags != None: prim.flags = attribs.flags
                if attribs.groupId != None: 
                    group = self.model.getGroupById(attribs.groupId)
                    if group == None:
                        # add group
                        group = imGroup(self.metadata.getGroupName(attribs.groupId), attribs.groupId)
                        self.model.groups.append(group)
                    prim.group = group
                elif mtmaxconfig.exportGroupPerMesh:
                    prim.group = imGroup(maxNode.name + '_' + str(i), len(self.model.groups)+1)
                    self.model.groups.append(prim.group)
                        
                if attribs.lodIndex != None: prim.lodIndex = attribs.lodIndex
                if attribs.renderFlags != None: prim.renderFlags = attribs.renderFlags
                if attribs.id != None: prim.id = attribs.id
                if attribs.field2c != None: prim.field2c = attribs.field2c
                if attribs.primitiveJointLinkCount != None and attribs.primitiveJointLinkIndex != None and len( self._refPrimitiveJointLinks ) > 0: 
                    # add primitive joint links from ref to the primitive
                    for i in range(attribs.primitiveJointLinkIndex, attribs.primitiveJointLinkIndex+attribs.primitiveJointLinkCount):
                        prim.primitiveJointLinks.append(self._refPrimitiveJointLinks[i])
                elif mtmaxconfig.exportGeneratePjl:
                    # TODO local transform/pivot, link to joint(s)
                    prim.primitiveJointLinks.append(imPrimitiveJointLink())
                if attribs.index != None: prim.index = attribs.index
                if attribs.vertexShader != None: prim.vertexFormat = imVertexFormat.createFromShader( attribs.vertexShader )
                
                if mtmaxconfig.debugExportForceShader != '':
                    # force shader on export if specified
                    prim.vertexFormat = imVertexFormat.createFromShader( mtmaxconfig.debugExportForceShader )
                                
                mtmaxlog.debug("generating tangents")
                prim.generateTangents( _progressCallback )
                
                mtmaxlog.debug("optimizing mesh")
                prim.makeIndexed( _progressCallback )
                
                self.model.primitives.append( prim )
            
        if removeEditNormals:
            mtmaxlog.debug('delete temporary edit normals modifier')
            try:
                rt.deleteModifier( maxNode, editNormalsMod )
            except:
                pass
            
        rt.delete( maxMesh )
        
    def _iterMeshNodes( self ):
        for maxNode in self._getObjects():
            if not self._shouldExportNode( maxNode ):
                continue
            
            if not self._isMeshNode( maxNode ) and not self._isSplineNode( maxNode ):
                continue
            
            yield maxNode
        
    def _processMeshes( self ):
        if not mtmaxconfig.exportPrimitives:
            mtmaxlog.info('exporting meshes skipped because it has been disabled through the config')
            return
        
        # convert meshes
        mtmaxlog.info('processing meshes')
        meshNodes = list(self._iterMeshNodes())
        for i, maxNode in enumerate( meshNodes ):
            _updateProgress('Processing meshes', i, len( meshNodes ) )
            self._processMesh( maxNode )
            self._processedNodes.add( maxNode )
            
    def _iterGroupNodes( self ):
        # process all groups in the scene
        for maxNode in self._getObjects():
            if not self._shouldExportNode( maxNode ) or not self._isGroupNode( maxNode ):
                continue
            yield maxNode

    def _processGroups( self ):
        if not mtmaxconfig.exportGroups:
            mtmaxlog.info('exporting groups skipped because it has been disabled through the config')
            return
        
        mtmaxlog.info('processing groups')
        if self.ref != None and mtmaxconfig.exportUseRefGroups:
            mtmaxlog.info('copying groups from reference model')
            for i, refGroup in enumerate(self.ref.groups):
                group = imGroup(
                    name=self.metadata.getGroupName(refGroup.id),
                    id=refGroup.id,
                    field04=refGroup.field04,
                    field08=refGroup.field08,
                    field0c=refGroup.field0c,
                    boundingSphere=refGroup.boundingSphere,
                    index=i,
                )
                self.model.groups.append(group)
        else:
            # process all groups in the scene
            groupNodes = list(self._iterGroupNodes())
            for i in range( 0, len( groupNodes ) ):
                _updateProgress( 'Processing groups', i, len( groupNodes ) )
                maxNode = groupNodes[i]
                
                mtmaxlog.info(f'processing group node {maxNode}')
                attribs = MtGroupAttribData(maxNode)
                group = imGroup(
                    name=maxNode.name,
                    id=attribs.id,
                    field04=attribs.field04 if attribs.field04 != None else 0,
                    field08=attribs.field08 if attribs.field08 != None else 0,
                    field0c=attribs.field0c if attribs.field0c != None else 0,
                    boundingSphere=attribs.bsphere if attribs.bsphere != None else None,
                    index=attribs.index,
                )
                self.model.groups.append(group)
                self._processedNodes.add( maxNode )
                
    def _processPjl( self ):
        if not mtmaxconfig.exportPjl:
            mtmaxlog.info('exporting pjl skipped because it has been disabled through the config')
            return
        
        mtmaxlog.info('processing pjl')
        if self.ref != None and mtmaxconfig.exportUseRefPjl:
            mtmaxlog.info('copying pjl from reference model')
            for i, refPjl in enumerate(self.ref.primitiveJointLinks):
                pjl = imPrimitiveJointLink(
                    name='pjl_'+str(i),
                    joint=self.model.joints[refPjl.jointIndex] if refPjl.jointIndex != 255 else None,
                    field04=refPjl.field04,
                    field08=refPjl.field08,
                    field0c=refPjl.field0c,
                    boundingSphere=refPjl.boundingSphere,
                    min=refPjl.min,
                    max=refPjl.max,
                    localMtx=refPjl.localMtx,
                    field80=refPjl.field80,
                    index=i,
                )
                self._refPrimitiveJointLinks.append( pjl )
        else:
            # TODO: represent these in the scene
            mtmaxlog.debug("exporting pjl from scene not implemented")
    
    def _writeBinaries( self ):
        mtmaxlog.info('writing files')
        mtmaxlog.debug('converting intermediate model to binary model format')
        _updateProgress( 'Writing files', 0 )
        binMod = self.model.toBinaryModel( _progressCallback )
        _updateProgress( 'Writing files', 25 )
        
        mtmaxlog.debug('writing binary model')
        stream = NclBitStream()
        binMod.write( stream )
        try:
            util.saveByteArrayToFile( self.outPath.fullPath, stream.getBuffer() )
        except PermissionError as e:
            raise RuntimeError( f"Unable to save mod file, make sure you have write permissions to {self.outPath.fullPath}" )
        
        if self.outPath.hash != None:
            mrlExportPath = self.outPath.basePath + '/' + self.outPath.baseName + '.2749c8a8.mrl' 
        else:
            mrlExportPath = self.outPath.basePath + '/' + self.outPath.baseName + '.mrl'
            
        _updateProgress( 'Writing files', 50 )
        if mtmaxconfig.exportGenerateMrl:
            mrlYmlExportPath = mrlExportPath + ".yml"
            mtmaxlog.info(f"writing generated mrl yml to {mrlYmlExportPath}")
            self.mrl.updateTextureList()
            try:
                self.mrl.saveYamlFile( mrlYmlExportPath )
            except PermissionError as e:
                raise RuntimeError( f"Unable to save mrl yml file, make sure you have write permissions to {mrlYmlExportPath}" )
          
        _updateProgress( 'Writing files', 75 )  
        if mtmaxconfig.exportGenerateMrl or (mtmaxconfig.exportExistingMrlYml and self.mrl != None):
            mtmaxlog.info(f'exporting mrl yml to {mrlExportPath}')
            
            try:
                self.mrl.saveBinaryFile( mrlExportPath )
            except PermissionError as e:
                raise RuntimeError( f"Unable to save mrl file, make sure you have write permissions to {mrlExportPath}" )
            
        _updateProgress( 'Writing files', 100 )
    
    def _calcMatrices( self ):
        self._transformMtx = nclCreateMat44()
        if mtmaxconfig.flipUpAxis:
            self._transformMtx *= util.Z_TO_Y_UP_MATRIX
            
        self._scaleMtx = nclScale( mtmaxconfig.exportScale )
        self._transformMtxNoScale = deepcopy( self._transformMtx )
        self._transformMtx *= self._scaleMtx
        self._transformMtxNormal = nclTranspose( nclInverse( self._transformMtx ) )
    
    def exportModel( self, path ):
        mtmaxlog.info(f'script version: {mtmaxver.version}')
        mtmaxlog.info(f'exporting to {path}')
        
        # start building intermediate model data for conversion
        self.model = imModel()
        self.outPath = util.ResourcePath(path, rootPath=mtmaxconfig.exportRoot)
        if self.outPath.relBasePath == None:
            raise RuntimeError("The model export path is not in a subfolder of the specified extracted archive directory.")
        
        self.metadata = ModelMetadata()
        self.mrl = None
        self._calcMatrices()

        if os.path.exists( mtmaxconfig.exportMetadataPath ):
            mtmaxlog.info(f'loading metadata file from {mtmaxconfig.exportMetadataPath}')
            self.metadata.loadFile( mtmaxconfig.exportMetadataPath )

        if os.path.exists( mtmaxconfig.exportRefPath ):
            mtmaxlog.info(f'loading reference model from {mtmaxconfig.exportRefPath}')
            self.ref = rModelData()
            self.ref.read( NclBitStream( util.loadIntoByteArray( mtmaxconfig.exportRefPath ) ) )
            
        if os.path.exists( mtmaxconfig.exportMrlYmlPath ):
            mtmaxlog.info(f'loading mrl yml from {mtmaxconfig.exportMrlYmlPath}')
            self.mrl = imMaterialLib()
            self.mrl.loadYamlFile( mtmaxconfig.exportMrlYmlPath )
        elif mtmaxconfig.exportGenerateMrl:
            mtmaxlog.info(f'generating new mrl')
            self.mrl = imMaterialLib()
            
        mtmaxlog.debug('creating output directories')
        if not os.path.exists( mtmaxconfig.exportRoot ):
            os.makedirs( mtmaxconfig.exportRoot )
        if not os.path.exists( os.path.dirname( mtmaxconfig.exportFilePath ) ):
            os.makedirs( mtmaxconfig.exportFilePath )

        mtmaxlog.info('processing scene')
        if self.ref != None and mtmaxconfig.exportUseRefBounds:
            # copy over header values
            mtmaxlog.debug('copying over header values from reference model')
            self.model.field90 = self.ref.header.field90
            self.model.field94 = self.ref.header.field94
            self.model.field98 = self.ref.header.field98
            self.model.field9c = self.ref.header.field9c
            self.model.center = self.ref.header.center
            self.model.max = self.ref.header.max
            self.model.min = self.ref.header.min
            self.model.radius = self.ref.header.radius
        
        # groups share types with bones, so we must disambiguate carefully
        # it's easier to distinguish a group from a bone, so process the groups first
        self._processGroups()
        
        # after the groups have been processed, there should be no room for error when finding
        # the bones in the scene
        self._processBones()
        self._processPjl()
        self._processMeshes()
        self._writeBinaries()
        
        _updateProgress( 'Done', 0 )
        _updateSubProgress( '', 0 )
        mtmaxlog.info('export completed successfully')