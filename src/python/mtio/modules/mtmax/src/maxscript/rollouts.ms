-- convert maxscript value to python value 
fn mtEscapeStr val =
(
	substituteString val @"\" @"\\"
)

fn mtMxsToPyVal val =
(
	result = "None"
	
	case ( classof val ) of
	(
		BooleanClass:
		(
			if val == true then result = "True"
			else result = "False"
		)
		String: result = "\"" + mtEscapeStr( val ) + "\""
		default: result = val as string
	)
	
	result
)

-- execute a python function from maxscript
fn mtCallPythonFunc module func args =
(
	try
	(
		local code = ""
		
		if module != undefined then
			code += module + "."
		
		code += func + "("
		if args.count > 0 do
		(
			code += mtMxsToPyVal( args[1] )
			
			for i = 2 to args.count do
				code += ", " + mtMxsToPyVal( args[i] )

		)
		
		code += ")"
		
		print code
		python.execute code
	) catch (
		print( "Exception while calling python function " + module + "." + func + "(" + ( args as string ) + ")" + "\nException: " + (getCurrentException() as string) )
	)
)

MtMaxVersionFull = "Version " + MtMaxVersion
MtMaxPluginTitle = "Mt Framework Importer/Exporter " + MtMaxVersionFull

rollout MtMaxInfoRollout MtMaxPluginTitle
(
	label lblVersion MtMaxVersionFull align:#center
	label lblAuthor "© 2021-2022 TGE" align:#center
)

rollout MtMaxSettingsRollout "Global settings"
(
	checkbox chkFlipUpAxis "Flip up axis" checked:true align:#left;
	checkbox chkLukasCompat "Compatibility with Lukas' script" checked:false align:#left;
	dropdownlist ddlGame "Game" selection:1 align:#left items:#(
		"Ultimate Marvel vs Capcom 3 (PC)", 
		"The Great Ace Attorney Chronicles (PC)"
	);

	fn emit args = 
	(
		mtCallPythonFunc "MtMaxSettingsRollout" "onEvent" args
	)
	
	on chkFlipUpAxis 	changed state do emit #("chkFlipUpAxisChanged", state)
	on chkLukasCompat 	changed state do emit #("chkLukasCompatChanged", state)
	on ddlGame 	selected i do emit #("ddlGameSelected", i)
)

rollout MtMaxUtilitiesRollout "Utilities"
(
	group "Add MT attributes to selected object" (
		button btnAddJointAttribs "Joint" across:8
		button btnAddGroupAttribs "Group"
		button btnAddEnvelopeAttribs "Envelope"
		button btnAddPrimAttribs "Primitive"
		label pad1;
		label pad2;
		label pad3;
		label pad4;
	)

	group "Remove MT attributes from selected object" (
		button btnRemJointAttribs "Joint" across:8
		button btnRemGroupAttribs "Group"
		button btnRemEnvelopeAttribs "Envelope"
		button btnRemPrimAttribs "Primitive"
		label pad5;
		label pad6;
		label pad7;
		label pad8;
	)

	group "Create MT helper" (
		button btnCreateGroup "Group" across:8
	)

	fn emit args = 
	(
		mtCallPythonFunc "MtMaxUtilitiesRollout" "onEvent" args
	)

	on btnAddJointAttribs	pressed do emit #("btnAddJointAttribsPressed")
	on btnAddGroupAttribs	pressed do emit #("btnAddGroupAttribsPressed")
	on btnAddEnvelopeAttribs		pressed do emit #("btnAddEnvelopeAttribsPressed")
	on btnAddPrimAttribs	pressed do emit #("btnAddPrimAttribsPressed")
	on btnRemJointAttribs	pressed do emit #("btnRemJointAttribsPressed")
	on btnRemGroupAttribs	pressed do emit #("btnRemGroupAttribsPressed")
	on btnRemEnvelopeAttribs		pressed do emit #("btnRemEnvelopeAttribsPressed")
	on btnRemPrimAttribs	pressed do emit #("btnRemPrimAttribsPressed")
	on btnCreateGroup 		pressed do emit #("btnCreateGroupPressed")
)

