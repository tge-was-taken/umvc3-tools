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
)

rollout MtInfoRollout "MT Framework Importer/Exporter"
(
	label lblTitle2 "Ultimate Marvel vs Capcom 3"
	label lblVersion "Version 0.1" align:#center
	label lblAuthor "© 2021 TGE" align:#center
)

rollout MtAttribsRollout "Attribs"
(
	checkbox chkFlipUpAxis "Flip up axis" checked:true align:#left;
	spinner spnScale "Scale" range:[0,1000000,1] align:#left;

	fn emit args = 
	(
		mtCallPythonFunc "MtAttribsRollout" "onEvent" args
	)
	
	on chkFlipUpAxis 	changed state do emit #("chkFlipUpAxisChanged", state)
	on spnScale 		changed state do emit #("spnScaleChanged", state)
)

rollout MtUtilitiesRollout "Utilities"
(
	group "Add MT attributes to selected object" (
		button btnAddJointAttribs "Joint"
		button btnAddGroupAttribs "Group"
		button btnAddPmlAttribs "PML"
		button btnAddPrimAttribs "Primitive"
	)

	group "Create MT helper" (
		button btnCreateGroup "Group"
	)

	fn emit args = 
	(
		mtCallPythonFunc "MtUtilitiesRollout" "onEvent" args
	)

	on btnAddJointAttribs	pressed do emit #("btnAddJointAttribsPressed")
	on btnAddGroupAttribs	pressed do emit #("btnAddGroupAttribsPressed")
	on btnAddPmlAttribs		pressed do emit #("btnAddPmlAttribsPressed")
	on btnAddPrimAttribs	pressed do emit #("btnAddPrimAttribsPressed")
	on btnCreateGroup 		pressed do emit #("btnCreateGroupPressed")
)

rollout MtModelImportRollout "Model import"
(	
	fn _width = ( MtModelImportRollout.width )
	fn _height = ( MtModelImportRollout.height )

	label lblFile "File" across:1 align:#left
	edittext edtFile across:2 width:(_width() - 60) offset:[0,0]
	button btnFile "..." align:#right across:2 offset:[10,-2]
	
	label lblMetadata "Metadata" across:1 align:#left
	edittext edtMetadata across:2 width:(_width() - 60) offset:[0,0]
	button btnMetadata "..." align:#right across:2 offset:[10,-2]
	
	label lblImportFilters "Import filters" offset:[0,10]
	checkbox chkImportWeights "Weights" checked:true across:3 align:#center --offset:[0, 20]
	checkbox chkImportNormals "Normals" checked:true  across:3 align:#center --offset:[0, 20]
	checkbox chkImportGroups "Groups" checked:true across:3 align:#center --offset:[0, 20]
	
	checkbox chkImportSkeleton "Skeleton" checked:true across:3 align:#center
	checkbox chkImportPrimitives "Primitives" checked:true across:3 align:#center
	label lblDummy ""
	
	checkbox chkConvertDDS "Convert textures to DDS" checked:true offset: [0, 10]
	checkbox chkSaveMrlYml "Convert MRL to YML" checked:true --offset: [0, 10]
	
	
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
	
	label lblRef "Reference model" across:1 align:#left
	edittext edtRef across:2 width:(_width() - 60) offset:[-0,0]
	button btnRef "..." align:#right across:2 offset:[10,-2]
	
	label lblMetadata "Metadata" across:1 align:#left
	edittext edtMetadata across:2 width:(_width() - 60) offset:[-0,0]
	button btnMetadata "..." align:#right across:2 offset:[10,-2]

	label lblFile "File" across:1 align:#left
	edittext edtFile across:2 width:(_width() - 60) offset:[-0,0]
	button btnFile "..." align:#right across:2 offset:[10,-2]
	
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
)

rollout MtLogRollout "Log" height:300
(
	edittext edtLog "" align:#center height:300
)