__package__ = 'modules.mtmax.src'

from typing import Dict
from ...mtlib.base_editor import *
from ...mtlib.base_exporter import *
import max_plugin
from mtmax.src import MtMaxModelExportRollout
from pymxs import runtime as rt
from max_plugin import MaxNodeProxy, MaxCustomAttributeSetProxy

def updateProgress( what, value, count = 0 ):
    rollout = MtMaxModelExportRollout.getMxsVar()
    rollout.pbExport.value = value if count == 0 else (value/count) * 100
    rollout.lblExportProgressCategory.text = what
    
def updateSubProgress( what, value, count = 0 ):
    rollout = MtMaxModelExportRollout.getMxsVar()
    rollout.pbExportSub.value = value if count == 0 else (value/count) * 100
    rollout.lblExportProgressSubCategory.text = what

def progressCallback( what, i, count ):
    if max_plugin.plugin.updateUI():
        max_plugin.plugin.logger.info( what + f' {i}/{count}' )
        updateSubProgress( what, i, count )

class MaxModelExporter(ModelExporterBase):
    def __init__(self) -> None:
        super().__init__(max_plugin.plugin)
        self.progressCallback = progressCallback

    def getEditorGroupCustomAttributeData( self, node: EditorNodeProxy  ) -> EditorCustomAttributeSetProxy:
        maxNode = node.unwrap()
        attribs = maxNode.MtMaxGroupAttributes if hasattr(maxNode, 'MtMaxGroupAttributes') else None
        if attribs is None:
            return None
        return MaxCustomAttributeSetProxy(attribs)

    def getEditorPrimitiveCustomAttributeData( self, node: EditorNodeProxy  ) -> EditorCustomAttributeSetProxy:
        maxNode = node.unwrap()
        attribs = maxNode.MtPrimitiveAttributes if hasattr(maxNode, 'MtPrimitiveAttributes') else None
        if attribs is None:
            return None
        return MaxCustomAttributeSetProxy(attribs)

    def getEditorJointCustomAttributeData( self, node: EditorNodeProxy  ) -> EditorCustomAttributeSetProxy:
        maxNode = node.unwrap()
        attribs = maxNode.MtMaxJointAttributes if hasattr(maxNode, 'MtMaxJointAttributes') else None
        if attribs is None:
            return None
        return MaxCustomAttributeSetProxy(attribs)

    def convertPoint3ToNclVec3( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], v[1], v[2]))

    def convertPoint3ToNclVec3UV( self, v: rt.Point3 ) -> NclVec3:
        return NclVec3((v[0], 1 - v[1], v[2]))
        
    def convertPoint3ToNclVec4( self, v: rt.Point3, w ) -> NclVec3:
        return NclVec4((v[0], v[1], v[2], w))
    
    def convertMatrix3ToNclMat43( self, v: rt.Matrix3 ) -> NclMat43:
        return nclCreateMat43((self.convertPoint3ToNclVec3(v[0]), 
                               self.convertPoint3ToNclVec3(v[1]), 
                               self.convertPoint3ToNclVec3(v[2]), 
                               self.convertPoint3ToNclVec3(v[3])))
        
    def convertMatrix3ToNclMat44( self, v: rt.Matrix3 ):
        return nclCreateMat44((self.convertPoint3ToNclVec4(v[0], 0), 
                               self.convertPoint3ToNclVec4(v[1], 0), 
                               self.convertPoint3ToNclVec4(v[2], 0), 
                               self.convertPoint3ToNclVec4(v[3], 1)))

    def getObjects( self ):
        # return a list of scene objects as opposed to enumerating directly to prevent crashes
        temp = list(rt.objects)
        objects = []
        for o in temp:
            if not o in self.processedNodes:
                objects.append( MaxNodeProxy( o ) )
        return objects

    def updateProgress( self, what, value, count = 0 ):
        updateProgress( what, value, count )
        
    def updateSubProgress( self, what, value, count = 0 ):
        updateSubProgress( what, value, count )

    def exportTextureMap( self, material, textureMapName ):
        def exportTextureMapInternal( textureMap ):
            if rt.classOf( textureMap ) in [rt.Bitmap, rt.Bitmaptexture]:
                self.convertTextureToTEX( textureMap.filename )
            elif rt.classOf( textureMap ) == rt.Normal_Bump:
                self.exportTextureMap( textureMap, 'normal_map' )
                self.exportTextureMap( textureMap, 'bump_map' )
            else:
                self.logger.warn(f'unknown texture map type: {rt.classOf( textureMap )}')

        materialName = getattr(material, "name", None)
        if hasattr( material, textureMapName ):
            if getattr( material, textureMapName, None ) != None:
                exportTextureMapInternal( getattr( material, textureMapName ) )
            else:
                self.logger.debug( f'material "{materialName}" texture map "{textureMapName}" not exported because it has not been assigned')
        else:
            self.logger.debug( f'material "{materialName}" texture map "{textureMapName}" not exported because it does not exist on the material')

    def getMaterialTextureMapResourcePathOrDefault( self, material, textureMapName, default ):
        textureMap = getattr( material, textureMapName, None )
        textureFileName = textureMap.filename if textureMap is not None else None
        return self.getTextureMapResourcePathOrDefault( textureFileName, default )

    def processMaterial_PBRSpecGloss( self, material ):
        assert rt.classOf( material ) == rt.PBRSpecGloss
        
        materialInstance = None
        if self.config.exportGenerateMrl:
            # create material instance
            normalMap = self.getMaterialTextureMapResourcePathOrDefault( material, 'norm_map', imMaterialInfo.DEFAULT_NORMAL_MAP )
            albedoMap = self.getMaterialTextureMapResourcePathOrDefault( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP )
            specularMap = self.getMaterialTextureMapResourcePathOrDefault( material, 'specular_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
            materialInstance = imMaterialInfo.createFromTemplate( 
                self.config.exportMaterialPreset,
                material.name, 
                normalMap=normalMap,
                albedoMap=albedoMap,
                specularMap=specularMap,
            )

        if self.config.exportTexturesToTex:
            self.exportTextureMap( material, 'base_color_map' )
            self.exportTextureMap( material, 'specular_map' )
            self.exportTextureMap( material, 'glossiness_map' )
            self.exportTextureMap( material, 'ao_map' )
            self.exportTextureMap( material, 'norm_map' )
            self.exportTextureMap( material, 'emit_color_map' )
            self.exportTextureMap( material, 'opacity_map' )
            self.exportTextureMap( material, 'displacement_map' )
            
        return materialInstance
    
    def processMaterial_PhysicalMaterial( self, material ):
        assert rt.classOf( material ) == rt.PhysicalMaterial
        
        materialInstance = None
        if self.config.exportGenerateMrl:
            # create material instance
            if getattr( material, 'bump_map', None ) != None and rt.classOf( material.bump_map ) == rt.Normal_Bump:
                normalMap = self.getMaterialTextureMapResourcePathOrDefault( material.bump_map, 'normal', imMaterialInfo.DEFAULT_NORMAL_MAP )
            else:
                # TODO handle different normal map assignments?
                normalMap = self.getTextureMapResourcePathInternal( imMaterialInfo.DEFAULT_NORMAL_MAP )
            
            albedoMap = self.getMaterialTextureMapResourcePathOrDefault( material, 'base_color_map', imMaterialInfo.DEFAULT_ALBEDO_MAP )
            # TODO is metalness correct for specular?
            specularMap = self.getMaterialTextureMapResourcePathOrDefault( material, 'metalness_map', imMaterialInfo.DEFAULT_SPECULAR_MAP )
            materialInstance = imMaterialInfo.createFromTemplate( 
                self.config.exportMaterialPreset,
                material.name, 
                normalMap=normalMap,
                albedoMap=albedoMap,
                specularMap=specularMap,
            )

        if self.config.exportTexturesToTex:
            self.exportTextureMap( material, 'base_weight_map' )
            self.exportTextureMap( material, 'base_color_map' )
            self.exportTextureMap( material, 'reflectivity_map' )
            self.exportTextureMap( material, 'refl_color_map' )
            self.exportTextureMap( material, 'metalness_map' )
            self.exportTextureMap( material, 'diff_rough_map' )
            self.exportTextureMap( material, 'anisotropy_map' )
            self.exportTextureMap( material, 'aniso_angle_map' )
            self.exportTextureMap( material, 'transparency_map' )
            self.exportTextureMap( material, 'trans_color_map' )
            self.exportTextureMap( material, 'trans_rough_map' )
            self.exportTextureMap( material, 'trans_ior_map' )
            self.exportTextureMap( material, 'scattering_map' )
            self.exportTextureMap( material, 'sss_color_map' )
            self.exportTextureMap( material, 'sss_scale_map' )
            self.exportTextureMap( material, 'emission_map' )
            self.exportTextureMap( material, 'emit_color_map' )
            self.exportTextureMap( material, 'coat_map' )
            self.exportTextureMap( material, 'coat_color_map' )
            self.exportTextureMap( material, 'bump_map' )
            self.exportTextureMap( material, 'coat_rough_map' )
            self.exportTextureMap( material, 'displacement_map' )
            self.exportTextureMap( material, 'cutout_map' )
            
        return materialInstance
     
    def processMaterial( self, material ):
        if material not in self.materialCache:
            # add to cache
            self.materialCache[material] = True
            
            self.logger.info(f'processing material: {material.name}')
            materialInstance = None
            if hasattr( rt, 'PBRSpecGloss' ) and rt.classOf( material ) == rt.PBRSpecGloss:
                materialInstance = self.processMaterial_PBRSpecGloss( material )
            elif rt.classOf( material ) == rt.PhysicalMaterial:
                materialInstance = self.processMaterial_PhysicalMaterial( material )
            else:
                self.logger.error( f"unsupported material type: {rt.classOf( material )}" )
                return
            
            if materialInstance != None:
                self.copyUsedDefaultTexturesToOutput( materialInstance )
                self.mrl.materials.append( materialInstance )

    def getMaterialName( self, material ):
        if material == None:
            return 'default_material'
        else:
            return material.name

    def processMesh( self, editorNode: EditorNodeProxy ):
        self.logger.info(f'processing mesh: {editorNode.getName()}')
        attribs = self.getPrimitiveCustomAttributeData(editorNode)
            
        if self.config.exportWeights:
            self.logger.debug('getting skin modifier')
            maxSkin = editorNode.unwrap().modifiers[rt.Name('Skin')]
            hasSkin = maxSkin != None
            if hasSkin:
                # fix unrigged vertices
                maxSkin.weightAllVertices = False
                maxSkin.weightAllVertices = True
                # node arg is ignored
                #rt.skinOps.removeZeroWeights( maxSkin, node=editorNode )
        else:
            hasSkin = False

        removeEditNormals = False
        editNormalsMod = editorNode.unwrap().modifiers[rt.Name('Edit_Normals')]
        if editNormalsMod == None:
            if self.config.exportNormals:
                self.logger.debug('adding temporary edit normals modifier to get the proper vertex normals')
                editNormalsMod = rt.Edit_Normals()
                rt.select( editorNode.unwrap() )
                rt.modPanel.addModToSelection( editNormalsMod, ui=False )
                removeEditNormals = True
        
        # collect all vertex data per material
        self.logger.debug('collecting vertex data')
        maxMesh = rt.snapshotAsMesh( editorNode.unwrap() )
        faceCount = rt.getNumFaces( maxMesh )
        hasUVs = rt.getNumTVerts( maxMesh ) > 0
        
        primWorkingSets: Dict[int, imPrimitiveWorkingSet] = dict()

        for i in range( 0, faceCount ):
            if self.plugin.updateUI(): self.updateSubProgress( 'Processing faces', i, faceCount )
            
            face = rt.getFace( maxMesh, i + 1 )
            tvFace = rt.getTVFace( maxMesh, i + 1 ) if hasUVs else None
            matId = rt.getFaceMatID( maxMesh, i + 1 ) 
            material = editorNode.unwrap().material[matId-1] if rt.classOf(editorNode.unwrap().material) == rt.Multimaterial else editorNode.unwrap().material
            

            if matId not in primWorkingSets:
                # create temporary mesh for this material
                prim = imPrimitive(
                    editorNode.getName(),
                    self.getMaterialName( material ),
                )
                primWorkingSets[matId] = imPrimitiveWorkingSet(prim, [prim])
            
            workingSet = primWorkingSets[matId]
            
            if len( workingSet.current.positions ) >= self.MAX_INDEX_COUNT:
                prim = imPrimitive(
                    editorNode.getName(),
                    self.getMaterialName( material ),
                )
                workingSet.current = prim
                workingSet.primitives.append( prim )
            
            for j in range( 0, 3 ):
                vertIdx = face[j]
                tvertIdx = tvFace[j] if hasUVs else None               
                tempMesh = workingSet.current
                                    
                if material != None:
                    self.processMaterial( material )
                
                pos = self.convertPoint3ToNclVec4( rt.getVert( maxMesh, vertIdx ), 1 )
                pos = self.transformMtx * pos  # needed with reference model
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
                    nrm = self.convertPoint3ToNclVec4( temp, 0 )
                else:
                    nrm = self.convertPoint3ToNclVec4( rt.getNormal( maxMesh, vertIdx ), 0 )
                nrm = nclNormalize( self.transformMtxNormal * nrm )
                nrm = NclVec3( nrm[0], nrm[1], nrm[2] )
                tempMesh.normals.append( nrm )
                
                # TODO other uv channels
                if hasUVs:
                    tempMesh.uvPrimary.append( self.convertPoint3ToNclVec3UV( rt.getTVert( maxMesh, tvertIdx ) ) )

                if hasSkin:
                    weightCount = rt.skinOps.getVertexWeightCount( maxSkin, vertIdx, node=editorNode.unwrap() )
                    weight = imVertexWeight()
                    for k in range( 0, weightCount ):
                        boneId = rt.skinops.getVertexWeightBoneId( maxSkin, vertIdx, k + 1, node=editorNode.unwrap() )
                        boneWeight = rt.skinOps.getVertexWeight( maxSkin, vertIdx, k + 1, node=editorNode.unwrap() )
                        if boneWeight < 0.001:
                            # ignore empty weights
                            continue
                            
                        boneName = rt.skinOps.getBoneName( maxSkin, boneId, 0, node=editorNode.unwrap() )
                        if boneName not in self.jointIdxByName:
                            raise RuntimeError(
f'''Mesh "{editorNode.getName()}" skin modifier references bone "{boneName}" that does not exist in the skeleton.
Verify that the metadata matches the model you are exporting and, in case you are exporting a custom skeleton,
don't have an reference/original model specified as it will override the skeleton in the scene.''' )
                            
                        jointIdx = self.jointIdxByName[ boneName ]
                        weight.weights.append( boneWeight )
                        weight.indices.append( jointIdx )
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
                        tempMesh.weights.append( weight )

        self.generatePrimitives( editorNode, attribs, primWorkingSets )
            
        if removeEditNormals:
            self.logger.debug('delete temporary edit normals modifier')
            try:
                rt.deleteModifier( editorNode.unwrap(), editNormalsMod )
            except:
                pass
            
        rt.delete( maxMesh )