rollout MtMaxModelImportRollout "Model import"
(	
	fn _width = ( MtMaxModelImportRollout.width )
	fn _height = ( MtMaxModelImportRollout.height )

	label lblFile "Input model file" across:1 align:#left
	edittext edtFile across:2 width:(_width() - 60) offset:[0,0]
	button btnFile "..." align:#right across:2 offset:[10,-2]
	
	label lblMetadata "Metadata file (optional)" across:1 align:#left
	edittext edtMetadata across:2 width:(_width() - 60) offset:[0,0]
	button btnMetadata "..." align:#right across:2 offset:[10,-2]
	
	group "Import filters" (
		checkbox chkImportWeights "Weights" checked:true across:3 align:#center --offset:[0, 20]
		checkbox chkImportNormals "Normals" checked:true  across:3 align:#center --offset:[0, 20]
		checkbox chkImportGroups "Groups" checked:true across:3 align:#center --offset:[0, 20]

		checkbox chkImportSkeleton "Skeleton" checked:true across:3 align:#center
		checkbox chkImportPrimitives "Meshes" checked:true across:3 align:#center
		label lblDummy ""
	)
	
	group "Additional options" (
		spinner spnScale "Scale" range:[0,1000000,1] align:#left;
		checkbox chkBakeScale "Bake scale into translation" checked:false
		checkbox chkConvertDDS "Convert textures to DDS" checked:true 
		checkbox chkSaveMrlYml "Convert MRL to YML" checked:true
		checkbox chkCreateLayer "Create layer" checked:true
	)
	
	label lblImportProgressCategory;
	progressBar pbImport;
	label lblImportProgressSubCategory;
	progressBar pbImportSub;
	
	button btnImport "Import" align:#center across:1;
	
	--groupbox grpImportFilter "Data import filters" pos: [12, 30] height:65
	
	fn emit args = 
	(
		mtCallPythonFunc "MtMaxModelImportRollout" "onEvent" args
	)
	
	on chkImportWeights 	changed state 	do emit #("chkImportWeightsChanged", state)
	on btnImport 			pressed 		do emit #("btnImportPressed")
	on btnFile 				pressed 		do emit #("btnFilePressed")
	on edtFile 				changed state 	do emit #("edtFileChanged", state)
	on edtMetadata 			changed state	do emit #("edtMetadataChanged", state)
	on btnMetadata			pressed 		do emit #("btnMetadataPressed")
	on chkImportNormals 	changed state	do emit #("chkImportNormalsChanged", state)
	on chkImportGroups		changed state	do emit #("chkImportGroupsChanged", state)
	on chkImportSkeleton 	changed state	do emit #("chkImportSkeletonChanged", state)
	on chkImportPrimitives	changed state	do emit #("chkImportPrimitivesChanged", state)
	on chkConvertDDS		changed state	do emit #("chkConvertDDSChanged", state)
	on chkSaveMrlYml		changed state	do emit #("chkSaveMrlYmlChanged", state)
	on chkCreateLayer		changed state	do emit #("chkCreateLayerChanged", state)
	on spnScale				changed state	do emit #("spnScaleChanged", state)
	on chkBakeScale			changed state	do emit #("chkBakeScaleChanged", state)
)

