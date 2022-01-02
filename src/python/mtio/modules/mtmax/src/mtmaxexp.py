import os
import sys
from typing import List, Tuple

from pymxs import runtime as rt
from mtlib import *
import mtmaxconfig
import mtmaxutil
from mtlib import texconv
import maxlog

class TempVertex:
    '''Trivially hash-able container for optimizing the vertex cache'''
    def __init__( self ):
        self.position = ()
        self.normal = ()
        self.tangent = ()
        self.uv = ()
        self.weights = ()
        self.weightIndices = ()
        
    def __eq__(self, o: object) -> bool:
        if isinstance( o, TempVertex ):
            return self.position == o.position and \
                   self.normal == o.normal and \
                   self.tangent == o.tangent and \
                   self.uv == o.uv and \
                   self.weights == o.weights and \
                   self.weightIndices == o.weightIndices
                   
    def __hash__( self ):
        return hash((self.position, self.normal, self.tangent, self.uv, self.weights, self.weightIndices))

class TempMesh:
    '''Temporary mesh data container'''
    def __init__( self, material ):
        self.material = material
        self.positions = []
        self.normals = []
        self.uvs = []
        self.weights = []
        self.weightIndices = []
        self.tangents = []

class MtGroupAttribData(object):
    '''Wrapper for group custom attribute data'''
    def __init__( self, maxNode ):
        attribs = maxNode.mtModelGroupAttributes if hasattr(maxNode, 'mtModelGroupAttributes') else None
        if attribs != None:
            self.id = int(attribs.id)
            self.field04 = int(attribs.field04)
            self.field08 = int(attribs.field08)
            self.field0c = int(attribs.field0c)
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
            self.flags = int(attribs.flags, base=0)
            if attribs.groupId == "inherit":
                if maxNode.parent != None:
                    self.groupId = MtGroupAttribData(maxNode.parent).id
                else:
                    # invalid
                    self.groupId = None
            else:
                self.groupId = int(attribs.groupId, base=0)
            self.lodIndex = int(attribs.lodIndex)
            self.renderFlags = int(attribs.renderFlags, base=0)
            self.id = int(attribs.id)
            self.field2c = int(attribs.field2c)
        else:
            self.flags = None
            self.groupId = None
            self.lodIndex = None
            self.renderFlags = None
            self.id = None
            self.field2c = None

