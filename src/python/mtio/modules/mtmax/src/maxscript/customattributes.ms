
global testCustomAttributes = False
if ( testCustomAttributes ) then
(
	clearListener()
	custAttributes.delete $ mtPrimitiveAttributesInstance
	custAttributes.delete $ mtJointAttributesInstance
	custAttributes.delete $ mtMaterialAttributesInstance
	custAttributes.delete $ mtModelGroupAttributesInstance
)

mtPrimitiveAttributesInstance = attributes mtPrimitiveAttributes attribID: #(0x1ffff7f5, 0x14cc7432)
(
	parameters main rollout:params
	(
		flags type:#string ui:flags default:""
		groupId type:#string ui:groupId default:"inherit"
		lodIndex type:#integer ui:lodIndex default:-1
		matIndex type:#string ui:matIndex default:""
		vertexFlags type:#string ui:vertexFlags default:""
		vertexStride type:#string ui:vertexStride default:""
		renderFlags type:#string ui:renderFlags default:""
		vertexStartIndex type:#string ui:vertexStartIndex default:""
		vertexBufferOffset type:#string ui:vertexBufferOffset default:""
		shaderName type:#string ui:shaderName default:""
		indexBufferOffset type:#string ui:indexBufferOffset default:""
		indexCount type:#string ui:indexCount default:""
		indexStartIndex type:#string ui:indexStartIndex default:""
		boneMapStartIndex type:#string ui:boneMapStartIndex default:""
		primitiveJointLinkCount type:#string ui:primitiveJointLinkCount default:""
		id type:#integer ui:id default:-1
		minVertexIndex type:#string ui:minVertexIndex default:""
		maxVertexIndex type:#string ui:maxVertexIndex default:""
		field2C type:#integer ui:field2C default:0
		primitiveJointLinkPtr type:#string ui:primitiveJointLinkPtr default:""
	)
	
	rollout params "MT Primitive Attributes"
	(
		label flagsLabel "Flags" across:2 align:#left
		edittext flags		"" type:#string across:2

		label groupIdLabel "Group ID" across:2 align:#left
		edittext groupId "" type:#string across:2
		
		label lodIndexLabel "LOD level" across:2 align:#left
		spinner lodIndex 	"" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label renderFlagsLabel "Render flags" across:2 align:#left
		edittext renderFlags "" type:#string across:2
		
		label idLabel "ID" across:2 align:#left
		spinner id	"" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label field2CLabel "Field 2C" across:2 align:#left
		spinner field2C	"" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]

		group "Read only" (
			label matIndexLabel "Material index" across:1 align:#left
			edittext matIndex 	"" type:#integer across:1 readonly:true

			label vertexFlagsLabel "Vertex flags" across:1 align:#left
			edittext vertexFlags	"" type:#string across:1 readonly:true

			label vertexStrideLabel "Vertex stride" across:1 align:#left
			edittext vertexStride	"" type:#string across:1 readonly:true

			label vertexStartIndexLabel "Vertex start index" across:1 align:#left
			edittext vertexStartIndex	"" type:#string across:1 readonly:true

			label vertexBufferOffsetLabel "Vertex buffer offset" across:1 align:#left
			edittext vertexBufferOffset	"" type:#string across:1 readonly:true

			label shaderNameLabel "Shader" across:1 align:#left
			edittext shaderName "" type:#string across:1 readonly:true
		
			label indexBufferOffsetLabel "Index buffer offset" across:1 align:#left
			edittext indexBufferOffset	"" type:#string across:1 readonly:true

			label indexCountLabel "Index count" across:1 align:#left
			edittext indexCount	"" type:#string across:1 readonly:true

			label indexStartIndexLabel "Index start index" across:1 align:#left
			edittext indexStartIndex	"" type:#string across:1 readonly:true

			label boneMapStartIndexLabel "Bone map start index" across:1 align:#left
			edittext boneMapStartIndex	"" type:#string across:1 readonly:true

			label primitiveJointLinkCountLabel "Primitive joint link count" across:1 align:#left
			edittext primitiveJointLinkCount	"" type:#string across:1 readonly:true

			label minVertexIndexLabel "Min vertex index" across:1 align:#left
			edittext minVertexIndex	"" type:#string across:1 readonly:true

			label maxVertexIndexLabel "Max vertex index" across:1 align:#left
			edittext maxVertexIndex	"" type:#string across:1 readonly:true

			label primitiveJointLinkPtrLabel "Primitive joint link pointer" across:1 align:#left
			edittext primitiveJointLinkPtr	"" type:#string across:1 readonly:true
		)
	)
)