rollout MtMaxModelExportRollout "Model export"
(
	fn _width = ( MtMaxModelImportRollout.width )
	fn _height = ( MtMaxModelImportRollout.height )
	
	label lblFile "Output model file" across:1 align:#left
	edittext edtFile across:2 width:(_width() - 60) offset:[-0,0]
	button btnFile "..." align:#right across:2 offset:[10,-2]

	label lblRoot "Extracted archive directory" across:1 align:#left
	edittext edtRoot across:2 width:(_width() - 60) offset:[-0,0]
	button btnRoot "..." align:#right across:2 offset:[10,-2]
	
	label lblRef "Reference/original model file (optional)" across:1 align:#left
	edittext edtRef across:2 width:(_width() - 60) offset:[-0,0]
	button btnRef "..." align:#right across:2 offset:[10,-2]
	
	label lblMetadata "Metadata file (optional)" across:1 align:#left
	edittext edtMetadata across:2 width:(_width() - 60) offset:[-0,0]
	button btnMetadata "..." align:#right across:2 offset:[10,-2]
	
	group "Export filters" (
		checkbox chkExportWeights "Weights" checked:true across:3 align:#center --offset:[0, 20]
		checkbox chkExportNormals "Explicit normals" checked:true  across:3 align:#center --offset:[0, 20]
		checkbox chkExportGroups "Groups" checked:true across:3 align:#center --offset:[0, 20]

		checkbox chkExportSkeleton "Skeleton" checked:true across:3 align:#center
		checkbox chkExportPrimitives "Meshes" checked:true across:3 align:#center
		label lblDummy ""
	)
	group "Generate MRL" (
		checkbox chkExportGenerateMrl "Enable" checked:true
		combobox cbxExportMaterialPreset "Material preset" --items:#("nDraw::MaterialChar", "nDraw::MaterialStgSimple")
	)

	group "Use existing MRL YML" (
		checkbox chkExportMrl "Enable" checked:true
		label lblMrlYml "File path" across:1 align:#left
		edittext edtMrlYml across:2 width:(_width() - 60) offset:[-0,0]
		button btnMrlYml "..." align:#right across:2 offset:[10,-2]
	)

	group "Additional options" (
		spinner spnScale "Scale" range:[0,1000000,1] align:#left;
		checkbox chkBakeScale "Bake scale into translation" checked:false
		checkbox chkExportTex "Convert textures to TEX" checked:true 
		checkbox chkExportTexOverwrite "Overwrite existing textures" checked:false
		checkbox chkExportGroupPerMesh "Export group per mesh" checked:false
		checkbox chkExportGenerateEnvelopes "Generate envelopes" checked:true
	)

	label lblExportProgressCategory;
	progressBar pbExport;
	label lblExportProgressSubCategory;
	progressBar pbExportSub;
	
	button btnExport "Export" align:#center across:1;

	fn emit args = 
	(
		mtCallPythonFunc "MtMaxModelExportRollout" "onEvent" args
	)
	
	on btnExport 			pressed 		do emit #("btnExportPressed" )
	on btnFile 				pressed 		do emit #("btnFilePressed")
	on edtFile 				changed state 	do emit #("edtFileChanged", state)
	on edtMetadata 			changed state	do emit #("edtMetadataChanged", state)
	on btnMetadata			pressed 		do emit #("btnMetadataPressed")
	on edtRef 				changed state	do emit #("edtRefChanged", state)
	on btnRef				pressed 		do emit #("btnRefPressed")
	on edtMrlYml 			changed state	do emit #("edtMrlYmlChanged", state)
	on btnMrlYml			pressed 		do emit #("btnMrlYmlPressed")
	on chkExportTex			changed state	do emit #("chkExportTexChanged", state)
	on chkExportMrl			changed state 	do emit #("chkExportMrlChanged", state)
	on chkExportNormals		changed state 	do emit #("chkExportNormalsChanged", state)
	on chkExportWeights 	changed state 	do emit #("chkExportWeightsChanged", state)
	on chkExportGroups		changed state	do emit #("chkExportGroupsChanged", state)
	on chkExportSkeleton	changed state	do emit #("chkExportSkeletonChanged", state)
	on chkExportPrimitives	changed state	do emit #("chkExportPrimitivesChanged", state)
	on chkExportGenerateMrl changed state	do emit #("chkExportGenerateMrlChanged", state)
	on edtTextureRoot		changed state	do emit #("edtTextureRootChanged", state)
	on btnTextureRoot		pressed			do emit #("btnTextureRootPressed")
	on edtRoot				changed state	do emit #("edtRootChanged", state)
	on btnRoot				pressed			do emit #("btnRootPressed")
	on chkExportTexOverwrite changed state 	do emit #("chkExportTexOverwriteChanged", state)
	on spnScale				changed state	do emit #("spnScaleChanged", state)
	on chkBakeScale			changed state	do emit #("chkBakeScaleChanged", state)
	on chkExportGroupPerMesh changed state do emit #("chkExportGroupPerMeshChanged", state)
	on chkExportGenerateEnvelopes changed state do emit #("chkExportGenerateEnvelopesChanged", state)
	on cbxExportMaterialPreset selected i do emit #("cbxExportMaterialPresetSelected", cbxExportMaterialPreset.items[i])
)

rollout MtMaxDebugRollout "Debug"
(
	checkbox chkDisableLog "Disable logging"
	edittext edtExportForceShader "Force shader on export"
	checkbox chkDisableTransform "Disable transform"

	fn emit args = 
	(
		mtCallPythonFunc "MtMaxDebugRollout" "onEvent" args
	)

	on chkDisableLog changed state do emit #("chkDisableLogChanged", state)
	on edtExportForceShader changed state do emit #("edtExportForceShaderChanged", state)
	on chkDisableTransform changed state do emit #("chkDisableTransformChanged", state)
)