class MtJointAttribData(object):
    '''Wrapper for joint custom attribute data'''
    def __init__( self, maxNode, jointMeta ):
        attribs = maxNode.mtJointAttributes if hasattr(maxNode, 'mtJointAttributes') else None
        if attribs != None:
            # grab attributes from custom attributes on node
            self.id = int(attribs.id)
            self.symmetryNode = rt.getNodeByName( attribs.symmetryName )
            self.field03 = int(attribs.field03)
            self.field04 = int(attribs.field04)
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
        self.exportSkin = True
        self.exportVertexNormals = True
        self.useRefJoints = True
        self.useRefGroups = True
        self.useRefPml = True
        self.useRefBounds = True
        self._textureMapCache = dict()
        self._materialCache = dict()
        
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
        
    # '''
    # void CalculateTangentsBitangents(
    # Point3 pos[3], Point3 norm[3], Point3 uv[3],
    # Point3 tangent[3], Point3 bitangent[3])
    # {
    #     float uv1x = uv[1].x - uv[0].x;
    #     float uv2x = uv[2].x - uv[0].x;
    #     float uv1y = uv[1].y - uv[0].y;
    #     float uv2y = uv[2].y - uv[0].y;
    #     float uvk = uv2x * uv1y - uv1x * uv2y;

    #     Point3 v1 = pos[1] - pos[0];
    #     Point3 v2 = pos[2] - pos[0];

    #     Point3 faceTangent;
    #     if (uvk != 0) {
    #     faceTangent = (uv1y * v2 - uv2y * v1) / uvk;
    #     } else {
    #     if (uv1x != 0) faceTangent = v1 / uv1x;
    #     else if (uv2x != 0) faceTangent = v2 / uv2x;
    #     else faceTangent = Point3(0.0f, 0.0f, 0.0f);
    #     }
    #     Normalize(faceTangent);

    #     Point3 mapNormal = CrossProduct(uv[1] - uv[0], uv[2] - uv[1]);
    #     bool flip = mapNormal.z < 0;

    #     for (int i = 0; i < 3; ++i)
    #     {
    #     // Make tangent perpendicular to normal
    #     tangent[i] = faceTangent - DotProduct(norm[i], faceTangent) * norm[i];
    #     Normalize(tangent[i]);

    #     bitangent[i] = CrossProduct(norm[i], tangent[i]);
    #     if (flip) bitangent[i] = -bitangent[i];
    #     }
    # }

    # def CalculateTangentsBitangents( self, pos, norm, uv, tangent, bitangent ):
    #     uv1x = uv[1][0] - uv[0][0]
    #     uv2x = uv[2][0] - uv[0][0]
    #     uv1y = uv[1][1] - uv[0][1]
    #     uv2y = uv[2][1] - uv[0][1]
    #     uvk = uv2x * uv1y - uv1x * uv2y

    #     v1 = pos[1] - pos[0]
    #     v2 = pos[2] - pos[0]

    #     if uvk != 0:
    #         faceTangent = (uv1y * v2 - uv2y * v1) / uvk
    #     else:
    #         if uv1x != 0: faceTangent = v1 / uv1x
    #         elif uv2x != 0: faceTangent = v2 / uv2x
    #         else: faceTangent = glm.vec3(0.0, 0.0, 0.0)

    #     faceTangent = glm.normalize(faceTangent)

    #     mapNormal = glm.cross(uv[1] - uv[0], uv[2] - uv[1])
    #     flip = mapNormal[2] < 0

    #     for i in range(0, 3):
    #         # Make tangent perpendicular to normal
    #         tangent[i] = faceTangent - glm.dot(norm[i], faceTangent) * norm[i];
    #         tangent[i] = glm.normalize(tangent[i]);

    #         bitangent[i] = glm.cross(norm[i], tangent[i])
    #         if flip: bitangent[i] = -bitangent[i]

    # def _computeTangentBasis( self, indices: List[int], vertex: List[NclVec3], texcoord: List[NclVec3], normal: List[NclVec3] ) -> List[NclVec3]:
    #     tan1 = []
    #     tan2 = []
    #     for i in range(len(vertex)):
    #         tan1.append(glm.vec3())
    #         tan2.append(glm.vec3())

        
    #     for i in range(0, len(indices), 3):
    #         i1 = indices[i+0]
    #         i2 = indices[i+1]
    #         i3 = indices[i+2]

    #         v1 = vertex[i1];
    #         v2 = vertex[i2];
    #         v3 = vertex[i3];
        
    #         w1 = texcoord[i1];
    #         w2 = texcoord[i2];
    #         w3 = texcoord[i3];
            
    #         x1 = v2[0] - v1[0];
    #         x2 = v3[0] - v1[0];
    #         y1 = v2[1] - v1[1];
    #         y2 = v3[1] - v1[1];
    #         z1 = v2[2] - v1[2];
    #         z2 = v3[2] - v1[2];
        
    #         s1 = w2[0] - w1[0];
    #         s2 = w3[0] - w1[0];
    #         t1 = w2[1] - w1[1];
    #         t2 = w3[1] - w1[1];
        
    #         temp = (s1 * t2 - s2 * t1)
    #         if temp == 0:
    #             r = 0
    #         else:
    #             r = 1.0 / (s1 * t2 - s2 * t1);
    #         sdir = glm.vec3((t2 * x1 - t1 * x2) * r, (t2 * y1 - t1 * y2) * r,
    #                 (t2 * z1 - t1 * z2) * r);
    #         tdir = glm.vec3((s1 * x2 - s2 * x1) * r, (s1 * y2 - s2 * y1) * r,
    #                 (s1 * z2 - s2 * z1) * r);
            
    #         tan1[i1] += sdir;
    #         tan1[i2] += sdir;
    #         tan1[i3] += sdir;
            
    #         tan2[i1] += tdir;
    #         tan2[i2] += tdir;
    #         tan2[i3] += tdir;

    #     tangents = []
    #     for a in range(len(vertex)):
    #         n = normal[a];
    #         t = tan1[a];
            
    #         # Gram-Schmidt orthogonalize
    #         tangent = glm.normalize(t - n * glm.dot(n, t))
            
    #         # Calculate handedness
    #         handedness = -1.0 if (glm.dot(glm.cross(n, t), tan2[a]) < 0.0) else -1.0
    #         tangents.append(tangent * handedness)

    #     return tangents
        
    # def CalculateTangentBinormal( self, vertex1, vertex2, vertex3 ):
    #     vector1 = [0,0,0]
    #     vector2 = [0,0,0]
    #     tuVector = [0,0]
    #     tvVector = [0,0]
    #     tangent = glm.vec3()
    #     binormal = glm.vec3()
        
    #     # Calculate the two vectors for this face.
    #     vector1[0] = vertex2.position[0] - vertex1.position[0];
    #     vector1[1] = vertex2.position[1] - vertex1.position[1];
    #     vector1[2] = vertex2.position[2] - vertex1.position[2];

    #     vector2[0] = vertex3.position[0] - vertex1.position[0];
    #     vector2[1] = vertex3.position[1] - vertex1.position[1];
    #     vector2[2] = vertex3.position[2] - vertex1.position[2];

    #     # Calculate the tu and tv texture space vectors.
    #     tuVector[0] = vertex2.uv[0] - vertex1.uv[0];
    #     tvVector[0] = vertex2.uv[1] - vertex1.uv[1];

    #     tuVector[1] = vertex3.uv[0] - vertex1.uv[0];
    #     tvVector[1] = vertex3.uv[1] - vertex1.uv[1];

    #     # Calculate the denominator of the tangent/binormal equation.
    #     temp = (tuVector[0] * tvVector[1] - tuVector[1] * tvVector[0])
    #     den = 0
    #     if temp != 0:
    #         den = 1.0 / (tuVector[0] * tvVector[1] - tuVector[1] * tvVector[0]);

    #     # Calculate the cross products and multiply by the coefficient to get the tangent and binormal.
    #     tangent[0] = (tvVector[1] * vector1[0] - tvVector[0] * vector2[0]) * den;
    #     tangent[1] = (tvVector[1] * vector1[1] - tvVector[0] * vector2[1]) * den;
    #     tangent[2] = (tvVector[1] * vector1[2] - tvVector[0] * vector2[2]) * den;

    #     binormal[0] = (tuVector[0] * vector2[0] - tuVector[1] * vector1[0]) * den;
    #     binormal[1] = (tuVector[0] * vector2[1] - tuVector[1] * vector1[1]) * den;
    #     binormal[2] = (tuVector[0] * vector2[2] - tuVector[1] * vector1[2]) * den;

    #     # Calculate the length of this normal.
    #     length = math.sqrt((tangent[0] * tangent[0]) + (tangent[1] * tangent[1]) + (tangent[2] * tangent[2]));

    #     if length != 0:
    #         # Normalize the normal and then store it
    #         tangent[0] = tangent[0] / length;
    #         tangent[1] = tangent[1] / length;
    #         tangent[2] = tangent[2] / length;

    #     # Calculate the length of this normal.
    #     length = math.sqrt((binormal[0] * binormal[0]) + (binormal[1] * binormal[1]) + (binormal[2] * binormal[2]));

    #     if length != 0:
    #         # Normalize the normal and then store it
    #         binormal[0] = binormal[0] / length;
    #         binormal[1] = binormal[1] / length;
    #         binormal[2] = binormal[2] / length;

    #     return tangent, binormal

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

    def _processBone( self, maxNode ): 
        assert( self._isBoneNode( maxNode ) )

        if maxNode in self.maxNodeToJointMap:
            # prevent recursion
            return self.maxNodeToJointMap[maxNode]

        maxlog.info(f'processing bone: {maxNode.name}')
        jointMeta = self.metadata.getJointByName( maxNode.name )
        attribs = MtJointAttribData( maxNode, jointMeta )
        joint = imJoint(
            name=maxNode.name, 
            id=attribs.id, 
            worldMtx=self._convertMaxMatrix3ToNclMat44( maxNode.transform ),
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
        maxlog.info('processing bones')
        
        # convert all joints first
        # so we can reference them when building the primitives
        self.maxNodeToJointMap = dict()
        self.jointToMaxNodeMap = dict()
        self.jointIdxByName = dict()
        
        if self.ref != None and self.useRefJoints:
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
            for maxNode in rt.objects:
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
        
        if inExt == 'tex':
            # convert tex to dds
            maxlog.info('converting TEX {} to DDS {}'.format(inPath, outPath))
            tex = rTextureData()
            tex.loadBinaryFile( inPath )
            tex.toDDS().saveFile( outPath )
            
            if outExt != 'dds':
                # try to convert with texconv
                maxlog.debug('\texconv start')
                texconv( outPath, outPath=outBasePath, fileType=outExt, pow2=False, fmt='RGBA', srgb=True)
                maxlog.debug('texconv end\n')
        else:
            if outExt != 'tex':
                raise Exception( "Unsupported output format: " + outExt )
            
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
            
            tex.saveBinaryFile( outPath )
            
    def _processTextureMap( self, textureMap ):
        if textureMap != None and not textureMap in self._textureMapCache:
            # add to cache
            self._textureMapCache[textureMap] = True
            
            maxlog.info(f'processing texture: {textureMap.filename}')
            if os.path.exists(textureMap.filename):
                if self.outPath.hash != None:
                    outTexPath = os.path.splitext(textureMap.filename)[0] + '.241f5deb.tex'
                else:
                    outTexPath = os.path.splitext(textureMap.filename)[0] + '.tex'
                if not os.path.exists(outTexPath):
                    maxlog.info('converting texture to TEX')
                    self._convertTextureToTEX( textureMap.filename, outTexPath, None, None )
                else:
                    maxlog.info(f'skipping texture conversion because {outTexPath} already exists')
            else:
                maxlog.info('skipping texture conversion because {textureMap.filename} does not exist')
     
    def _processMaterial( self, material ):
        if material not in self._materialCache:
            # add to cache
            self._materialCache[material] = True
            
            maxlog.info(f'processing material: {material.name}')
            if mtmaxconfig.exportTexturesToTex:
                if hasattr(material, 'base_color_map'): self._processTextureMap( material.base_color_map )
                if hasattr(material, 'specular_map'): self._processTextureMap( material.specular_map )
                if hasattr(material, 'glossiness_map' ): self._processTextureMap( material.glossiness_map )
                if hasattr(material, 'ao_map' ): self._processTextureMap( material.ao_map )
                if hasattr(material, 'norm_map' ): self._processTextureMap( material.norm_map )
                if hasattr(material, 'emit_color_map' ): self._processTextureMap( material.emit_color_map )
                if hasattr(material, 'opacity_map' ): self._processTextureMap( material.opacity_map )
                if hasattr(material, 'displacement_map' ): self._processTextureMap( material.displacement_map )
            
    def _processMesh( self, maxNode ):
        maxlog.info(f'processing mesh: {maxNode.name}')
        attribs = MtPrimitiveAttribData(maxNode)
            
        if self.exportSkin:
            maxlog.debug('getting skin modifier')
            rt.execute('max modify mode')
            rt.select( maxNode )
            maxSkin = rt.modPanel.getCurrentObject()
            hasSkin = rt.isKindOf( maxSkin, rt.Skin )
        else:
            hasSkin = False

        if self.exportVertexNormals:
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
            
            for j in range( 0, 3 ):
                vertIdx = face[j]
                tvertIdx = tvFace[j]

                if matId not in tempMeshes:
                    # create temporary mesh for this material
                    tempMeshes[matId] = TempMesh(
                        maxNode.material[matId-1] if rt.classOf(maxNode.material) == rt.Multimaterial else maxNode.material
                    )

                tempMesh = tempMeshes[matId]
                if tempMesh.material != None:
                    self._processMaterial( tempMesh.material )
                
                tempMesh.positions.append( self._convertMaxPoint3ToNclVec3( rt.getVert( maxMesh, vertIdx ) ) )
                
                if self.exportVertexNormals:
                    tempMesh.normals.append( self._convertMaxPoint3ToNclVec3( editNormalsMod.GetNormal( editNormalsMod.GetNormalId( i + 1, j + 1 ) )))
                else:
                    tempMesh.normals.append( self._convertMaxPoint3ToNclVec3( rt.getNormal( maxMesh, vertIdx ) ) )
                
                tempMesh.uvs.append( self._convertMaxPoint3ToNclVec3UV( rt.getTVert( maxMesh, tvertIdx ) ) )

                if hasSkin:
                    weightCount = rt.skinOps.getVertexWeightCount( maxSkin, vertIdx )
                    vertexWeights = []
                    vertexWeightIndices = []
                    for k in range( 0, weightCount ):
                        boneId = rt.skinops.getVertexWeightBoneId( maxSkin, vertIdx, k + 1 )
                        boneWeight = rt.skinOps.getVertexWeight( maxSkin, vertIdx, k + 1 )
                        boneName = rt.skinOps.getBoneName( maxSkin, boneId, 0 )
                        jointIdx = self.jointIdxByName[ boneName ]
                        vertexWeights.append( boneWeight )
                        vertexWeightIndices.append( jointIdx )
                    tempMesh.weights.append( vertexWeights )
                    tempMesh.weightIndices.append( vertexWeightIndices )
                else:
                    tempMesh.weights.append( [1] )
                    tempMesh.weightIndices.append( [2] )

        # remove temporary modifiers
        if self.exportVertexNormals:
            maxlog.debug('delete temporary edit normals modifier')
            rt.deleteModifier( maxNode, editNormalsMod )

        # # calculate tangents
        # for i in range( 0, len( positions ), 3 ):
        #     faceTangents = [glm.vec3(),glm.vec3(),glm.vec3()]
        #     faceBitangents = [glm.vec3(),glm.vec3(),glm.vec3()]
        #     self.CalculateTangentsBitangents(
        #         [positions[i+0], positions[i+1], positions[i+2]],
        #         [normals[i+0], normals[i+1], normals[i+2]],
        #         [uvs[i+0], uvs[i+1], uvs[i+2]],
        #         faceTangents,
        #         faceBitangents)
        #     tangents.append(faceTangents[0])
        #     tangents.append(faceTangents[1])
        #     tangents.append(faceTangents[2])

        # create optimized primitives
        for tempMesh in tempMeshes.values():
            prim = imPrimitive(
                maxNode.name, 
                tempMesh.material.name if tempMesh.material != None else "default_material",
            )
            maxlog.info(f'processing submesh with material {prim.materialName}')

            # copy over attribs
            if attribs.flags != None: prim.flags = attribs.flags
            if attribs.groupId != None: prim.group = self.model.getGroupById(attribs.groupId)
            if attribs.lodIndex != None: prim.lodIndex = attribs.lodIndex
            if attribs.renderFlags != None: prim.renderFlags = attribs.renderFlags
            if attribs.id != None: prim.id = attribs.id
            if attribs.field2c != None: prim.field2c = attribs.field2c

            # optimize vertex buffer
            vertexIdxLookup = dict()
            nextVertexIdx = 0
            for i in range( 0, len( tempMesh.positions ) ):
                cv = TempVertex()
                cv.position = (tempMesh.positions[i][0], tempMesh.positions[i][1], tempMesh.positions[i][2])
                cv.normal = (tempMesh.normals[i][0], tempMesh.normals[i][1], tempMesh.normals[i][2])
                cv.uv = (tempMesh.uvs[i][0], tempMesh.uvs[i][1])

                # TODO: figure out how to generate proper tangents
                #cv.tangent = cv.normal
                #cv.tangent = (tangents[i][0], tangents[i][1], tangents[i][2])

                if hasSkin:
                    cv.weights = tuple(tempMesh.weights[i])
                    cv.weightIndices = tuple(tempMesh.weightIndices[i])    

                if cv not in vertexIdxLookup:
                    idx = nextVertexIdx
                    nextVertexIdx += 1
                    vertexIdxLookup[cv] = idx

                    prim.positions.append( NclVec3( cv.position ) )
                    prim.normals.append( NclVec3( cv.normal ) )
                    prim.uvs.append( NclVec2( cv.uv ) ) 
                    prim.tangents.append( NclVec3( cv.tangent ) )

                    vtxWeight = imVertexWeight()
                    vtxWeight.indices = cv.weightIndices
                    vtxWeight.weights = cv.weights
                    prim.weights.append( vtxWeight )
                else:
                    idx = vertexIdxLookup.get(cv)

                prim.indices.append(idx)

            self.model.primitives.append( prim )
        
    def _processMeshes( self ):
        # convert meshes
        maxlog.info('processing meshes')
        for maxNode in rt.objects:
            if not self._shouldExportNode( maxNode ) or not self._isMeshNode( maxNode ):
                continue
            
            mtmaxutil.updateUI()
            self._processMesh( maxNode )

    def _processGroups( self ):
        maxlog.info('processing groups')
        if self.ref != None and self.useRefGroups:
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
                maxlog.debug(str(group))
                self.model.groups.append(group)
        else:
            # process all groups in the scene
            for maxNode in rt.objects:
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
                    #boundingSphere=attribs.bsphere if attribs.bsphere != None else None,
                )
                maxlog.debug(str(group))

    def _processPml( self ):
        maxlog.info('processing pml')
        if self.ref != None and self.useRefPml:
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
                maxlog.debug(str(pml))
                self.model.primitiveJointLinks.append(pml)
        else:
            # TODO: represent these in the scene
            pass
    
    def _writeBinaries( self ):
        maxlog.debug('converting intermediate model to binary model format')
        binMod = self.model.toBinaryModel()
        
        maxlog.debug('writing binary model')
        stream = NclBitStream()
        binMod.write( stream )
        util.saveByteArrayToFile( self.outPath.fullPath, stream.getBuffer() )
        
        if mtmaxconfig.exportMrlYml and self.mrl != None:
            if self.outPath.hash != None:
                mrlExportPath = self.outPath.basePath + '/' + self.outPath.baseName + '.2749c8a8.mrl' 
            else:
                mrlExportPath = self.outPath.basePath + '/' + self.outPath.baseName + '.mrl'
            maxlog.info(f'exporting mrl yml to {mrlExportPath}')
            self.mrl.saveBinaryFile( mrlExportPath )
    
    def exportModel( self, path ):
        maxlog.info(f'exporting to {path}')
        
        # start building intermediate model data for conversion
        self.model = imModel()
        self.outPath = util.ResourcePath(path)
        self.metadata = ModelMetadata()
        self.mrl = None

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

        maxlog.info('processing scene')
        if self.ref != None and self.useRefBounds:
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