mtJointAttributesInstance = attributes mtJointAttributes attribID: #(0x14e24dd0, 0xafeac75)
(
	parameters main rollout:params
	(
		id type:#integer ui:id default:-1
		parentIndex type:#string ui:parentIndex default:""
		symmetryIndex type:#string ui:symmetryIndex default:""
		symmetryName type:#string ui:symmetryName default:""
		field03 type:#integer ui:field03 default:0
		field04 type:#float ui:field04 default:0.0
		length type:#string ui:length default:""
		offsetX type:#string ui:offsetX default:""
		offsetY type:#string ui:offsetY default:""
		offsetZ type:#string ui:offsetZ default:""
	)
	
	rollout params "MT Joint Attributes"
	(
		label idLabel "ID" across:2 align:#left
		spinner id "" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label symmetryNameLabel "Symmetrical opposite" across:1 align:#left
		edittext symmetryName 	"" type:#string across:1
		
		label field03Label "Field 03" across:2 align:#left
		spinner field03 "" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label field04Label "Field 04" across:2 align:#left
		spinner field04 "" type:#float across:2 width:64 offset:[-15,0] range:[-999999, 999999, 0.001]

		group "Read only" (
			label parentIndexLabel "Parent index" across:1 align:#left
			edittext parentIndex 	"" type:#string across:1 readonly:true

			label symmetryIndexLabel "Symmetry index" across:1 align:#left
			edittext symmetryIndex 	"" type:#string across:1 readonly:true

			label lengthLabel "Length" across:1 align:#left
			edittext length 	"" type:#string across:1 readonly:true
	
			label offsetXLabel "Offset X" across:1 align:#left
			edittext offsetX 	"" type:#string across:1 readonly:true

			label offsetYLabel "Offset Y" across:1 align:#left
			edittext offsetY 	"" type:#string across:1 readonly:true

			label offsetZLabel "Offset Z" across:1 align:#left
			edittext offsetZ 	"" type:#string across:1 readonly:true
		)
	)
)

mtMaterialAttributesInstance = attributes mtMaterialAttributes attribID: #(0x4256de97, 0x7fbd90)
(
	parameters main rollout:params
	(
		type type:#string ui:type default:"nDraw::MaterialChar"
		blendState type:#string ui:blendState default:"BSSolid"
		depthStencilState type:#string ui:depthStencilState default:"DSZTestWriteStencilWrite"
		rasterizerState type:#string ui:rasterizerState default:"RSMeshCN"
		cmdListFlags type:#string ui:cmdListFlags default:"0x400"
		matFlags type:#string ui:matFlags default:"0x8c800803"
	)
	
	rollout params "MT Material Attributes"
	(
		label typeLabel "Type" across:1 align:#left
		edittext type "" type:#string across:1
		
		label blendStateLabel "Blend state" across:1 align:#left
		edittext blendState "" type:#string across:1
	
		label depthStencilStateLabel "Depth stencil state" across:1 align:#left
		edittext depthStencilState "" type:#string across:1
		
		label rasterizerStateLabel "Rasterizer state" across:1 align:#left
		edittext rasterizerState "" type:#string across:1
		
		label cmdListFlagsLabel "Command list flags" across:1 align:#left
		edittext cmdListFlags "" type:#string across:1
		
		label matFlagsLabel "Material flags" across:1 align:#left
		edittext matFlags "" type:#string across:1
	)
)

mtModelGroupAttributesInstance = attributes mtModelGroupAttributes attribID: #(0x23f7b5ab, 0x6c9d680b)
(
	parameters main rollout:params
	(
		id type:#integer ui:id default:1
		field04 type:#integer ui:field04 default:0
		field08 type:#integer ui:field08 default:0
		field0c type:#integer ui:field0c default:0
		bsphere type:#point3 default:[0,0,0]
	)
	
	rollout params "MT Group Attributes"
	(
		label idLabel "ID" across:2 align:#left
		spinner id "" type:#integer across:2 width:64 offset:[-15,0] range:[0, 999999, 1]
		
		label field04Label "Field 04" across:2 align:#left
		spinner field04 "" type:#integer across:2 width:64 offset:[-15,0] range:[0, 999999, 1]
		
		label field08Label "Field 08" across:2 align:#left
		spinner field08 "" type:#integer across:2 width:64 offset:[-15,0] range:[0, 999999, 1]
		
		label field0cLabel "Field 0C" across:2 align:#left
		spinner field0c "" type:#integer across:2 width:64 offset:[-15,0] range:[0, 999999, 1]
	)
)

fn doTestCustomAttributes =
(
	if ( testCustomAttributes ) then
	(
		custAttributes.add $ mtPrimitiveAttributesInstance
		custAttributes.add $ mtJointAttributesInstance
		custAttributes.add $ mtMaterialAttributesInstance
		custAttributes.add $ mtModelGroupAttributesInstance
	)
)

doTestCustomAttributes()