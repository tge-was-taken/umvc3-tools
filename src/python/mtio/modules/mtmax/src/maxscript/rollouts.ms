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

rollout MtInfoRollout "MT Framework Importer/Exporter"
(
	label lblTitle2 "Ultimate Marvel vs Capcom 3"
	label lblVersion "Version 1.0.10 Beta" align:#center
	label lblAuthor "© 2021-2022 TGE" align:#center
)

rollout MtSettingsRollout "Global settings"
(
	checkbox chkFlipUpAxis "Flip up axis" checked:true align:#left;
	spinner spnScale "Scale" range:[0,1000000,1] align:#left;

	fn emit args = 
	(
		mtCallPythonFunc "MtSettingsRollout" "onEvent" args
	)
	
	on chkFlipUpAxis 	changed state do emit #("chkFlipUpAxisChanged", state)
	on spnScale 		changed state do emit #("spnScaleChanged", state)
)

rollout MtUtilitiesRollout "Utilities"
(
	group "Add MT attributes to selected object" (
		button btnAddJointAttribs "Joint" across:8
		button btnAddGroupAttribs "Group"
		button btnAddPmlAttribs "PML"
		button btnAddPrimAttribs "Primitive"
		label pad1;
		label pad2;
		label pad3;
		label pad4;
	)

	group "Remove MT attributes from selected object" (
		button btnRemJointAttribs "Joint" across:8
		button btnRemGroupAttribs "Group"
		button btnRemPmlAttribs "PML"
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
		mtCallPythonFunc "MtUtilitiesRollout" "onEvent" args
	)

	on btnAddJointAttribs	pressed do emit #("btnAddJointAttribsPressed")
	on btnAddGroupAttribs	pressed do emit #("btnAddGroupAttribsPressed")
	on btnAddPmlAttribs		pressed do emit #("btnAddPmlAttribsPressed")
	on btnAddPrimAttribs	pressed do emit #("btnAddPrimAttribsPressed")
	on btnRemJointAttribs	pressed do emit #("btnRemJointAttribsPressed")
	on btnRemGroupAttribs	pressed do emit #("btnRemGroupAttribsPressed")
	on btnRemPmlAttribs		pressed do emit #("btnRemPmlAttribsPressed")
	on btnRemPrimAttribs	pressed do emit #("btnRemPrimAttribsPressed")
	on btnCreateGroup 		pressed do emit #("btnCreateGroupPressed")
)

rollout MtModelImportRollout "Model import"
(	
	fn _width = ( MtModelImportRollout.width )
	fn _height = ( MtModelImportRollout.height )

	label lblFile "Input file" across:1 align:#left
	edittext edtFile across:2 width:(_width() - 60) offset:[0,0]
	button btnFile "..." align:#right across:2 offset:[10,-2]
	
	label lblMetadata "Metadata (optional)" across:1 align:#left
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
		checkbox chkConvertDDS "Convert textures to DDS" checked:true 
		checkbox chkSaveMrlYml "Convert MRL to YML" checked:true
	)
	
	
	button btnImport "Import" align:#center across:1;
	
	--groupbox grpImportFilter "Data import filters" pos: [12, 30] height:65
	
	fn emit args = 
	(
		mtCallPythonFunc "MtModelImportRollout" "onEvent" args
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
)

rollout MtModelExportRollout "Model export"
(
	fn _width = ( MtModelImportRollout.width )
	fn _height = ( MtModelImportRollout.height )
	
	label lblFile "Output file" across:1 align:#left
	edittext edtFile across:2 width:(_width() - 60) offset:[-0,0]
	button btnFile "..." align:#right across:2 offset:[10,-2]

	label lblRoot "Archive root path" across:1 align:#left
	edittext edtRoot across:2 width:(_width() - 60) offset:[-0,0]
	button btnRoot "..." align:#right across:2 offset:[10,-2]
	
	label lblRef "Reference/original model (optional)" across:1 align:#left
	edittext edtRef across:2 width:(_width() - 60) offset:[-0,0]
	button btnRef "..." align:#right across:2 offset:[10,-2]
	
	label lblMetadata "Metadata (optional)" across:1 align:#left
	edittext edtMetadata across:2 width:(_width() - 60) offset:[-0,0]
	button btnMetadata "..." align:#right across:2 offset:[10,-2]
	
	group "Export filters" (
		checkbox chkExportWeights "Weights" checked:true across:3 align:#center --offset:[0, 20]
		-- checkbox chkExportNormals "Normals" checked:true  across:3 align:#center --offset:[0, 20]
		checkbox chkExportGroups "Groups" checked:true across:3 align:#center --offset:[0, 20]
		label lblDummy2 ""

		checkbox chkExportSkeleton "Skeleton" checked:true across:3 align:#center
		checkbox chkExportPrimitives "Meshes" checked:true across:3 align:#center
		label lblDummy ""
	)
	group "Generate MRL" (
		checkbox chkExportGenerateMrl "Enable" checked:true
	)

	group "Use existing MRL YML" (
		checkbox chkExportMrl "Enable" checked:true
		label lblMrlYml "File path" across:1 align:#left
		edittext edtMrlYml across:2 width:(_width() - 60) offset:[-0,0]
		button btnMrlYml "..." align:#right across:2 offset:[10,-2]
	)

	group "Additional options" (
		checkbox chkExportTex "Convert textures to TEX" checked:true 
	)
	
	button btnExport "Export" align:#center across:1;

	fn emit args = 
	(
		mtCallPythonFunc "MtModelExportRollout" "onEvent" args
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
)