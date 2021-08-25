
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
		lodIndex type:#integer ui:lodIndex default:-1
		vertexFlags type:#string ui:vertexFlags default:""
		renderFlags type:#string ui:renderFlags default:""
		shaderName type:#string ui:shaderName default:""
		id type:#integer ui:id default:-1
		field2C type:#integer ui:field2C default:0
	)
	
	rollout params "MT Primitive Settings"
	(
		label flagsLabel "Flags" across:2 align:#left
		edittext flags		"" type:#string across:2
		
		label lodIndexLabel "LOD level" across:2 align:#left
		spinner lodIndex 	"" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label vertexFlagsLabel "Vertex flags" across:2 align:#left
		edittext vertexFlags	"" type:#string across:2 readonly:true
		
		label renderFlagsLabel "Render flags" across:2 align:#left
		edittext renderFlags "" type:#string across:2
		
		label shaderNameLabel "Shader" across:1 align:#left
		edittext shaderName "" type:#string across:1 readonly:true
		
		label idLabel "ID" across:2 align:#left
		spinner id	"" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label field2CLabel "Field 2C" across:2 align:#left
		spinner field2C	"" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
	)
)

mtJointAttributesInstance = attributes mtJointAttributes attribID: #(0x14e24dd0, 0xafeac75)
(
	parameters main rollout:params
	(
		id type:#integer ui:id default:-1
		symmetryName type:#string ui:symmetryName default:""
		field03 type:#integer ui:field03 default:0
		field04 type:#float ui:field04 default:0.0
	)
	
	rollout params "MT Joint Settings"
	(
		label idLabel "ID" across:2 align:#left
		spinner id "" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label symmetryNameLabel "Symmetrical opposite" across:1 align:#left
		edittext symmetryName 	"" type:#string across:1
		
		label field03Label "Field 03" across:2 align:#left
		spinner field03 "" type:#integer across:2 width:64 offset:[-15,0] range:[-1, 999999, 1]
		
		label field04Label "Field 04" across:2 align:#left
		spinner field04 "" type:#float across:2 width:64 offset:[-15,0] range:[-999999, 999999, 0.001]
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
	
	rollout params "MT Material Settings"
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
	
	rollout params "MT Group Settings"
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