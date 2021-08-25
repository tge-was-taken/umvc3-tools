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
fn mtExecPythonFunc module func args =
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

rollout MtSettingsRollout "Settings"
(
	checkbox chkConvertToZUp "Convert to Z Up" checked:true align:#left;
	spinner spnScale "Scale" range:[0,1000000,1] align:#left;
	
	on chkConvertToZUp 	changed state do mtExecPythonFunc "MtSettingsRollout" "chkConvertToZUpChanged" #(state)
	on spnScale 		changed state do mtExecPythonFunc "MtSettingsRollout" "spnScaleChanged" #(state)
)

rollout MtModelImportRollout "Model import" width:162 height:300
(
	label lblFile "File" across:3 align:#left
	edittext edtFile across:3 width:150 offset:[-35,0]
	button btnFile "..." align:#right across:3 offset:[10,-2]
	
	label lblProfile "Profile" across:2 align:#left
	edittext edtProfile across:2 width:150 offset:[-70,0]
	
	--label lblProfileFile "File" across:3 align:#left
	--edittext edtProfileFile across:3 width:170 offset:[-50,0]
	--button btnProfileFile "..." align:#right across:3 offset:[10,-2]
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

	fn mtCall func args = 
	(
		mtExecPythonFunc "MtModelImportRollout" func args
	)
	
	on chkImportWeights 	changed state 	do mtCall "chkImportWeightsChanged" #(state)
	on btnImport 			pressed 		do mtCall "btnImportPressed" #()
	on btnFile 				pressed 		do mtCall "btnFilePressed" #()
	on edtFile 				changed state 	do mtCall "edtFileChanged" #(state)
	on edtProfile 			changed state	do mtCall "edtProfileChanged" #(state)
	on chkImportNormals 	changed state	do mtCall "chkImportNormalsChanged" #(state)
	on chkImportGroups		changed state	do mtCall "chkImportGroupsChanged" #(state)
	on chkImportSkeleton 	changed state	do mtCall "chkImportSkeletonChanged" #(state)
	on chkImportPrimitives	changed state	do mtCall "chkImportPrimitivesChanged" #(state)
	on chkConvertDDS		changed state	do mtCall "chkConvertDDSChanged" #(state)
	on chkSaveMrlYml		changed state	do mtCall "chkSaveMrlYmlChanged" #(state)
)

rollout MtLogRollout "Log" height:300
(
	edittext edtLog "" align:#center height:300
)