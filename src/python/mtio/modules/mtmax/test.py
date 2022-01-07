from pymxs import runtime as rt
import glm


def dumpNormals():
	maxNode = rt.selection[0]
	maxMesh = rt.snapshotAsMesh(maxNode)
	faceCount = rt.getNumFaces(maxMesh)
	editNormalsMod = maxNode.modifiers[rt.Name('Edit_Normals')]

	positions = []
	normals = []

	for i in range(0, faceCount):
		face = rt.getFace(maxMesh, i + 1)
		tvFace = rt.getTVFace(maxMesh, i + 1)
		matId = rt.getFaceMatID(maxMesh, i + 1)
		material = maxNode.material[matId-1] if rt.classOf(
			maxNode.material) == rt.Multimaterial else maxNode.material

		for j in range(0, 3):
			vertIdx = face[j]
			tvertIdx = tvFace[j]

			pos = rt.getVert(maxMesh, vertIdx)
			#pos = pos * self.transformMtx # needed with reference model
			positions.append(pos)

			if editNormalsMod != None:
				temp = editNormalsMod.GetNormal(editNormalsMod.GetNormalId(i + 1, j + 1))
				if temp == None:
					# TODO figure out why this happens
					# my guess is that it only returns normals that have been explicitly set with the modifier
					temp = rt.getNormal(maxMesh, vertIdx)
				nrm = temp
			else:
				nrm = rt.getNormal(maxMesh, vertIdx)
			#nrm = nrm * self.transformMtx # needed with reference model
			normals.append(nrm)

	vertices = []
	for i in range(0, len(positions)):
		vertices.append((i, positions[i], normals[i]))

	vertices = sorted(vertices, key=lambda x: x[1][0] + x[1][1] + x[1][2])

	for i, v in enumerate(vertices):
		print(i, v[1], v[2], sep='\t')


def extractVertices(maxNode):
	maxMesh = rt.snapshotAsMesh(maxNode)
	faceCount = rt.getNumFaces(maxMesh)
	editNormalsMod = maxNode.modifiers[rt.Name('Edit_Normals')]
	transformMtx = rt.Matrix3(1)

	positions = []
	normals = []

	for i in range(0, faceCount):
		face = rt.getFace(maxMesh, i + 1)
		tvFace = rt.getTVFace(maxMesh, i + 1)
		matId = rt.getFaceMatID(maxMesh, i + 1)
		material = maxNode.material[matId-1] if rt.classOf(maxNode.material) == rt.Multimaterial else maxNode.material

		for j in range(0, 3):
			vertIdx = face[j]
			tvertIdx = tvFace[j]

			pos = rt.getVert(maxMesh, vertIdx)
			#pos = pos * self.transformMtx
			positions.append(pos)

			if editNormalsMod != None:
				temp = editNormalsMod.GetNormal(editNormalsMod.GetNormalId(i + 1, j + 1))
				if temp == None:
					# TODO figure out why this happens
					# my guess is that it only returns normals that have been explicitly set with the modifier
					temp = rt.getNormal(maxMesh, vertIdx)
				nrm = temp
			else:
				nrm = rt.getNormal(maxMesh, vertIdx)
			#nrm = nrm * self.transformMtx # needed with reference model
			normals.append(nrm)

	return positions, normals

def testNormals():
    node = rt.selection[0]
    positions, normals = extractVertices(node)
    
    
    modelMtxNormal = glm.transpose( glm.inverse( modelMtx ) )

dumpNormals()
