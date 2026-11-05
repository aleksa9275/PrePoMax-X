// NetGenLibTest.cpp : Defines the entry point for the console application.
//
#include "stdafx.h"
#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <set>
#include <vector>
#include <chrono>
#include <map>
#include <algorithm>

#include <climits>
#include "TopTools_IndexedMapOfShape.hxx"
#include "TopoDS.hxx"
#include "TopoDS_Face.hxx"
#include "TopoDS_Shape.hxx"
#include "GProp_GProps.hxx"
#include "BRepGProp.hxx"
#include "BRep_Builder.hxx"
#include "BRepTools.hxx"
#include "BRepBndLib.hxx"
#include "BRepAdaptor_Surface.hxx"
#include "BRepClass_FaceClassifier.hxx"
#include "BRepClass3d_SolidClassifier.hxx"
#include "Bnd_Box.hxx"
#include "TopExp_Explorer.hxx"
#include "gp_Pnt2d.hxx"
#include "Precision.hxx"
#include "TopExp.hxx"
#include "TopoDS_Edge.hxx"
#include "BRep_Tool.hxx"
#include "BRepAdaptor_Curve.hxx"
#include "BRepBuilderAPI_MakeVertex.hxx"
#include "BRepExtrema_DistShapeShape.hxx"
#include "BRepAlgoAPI_Defeaturing.hxx"
#include "BRepAlgoAPI_Splitter.hxx"
#include "TopTools_DataMapOfShapeInteger.hxx"
#include "BRepCheck_Analyzer.hxx"
#include "Standard_Failure.hxx"
#include "GCPnts_TangentialDeflection.hxx"
#include "gp_Trsf.hxx"
#include "gp_GTrsf.hxx"
#include "gp_Ax1.hxx"
#include "gp_Ax2.hxx"
#include "BRepBuilderAPI_Transform.hxx"
#include "BRepBuilderAPI_GTransform.hxx"
#include "TopoDS_Iterator.hxx"
#include "TopTools_IndexedDataMapOfShapeListOfShape.hxx"
#include "TopTools_ListOfShape.hxx"

#include "windows.h"
//#include "nglib.h"

namespace nglib {
#include "nglib.h"
}

using namespace std;
using namespace nglib;


// Methods
void ConvertToUpper(char* data);
void PrintUsage(const char* exePath);
// Assembly - Split
bool AssemblySplitStepToCompounds(int argc, char* argv[]);
bool AssemblySplitIgesToCompounds(int argc, char* argv[]);
bool AssemblySplitBrepToCompounds(int argc, char* argv[]);
bool AssemblySplitBrepToParts(int argc, char* argv[]);
// Assembly - Create
bool CompoundBrep(int argc, char* argv[]);
static bool RemoveRepeatedCompoundSolids(const char * fileName);
static bool WriteCompoundSolidOrigins(int argc, char* argv[]);
bool AssemblyBrep(int argc, char* argv[], bool saveAsStep);
// Part
bool SaveBrepAsStep(int argc, char* argv[]);
// Visualization
bool OccVisualization(int argc, char* argv[]);
// Geometry operations
bool TransformGeometry(int argc, char* argv[]);
bool ReverseBrepFaceOrientations(int argc, char* argv[]);
bool SplitAFaceUsingTwoPoints(int argc, char* argv[]);
bool SplitGeometry(int argc, char* argv[], bool preview);
bool RemoveSolids(int argc, char* argv[]);
bool MergeSolids(int argc, char* argv[]);
bool DefeatureBrep(int argc, char* argv[]);
bool DefeatureCompoundBrep(int argc, char* argv[]);
TopoDS_Shape RestoreMergedFaces(const TopoDS_Shape& inputShape, BRepAlgoAPI_Defeaturing& defeaturing,
								const TopoDS_Shape& result);
bool SplitClosedFaces(int argc, char* argv[]);
bool ConvertToShell(int argc, char* argv[]);
bool OffsetFaces(int argc, char* argv[]);
bool RemoveFaces(int argc, char* argv[], bool compound);
bool FuseFaces(int argc, char* argv[]);
bool RepairBrep(int argc, char* argv[], bool preview);
bool ConvertToSolid(int argc, char* argv[]);
// Stl Mesh
bool StlMesh(int argc, char* argv[]);
bool StlSurfaceMesh(int argc, char* argv[]);
bool StlEdgeMesh(int argc, char* argv[]);
void ReadEdgeNodes(const char *fileName, int &numOfNodes, double** &nodes);
// Occ Mesh
bool OccMesh(int argc, char* argv[]);
bool OccEdgeMesh(int argc, char* argv[]);
// Vol Mesh
bool VolVolumeMesh(int argc, char* argv[]);
Ng_Meshing_Parameters ReadParameters(const char *fileName, double &deflection);
// The rest
bool Test(int argc, char* argv[]);
char** ReadDataFile(int &argc, char* argv[]);


//BREP_MESH C:\Temp\test.brep C:\Temp\geometry.vol C:\Temp\meshParameters C:\Temp\meshRefinement
//BREP_MESH C:\Temp\Salome\2_box_Partition.brep C:\Temp\geometry.vol C:\Temp\meshParameters C:\Temp\meshRefinement
//BREP_MESH C:\Temp\geometry.brep C:\Temp\geometry.vol C:\Temp\meshParameters C:\Temp\meshRefinement
//BREP_MESH C:\Temp\test.brep C:\Temp\geometry.vol C:\Temp\meshParameters
//BREP_MESH C:\Temp\geometry_partition.brep C:\Temp\geometry_partition.vol C:\Temp\meshParameters C:\Temp\meshRefinement
//BREP_MESH C:\Temp\geometry_partition.brep C:\Temp\geometry_partition.vol C:\Temp\meshParameters C:\Temp\meshRefinement
//
//BREP_ASSEMBLY_SPLIT C:\Temp\Salome\2_box_Partition.brep C:\Temp\geometry.brep
//BREP_ASSEMBLY_SPLIT C:\Temp\Salome\3_box_Compound_Partition.brep C:\Temp\geometry.brep
//BREP_ASSEMBLY_SPLIT C:\Temp\Partition_1.brep C:\Temp\Partition_out.brep
//
//BREP_COMPOUND C:\Temp\box_1.brep C:\Temp\box_2.brep C:\Temp\geometry.brep
//BREP_COMPOUND C:\Temp\box_1.brep C:\Temp\cylinder_2.brep C:\Temp\geometry_partition.brep
//BREP_COMPOUND "C:\Temp\if91LnA0._1.brep" "C:\Temp\if91LnA0._2.brep" "C:\Temp\geometry.brep"
//BREP_COMPOUND "C:\Temp\r4sXIMtY._1.brep" "C:\Temp\r4sXIMtY._2.brep" "C:\Temp\geometry.brep"
//BREP_COMPOUND "C:\Temp\Partition_out_1.brep" "C:\Temp\Partition_out_2.brep" "C:\Temp\Partition_out_3.brep" "C:\Temp\geometry.brep"
//
//BREP_VISUALIZATION C:\Temp\box_2.brep C:\Temp\geometry.vis 0.01
//BREP_VISUALIZATION C:\Temp\lever.brep C:\Temp\geometry.vis 0.01
//BREP_VISUALIZATION C:\Temp\box_2.brep C:\Temp\geometry.vis 0.01
//BREP_VISUALIZATION C:\Temp\Partition_out_1.brep C:\Temp\geometry.vis 0.01
//BREP_VISUALIZATION C:\Temp\edge.brep C:\Temp\geometry.vis 0.01 
//
//BREP_TRANSFORM C:\Temp\scale.brep C:\Temp\scale_out.brep C:\Temp\transform
//
//SAVE_BREP_AS_STEP "C:\Temp\geometry.brep" "C:\Temp\geometry.step"
//
//STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS "C:\Temp\ptc.stp" "C:\Temp\geometry.brep"
//BREP_CONVERT_SOLID_TO_SHELL "C:\Temp\solidBox.brep" "C:\Temp\geometry.brep"
//BREP_OFFSET_FACES "C:\Temp\solidBox.brep" "C:\Temp\geometry.brep" 0 1 0 3 1 2 3
//IGES_ASSEMBLY_SPLIT_TO_COMPOUNDS "C:\Temp\NX-2D-bracket.igs" "C:\Temp\geometry.brep"
//BREP_COMPOUND "C:\Temp\geometry_face_2.brep" "C:\Temp\geometry_face_3.brep" "C:\Temp\geometry.brep"

// MAIN
//int _tmain(int argc, _TCHAR* argv[])
static int RunCommand(int argc, char* argv[])
{
	// occ_visualization "C:\Temp\Bearing_bracket.STEP" "C:\Temp\Bearing_bracket.vis" 0.01
	// occ_visualization "C:\Temp\Bearing_bracket.STEP" "D:\Pc\Programiranje\NetGenLibOC v2\Working folder\part1.stl" "D:\Pc\Programiranje\NetGenLibOC v2\Working folder\parametres" "D:\Pc\Programiranje\NetGenLibOC v2\Working folder\part1.vol"

	// argv[0]	...	exe
	// argv[1]	...	function
	// argv[2]	...	input file nam
	// argv[3]	...	output file name
	// argv[4]	...	mesh parameters
	// argv[5]	...	mesh refinement
	// argv[6]	...	edge file name
	//
	if (argc < 2)
	{
		PrintUsage(argv[0]);
		return 1;
	}
	//
	ConvertToUpper(argv[1]);
	// Assembly - Split
	if (strcmp(argv[1], "STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS") == 0) return AssemblySplitStepToCompounds(argc, argv);
	else if (strcmp(argv[1], "IGES_ASSEMBLY_SPLIT_TO_COMPOUNDS") == 0) return AssemblySplitIgesToCompounds(argc, argv);
	else if (strcmp(argv[1], "BREP_ASSEMBLY_SPLIT_TO_COMPOUNDS") == 0) return AssemblySplitBrepToCompounds(argc, argv);
	else if (strcmp(argv[1], "BREP_ASSEMBLY_SPLIT_TO_PARTS") == 0) return AssemblySplitBrepToParts(argc, argv);
	// Assembly - Create
	else if (strcmp(argv[1], "BREP_COMPOUND") == 0) return CompoundBrep(argc, argv);
	else if (strcmp(argv[1], "BREP_ASSEMBLY") == 0) return AssemblyBrep(argc, argv, false);
	else if (strcmp(argv[1], "STEP_ASSEMBLY") == 0) return AssemblyBrep(argc, argv, true);
	// Part
	else if (strcmp(argv[1], "SAVE_BREP_AS_STEP") == 0) return SaveBrepAsStep(argc, argv);
	// Visualization
	else if (strcmp(argv[1], "BREP_VISUALIZATION") == 0) return OccVisualization(argc, argv);
	// Geometry operations
	else if (strcmp(argv[1], "BREP_TRANSFORM") == 0) return TransformGeometry(argc, argv);
	else if (strcmp(argv[1], "BREP_REVERSE_FACES") == 0) return ReverseBrepFaceOrientations(argc, argv);
	else if (strcmp(argv[1], "BREP_SPLIT_A_FACE_USING_TWO_POINTS") == 0) return SplitAFaceUsingTwoPoints(argc, argv);
	else if (strcmp(argv[1], "BREP_SPLIT") == 0) return SplitGeometry(argc, argv, false);
	else if (strcmp(argv[1], "BREP_SPLIT_PREVIEW") == 0) return SplitGeometry(argc, argv, true);
	else if (strcmp(argv[1], "BREP_REMOVE_SOLIDS") == 0) return RemoveSolids(argc, argv);
	else if (strcmp(argv[1], "BREP_MERGE_SOLIDS") == 0) return MergeSolids(argc, argv);
	else if (strcmp(argv[1], "BREP_DEFEATURE") == 0) return DefeatureBrep(argc, argv);
	else if (strcmp(argv[1], "BREP_DEFEATURE_COMPOUND") == 0) return DefeatureCompoundBrep(argc, argv);
	else if (strcmp(argv[1], "BREP_SPLIT_CLOSED_FACES") == 0) return SplitClosedFaces(argc, argv);
	else if (strcmp(argv[1], "BREP_CONVERT_SOLID_TO_SHELL") == 0) return ConvertToShell(argc, argv);
	else if (strcmp(argv[1], "BREP_CONVERT_SHELL_TO_SOLID") == 0) return ConvertToSolid(argc, argv);
	else if (strcmp(argv[1], "BREP_OFFSET_FACES") == 0) return OffsetFaces(argc, argv);
	else if (strcmp(argv[1], "BREP_REMOVE_FACES") == 0) return RemoveFaces(argc, argv, false);
	else if (strcmp(argv[1], "BREP_REMOVE_COMPOUND_FACES") == 0) return RemoveFaces(argc, argv, true);
	else if (strcmp(argv[1], "BREP_FUSE_FACES") == 0) return FuseFaces(argc, argv);
	else if (strcmp(argv[1], "BREP_REPAIR") == 0) return RepairBrep(argc, argv, false);
	else if (strcmp(argv[1], "BREP_REPAIR_PREVIEW") == 0) return RepairBrep(argc, argv, true);
	// Stl Mesh
	else if (strcmp(argv[1], "STL_MESH") == 0) return StlMesh(argc, argv);
	else if (strcmp(argv[1], "STL_SURFACE_MESH") == 0) return StlSurfaceMesh(argc, argv);
	else if (strcmp(argv[1], "STL_EDGE_MESH") == 0) return StlEdgeMesh(argc, argv);
	// Occ Mesh
	else if (strcmp(argv[1], "BREP_MESH") == 0) return OccMesh(argc, argv);
	else if (strcmp(argv[1], "BREP_EDGE_MESH") == 0) return OccEdgeMesh(argc, argv);
	// Vol Mesh
	else if (strcmp(argv[1], "VOL_VOLUME_MESH") == 0) return VolVolumeMesh(argc, argv);
	// The rest
	else if (strcmp(argv[1], "TEST") == 0) return Test(argc, argv);
	else
	{
		//cout << "Netgen (nglib) STL Testing" << endl;
		cerr << "The first parameter must be a valid command." << endl;
		return 1;
	}
	return 0;
}


// A meshing routine that fails reports it by throwing.  Without a handler the
// runtime terminates the process, which looks like a crash and hides the
// reason, so every command runs under this backstop.
int main(int argc, char* argv[])
{
	try
	{
		return RunCommand(argc, argv);
	}
	catch (const std::exception & exception)
	{
		cerr << "Error: " << exception.what() << endl;
		return 1;
	}
	catch (...)
	{
		cerr << "Error: the operation failed and could not be completed." << endl;
		return 1;
	}
}


// Methods
void ConvertToUpper(char* data)
{
	for (int i = 0; i < strlen(data); i++)
	{
		data[i] = toupper(data[i]);
	}
}
void PrintUsage(const char* exePath)
{
	// argv[0] may carry the full path; show just the file name
	string exeName = (exePath == NULL) ? "NetGenMesher.exe" : string(exePath);
	size_t slash = exeName.find_last_of("\\/");
	if (slash != string::npos) exeName = exeName.substr(slash + 1);
	//
	cout << endl;
	cout << "NetGenMesher - meshing and geometry utility built on Netgen 5.3.1 / OpenCASCADE 8.0.1" << endl;
	cout << endl;
	cout << "Usage:  " << exeName << " <COMMAND> <arguments>" << endl;
	cout << endl;
	cout << "The command is case insensitive. Arguments in [] are optional." << endl;
	cout << "Paths containing spaces must be quoted." << endl;
	cout << endl;
	cout << "Assembly - split" << endl;
	cout << "  STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS   <in.step> <out.brep> [maxSplitFaces]" << endl;
	cout << "  IGES_ASSEMBLY_SPLIT_TO_COMPOUNDS   <in.iges> <out.brep> [maxSplitFaces]" << endl;
	cout << "  BREP_ASSEMBLY_SPLIT_TO_COMPOUNDS   <in.brep> <out.brep> [maxSplitFaces]" << endl;
	cout << "  BREP_ASSEMBLY_SPLIT_TO_PARTS       <in.brep> <out.brep> [maxSplitFaces]" << endl;
	cout << "      One file is written per part, named <out>_solid_0001.brep," << endl;
	cout << "      <out>_shell_0001.brep, ... maxSplitFaces defaults to 1." << endl;
	cout << endl;
	cout << "Assembly - create" << endl;
	cout << "  BREP_COMPOUND                      <in1.brep> <in2.brep> [...] <out.brep>" << endl;
	cout << "  BREP_ASSEMBLY                      <in1.brep> <in2.brep> [...] <out.brep>" << endl;
	cout << "  STEP_ASSEMBLY                      <in1.brep> <in2.brep> [...] <out.step>" << endl;
	cout << "      BREP_COMPOUND imprints the parts on one another; the two assembly" << endl;
	cout << "      commands only gather them into one compound, unchanged." << endl;
	cout << "      BREP_COMPOUND writes <out.brep>.origins: one line per solid of the" << endl;
	cout << "      result, listing every input solid it lies in, numbered over all the" << endl;
	cout << "      input files in order, or 0 where it lies in none." << endl;
	cout << endl;
	cout << "Part" << endl;
	cout << "  SAVE_BREP_AS_STEP                  <in.brep> <out.step>" << endl;
	cout << endl;
	cout << "Visualization" << endl;
	cout << "  BREP_VISUALIZATION                 <in.brep> <out.vis> <linearDeflection>" << endl;
	cout << "                                     <relative> <angularDeflection>" << endl;
	cout << "      relative: 0 = absolute deflection, non-zero = relative to size." << endl;
	cout << endl;
	cout << "Geometry operations" << endl;
	cout << "  BREP_TRANSFORM                     <in.brep> <out.brep> <transformDefinition>" << endl;
	cout << "      <transformDefinition> is a text file of <property>: <values> lines" << endl;
	cout << "        Transform type: Translate | Rotate | Mirror | Scale" << endl;
	cout << "        Point: x y z          centre of the rotation or the scaling, or a point" << endl;
	cout << "                              on the mirror plane" << endl;
	cout << "        Direction: x y z      translation vector, rotation axis or mirror" << endl;
	cout << "                              plane normal" << endl;
	cout << "        Angle: <degrees>      rotation angle, right handed about the axis" << endl;
	cout << "        Factors: sx sy sz     scale factors" << endl;
	cout << "        Number of copies: <n> (optional, Translate and Rotate)" << endl;
	cout << "          0, the default, transforms the shape into <out.brep>; n > 0 writes" << endl;
	cout << "          copy k, transformed k times, to <out>_000k.brep and leaves" << endl;
	cout << "          <out.brep> alone" << endl;
	cout << "      Every transform keeps the order of the faces, edges and vertices, so" << endl;
	cout << "      their ids stay what they were; a non-uniform scale turns the curves" << endl;
	cout << "      and surfaces into splines, every other transform keeps them exact." << endl;
	cout << "  BREP_REVERSE_FACES                 <in.brep> <out.brep>" << endl;
	cout << "  BREP_SPLIT_A_FACE_USING_TWO_POINTS <in.brep> <out.brep> <faceId>" << endl;
	cout << "                                     <x1> <y1> <z1> <x2> <y2> <z2>" << endl;
	cout << "  BREP_SPLIT                         <in.brep> <out.brep> <toolDefinition>" << endl;
	cout << "      <toolDefinition> is a text file of <property>: <values> lines that" << endl;
	cout << "      define the splitting tool.  Every tool accepts" << endl;
	cout << "        Tool type: Plane | ExtendFace | ExtrudeEdges | TwoPointLine" << endl;
	cout << "        Extent: x_min x_max y_min y_max z_min z_max" << endl;
	cout << "        Fuzzy value: <tolerance>                       (optional)" << endl;
	cout << "        Solid ids: <id> <id> ...                       (optional)" << endl;
	cout << "          cuts only those solids of the shape and gathers every solid," << endl;
	cout << "          cut or not, back into one compound" << endl;
	cout << "        Source file: <in.brep>                         (optional, repeatable)" << endl;
	cout << "          the edge ids that follow it are read from that file; ids given" << endl;
	cout << "          before any source file are read from the shape being split" << endl;
	cout << "        Split target: Shell                            (optional)" << endl;
	cout << "          divides the named faces and leaves the body they belong to" << endl;
	cout << "          whole, instead of cutting through it" << endl;
	cout << "        Target solid: <n>                              (optional, repeatable)" << endl;
	cout << "          the target face ids that follow it are numbered inside that" << endl;
	cout << "          solid of the shape; ids given before any target solid are" << endl;
	cout << "          numbered in the shape itself" << endl;
	cout << "        Target face ids: <id> <id> ...                 (with Split target)" << endl;
	cout << "      Plane adds         Plane origin: x y z" << endl;
	cout << "                         Plane normal: x y z" << endl;
	cout << "      ExtendFace adds    Face ids: <id> <id> ..." << endl;
	cout << "                         Offset: <distance>           (optional)" << endl;
	cout << "          moves each continued surface along its own normal, which" << endl;
	cout << "          grows the radius of a cylinder, a cone, a sphere or a torus" << endl;
	cout << "      ExtrudeEdges adds  Edge ids: <id> <id> ..." << endl;
	cout << "      TwoPointLine adds  Point 1: x y z" << endl;
	cout << "                         Point 2: x y z" << endl;
	cout << "          draws the line between the two points in the parameter space" << endl;
	cout << "          of each target surface and divides it along that line; it" << endl;
	cout << "          needs Split target and cannot cut through a body" << endl;
	cout << "                         Extrusion offset: x y z      (optional)" << endl;
	cout << "                         Extrusion vector: x y z" << endl;
	cout << "      The extent is the box the tool has to cover, so that one tool is the" << endl;
	cout << "      same for every part it is applied to.  Face and edge ids are read from" << endl;
	cout << "      the source file when one is given, otherwise from the input file." << endl;
	cout << "  BREP_SPLIT_PREVIEW                 <in.brep> <out.edges> <toolDefinition>" << endl;
	cout << "      Splits as BREP_SPLIT does and writes only the edges the split made," << endl;
	cout << "      each as a line Edge: <n> followed by n lines of x y z on it, instead" << endl;
	cout << "      of the result" << endl;
	cout << "  BREP_SPLIT_CLOSED_FACES            <in.brep> <out.brep> [maxSplitFaces]" << endl;
	cout << "      Divides every closed face of the whole shape, the way the parts of" << endl;
	cout << "      an assembly are divided when they are written out, so that a shape" << endl;
	cout << "      and the parts taken from it are numbered the same.  Defaults to 1," << endl;
	cout << "      which divides nothing." << endl;
	cout << "  BREP_DEFEATURE                     <in.brep> <out.brep> <faceId> [faceId ...]" << endl;
	cout << "      Removes selected faces from one CAD solid and closes the gap. The" << endl;
	cout << "      splits of every other face - the halves of a periodic face, the pieces" << endl;
	cout << "      of a shell split - are kept." << endl;
	cout << "  BREP_DEFEATURE_COMPOUND            <in.brep> <out.brep> <numOfGroups>" << endl;
	cout << "                                     {<solid> <numOfFaces> <faceId> ...}" << endl;
	cout << "      As BREP_DEFEATURE, for a compound of solids defeatured as a whole, so" << endl;
	cout << "      that a face two solids share changes on both of them. The face ids of" << endl;
	cout << "      a group are numbered inside that solid. <out.brep> holds the solids in" << endl;
	cout << "      the order of <in.brep>." << endl;
	cout << "  BREP_REMOVE_FACES                  <in.brep> <out.brep> <numOfGroups>" << endl;
	cout << "                                     {<solid> <numOfFaces> <faceId> ...}" << endl;
	cout << "      Deletes the faces and leaves the gap open. A solid that loses a" << endl;
	cout << "      face comes back as the shells that are left of it. The face ids of" << endl;
	cout << "      a group are numbered inside that solid, or in the shape when it is 0." << endl;
	cout << "      Pieces that no longer touch are written as <out>_000k.brep beside" << endl;
	cout << "      the largest, and their number to <out>.pieces." << endl;
	cout << "  BREP_REMOVE_COMPOUND_FACES         <in.brep> <out.brep> <numOfGroups> {...}" << endl;
	cout << "      As BREP_REMOVE_FACES, for a compound of solids: <out.brep> keeps the" << endl;
	cout << "      solids that lost nothing, every opened solid is written as the shell" << endl;
	cout << "      <out>_000k.brep, one file per piece, and <out>.opened lists the" << endl;
	cout << "      solid each came from with its number of files." << endl;
	cout << "      A solid that loses every face is gone and listed in <out>.removed." << endl;
	cout << "  BREP_FUSE_FACES                    <in.brep> <out.brep> <numOfGroups>" << endl;
	cout << "                                     {<solid> <numOfFaces> <faceId> ...}" << endl;
	cout << "      Makes the faces one across the edges they share where they lie on" << endl;
	cout << "      one surface and bound the same solids, and joins the edges at the" << endl;
	cout << "      vertices of the edges taken out. Ids are grouped as for" << endl;
	cout << "      BREP_REMOVE_FACES. Fails when no face was fused." << endl;
	cout << "  BREP_REPAIR                        <in.brep> <out.brep> <options> <tolerance>" << endl;
	cout << "      Repairs the whole shape. <options> adds up 1 fix shape, 2 remove small" << endl;
	cout << "      edges, 4 remove small faces, 8 sew faces (no solids only), 16 fuse" << endl;
	cout << "      faces on one surface and 32 join edges on one curve. Fails when the" << endl;
	cout << "      repair changes the number of solids or breaks a valid shape." << endl;
	cout << "  BREP_REPAIR_PREVIEW                <in.brep> <out.preview> <options> <tolerance>" << endl;
	cout << "                                     [maxSplitFaces]" << endl;
	cout << "      Repairs as BREP_REPAIR does and writes only what it would take away:" << endl;
	cout << "      every removed or sewn edge as Edge: <n> followed by n lines of x y z," << endl;
	cout << "      and every removed vertex as Point: x y z. The result is compared with" << endl;
	cout << "      its closed faces divided as BREP_SPLIT_CLOSED_FACES divides them." << endl;
	cout << "  BREP_CONVERT_SOLID_TO_SHELL        <in.brep> <out.brep>" << endl;
	cout << "  BREP_CONVERT_SHELL_TO_SOLID        <in.brep> <out.brep>" << endl;
	cout << endl;
	cout << "STL meshing" << endl;
	cout << "  STL_MESH                           <in.stl> <out.vol> <parameters>" << endl;
	cout << "                                     [refinement] [edgeNodes]" << endl;
	cout << "  STL_SURFACE_MESH                   <in.stl> <out.vol> <parameters>" << endl;
	cout << "                                     [refinement] [edgeNodes]" << endl;
	cout << "  STL_EDGE_MESH                      <in.stl> <out.vol> <parameters>" << endl;
	cout << "                                     [refinement] [edgeNodes]" << endl;
	cout << endl;
	cout << "BREP meshing" << endl;
	cout << "  BREP_MESH                          <in.brep> <out.vol> <parameters>" << endl;
	cout << "                                     [refinement]" << endl;
	cout << "  BREP_EDGE_MESH                     <in.brep> <out.vol> <parameters>" << endl;
	cout << "                                     [refinement]" << endl;
	cout << endl;
	cout << "Volume meshing of a given boundary" << endl;
	cout << "  VOL_VOLUME_MESH                    <in.vol> <out.vol> <parameters>" << endl;
	cout << "      <in.vol> holds the points and the closed boundary of every domain," << endl;
	cout << "      triangles and quadrilaterals; pyramids and prisms are built on the" << endl;
	cout << "      quadrilaterals. The boundary points stay fixed and are the first" << endl;
	cout << "      points of <out.vol>, in their input order." << endl;
	cout << endl;
	cout << "  <parameters> is a text file of meshing parameters; [refinement] is a" << endl;
	cout << "  local mesh size file; [edgeNodes] is a file of prescribed edge nodes." << endl;
	cout << endl;
	cout << "Examples" << endl;
	cout << "  " << exeName << " STL_MESH part1.stl part1.vol parametres" << endl;
	cout << "  " << exeName << " STEP_ASSEMBLY_SPLIT_TO_COMPOUNDS in.step geometry.brep" << endl;
	cout << "  " << exeName << " BREP_MESH geometry_solid_0001.brep out.vol parametres" << endl;
	cout << endl;
}
// Assembly - Split
bool AssemblySplitStepToCompounds(int argc, char* argv[])
{
	//Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;
	// Read in the OCC File
	occ_geom = Ng_OCC_Load_STEP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in STEP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded STEP File: " << argv[2] << endl;
	// Save as parts
	int numOfSplitFaces = 1;
	if (argc == 5)
	{
		std::string::size_type sz;     // alias of size_t
		numOfSplitFaces = std::stoi(argv[4], &sz);
	}
	Ng_OCC_WriteAssemblyAsCompounds(occ_geom, argv[3], numOfSplitFaces, true);
	//
	return 0;
}
bool AssemblySplitIgesToCompounds(int argc, char* argv[])
{
	//Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;
	// Read in the OCC File
	occ_geom = Ng_OCC_Load_IGES(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in IGES File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded IGES File: " << argv[2] << endl;
	int numOfSplitFaces = 1;
	if (argc == 5)
	{
		std::string::size_type sz;     // alias of size_t
		numOfSplitFaces = std::stoi(argv[4], &sz);
	}
	Ng_OCC_WriteAssemblyAsCompounds(occ_geom, argv[3], numOfSplitFaces, true);
	//
	return 0;
}
bool AssemblySplitBrepToCompounds(int argc, char* argv[])
{
	//Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;
	// Read in the OCC File
	occ_geom = Ng_OCC_Load_BREP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in BREP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded BREP File: " << argv[2] << endl;
	// Save as parts
	int numOfSplitFaces = 1;
	if (argc == 5)
	{
		std::string::size_type sz;     // alias of size_t
		numOfSplitFaces = std::stoi(argv[4], &sz);
	}
	Ng_OCC_WriteAssemblyAsCompounds(occ_geom, argv[3], numOfSplitFaces, false);
	//
	return 0;
}
bool AssemblySplitBrepToParts(int argc, char* argv[])
{
	//Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;

	// Read in the OCC File
	occ_geom = Ng_OCC_Load_BREP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in BREP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded BREP File: " << argv[2] << endl;
	// Save parts
	int numOfSplitFaces = 1;
	if (argc == 5)
	{
		std::string::size_type sz;     // alias of size_t
		numOfSplitFaces = std::stoi(argv[4], &sz);
	}
	int numOfSolids = Ng_OCC_WriteAssemblyAsSolidParts(occ_geom, 1, argv[3], numOfSplitFaces) - 1;
	int numOfShells = Ng_OCC_WriteAssemblyAsShellParts(occ_geom, numOfSolids, argv[3], numOfSplitFaces) - numOfSolids;

	return 0;
}
// Assembly - Create
bool CompoundBrep(int argc, char* argv[])
{
	try
	{
		// Result of Netgen Operations
		Ng_Result ng_res;
		//
		ng_res = Ng_OCC_CreateCompoundFromBrep(argc, argv);
		//
		if (ng_res != NG_OK)
		{
			cout << "Error combining BREP files." << endl;
			return 1;
		}
		if (!RemoveRepeatedCompoundSolids(argv[argc - 1]))
		{
			cout << "Error removing the repeated solids of the compound." << endl;
			return 1;
		}
		// The compound is usable without the origins, so a failure to write them is only reported
		if (!WriteCompoundSolidOrigins(argc, argv))
			cout << "The solids the compound solids came from could not be written." << endl;
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
bool AssemblyBrep(int argc, char* argv[], bool saveAsStep)
{
	try
	{
		// Result of Netgen Operations
		Ng_Result ng_res;
		//
		ng_res = Ng_OCC_CreateAssemblyFromBrep(argc, argv, saveAsStep);
		//
		if (ng_res != NG_OK)
		{
			cout << "Error joining BREP files." << endl;
			return 1;
		}
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
// Part
bool SaveBrepAsStep(int argc, char* argv[])
{
	//Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;
	// Read in the OCC File
	occ_geom = Ng_OCC_Load_BREP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in BREP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded BREP File: " << argv[2] << endl;
	// Save
	Ng_OCC_Save_STEP(occ_geom, argv[3]);
	//
	return 0;
}
// Visualization
bool OccVisualization(int argc, char* argv[])
{
	//Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;
	// Read in the OCC File
	cout << "Ng_OCC_Load_BREP" << endl;
	occ_geom = Ng_OCC_Load_BREP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in BREP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded BREP File: " << argv[2] << endl;
	//
	std::string::size_type sz1;     // alias of size_t
	double linearDeflection = std::stod(argv[4], &sz1);
	//
	std::string::size_type sz2;     // alias of size_t
	bool relative = std::stod(argv[5], &sz2);
	//
	std::string::size_type sz3;     // alias of size_t
	double angularDeflection = std::stod(argv[6], &sz3);
	//
	cout << "Ng_OCC_ExportVisualization" << endl;
	Ng_OCC_ExportVisualization(occ_geom, linearDeflection, relative, angularDeflection, argv[3]);
	cout << "Export visualization finished successfully." << endl;
	//
	return 0;
}
// Geometry operations
bool ReverseBrepFaceOrientations(int argc, char* argv[])
{
	try
	{
		//Define pointer to OCC Geometry
		Ng_OCC_Geometry *occ_geom;
		// Result of Netgen Operations
		Ng_Result ng_res;
		int np, ne;
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		int faceId;
		int numOfFaceIds = argc - 4;
		int * faceIds = new int[numOfFaceIds];
		std::string::size_type sz;     // alias of size_t
		for (int i = 0; i < numOfFaceIds; i++)
		{
			faceId = std::stoi(argv[4 + i], &sz);
			faceIds[i] = faceId;
		}
		//
		cout << "Ng_OCC_ReverseBrepFaceOrientations" << endl;
		occ_geom = Ng_OCC_ReverseFaceOrientations(occ_geom, faceIds, numOfFaceIds);
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Reverse face orientations finished successfully." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
bool SplitAFaceUsingTwoPoints(int argc, char* argv[])
{
	try
	{
		//Define pointer to OCC Geometry
		Ng_OCC_Geometry *occ_geom;
		// Result of Netgen Operations
		Ng_Result ng_res;
		int np, ne;
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		std::string::size_type sz;     // alias of size_t
		int faceId = std::stoi(argv[4], &sz);
		double x1 = std::stod(argv[5], &sz);
		double y1 = std::stod(argv[6], &sz);
		double z1 = std::stod(argv[7], &sz);
		double x2 = std::stod(argv[8], &sz);
		double y2 = std::stod(argv[9], &sz);
		double z2 = std::stod(argv[10], &sz);
		//
		cout << "Ng_OCC_SplitAFaceUsingTwoPoints" << endl;
		occ_geom = Ng_OCC_SplitAFaceUsingTwoPoints(occ_geom, faceId, x1, y1, z1, x2, y2, z2);
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Split face finished successfully." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
// A tool definition file holds one <property>: <values> line per property, in the style of the
// visualization file.  Unknown properties are ignored so that a property can be added without
// breaking an older executable, and a missing property keeps its default.
static string TrimToolText(const string & text)
{
	size_t first = text.find_first_not_of(" \t\r\n");
	if (first == string::npos) return "";
	size_t last = text.find_last_not_of(" \t\r\n");
	return text.substr(first, last - first + 1);
}
static string ToolKeyFromText(const string & text)
{
	string key;
	for (size_t i = 0; i < text.size(); i++)
	{
		if (text[i] == ' ' || text[i] == '\t') continue;
		key += (char)tolower(text[i]);
	}
	return key;
}
static void ReadToolValues(const string & text, double * values, int numOfValues)
{
	istringstream stream(text);
	for (int i = 0; i < numOfValues; i++) stream >> values[i];
}
// Copy k of a pattern is written next to the output file, as <out>_000k.brep, the way the parts of a split
// assembly are
static string PatternCopyFileName(const string & outputFileName, int copy)
{
	size_t slash = outputFileName.find_last_of("\\/");
	size_t dot = outputFileName.find_last_of('.');
	if (dot == string::npos || (slash != string::npos && dot < slash)) dot = outputFileName.size();
	char suffix[16];
	snprintf(suffix, sizeof(suffix), "_%04d", copy);
	return outputFileName.substr(0, dot) + suffix + outputFileName.substr(dot);
}
// A move, a rotation, a mirror and a uniform scale keep every curve and surface of its kind, so they are
// applied exactly; only a non-uniform scale needs the general transformation, which turns them into splines.
// Both rebuild the shape through the same modifier, so the order of its faces, edges and vertices is kept
static TopoDS_Shape TransformShape(const TopoDS_Shape & shape, const string & transformType, const double point[3],
								   const double direction[3], double angle, const double factors[3], int step)
{
	gp_Pnt origin(point[0], point[1], point[2]);
	gp_Vec vector(direction[0], direction[1], direction[2]);
	gp_Trsf trsf;
	if (transformType == "translate") trsf.SetTranslation(vector * step);
	else if (transformType == "rotate") trsf.SetRotation(gp_Ax1(origin, gp_Dir(vector)), angle * step);
	else if (transformType == "mirror") trsf.SetMirror(gp_Ax2(origin, gp_Dir(vector)));
	else if (factors[0] == factors[1] && factors[1] == factors[2]) trsf.SetScale(origin, factors[0]);
	else
	{
		gp_Trsf toZero;
		toZero.SetTranslation(origin, gp_Pnt(0, 0, 0));
		gp_Trsf toPoint;
		toPoint.SetTranslation(gp_Pnt(0, 0, 0), origin);
		gp_GTrsf scale;
		scale.SetValue(1, 1, factors[0]);
		scale.SetValue(2, 2, factors[1]);
		scale.SetValue(3, 3, factors[2]);
		gp_GTrsf gTrsf = gp_GTrsf(toPoint) * scale * gp_GTrsf(toZero);
		BRepBuilderAPI_GTransform gTransform(shape, gTrsf, Standard_True);
		return gTransform.Shape();
	}
	BRepBuilderAPI_Transform transform(shape, trsf, Standard_True);
	return transform.Shape();
}
// Translate, rotate, mirror or scale a shape as the transform definition file says. The transformed shape
// has as many faces as the given one, in the same order, so a part rebuilt from it keeps every id it had
bool TransformGeometry(int argc, char* argv[])
{
	try
	{
		if (argc < 5)
		{
			cerr << "The BREP_TRANSFORM command needs an input file, an output file and a transform definition "
			     << "file." << endl;
			return 1;
		}
		BRep_Builder builder;
		TopoDS_Shape inputShape;
		if (!BRepTools::Read(inputShape, argv[2], builder))
		{
			cerr << "Error reading BREP file: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		// Read the transform definition
		ifstream definitionFile(argv[4]);
		if (!definitionFile)
		{
			cerr << "Error reading the transform definition file: " << argv[4] << endl;
			return 1;
		}
		//
		string transformType;
		double point[3] = { 0, 0, 0 };
		double direction[3] = { 0, 0, 0 };
		double angleDeg = 0;
		double factors[3] = { 1, 1, 1 };
		int numOfCopies = 0;
		//
		string line;
		while (getline(definitionFile, line))
		{
			size_t colon = line.find(':');
			if (colon == string::npos) continue;
			string key = ToolKeyFromText(line.substr(0, colon));
			string value = TrimToolText(line.substr(colon + 1));
			//
			if (key == "transformtype") transformType = ToolKeyFromText(value);
			else if (key == "point") ReadToolValues(value, point, 3);
			else if (key == "direction") ReadToolValues(value, direction, 3);
			else if (key == "angle") angleDeg = stod(value);
			else if (key == "factors") ReadToolValues(value, factors, 3);
			else if (key == "numberofcopies") numOfCopies = stoi(value);
		}
		//
		if (transformType != "translate" && transformType != "rotate" && transformType != "mirror" &&
			transformType != "scale")
		{
			cerr << "The transform type must be Translate, Rotate, Mirror or Scale." << endl;
			return 1;
		}
		double length = sqrt(direction[0] * direction[0] + direction[1] * direction[1] +
							 direction[2] * direction[2]);
		if (transformType != "scale" && length < gp::Resolution())
		{
			cerr << "The direction of the transform must not be a zero vector." << endl;
			return 1;
		}
		if (transformType == "scale" && (factors[0] == 0 || factors[1] == 0 || factors[2] == 0))
		{
			cerr << "The scale factors must not be zero." << endl;
			return 1;
		}
		if (numOfCopies < 0 ||
			(numOfCopies > 1 && transformType != "translate" && transformType != "rotate"))
		{
			cerr << "The number of copies must be 0 or larger, and only Translate and Rotate make more than "
			     << "one." << endl;
			return 1;
		}
		//
		TopTools_IndexedMapOfShape inputFaces;
		TopExp::MapShapes(inputShape, TopAbs_FACE, inputFaces);
		double angle = angleDeg * M_PI / 180;
		int numOfShapes = numOfCopies == 0 ? 1 : numOfCopies;
		for (int step = 1; step <= numOfShapes; step++)
		{
			TopoDS_Shape result = TransformShape(inputShape, transformType, point, direction, angle, factors,
												 step);
			TopTools_IndexedMapOfShape resultFaces;
			TopExp::MapShapes(result, TopAbs_FACE, resultFaces);
			if (result.IsNull() || resultFaces.Extent() != inputFaces.Extent())
			{
				cerr << "The transform did not return the shape it was given." << endl;
				return 1;
			}
			//
			string fileName = numOfCopies == 0 ? string(argv[3]) : PatternCopyFileName(argv[3], step);
			if (!BRepTools::Write(result, fileName.c_str()))
			{
				cerr << "Error writing BREP file: " << fileName << endl;
				return 1;
			}
		}
		//
		if (numOfCopies == 0) cout << "Transform geometry finished successfully." << endl;
		else cout << "Transform geometry finished successfully: " << numOfCopies << " copies were written." << endl;
		return 0;
	}
	catch (const Standard_Failure & error)
	{
		cerr << "The transform failed: " << error.GetMessageString() << endl;
		return 1;
	}
	catch (const std::exception & error)
	{
		cerr << "The transform failed: " << error.what() << endl;
		return 1;
	}
}
// The solids that are left keep their shapes, so a part built from one of them keeps every id
// the geometry gave it and PrePoMax can leave the part it already holds alone
bool RemoveSolids(int argc, char* argv[])
{
	try
	{
		if (argc < 5)
		{
			cerr << "The BREP_REMOVE_SOLIDS command needs an input file, an output file and at least "
			     << "one solid id." << endl;
			return 1;
		}
		//
		vector<int> solidIds;
		for (int i = 4; i < argc; i++)
		{
			istringstream stream(argv[i]);
			int solidId;
			while (stream >> solidId) solidIds.push_back(solidId);
		}
		if (solidIds.size() == 0)
		{
			cerr << "No solid id was given." << endl;
			return 1;
		}
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		TopTools_IndexedMapOfShape RemovalFMap;
		Ng_OCC_TopTools_IndexedMapOfShape * occ_removal_fmap = (Ng_OCC_TopTools_IndexedMapOfShape*)&RemovalFMap;
		Ng_OCC_GetFMap(occ_geom, occ_removal_fmap);
		int numOfFacesBefore = RemovalFMap.Extent();
		//
		cout << "Ng_OCC_RemoveSolids" << endl;
		occ_geom = Ng_OCC_RemoveSolids(occ_geom, &solidIds[0], (int)solidIds.size());
		//
		RemovalFMap.Clear();
		Ng_OCC_GetFMap(occ_geom, occ_removal_fmap);
		if (RemovalFMap.Extent() >= numOfFacesBefore)
		{
			cerr << "No solid was removed from the geometry." << endl;
			return 1;
		}
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Remove solids finished successfully: " << numOfFacesBefore - RemovalFMap.Extent()
		     << " faces were removed with them." << endl;
	}
	catch (const std::exception& e)
	{
		cerr << "Error: " << e.what() << endl;
		return 1;
	}
	return 0;
}
// The named solids become one, which takes the place of the first of them, and every other solid is
// written out as it is. A merge always loses the faces the solids shared, so a result with as many faces
// as before is one the modelling kernel refused.
bool MergeSolids(int argc, char* argv[])
{
	try
	{
		if (argc < 6)
		{
			cerr << "The BREP_MERGE_SOLIDS command needs an input file, an output file and at least "
			     << "two solid ids." << endl;
			return 1;
		}
		//
		vector<int> solidIds;
		for (int i = 4; i < argc; i++)
		{
			istringstream stream(argv[i]);
			int solidId;
			while (stream >> solidId) solidIds.push_back(solidId);
		}
		if (solidIds.size() < 2)
		{
			cerr << "At least two solid ids must be given." << endl;
			return 1;
		}
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		TopTools_IndexedMapOfShape MergeFMap;
		Ng_OCC_TopTools_IndexedMapOfShape * occ_merge_fmap = (Ng_OCC_TopTools_IndexedMapOfShape*)&MergeFMap;
		Ng_OCC_GetFMap(occ_geom, occ_merge_fmap);
		int numOfFacesBefore = MergeFMap.Extent();
		//
		cout << "Ng_OCC_MergeSolids" << endl;
		occ_geom = Ng_OCC_MergeSolids(occ_geom, &solidIds[0], (int)solidIds.size());
		//
		MergeFMap.Clear();
		Ng_OCC_GetFMap(occ_geom, occ_merge_fmap);
		if (MergeFMap.Extent() >= numOfFacesBefore)
		{
			cerr << "The solids were not merged." << endl;
			return 1;
		}
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Merge solids finished successfully: " << numOfFacesBefore - MergeFMap.Extent()
		     << " faces were removed." << endl;
	}
	catch (const std::exception& e)
	{
		cerr << "Error: " << e.what() << endl;
		return 1;
	}
	return 0;
}
// The defeaturing of the modelling kernel simplifies its result: every two neighbouring faces that lie on one
// surface are made one, anywhere in the shape and not only around the removed features. A periodic face split in
// two halves comes back as one closed face and a face a shell split divided comes back whole, so splits the model
// was given - by the exporter of the CAD file or in PrePoMax - were lost to a defeaturing of something else.
// The edges that separated two input faces which came out as one face are cut into the result again, the way a
// shell split cuts them, so that only the faces of the removed features change. An edge only one of the two faces
// keeps, or one the removed features touched, leaves a face that is not cut through, and the result is then kept
// as the defeaturing made it.
TopoDS_Shape RestoreMergedFaces(const TopoDS_Shape& inputShape, BRepAlgoAPI_Defeaturing& defeaturing,
								const TopoDS_Shape& result)
{
	TopTools_IndexedMapOfShape resultFaces;
	TopTools_IndexedMapOfShape resultEdges;
	TopExp::MapShapes(result, TopAbs_FACE, resultFaces);
	TopExp::MapShapes(result, TopAbs_EDGE, resultEdges);
	// The face of the result every input face became
	TopTools_IndexedMapOfShape inputFaces;
	TopExp::MapShapes(inputShape, TopAbs_FACE, inputFaces);
	TopTools_DataMapOfShapeInteger faceImages;
	for (int i = 1; i <= inputFaces.Extent(); i++)
	{
		const TopoDS_Shape& face = inputFaces(i);
		if (defeaturing.IsDeleted(face)) continue;
		const TopTools_ListOfShape& modified = defeaturing.Modified(face);
		if (modified.Extent() > 1) continue;
		int index = resultFaces.FindIndex(modified.IsEmpty() ? face : modified.First());
		if (index > 0) faceImages.Bind(face, index);
	}
	// The edges between two faces that became one, which the result no longer holds
	TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
	TopExp::MapShapesAndAncestors(inputShape, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
	TopTools_ListOfShape tools;
	for (int i = 1; i <= edgeFaces.Extent(); i++)
	{
		TopTools_IndexedMapOfShape faces;
		for (TopTools_ListIteratorOfListOfShape it(edgeFaces(i)); it.More(); it.Next()) faces.Add(it.Value());
		if (faces.Extent() != 2) continue;
		if (!faceImages.IsBound(faces(1)) || !faceImages.IsBound(faces(2))) continue;
		if (faceImages.Find(faces(1)) != faceImages.Find(faces(2))) continue;
		const TopoDS_Shape& edge = edgeFaces.FindKey(i);
		bool kept = resultEdges.Contains(edge);
		if (!defeaturing.IsDeleted(edge))
		{
			for (TopTools_ListIteratorOfListOfShape it(defeaturing.Modified(edge)); it.More() && !kept; it.Next())
				kept = resultEdges.Contains(it.Value());
		}
		if (!kept) tools.Append(edge);
	}
	// An edge that ended on the removed features no longer reaches across its face, and cut in it would leave the
	// face with an edge inside: only the edges whose ends lie on the edges of the result, or on another edge cut in
	// again, are cut
	TopoDS_Compound resultEdgeCompound;
	BRep_Builder edgeBuilder;
	edgeBuilder.MakeCompound(resultEdgeCompound);
	for (int i = 1; i <= resultEdges.Extent(); i++) edgeBuilder.Add(resultEdgeCompound, resultEdges(i));
	int numOfDropped = 0;
	while (true)
	{
		TopoDS_Shape loose;
		for (TopTools_ListIteratorOfListOfShape it(tools); it.More() && loose.IsNull(); it.Next())
		{
			for (TopExp_Explorer exp0(it.Value(), TopAbs_VERTEX); exp0.More() && loose.IsNull(); exp0.Next())
			{
				const TopoDS_Vertex& vertex = TopoDS::Vertex(exp0.Current());
				bool held = false;
				for (TopTools_ListIteratorOfListOfShape other(tools); other.More() && !held; other.Next())
				{
					if (other.Value().IsSame(it.Value())) continue;
					for (TopExp_Explorer exp1(other.Value(), TopAbs_VERTEX); exp1.More() && !held; exp1.Next())
						held = exp1.Current().IsSame(vertex);
				}
				if (!held)
				{
					BRepExtrema_DistShapeShape distance(vertex, resultEdgeCompound);
					double tolerance = std::max(10 * BRep_Tool::Tolerance(vertex), 1E-5);
					held = distance.IsDone() && distance.Value() <= tolerance;
				}
				if (!held) loose = it.Value();
			}
		}
		if (loose.IsNull()) break;
		tools.Remove(loose);
		numOfDropped++;
	}
	if (numOfDropped > 0)
		cout << "WARNING: " << numOfDropped << " edges between faces the defeaturing joined ended on the removed"
			 << " features and were not restored." << endl;
	if (tools.IsEmpty()) return result;
	//
	BRepAlgoAPI_Splitter splitter;
	TopTools_ListOfShape arguments;
	arguments.Append(result);
	splitter.SetArguments(arguments);
	splitter.SetTools(tools);
	splitter.SetRunParallel(false);
	splitter.Build();
	if (!splitter.IsDone())
	{
		cout << "WARNING: the faces the defeaturing joined could not be split again." << endl;
		return result;
	}
	// The solids in the order of the result, the one solid of a solid
	TopoDS_Compound split;
	BRep_Builder builder;
	builder.MakeCompound(split);
	int numOfSolids = 0;
	for (TopExp_Explorer exp0(result, TopAbs_SOLID); exp0.More(); exp0.Next())
	{
		const TopTools_ListOfShape& modified = splitter.Modified(exp0.Current());
		if (modified.Extent() > 1)
		{
			cout << "WARNING: splitting the joined faces again cut a solid, so they were left joined." << endl;
			return result;
		}
		builder.Add(split, modified.IsEmpty() ? exp0.Current() : modified.First());
		numOfSolids++;
	}
	TopoDS_Shape restored = split;
	if (result.ShapeType() == TopAbs_SOLID && numOfSolids == 1) restored = TopoDS_Iterator(split).Value();
	// An edge that does not cut its face through stays inside it
	for (TopExp_Explorer exp0(restored, TopAbs_EDGE); exp0.More(); exp0.Next())
	{
		if (exp0.Current().Orientation() == TopAbs_INTERNAL)
		{
			cout << "WARNING: an edge between faces the defeaturing joined no longer cuts its face through, so the"
				 << " faces were left joined." << endl;
			return result;
		}
	}
	if (!BRepCheck_Analyzer(restored).IsValid())
	{
		cout << "WARNING: the faces the defeaturing joined could not be split again into a valid shape." << endl;
		return result;
	}
	TopTools_IndexedMapOfShape restoredFaces;
	TopExp::MapShapes(restored, TopAbs_FACE, restoredFaces);
	cout << "The splits of " << tools.Extent() << " edges the defeaturing joined were restored: "
		 << restoredFaces.Extent() - resultFaces.Extent() << " faces." << endl;
	return restored;
}
// The face ids are the order Netgen uses when it builds its face map from a loaded solid.
// Read the BREP ourselves so the faces given to OCCT belong to the shape being defeatured.
bool DefeatureBrep(int argc, char* argv[])
{
	try
	{
		if (argc < 5)
		{
			cerr << "The BREP_DEFEATURE command needs an input file, an output file and face ids." << endl;
			return 1;
		}
		BRep_Builder builder;
		TopoDS_Shape inputShape;
		if (!BRepTools::Read(inputShape, argv[2], builder))
		{
			cerr << "Error reading BREP file: " << argv[2] << endl;
			return 1;
		}
		TopTools_IndexedMapOfShape faces;
		TopTools_IndexedMapOfShape solids;
		TopExp::MapShapes(inputShape, TopAbs_FACE, faces);
		TopExp::MapShapes(inputShape, TopAbs_SOLID, solids);
		if (solids.Extent() != 1)
		{
			cerr << "Defeaturing needs a BREP containing one solid." << endl;
			return 1;
		}
		std::set<int> selectedFaceIds;
		for (int i = 4; i < argc; i++)
		{
			istringstream stream(argv[i]);
			int faceId;
			while (stream >> faceId)
			{
				if (faceId < 1 || faceId > faces.Extent())
				{
					cerr << "Face id " << faceId << " is outside 1 to " << faces.Extent() << "." << endl;
					return 1;
				}
				selectedFaceIds.insert(faceId);
			}
			if (!stream.eof())
			{
				cerr << "Invalid face id: " << argv[i] << endl;
				return 1;
			}
		}
		if (selectedFaceIds.empty())
		{
			cerr << "No face ids were given." << endl;
			return 1;
		}
		BRepAlgoAPI_Defeaturing defeaturing;
		defeaturing.SetShape(inputShape);
		defeaturing.SetRunParallel(false);
		defeaturing.SetToFillHistory(true);
		for (int faceId : selectedFaceIds) defeaturing.AddFaceToRemove(faces(faceId));
		defeaturing.Build();
		if (!defeaturing.IsDone())
		{
			defeaturing.DumpErrors(cerr);
			cerr << "The selected faces could not be defeatured." << endl;
			return 1;
		}
		if (defeaturing.HasWarnings()) defeaturing.DumpWarnings(cout);
		TopoDS_Shape result = defeaturing.Shape();
		if (result.IsNull())
		{
			cerr << "Defeaturing returned no shape." << endl;
			return 1;
		}
		result = RestoreMergedFaces(inputShape, defeaturing, result);
		TopTools_IndexedMapOfShape resultFaces;
		TopTools_IndexedMapOfShape resultSolids;
		TopExp::MapShapes(result, TopAbs_FACE, resultFaces);
		TopExp::MapShapes(result, TopAbs_SOLID, resultSolids);
		if (resultSolids.Extent() != 1 || resultFaces.Extent() > faces.Extent() ||
			!BRepCheck_Analyzer(result).IsValid())
		{
			cerr << "Defeaturing did not return a valid single solid." << endl;
			return 1;
		}
		// A no-op may still return a rebuilt shape. Keep the input if no face was removed.
		if (resultFaces.Extent() == faces.Extent()) result = inputShape;
		if (!BRepTools::Write(result, argv[3]))
		{
			cerr << "Error writing BREP file: " << argv[3] << endl;
			return 1;
		}
		cout << "Defeature finished successfully: " << faces.Extent() - resultFaces.Extent()
		     << " faces were removed." << endl;
		return 0;
	}
	catch (const Standard_Failure & error)
	{
		cerr << "Defeaturing failed: " << error.GetMessageString() << endl;
		return 1;
	}
	catch (const std::exception & error)
	{
		cerr << "Defeaturing failed: " << error.what() << endl;
		return 1;
	}
}
// A point strictly inside the solid, found just behind one of its faces. The classifier confirms it,
// so a face whose normal points the other way, or a sample that falls in a hole, only costs a retry
static bool FindPointInsideSolid(const TopoDS_Shape & solid, gp_Pnt & point)
{
	Bnd_Box box;
	BRepBndLib::Add(solid, box);
	if (box.IsVoid()) return false;
	double diagonal = sqrt(box.SquareExtent());
	double tolerance = 1e-7 * diagonal;
	const double fractions[3] = { 1e-3, 1e-4, 1e-2 };
	//
	for (TopExp_Explorer exp0(solid, TopAbs_FACE); exp0.More(); exp0.Next())
	{
		TopoDS_Face face = TopoDS::Face(exp0.Current());
		BRepAdaptor_Surface surface(face);
		double u1, u2, v1, v2;
		BRepTools::UVBounds(face, u1, u2, v1, v2);
		//
		for (int i = 1; i <= 3; i++)
		{
			for (int j = 1; j <= 3; j++)
			{
				double u = u1 + (u2 - u1) * i / 4.0;
				double v = v1 + (v2 - v1) * j / 4.0;
				BRepClass_FaceClassifier faceClassifier(face, gp_Pnt2d(u, v), Precision::PConfusion());
				if (faceClassifier.State() != TopAbs_IN) continue;
				//
				gp_Pnt onFace;
				gp_Vec du, dv;
				surface.D1(u, v, onFace, du, dv);
				gp_Vec normal = du.Crossed(dv);
				if (normal.Magnitude() < gp::Resolution()) continue;
				normal.Normalize();
				//
				for (double fraction : fractions)
				{
					for (int side = -1; side <= 1; side += 2)
					{
						gp_Pnt inside = onFace.Translated(normal * (side * fraction * diagonal));
						BRepClass3d_SolidClassifier solidClassifier(solid, inside, tolerance);
						if (solidClassifier.State() == TopAbs_IN)
						{
							point = inside;
							return true;
						}
					}
				}
			}
		}
	}
	return false;
}
// A split only divides solids, so every solid it gives back lies inside exactly one of the solids it
// was given. Which one is written next to the result, one line per solid in the order the explorer
// walks them, as the number of the solid it came from counted the same way, or 0 where no solid holds
// it. The caller keeps what it knew about a solid - its name, its part - on the pieces it became.
static bool WriteSplitSolidOrigins(const TopoDS_Shape & inputShape, const char * outputFileName)
{
	BRep_Builder builder;
	TopoDS_Shape outputShape;
	if (!BRepTools::Read(outputShape, outputFileName, builder)) return false;
	//
	vector<TopoDS_Shape> inputSolids;
	for (TopExp_Explorer exp0(inputShape, TopAbs_SOLID); exp0.More(); exp0.Next())
		inputSolids.push_back(exp0.Current());
	//
	vector<int> origins;
	for (TopExp_Explorer exp0(outputShape, TopAbs_SOLID); exp0.More(); exp0.Next())
	{
		int origin = 0;
		if (inputSolids.size() == 1) origin = 1;
		else
		{
			gp_Pnt inside;
			if (FindPointInsideSolid(exp0.Current(), inside))
			{
				Bnd_Box box;
				BRepBndLib::Add(exp0.Current(), box);
				double tolerance = 1e-7 * sqrt(box.SquareExtent());
				for (size_t i = 0; i < inputSolids.size(); i++)
				{
					BRepClass3d_SolidClassifier classifier(inputSolids[i], inside, tolerance);
					if (classifier.State() == TopAbs_IN) { origin = (int)i + 1; break; }
				}
			}
		}
		origins.push_back(origin);
	}
	//
	string originsFileName = string(outputFileName) + ".origins";
	ofstream originsFile(originsFileName);
	if (!originsFile) return false;
	for (size_t i = 0; i < origins.size(); i++) originsFile << origins[i] << endl;
	originsFile.close();
	//
	return true;
}
// The general fuse gives every argument its own image, so the solid where two parts overlap is listed once in the
// image of each of them, and a reader walking the result would take it twice. Each solid is kept once, in the order
// it first appears. A result with a face that lies on no solid holds more than solids and is left as it is.
static bool RemoveRepeatedCompoundSolids(const char * fileName)
{
	BRep_Builder builder;
	TopoDS_Shape shape;
	if (!BRepTools::Read(shape, fileName, builder)) return false;
	//
	TopTools_IndexedMapOfShape solids;
	int numOfSolidOccurrences = 0;
	for (TopExp_Explorer exp0(shape, TopAbs_SOLID); exp0.More(); exp0.Next())
	{
		solids.Add(exp0.Current());
		numOfSolidOccurrences++;
	}
	if (solids.Extent() == numOfSolidOccurrences) return true;
	//
	TopTools_IndexedMapOfShape faces;
	TopTools_IndexedMapOfShape solidFaces;
	TopExp::MapShapes(shape, TopAbs_FACE, faces);
	for (int i = 1; i <= solids.Extent(); i++) TopExp::MapShapes(solids(i), TopAbs_FACE, solidFaces);
	if (faces.Extent() != solidFaces.Extent()) return true;
	//
	TopoDS_Compound compound;
	builder.MakeCompound(compound);
	for (int i = 1; i <= solids.Extent(); i++) builder.Add(compound, solids(i));
	BRepTools::Write(compound, fileName, Message_ProgressRange());
	cout << "Solids listed more than once: " << numOfSolidOccurrences - solids.Extent() << " were removed." << endl;
	//
	return true;
}
// A compound imprints its parts on one another, so a solid of the result lies inside one solid it was given
// or, where the parts overlap, inside several. All of them are written next to the result, one line per
// solid in the order the explorer walks them, numbered over the solids of all the input files in the order
// the files were given, or 0 where no solid holds it. The caller decides what a solid of several parts is.
static bool WriteCompoundSolidOrigins(int argc, char* argv[])
{
	const char * outputFileName = argv[argc - 1];
	BRep_Builder builder;
	vector<TopoDS_Shape> inputSolids;
	vector<Bnd_Box> inputBoxes;
	for (int i = 2; i < argc - 1; i++)
	{
		TopoDS_Shape inputShape;
		if (!BRepTools::Read(inputShape, argv[i], builder)) return false;
		for (TopExp_Explorer exp0(inputShape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			Bnd_Box box;
			BRepBndLib::Add(exp0.Current(), box);
			inputSolids.push_back(exp0.Current());
			inputBoxes.push_back(box);
		}
	}
	//
	TopoDS_Shape outputShape;
	if (!BRepTools::Read(outputShape, outputFileName, builder)) return false;
	//
	vector<vector<int>> origins;
	for (TopExp_Explorer exp0(outputShape, TopAbs_SOLID); exp0.More(); exp0.Next())
	{
		vector<int> solidOrigins;
		gp_Pnt inside;
		if (FindPointInsideSolid(exp0.Current(), inside))
		{
			Bnd_Box box;
			BRepBndLib::Add(exp0.Current(), box);
			double tolerance = 1e-7 * sqrt(box.SquareExtent());
			for (size_t i = 0; i < inputSolids.size(); i++)
			{
				if (inputBoxes[i].IsOut(inside)) continue;
				BRepClass3d_SolidClassifier classifier(inputSolids[i], inside, tolerance);
				if (classifier.State() == TopAbs_IN) solidOrigins.push_back((int)i + 1);
			}
		}
		origins.push_back(solidOrigins);
	}
	//
	string originsFileName = string(outputFileName) + ".origins";
	ofstream originsFile(originsFileName);
	if (!originsFile) return false;
	for (size_t i = 0; i < origins.size(); i++)
	{
		if (origins[i].size() == 0) originsFile << 0;
		for (size_t j = 0; j < origins[i].size(); j++) originsFile << (j > 0 ? " " : "") << origins[i][j];
		originsFile << endl;
	}
	originsFile.close();
	//
	return true;
}
// An edge of a split lies on the edges the shape already had when every point sampled inside it does. A
// piece of an edge the tool crossed is the same curve cut shorter, so its points lie on the edge it came
// from, while an edge the tool made runs across faces and meets the old edges only at its ends. The
// tolerances the edges carry are added to the distance allowed, unless the edges are those of a repair,
// which grows them to cover what it merged and would hide an edge smaller than that.
static bool EdgeLiesOnEdges(const TopoDS_Edge & edge, const TopTools_IndexedMapOfShape & edges,
                            const vector<Bnd_Box> & edgeBoxes, double tolerance, bool addEdgesTolerance = true)
{
	BRepAdaptor_Curve curve(edge);
	double first = curve.FirstParameter();
	double last = curve.LastParameter();
	const double fractions[3] = { 0.5, 0.25, 0.75 };
	//
	for (double fraction : fractions)
	{
		gp_Pnt point = curve.Value(first + (last - first) * fraction);
		TopoDS_Vertex vertex = BRepBuilderAPI_MakeVertex(point);
		bool onEdge = false;
		for (int i = 1; i <= edges.Extent() && !onEdge; i++)
		{
			if (edgeBoxes[i - 1].IsOut(point)) continue;
			//
			const TopoDS_Edge & oldEdge = TopoDS::Edge(edges(i));
			BRepExtrema_DistShapeShape distance(vertex, oldEdge);
			double allowed = tolerance + BRep_Tool::Tolerance(edge) +
			                 (addEdgesTolerance ? BRep_Tool::Tolerance(oldEdge) : 0);
			if (distance.IsDone() && distance.Value() <= allowed)
				onEdge = true;
		}
		if (!onEdge) return false;
	}
	return true;
}
// A face of a split lies on the faces the shape already had when a point inside it does. A piece of a face the
// tool crossed lies on the face it came from, while a face the tool made runs through the inside of a solid.
static bool FaceLiesOnFaces(const TopoDS_Face & face, const TopTools_IndexedMapOfShape & faces,
                            const vector<Bnd_Box> & faceBoxes, double tolerance)
{
	BRepAdaptor_Surface surface(face);
	double u1, u2, v1, v2;
	BRepTools::UVBounds(face, u1, u2, v1, v2);
	for (int i = 1; i <= 3; i++)
	{
		for (int j = 1; j <= 3; j++)
		{
			gp_Pnt2d uv(u1 + (u2 - u1) * i / 4.0, v1 + (v2 - v1) * j / 4.0);
			BRepClass_FaceClassifier classifier(face, uv, Precision::PConfusion());
			if (classifier.State() != TopAbs_IN) continue;
			//
			gp_Pnt point = surface.Value(uv.X(), uv.Y());
			TopoDS_Vertex vertex = BRepBuilderAPI_MakeVertex(point);
			for (int k = 1; k <= faces.Extent(); k++)
			{
				if (faceBoxes[k - 1].IsOut(point)) continue;
				//
				const TopoDS_Face & oldFace = TopoDS::Face(faces(k));
				BRepExtrema_DistShapeShape distance(vertex, oldFace);
				if (distance.IsDone() && distance.Value() <= tolerance + BRep_Tool::Tolerance(face) +
				                                             BRep_Tool::Tolerance(oldFace)) return true;
			}
			return false;
		}
	}
	return true;
}
// The edges a split made, each written as a polyline of points on it, so that the caller can show where
// the tool will cut without taking the result in. An edge the shape had before, whole or cut shorter, is
// left out, except that with outlineNewFaces every edge of a face the split made is written: a tool that
// runs along edges the shape already had makes a face whose outline lies on them, and that outline is
// where it cuts.
static bool WriteSplitPreviewEdges(const TopTools_IndexedMapOfShape & facesBefore,
                                   const TopTools_IndexedMapOfShape & facesAfter, const char * fileName,
                                   bool outlineNewFaces)
{
	TopTools_IndexedMapOfShape edgesBefore;
	TopTools_IndexedMapOfShape edgesAfter;
	for (int i = 1; i <= facesBefore.Extent(); i++) TopExp::MapShapes(facesBefore(i), TopAbs_EDGE, edgesBefore);
	for (int i = 1; i <= facesAfter.Extent(); i++) TopExp::MapShapes(facesAfter(i), TopAbs_EDGE, edgesAfter);
	//
	Bnd_Box shapeBox;
	for (int i = 1; i <= facesAfter.Extent(); i++) BRepBndLib::Add(facesAfter(i), shapeBox);
	if (shapeBox.IsVoid()) return false;
	double diagonal = sqrt(shapeBox.SquareExtent());
	double tolerance = 1e-7 * diagonal;
	//
	vector<Bnd_Box> edgeBoxes(edgesBefore.Extent());
	for (int i = 1; i <= edgesBefore.Extent(); i++)
	{
		BRepBndLib::Add(edgesBefore(i), edgeBoxes[i - 1]);
		edgeBoxes[i - 1].Enlarge(tolerance + BRep_Tool::Tolerance(TopoDS::Edge(edgesBefore(i))));
	}
	//
	TopTools_IndexedMapOfShape outlineEdges;
	if (outlineNewFaces)
	{
		vector<Bnd_Box> faceBoxes(facesBefore.Extent());
		for (int i = 1; i <= facesBefore.Extent(); i++)
		{
			BRepBndLib::Add(facesBefore(i), faceBoxes[i - 1]);
			faceBoxes[i - 1].Enlarge(tolerance + BRep_Tool::Tolerance(TopoDS::Face(facesBefore(i))));
		}
		for (int i = 1; i <= facesAfter.Extent(); i++)
		{
			if (facesBefore.Contains(facesAfter(i))) continue;
			if (!FaceLiesOnFaces(TopoDS::Face(facesAfter(i)), facesBefore, faceBoxes, tolerance))
				TopExp::MapShapes(facesAfter(i), TopAbs_EDGE, outlineEdges);
		}
	}
	//
	ofstream file(fileName);
	if (!file) return false;
	file.precision(15);
	file << "Split preview format: 1" << endl;
	//
	int numOfEdges = 0;
	for (int i = 1; i <= edgesAfter.Extent(); i++)
	{
		const TopoDS_Edge & edge = TopoDS::Edge(edgesAfter(i));
		if (BRep_Tool::Degenerated(edge)) continue;
		if (!outlineEdges.Contains(edge) &&
		    (edgesBefore.Contains(edge) || EdgeLiesOnEdges(edge, edgesBefore, edgeBoxes, tolerance))) continue;
		//
		BRepAdaptor_Curve curve(edge);
		GCPnts_TangentialDeflection points(curve, 0.1, 1e-3 * diagonal);
		if (points.NbPoints() < 2) continue;
		//
		file << "Edge: " << points.NbPoints() << endl;
		for (int j = 1; j <= points.NbPoints(); j++)
		{
			gp_Pnt point = points.Value(j);
			file << point.X() << " " << point.Y() << " " << point.Z() << endl;
		}
		numOfEdges++;
	}
	file.close();
	//
	cout << "Split preview finished successfully: " << numOfEdges << " edges were made." << endl;
	return true;
}
bool SplitGeometry(int argc, char* argv[], bool preview)
{
	try
	{
		if (argc < 5)
		{
			cerr << "The BREP_SPLIT command needs an input file, an output file and a tool definition file." << endl;
			return 1;
		}
		// The face count is what says whether the split happened, since the modelling kernel returns
		// a shape whether or not it made the cut
		TopTools_IndexedMapOfShape FMap;
		Ng_OCC_TopTools_IndexedMapOfShape * occ_fmap = (Ng_OCC_TopTools_IndexedMapOfShape*)&FMap;
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		// The shape as it was given, read before the result is written, since the two may be one file
		BRep_Builder inputBuilder;
		TopoDS_Shape inputShape;
		BRepTools::Read(inputShape, argv[2], inputBuilder);
		//
		Ng_OCC_GetFMap(occ_geom, occ_fmap);
		int numOfFacesBefore = FMap.Extent();
		// The splitter leaves its arguments as they were, so the faces of the shape stay what a preview
		// compares the result with
		TopTools_IndexedMapOfShape facesBefore;
		facesBefore.Assign(FMap);
		// Read the tool definition
		ifstream toolFile(argv[4]);
		if (!toolFile)
		{
			cerr << "Error reading the tool definition file: " << argv[4] << endl;
			return 1;
		}
		//
		string toolType;
		vector<string> sourceFileNames;
		vector<int> edgeIdCounts;
		double fuzzyValue = 0;
		double offset = 0;
		double extent[6] = { 0, 0, 0, 0, 0, 0 };
		double origin[3] = { 0, 0, 0 };
		double normal[3] = { 0, 0, 1 };
		double extrusionOffset[3] = { 0, 0, 0 };
		double extrusionVector[3] = { 0, 0, 0 };
		vector<int> faceIds;
		vector<int> faceIdCounts;
		vector<int> edgeIds;
		vector<int> solidIds;
		string splitTarget;
		vector<int> targetSolids;
		vector<int> targetFaceCounts;
		vector<int> targetFaceIds;
		double firstPoint[3] = { 0, 0, 0 };
		double secondPoint[3] = { 0, 0, 0 };
		//
		string line;
		while (getline(toolFile, line))
		{
			size_t colon = line.find(':');
			if (colon == string::npos) continue;
			string key = ToolKeyFromText(line.substr(0, colon));
			string value = TrimToolText(line.substr(colon + 1));
			//
			if (key == "tooltype") toolType = ToolKeyFromText(value);
			// Each source file opens a group; the edge ids that follow it are read from that file
			else if (key == "sourcefile")
			{
				sourceFileNames.push_back(value);
				edgeIdCounts.push_back(0);
				faceIdCounts.push_back(0);
			}
			else if (key == "fuzzyvalue") fuzzyValue = stod(value);
			else if (key == "offset") offset = stod(value);
			else if (key == "extent") ReadToolValues(value, extent, 6);
			else if (key == "planeorigin") ReadToolValues(value, origin, 3);
			else if (key == "planenormal") ReadToolValues(value, normal, 3);
			else if (key == "point1") ReadToolValues(value, firstPoint, 3);
			else if (key == "point2") ReadToolValues(value, secondPoint, 3);
			else if (key == "faceid" || key == "faceids")
			{
				istringstream stream(value);
				int id;
				int numOfIds = 0;
				while (stream >> id) { faceIds.push_back(id); numOfIds++; }
				// Ids given before any source file are read from the shape being split
				if (faceIdCounts.size() == 0) faceIdCounts.push_back(numOfIds);
				else faceIdCounts[faceIdCounts.size() - 1] += numOfIds;
			}
			else if (key == "extrusionoffset") ReadToolValues(value, extrusionOffset, 3);
			else if (key == "extrusionvector") ReadToolValues(value, extrusionVector, 3);
			else if (key == "edgeids")
			{
				istringstream stream(value);
				int edgeId;
				int numOfIds = 0;
				while (stream >> edgeId) { edgeIds.push_back(edgeId); numOfIds++; }
				// Ids given before any source file are read from the shape being split
				if (edgeIdCounts.size() == 0) edgeIdCounts.push_back(numOfIds);
				else edgeIdCounts[edgeIdCounts.size() - 1] += numOfIds;
			}
			else if (key == "solidids")
			{
				istringstream stream(value);
				int solidId;
				while (stream >> solidId) solidIds.push_back(solidId);
			}
			else if (key == "splittarget") splitTarget = ToolKeyFromText(value);
			// Each target solid opens a group; the face ids that follow it are numbered inside that solid
			else if (key == "targetsolid")
			{
				targetSolids.push_back(stoi(value));
				targetFaceCounts.push_back(0);
			}
			else if (key == "targetfaceid" || key == "targetfaceids")
			{
				istringstream stream(value);
				int id;
				int numOfIds = 0;
				while (stream >> id) { targetFaceIds.push_back(id); numOfIds++; }
				// Ids given before any target solid are numbered in the shape being split
				if (targetFaceCounts.size() == 0)
				{
					targetSolids.push_back(0);
					targetFaceCounts.push_back(numOfIds);
				}
				else targetFaceCounts[targetFaceCounts.size() - 1] += numOfIds;
			}
		}
		toolFile.close();
		// The tool geometry may live on other parts than the geometry being split, and on more than
		// one of them, because a compound is split as a whole while its pieces carry the picked edges
		vector<Ng_OCC_Geometry *> source_geoms;
		for (size_t i = 0; i < sourceFileNames.size(); i++)
		{
			cout << "Ng_OCC_Load_BREP" << endl;
			Ng_OCC_Geometry * source_geom = Ng_OCC_Load_BREP(sourceFileNames[i].c_str());
			if (!source_geom)
			{
				cout << "Error reading in the source BREP File: " << sourceFileNames[i] << endl;
				return 1;
			}
			cout << "Successfully loaded the source BREP File: " << sourceFileNames[i] << endl;
			source_geoms.push_back(source_geom);
		}
		//
		int * solidIdsData = solidIds.size() == 0 ? NULL : &solidIds[0];
		int numOfSolidIds = (int)solidIds.size();
		// A shell split divides the faces it is given and leaves the body they belong to whole, so
		// it has to be told which faces those are. Without the target the tool cuts through, as before.
		bool splitShell = splitTarget == "shell";
		if (splitShell && targetFaceCounts.size() == 0)
		{
			cerr << "A shell split needs the ids of the surfaces to split." << endl;
			return 1;
		}
		int * targetSolidsData = !splitShell || targetSolids.size() == 0 ? NULL : &targetSolids[0];
		int * targetFaceCountsData = !splitShell || targetFaceCounts.size() == 0 ?
		                             NULL : &targetFaceCounts[0];
		int * targetFaceIdsData = !splitShell || targetFaceIds.size() == 0 ? NULL : &targetFaceIds[0];
		int numOfTargetGroups = splitShell ? (int)targetFaceCounts.size() : 0;
		//
		if (toolType == "plane")
		{
			cout << "Ng_OCC_SplitWithPlane" << endl;
			occ_geom = Ng_OCC_SplitWithPlane(occ_geom, origin, normal, extent, fuzzyValue, solidIdsData,
			                                 numOfSolidIds, targetSolidsData, targetFaceCountsData,
			                                 numOfTargetGroups, targetFaceIdsData);
		}
		else if (toolType == "extendface")
		{
			cout << "Ng_OCC_SplitWithExtendedFace" << endl;
			occ_geom = Ng_OCC_SplitWithExtendedFace(occ_geom,
			                                        source_geoms.size() == 0 ? NULL : &source_geoms[0],
			                                        faceIdCounts.size() == 0 ? NULL : &faceIdCounts[0],
			                                        (int)faceIdCounts.size(),
			                                        faceIds.size() == 0 ? NULL : &faceIds[0],
			                                        extent, offset, fuzzyValue, solidIdsData, numOfSolidIds,
			                                        targetSolidsData, targetFaceCountsData,
			                                        numOfTargetGroups, targetFaceIdsData);
		}
		else if (toolType == "extrudeedges")
		{
			cout << "Ng_OCC_SplitWithExtrudedEdges" << endl;
			occ_geom = Ng_OCC_SplitWithExtrudedEdges(occ_geom,
			                                         source_geoms.size() == 0 ? NULL : &source_geoms[0],
			                                         edgeIdCounts.size() == 0 ? NULL : &edgeIdCounts[0],
			                                         (int)edgeIdCounts.size(),
			                                         edgeIds.size() == 0 ? NULL : &edgeIds[0],
			                                         extrusionOffset, extrusionVector, fuzzyValue,
			                                         solidIdsData, numOfSolidIds, targetSolidsData,
			                                         targetFaceCountsData, numOfTargetGroups,
			                                         targetFaceIdsData);
		}
		else if (toolType == "twopointline")
		{
			// The line belongs to the surface it is drawn on, so this tool divides faces and nothing else
			if (numOfTargetGroups == 0)
			{
				cerr << "A split along the line between two points needs the ids of the surfaces to split."
				     << endl;
				return 1;
			}
			cout << "Ng_OCC_SplitWithSurfaceLine" << endl;
			occ_geom = Ng_OCC_SplitWithSurfaceLine(occ_geom, firstPoint, secondPoint, fuzzyValue,
			                                       targetSolidsData, targetFaceCountsData, numOfTargetGroups,
			                                       targetFaceIdsData);
		}
		else
		{
			cerr << "The splitting tool type is not supported: " << toolType << endl;
			return 1;
		}
		//
		FMap.Clear();
		Ng_OCC_GetFMap(occ_geom, occ_fmap);
		int numOfFacesAfter = FMap.Extent();
		//
		if (numOfFacesAfter <= numOfFacesBefore)
		{
			cerr << "The splitting tool did not split the geometry." << endl;
			return 1;
		}
		//
		if (preview)
		{
			if (!WriteSplitPreviewEdges(facesBefore, FMap, argv[3], !splitShell))
			{
				cerr << "The edges the split made could not be written." << endl;
				return 1;
			}
			return 0;
		}
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		if (!WriteSplitSolidOrigins(inputShape, argv[3]))
		{
			cerr << "The solids the split gave back could not be traced to the solids it was given." << endl;
			return 1;
		}
		//
		cout << "Split geometry finished successfully: " << numOfFacesAfter - numOfFacesBefore
		     << " faces were added." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
// A shape whose closed faces are divided the way the parts written out of it are, so that the two
// carry the same faces in the same order. Without it a compound keeps one closed face where the
// part taken from it has two, and a face id read on the part names nothing in the compound.
bool SplitClosedFaces(int argc, char* argv[])
{
	try
	{
		if (argc < 4)
		{
			cerr << "The BREP_SPLIT_CLOSED_FACES command needs an input file and an output file." << endl;
			return 1;
		}
		int numOfSplitFaces = argc > 4 ? atoi(argv[4]) : 1;
		//
		Ng_Init();
		//
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		cout << "Ng_OCC_SaveBrepWithSplitClosedFaces" << endl;
		if (Ng_OCC_SaveBrepWithSplitClosedFaces(occ_geom, argv[3], numOfSplitFaces) != NG_OK)
		{
			cerr << "The closed faces of the shape could not be divided." << endl;
			return 1;
		}
		//
		cout << "Split closed faces finished successfully." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
bool ConvertToShell(int argc, char* argv[])
{
	try
	{
		//Define pointer to OCC Geometry
		Ng_OCC_Geometry* occ_geom;
		// Result of Netgen Operations
		Ng_Result ng_res;
		int np, ne;
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		cout << "Ng_OCC_ConvertToShell" << endl;
		occ_geom = Ng_OCC_ConvertToShell(occ_geom);
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Convert ot shell finished successfully." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
bool OffsetFaces(int argc, char* argv[])
{
	try
	{
		if (argc < 8)
		{
			cerr << "BREP_OFFSET_FACES takes an input file, an output file, an offset and the number of"
			     << " face groups, each written as a solid number, a face count and that many face ids."
			     << endl;
			return 1;
		}
		//Define pointer to OCC Geometry
		Ng_OCC_Geometry* occ_geom;
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		std::string::size_type sz;     // alias of size_t
		double offset = std::stod(argv[4], &sz);
		// The face ids arrive in groups, each of them a solid number, a face count and that many ids. The
		// ids of a group are numbered inside that solid of the shape, or in the shape itself when it is 0
		int numOfTargetGroups = std::stoi(argv[5], &sz);
		if (numOfTargetGroups < 1)
		{
			cerr << "BREP_OFFSET_FACES takes at least one face group." << endl;
			return 1;
		}
		//
		int * targetSolids = new int[numOfTargetGroups];
		int * targetFaceCounts = new int[numOfTargetGroups];
		std::vector<int> faceIdList;
		int argument = 6;
		for (int group = 0; group < numOfTargetGroups; group++)
		{
			if (argument + 1 >= argc)
			{
				cerr << "BREP_OFFSET_FACES was given fewer face groups than it was told to expect." << endl;
				return 1;
			}
			targetSolids[group] = std::stoi(argv[argument++], &sz);
			targetFaceCounts[group] = std::stoi(argv[argument++], &sz);
			for (int i = 0; i < targetFaceCounts[group]; i++)
			{
				if (argument >= argc)
				{
					cerr << "BREP_OFFSET_FACES was given fewer face ids than it was told to expect." << endl;
					return 1;
				}
				faceIdList.push_back(std::stoi(argv[argument++], &sz));
			}
		}
		//
		cout << "Ng_OCC_OffsetFaces" << endl;
		occ_geom = Ng_OCC_OffsetFaces(occ_geom, targetSolids, targetFaceCounts, numOfTargetGroups,
		                              faceIdList.data(), offset);
		if (!occ_geom)
		{
			cout << "Offsetting the faces failed." << endl;
			return 1;
		}
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Offset face finished successfully." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
static int FindPieceGroup(vector<int> & groups, int i)
{
	while (groups[i] != i) i = groups[i] = groups[groups[i]];
	return i;
}
// The pieces the faces of a shape fall into, two faces being in one piece when they share an edge. Each is a
// shell of its faces with the orientations they had, and the largest by area comes first
static vector<TopoDS_Shape> SplitIntoPieces(const TopoDS_Shape & shape)
{
	TopTools_IndexedMapOfShape faces;
	TopExp::MapShapes(shape, TopAbs_FACE, faces);
	TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
	TopExp::MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
	//
	vector<int> groups(faces.Extent() + 1);
	for (int i = 0; i <= faces.Extent(); i++) groups[i] = i;
	for (int i = 1; i <= edgeFaces.Extent(); i++)
	{
		int first = 0;
		for (TopTools_ListIteratorOfListOfShape it(edgeFaces(i)); it.More(); it.Next())
		{
			int faceId = faces.FindIndex(it.Value());
			if (faceId < 1) continue;
			if (first == 0) { first = faceId; continue; }
			int firstGroup = FindPieceGroup(groups, first);
			int group = FindPieceGroup(groups, faceId);
			if (firstGroup != group) groups[group] = firstGroup;
		}
	}
	//
	BRep_Builder builder;
	map<int, int> pieceOfGroup;
	vector<TopoDS_Shell> shells;
	vector<bool> added(faces.Extent() + 1, false);
	for (TopExp_Explorer exp0(shape, TopAbs_FACE); exp0.More(); exp0.Next())
	{
		int faceId = faces.FindIndex(exp0.Current());
		if (faceId < 1 || added[faceId]) continue;
		added[faceId] = true;
		//
		int group = FindPieceGroup(groups, faceId);
		if (pieceOfGroup.find(group) == pieceOfGroup.end())
		{
			pieceOfGroup[group] = (int)shells.size();
			TopoDS_Shell shell;
			builder.MakeShell(shell);
			shells.push_back(shell);
		}
		builder.Add(shells[pieceOfGroup[group]], exp0.Current());
	}
	//
	vector<pair<double, int>> areas;
	for (size_t i = 0; i < shells.size(); i++)
	{
		shells[i].Closed(BRep_Tool::IsClosed(shells[i]));
		GProp_GProps properties;
		BRepGProp::SurfaceProperties(shells[i], properties);
		areas.push_back(make_pair(-properties.Mass(), (int)i));
	}
	sort(areas.begin(), areas.end());
	vector<TopoDS_Shape> pieces;
	for (size_t i = 0; i < areas.size(); i++) pieces.push_back(shells[areas[i].second]);
	return pieces;
}
// The pieces of a body are written as the files numbered from fileNumber when the deletion divided it, and
// the body as one file when it did not; answers the number of files written
static int WriteBodyPieces(const TopoDS_Shape & body, int numOfPiecesBefore, const string & outputFileName,
                           int fileNumber, bool firstIsOutput)
{
	vector<TopoDS_Shape> pieces = SplitIntoPieces(body);
	if ((int)pieces.size() <= numOfPiecesBefore) pieces = vector<TopoDS_Shape>(1, body);
	//
	for (size_t i = 0; i < pieces.size(); i++)
	{
		string fileName = firstIsOutput && i == 0 ? outputFileName :
		                  PatternCopyFileName(outputFileName, fileNumber + (int)i - (firstIsOutput ? 1 : 0));
		if (!BRepTools::Write(pieces[i], fileName.c_str())) return -1;
	}
	return (int)pieces.size();
}
// The face ids arrive grouped as BREP_OFFSET_FACES takes them. A solid that loses a face comes back as
// the shell that is left of it, and everything that loses nothing comes back as it was. A part that the
// deletion divides into pieces that no longer touch comes back as the largest of them, the others written
// beside it as <out>_000k.brep and their number in <out>.pieces. For a compound the output holds only the
// solids that were kept, each opened solid is written beside it as <out>_000k.brep, in as many files as it
// fell into pieces, <out>.opened names the solid each came from and its number of files, one solid per
// line, and <out>.removed names the solids that lost every face and are gone
// The compound is defeatured as a whole rather than solid by solid, so that a feature on a face two solids share,
// or one running across them, is removed from both and the solids still meet on the faces they share. The solids
// are written back in the order they were read, which is the order the sub parts of the compound are numbered in.
bool DefeatureCompoundBrep(int argc, char* argv[])
{
	try
	{
		if (argc < 7)
		{
			cerr << "BREP_DEFEATURE_COMPOUND takes an input file, an output file and the number of face groups, each"
			     << " written as a solid number, a face count and that many face ids." << endl;
			return 1;
		}
		BRep_Builder builder;
		TopoDS_Shape inputShape;
		if (!BRepTools::Read(inputShape, argv[2], builder))
		{
			cerr << "Error reading BREP file: " << argv[2] << endl;
			return 1;
		}
		std::vector<TopoDS_Shape> solids;
		for (TopExp_Explorer exp0(inputShape, TopAbs_SOLID); exp0.More(); exp0.Next()) solids.push_back(exp0.Current());
		if (solids.size() < 1)
		{
			cerr << "Defeaturing a compound needs a BREP containing solids." << endl;
			return 1;
		}
		TopTools_IndexedMapOfShape faces;
		TopExp::MapShapes(inputShape, TopAbs_FACE, faces);
		//
		std::string::size_type sz;
		int numOfGroups = std::stoi(argv[4], &sz);
		TopTools_IndexedMapOfShape selectedFaces;
		int argument = 5;
		for (int group = 0; group < numOfGroups; group++)
		{
			if (argument + 1 >= argc)
			{
				cerr << "BREP_DEFEATURE_COMPOUND was given fewer face groups than it was told to expect." << endl;
				return 1;
			}
			int solidNumber = std::stoi(argv[argument++], &sz);
			int numOfFaces = std::stoi(argv[argument++], &sz);
			if (solidNumber < 1 || solidNumber > (int)solids.size())
			{
				cerr << "Solid " << solidNumber << " is outside 1 to " << solids.size() << "." << endl;
				return 1;
			}
			TopTools_IndexedMapOfShape solidFaces;
			TopExp::MapShapes(solids[solidNumber - 1], TopAbs_FACE, solidFaces);
			for (int i = 0; i < numOfFaces; i++)
			{
				if (argument >= argc)
				{
					cerr << "BREP_DEFEATURE_COMPOUND was given fewer face ids than it was told to expect." << endl;
					return 1;
				}
				int faceId = std::stoi(argv[argument++], &sz);
				if (faceId < 1 || faceId > solidFaces.Extent())
				{
					cerr << "Face id " << faceId << " of solid " << solidNumber << " is outside 1 to "
					     << solidFaces.Extent() << "." << endl;
					return 1;
				}
				selectedFaces.Add(solidFaces(faceId));
			}
		}
		if (selectedFaces.Extent() == 0)
		{
			cerr << "No face ids were given." << endl;
			return 1;
		}
		BRepAlgoAPI_Defeaturing defeaturing;
		defeaturing.SetShape(inputShape);
		defeaturing.SetRunParallel(false);
		defeaturing.SetToFillHistory(true);
		for (int i = 1; i <= selectedFaces.Extent(); i++) defeaturing.AddFaceToRemove(selectedFaces(i));
		defeaturing.Build();
		if (!defeaturing.IsDone())
		{
			defeaturing.DumpErrors(cerr);
			cerr << "The selected faces could not be defeatured." << endl;
			return 1;
		}
		if (defeaturing.HasWarnings()) defeaturing.DumpWarnings(cout);
		TopoDS_Shape result = defeaturing.Shape();
		if (result.IsNull())
		{
			cerr << "Defeaturing returned no shape." << endl;
			return 1;
		}
		// Every solid is followed into the result through the history, so the order of the solids is kept
		TopTools_IndexedMapOfShape resultSolids;
		TopExp::MapShapes(result, TopAbs_SOLID, resultSolids);
		TopoDS_Compound ordered;
		builder.MakeCompound(ordered);
		TopTools_IndexedMapOfShape usedSolids;
		for (size_t i = 0; i < solids.size(); i++)
		{
			TopoDS_Shape solid = solids[i];
			if (defeaturing.IsDeleted(solid))
			{
				cerr << "Defeaturing removed the solid " << i + 1 << "." << endl;
				return 1;
			}
			const TopTools_ListOfShape & modified = defeaturing.Modified(solid);
			if (modified.Extent() > 1)
			{
				cerr << "Defeaturing split the solid " << i + 1 << "." << endl;
				return 1;
			}
			if (modified.Extent() == 1) solid = modified.First();
			if (!resultSolids.Contains(solid) || usedSolids.Contains(solid))
			{
				cerr << "The solid " << i + 1 << " could not be found in the defeatured compound." << endl;
				return 1;
			}
			usedSolids.Add(solid);
			builder.Add(ordered, solid);
		}
		if (usedSolids.Extent() != resultSolids.Extent())
		{
			cerr << "Defeaturing returned a different number of solids." << endl;
			return 1;
		}
		if (!BRepCheck_Analyzer(ordered).IsValid())
		{
			cerr << "Defeaturing did not return a valid compound of solids." << endl;
			return 1;
		}
		TopoDS_Shape restored = RestoreMergedFaces(inputShape, defeaturing, ordered);
		TopTools_IndexedMapOfShape resultFaces;
		TopExp::MapShapes(restored, TopAbs_FACE, resultFaces);
		if (resultFaces.Extent() >= faces.Extent())
		{
			cerr << "No face was removed from the geometry." << endl;
			return 1;
		}
		if (!BRepTools::Write(restored, argv[3]))
		{
			cerr << "Error writing BREP file: " << argv[3] << endl;
			return 1;
		}
		cout << "Defeature finished successfully: " << faces.Extent() - resultFaces.Extent()
		     << " faces were removed." << endl;
		return 0;
	}
	catch (const Standard_Failure & error)
	{
		cerr << "Defeaturing failed: " << error.GetMessageString() << endl;
		return 1;
	}
	catch (const std::exception & error)
	{
		cerr << "Defeaturing failed: " << error.what() << endl;
		return 1;
	}
}
bool RemoveFaces(int argc, char* argv[], bool compound)
{
	try
	{
		if (argc < 7)
		{
			cerr << "BREP_REMOVE_FACES takes an input file, an output file and the number of face groups, each"
			     << " written as a solid number, a face count and that many face ids." << endl;
			return 1;
		}
		std::string::size_type sz;     // alias of size_t
		int numOfTargetGroups = std::stoi(argv[4], &sz);
		if (numOfTargetGroups < 1)
		{
			cerr << "BREP_REMOVE_FACES takes at least one face group." << endl;
			return 1;
		}
		//
		std::vector<int> targetSolids;
		std::vector<int> targetFaceCounts;
		std::vector<int> faceIdList;
		int argument = 5;
		for (int group = 0; group < numOfTargetGroups; group++)
		{
			if (argument + 1 >= argc)
			{
				cerr << "BREP_REMOVE_FACES was given fewer face groups than it was told to expect." << endl;
				return 1;
			}
			targetSolids.push_back(std::stoi(argv[argument++], &sz));
			targetFaceCounts.push_back(std::stoi(argv[argument++], &sz));
			for (int i = 0; i < targetFaceCounts[group]; i++)
			{
				if (argument >= argc)
				{
					cerr << "BREP_REMOVE_FACES was given fewer face ids than it was told to expect." << endl;
					return 1;
				}
				faceIdList.push_back(std::stoi(argv[argument++], &sz));
			}
		}
		if (faceIdList.size() == 0)
		{
			cerr << "No face id was given." << endl;
			return 1;
		}
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		TopTools_IndexedMapOfShape removalFMap;
		Ng_OCC_TopTools_IndexedMapOfShape * occ_removal_fmap = (Ng_OCC_TopTools_IndexedMapOfShape*)&removalFMap;
		Ng_OCC_GetFMap(occ_geom, occ_removal_fmap);
		int numOfFacesBefore = removalFMap.Extent();
		//
		BRep_Builder builder;
		TopoDS_Shape inputShape;
		TopTools_IndexedMapOfShape inputSolids;
		if (BRepTools::Read(inputShape, argv[2], builder)) TopExp::MapShapes(inputShape, TopAbs_SOLID, inputSolids);
		std::vector<int> openedSolids(inputSolids.Extent() + 1);
		std::vector<int> removedSolids(inputSolids.Extent() + 1);
		int numOfOpenedSolids = 0;
		int numOfRemovedSolids = 0;
		//
		cout << "Ng_OCC_RemoveFaces" << endl;
		occ_geom = Ng_OCC_RemoveFaces(occ_geom, targetSolids.data(), targetFaceCounts.data(), numOfTargetGroups,
		                              faceIdList.data(), openedSolids.data(), (int)openedSolids.size(),
		                              &numOfOpenedSolids, removedSolids.data(), &numOfRemovedSolids);
		if (!occ_geom)
		{
			cerr << "The selected faces could not be deleted." << endl;
			return 1;
		}
		//
		removalFMap.Clear();
		Ng_OCC_GetFMap(occ_geom, occ_removal_fmap);
		if (removalFMap.Extent() >= numOfFacesBefore)
		{
			cerr << "No face was deleted from the geometry." << endl;
			return 1;
		}
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		// The kept solids come first in the result and one shell for every opened solid follows them
		if (!compound)
		{
			TopoDS_Shape result;
			if (!BRepTools::Read(result, argv[3], builder))
			{
				cerr << "Error reading BREP file: " << argv[3] << endl;
				return 1;
			}
			int numOfFiles = WriteBodyPieces(result, (int)SplitIntoPieces(inputShape).size(), argv[3], 1, true);
			if (numOfFiles < 1)
			{
				cerr << "Error writing BREP file: " << argv[3] << endl;
				return 1;
			}
			ofstream piecesFile(string(argv[3]) + ".pieces");
			piecesFile << numOfFiles - 1 << endl;
			piecesFile.close();
		}
		else
		{
			TopoDS_Shape result;
			if (!BRepTools::Read(result, argv[3], builder))
			{
				cerr << "Error reading BREP file: " << argv[3] << endl;
				return 1;
			}
			int numOfKeptSolids = 0;
			for (TopExp_Explorer exp0(result, TopAbs_SOLID); exp0.More(); exp0.Next()) numOfKeptSolids++;
			//
			TopoDS_Compound keptSolids;
			builder.MakeCompound(keptSolids);
			ofstream openedFile(string(argv[3]) + ".opened");
			int child = 0;
			int fileNumber = 1;
			for (TopoDS_Iterator it(result); it.More(); it.Next(), child++)
			{
				if (child < numOfKeptSolids) builder.Add(keptSolids, it.Value());
				else if (child < numOfKeptSolids + numOfOpenedSolids)
				{
					int opened = child - numOfKeptSolids;
					int solidNumber = openedSolids[opened];
					int numOfPiecesBefore = solidNumber <= inputSolids.Extent() ?
					                        (int)SplitIntoPieces(inputSolids(solidNumber)).size() : 1;
					int numOfFiles = WriteBodyPieces(it.Value(), numOfPiecesBefore, argv[3], fileNumber, false);
					if (numOfFiles < 1)
					{
						cerr << "Error writing the opened solid " << solidNumber << "." << endl;
						return 1;
					}
					openedFile << solidNumber << " " << numOfFiles << endl;
					fileNumber += numOfFiles;
				}
			}
			openedFile.close();
			ofstream removedFile(string(argv[3]) + ".removed");
			for (int i = 0; i < numOfRemovedSolids; i++) removedFile << removedSolids[i] << endl;
			removedFile.close();
			if (child != numOfKeptSolids + numOfOpenedSolids)
			{
				cerr << "The compound holds more than its solids." << endl;
				return 1;
			}
			if (!BRepTools::Write(keptSolids, argv[3]))
			{
				cerr << "Error writing BREP file: " << argv[3] << endl;
				return 1;
			}
		}
		//
		cout << "Remove faces finished successfully: " << numOfFacesBefore - removalFMap.Extent()
		     << " faces were removed." << endl;
		return 0;
	}
	catch (const std::exception& e)
	{
		cerr << "Error: " << e.what() << endl;
		return 1;
	}
}
// The face ids are grouped as BREP_REMOVE_FACES takes them: the ids of a group are numbered inside that solid,
// or in the face map of the whole shape when the solid is 0
bool FuseFaces(int argc, char* argv[])
{
	try
	{
		if (argc < 7)
		{
			cerr << "BREP_FUSE_FACES takes an input file, an output file and the number of face groups, each"
			     << " written as a solid number, a face count and that many face ids." << endl;
			return 1;
		}
		std::string::size_type sz;
		int numOfTargetGroups = std::stoi(argv[4], &sz);
		if (numOfTargetGroups < 1)
		{
			cerr << "BREP_FUSE_FACES takes at least one face group." << endl;
			return 1;
		}
		//
		std::vector<int> targetSolids;
		std::vector<int> targetFaceCounts;
		std::vector<int> faceIdList;
		int argument = 5;
		for (int group = 0; group < numOfTargetGroups; group++)
		{
			if (argument + 1 >= argc)
			{
				cerr << "BREP_FUSE_FACES was given fewer face groups than it was told to expect." << endl;
				return 1;
			}
			targetSolids.push_back(std::stoi(argv[argument++], &sz));
			targetFaceCounts.push_back(std::stoi(argv[argument++], &sz));
			for (int i = 0; i < targetFaceCounts[group]; i++)
			{
				if (argument >= argc)
				{
					cerr << "BREP_FUSE_FACES was given fewer face ids than it was told to expect." << endl;
					return 1;
				}
				faceIdList.push_back(std::stoi(argv[argument++], &sz));
			}
		}
		if (faceIdList.size() < 2)
		{
			cerr << "At least two face ids must be given." << endl;
			return 1;
		}
		//
		Ng_Init();
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cerr << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Ng_OCC_FuseFaces" << endl;
		occ_geom = Ng_OCC_FuseFaces(occ_geom, targetSolids.data(), targetFaceCounts.data(), numOfTargetGroups,
		                            faceIdList.data());
		if (!occ_geom)
		{
			cerr << "The selected faces could not be fused." << endl;
			return 1;
		}
		cout << "Ng_OCC_Save_BREP" << endl;
		if (Ng_OCC_Save_BREP(occ_geom, argv[3]) != NG_OK)
		{
			cerr << "Error writing BREP file: " << argv[3] << endl;
			return 1;
		}
	}
	catch (const std::exception& e)
	{
		cerr << "Error: " << e.what() << endl;
		return 1;
	}
	return 0;
}
static vector<Bnd_Box> GetEdgeBoxes(const TopTools_IndexedMapOfShape & edges, double tolerance)
{
	vector<Bnd_Box> boxes(edges.Extent());
	for (int i = 1; i <= edges.Extent(); i++)
	{
		BRepBndLib::Add(edges(i), boxes[i - 1]);
		boxes[i - 1].Enlarge(tolerance + BRep_Tool::Tolerance(TopoDS::Edge(edges(i))));
	}
	return boxes;
}
// An edge is free when one face holds it and it is not the seam of that face
static TopTools_IndexedMapOfShape GetFreeEdges(const TopoDS_Shape & shape)
{
	TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
	TopExp::MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
	TopTools_IndexedMapOfShape freeEdges;
	for (int i = 1; i <= edgeFaces.Extent(); i++)
	{
		TopTools_IndexedMapOfShape faces;
		for (TopTools_ListOfShape::Iterator it(edgeFaces(i)); it.More(); it.Next()) faces.Add(it.Value());
		const TopoDS_Edge & edge = TopoDS::Edge(edgeFaces.FindKey(i));
		if (faces.Extent() == 1 && !BRep_Tool::Degenerated(edge) &&
		    !BRep_Tool::IsClosed(edge, TopoDS::Face(faces(1)))) freeEdges.Add(edge);
	}
	return freeEdges;
}
// What a repair takes away from the shape, so that the caller can show where it changes the shape without
// taking the result in. Only the tolerances of the shape before the repair are allowed for: a repair grows the
// tolerances of what it merges to cover it, so those of the result would hide the small edges it removed. Every edge is written as a polyline of points on it and every vertex as a point. An
// edge is taken away when a point sampled inside it lies on no edge of the result, which holds for the edge
// between two fused faces, for a small edge and for the edges of a small face; an edge only joined with its
// neighbour lies on the joined edge and is left out, while the vertex they shared is written, since no vertex
// of the result is at its place. A free edge sewing closed lies on an edge of the result that is no longer free,
// and is written as well.
static bool WriteRepairPreview(const TopoDS_Shape & before, const TopoDS_Shape & after, const char * fileName)
{
	Bnd_Box shapeBox;
	BRepBndLib::Add(before, shapeBox);
	if (shapeBox.IsVoid()) return false;
	double diagonal = sqrt(shapeBox.SquareExtent());
	double tolerance = 1e-7 * diagonal;
	//
	TopTools_IndexedMapOfShape edgesBefore;
	TopTools_IndexedMapOfShape edgesAfter;
	TopExp::MapShapes(before, TopAbs_EDGE, edgesBefore);
	TopExp::MapShapes(after, TopAbs_EDGE, edgesAfter);
	vector<Bnd_Box> edgeBoxesAfter = GetEdgeBoxes(edgesAfter, tolerance);
	TopTools_IndexedMapOfShape freeEdgesBefore = GetFreeEdges(before);
	TopTools_IndexedMapOfShape freeEdgesAfter = GetFreeEdges(after);
	vector<Bnd_Box> freeEdgeBoxesAfter = GetEdgeBoxes(freeEdgesAfter, tolerance);
	//
	ofstream file(fileName);
	if (!file) return false;
	file.precision(15);
	file << "Repair preview format: 1" << endl;
	//
	int numOfRemovedEdges = 0;
	int numOfSewnEdges = 0;
	for (int i = 1; i <= edgesBefore.Extent(); i++)
	{
		const TopoDS_Edge & edge = TopoDS::Edge(edgesBefore(i));
		if (BRep_Tool::Degenerated(edge)) continue;
		//
		bool removed = !EdgeLiesOnEdges(edge, edgesAfter, edgeBoxesAfter, tolerance, false);
		bool sewn = !removed && freeEdgesBefore.Contains(edge) &&
		            !EdgeLiesOnEdges(edge, freeEdgesAfter, freeEdgeBoxesAfter, tolerance, false);
		if (!removed && !sewn) continue;
		//
		BRepAdaptor_Curve curve(edge);
		GCPnts_TangentialDeflection points(curve, 0.1, 1e-3 * diagonal);
		if (points.NbPoints() < 2) continue;
		//
		file << "Edge: " << points.NbPoints() << endl;
		for (int j = 1; j <= points.NbPoints(); j++)
		{
			gp_Pnt point = points.Value(j);
			file << point.X() << " " << point.Y() << " " << point.Z() << endl;
		}
		if (removed) numOfRemovedEdges++;
		else numOfSewnEdges++;
	}
	//
	TopTools_IndexedMapOfShape verticesBefore;
	TopTools_IndexedMapOfShape verticesAfter;
	TopExp::MapShapes(before, TopAbs_VERTEX, verticesBefore);
	TopExp::MapShapes(after, TopAbs_VERTEX, verticesAfter);
	int numOfRemovedVertices = 0;
	for (int i = 1; i <= verticesBefore.Extent(); i++)
	{
		const TopoDS_Vertex & vertex = TopoDS::Vertex(verticesBefore(i));
		gp_Pnt point = BRep_Tool::Pnt(vertex);
		bool kept = false;
		for (int j = 1; j <= verticesAfter.Extent() && !kept; j++)
		{
			const TopoDS_Vertex & vertexAfter = TopoDS::Vertex(verticesAfter(j));
			kept = point.Distance(BRep_Tool::Pnt(vertexAfter)) <= tolerance + BRep_Tool::Tolerance(vertex);
		}
		if (kept) continue;
		//
		file << "Point: " << point.X() << " " << point.Y() << " " << point.Z() << endl;
		numOfRemovedVertices++;
	}
	file.close();
	//
	cout << "Repair preview finished successfully: " << numOfRemovedEdges << " edges and " << numOfRemovedVertices
	     << " vertices would be removed and " << numOfSewnEdges << " free edges would be sewn." << endl;
	return true;
}
// A preview writes what the repair would take away to <out> in place of the result
bool RepairBrep(int argc, char* argv[], bool preview)
{
	try
	{
		if (argc < 6)
		{
			cerr << "BREP_REPAIR takes an input file, an output file, the sum of the repair options and a"
			     << " tolerance." << endl;
			return 1;
		}
		std::string::size_type sz;
		int options = std::stoi(argv[4], &sz);
		double tolerance = std::stod(argv[5], &sz);
		if (options <= 0)
		{
			cerr << "BREP_REPAIR was given no repair to make." << endl;
			return 1;
		}
		//
		Ng_Init();
		cout << "Ng_OCC_Load_BREP" << endl;
		Ng_OCC_Geometry * occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cerr << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Ng_OCC_RepairShape" << endl;
		occ_geom = Ng_OCC_RepairShape(occ_geom, options, tolerance);
		if (!occ_geom)
		{
			cerr << "The geometry could not be repaired." << endl;
			return 1;
		}
		string resultFileName = preview ? string(argv[3]) + ".brep" : string(argv[3]);
		// The caller divides every closed face of a repaired shape, so a preview divides them as well; a fused
		// face that closes on itself is divided again, and its seams are not taken away
		int numOfSplitFaces = preview && argc > 6 ? std::stoi(argv[6], &sz) : 1;
		cout << "Ng_OCC_Save_BREP" << endl;
		if ((numOfSplitFaces > 1 ? Ng_OCC_SaveBrepWithSplitClosedFaces(occ_geom, resultFileName.c_str(), numOfSplitFaces) :
		                           Ng_OCC_Save_BREP(occ_geom, resultFileName.c_str())) != NG_OK)
		{
			cerr << "Error writing BREP file: " << resultFileName << endl;
			return 1;
		}
		if (preview)
		{
			BRep_Builder builder;
			TopoDS_Shape before;
			TopoDS_Shape after;
			bool read = BRepTools::Read(before, argv[2], builder) && BRepTools::Read(after, resultFileName.c_str(),
			                                                                        builder);
			remove(resultFileName.c_str());
			if (!read || !WriteRepairPreview(before, after, argv[3]))
			{
				cerr << "Error writing the repair preview: " << argv[3] << endl;
				return 1;
			}
		}
	}
	catch (const std::exception& e)
	{
		cerr << "Error: " << e.what() << endl;
		return 1;
	}
	return 0;
}
bool ConvertToSolid(int argc, char* argv[])
{
	try
	{
		//Define pointer to OCC Geometry
		Ng_OCC_Geometry* occ_geom;
		// Result of Netgen Operations
		Ng_Result ng_res;
		int np, ne;
		// Initialise the Netgen Core library
		Ng_Init();
		// Read in the OCC File
		cout << "Ng_OCC_Load_BREP" << endl;
		occ_geom = Ng_OCC_Load_BREP(argv[2]);
		if (!occ_geom)
		{
			cout << "Error reading in BREP File: " << argv[2] << endl;
			return 1;
		}
		cout << "Successfully loaded BREP File: " << argv[2] << endl;
		//
		cout << "Ng_OCC_ConvertToSolid" << endl;
		occ_geom = Ng_OCC_ConvertToSolid(occ_geom);
		// Save
		cout << "Ng_OCC_Save_BREP" << endl;
		Ng_OCC_Save_BREP(occ_geom, argv[3]);
		//
		cout << "Convert ot solid finished successfully." << endl;
		//
		return 0;
	}
	catch (exception ex)
	{
		return 1;
	}
}
// Stl Mesh
bool StlMesh(int argc, char* argv[])
{
	// Define pointer to a new Netgen Mesh
	Ng_Mesh *mesh;

	// Define pointer to STL Geometry
	Ng_STL_Geometry *stl_geom;

	// Result of Netgen Operations
	Ng_Result ng_res;

	// Initialise the Netgen Core library
	Ng_Init();

	// Actually create the mesh structure
	mesh = Ng_NewMesh();

	int np, ne;

	// Read in the STL File
	stl_geom = Ng_STL_LoadGeometry(argv[2]);
	if (!stl_geom)
	{
		cout << "Error reading in STL File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded STL File: " << argv[2] << endl;

	// Set the Meshing Parameters to be used
	double deflection = 0;
	Ng_Meshing_Parameters mp;

	mp = ReadParameters(argv[4], deflection);
	mp.meshsize_filename = argc >= 6 ? argv[5] : NULL;

	// Add user edges if any
	if (argc >= 7)
	{
		int numOfNodes;
		double **nodes;
		ReadEdgeNodes(argv[6], numOfNodes, nodes);

		if (numOfNodes > 0)
		{
			cout << "Adding user edges...." << endl;
			for (int i = 0; i < numOfNodes / 2; i++)
			{
				Ng_STL_AddEdge(stl_geom, nodes[2 * i], nodes[2 * i + 1]);
			}

			for (int i = 0; i < numOfNodes; i++)
				delete[] nodes[i];
			delete[] nodes;
		}
	}

	cout << "Initialise the STL Geometry structure...." << endl;
	ng_res = Ng_STL_InitSTLGeometry(stl_geom);
	if (ng_res != NG_OK)
	{
		cout << "Error Initialising the STL Geometry....Aborting!!" << endl;
		return 1;
	}

	cout << "Start Edge Meshing...." << endl;
	ng_res = Ng_STL_MakeEdges(stl_geom, mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Edge Meshing....Aborting!!" << endl;
		return 1;
	}

	cout << "Start Surface Meshing...." << endl;
	ng_res = Ng_STL_GenerateSurfaceMesh(stl_geom, mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Surface Meshing....Aborting!!" << endl;
		return 1;
	}

	cout << "Start Volume Meshing...." << endl;
	ng_res = Ng_GenerateVolumeMesh(mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Volume Meshing....Aborting!!" << endl;
		return 1;
	}

	if (mp.second_order > 0)
	{
		cout << endl << "Converting mesh to second order elements...." << endl << endl;
		Ng_STL_Generate_SecondOrder(stl_geom, mesh);
	}

	cout << "Meshing successfully completed....!!" << endl << endl;

	// volume mesh output
	np = Ng_GetNP(mesh);
	cout << "Points: " << np << endl;

	ne = Ng_GetNE(mesh);
	cout << "Elements: " << ne << endl;

	// refinement without geomety adaption:
	//Ng_Uniform_Refinement(mesh);

	// refinement with geomety adaption:   
	//Ng_STL_Uniform_Refinement(stl_geom, mesh);

	//cout << "elements after refinement: " << Ng_GetNE(mesh) << endl;
	//cout << "points   after refinement: " << Ng_GetNP(mesh) << endl;

	//cout << "Saving Mesh in VOL Format...." << endl;
	Ng_SaveMesh(mesh, argv[3]);

	Ng_Exit();

	//string mystr;
	//cout << "Press enter to continue...";
	//getline(cin, mystr);

	return 0;
}
bool StlSurfaceMesh(int argc, char* argv[])
{
	// Define pointer to a new Netgen Mesh
	Ng_Mesh *mesh;

	// Define pointer to STL Geometry
	Ng_STL_Geometry *stl_geom;

	// Result of Netgen Operations
	Ng_Result ng_res;

	// Initialise the Netgen Core library
	Ng_Init();

	// Actually create the mesh structure
	mesh = Ng_NewMesh();

	int np, ne;

	// Read in the STL File
	stl_geom = Ng_STL_LoadGeometry(argv[2]);
	if (!stl_geom)
	{
		cout << "Error reading in STL File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded STL File: " << argv[2] << endl;

	// Set the Meshing Parameters to be used
	double deflection = 0;
	Ng_Meshing_Parameters mp;

	mp = ReadParameters(argv[4], deflection);
	mp.meshsize_filename = argc >= 6 ? argv[5] : NULL;

	// Add user edges if any
	if (argc >= 7)
	{
		int numOfNodes;
		double **nodes;
		ReadEdgeNodes(argv[6], numOfNodes, nodes);

		if (numOfNodes > 0)
		{
			cout << "Adding user edges...." << endl;
			for (int i = 0; i < numOfNodes / 2; i++)
			{
				Ng_STL_AddEdge(stl_geom, nodes[2 * i], nodes[2 * i + 1]);
			}

			for (int i = 0; i < numOfNodes; i++)
				delete[] nodes[i];
			delete[] nodes;
		}
	}

	cout << "Initialise the STL Geometry structure...." << endl;
	ng_res = Ng_STL_InitSTLGeometryEx(stl_geom, 1);
	if (ng_res != NG_OK)
	{
		cout << "Error Initialising the STL Geometry....Aborting!!" << endl;
		return 1;
	}

	cout << "Start Edge Meshing...." << endl;
	ng_res = Ng_STL_MakeEdges(stl_geom, mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Edge Meshing....Aborting!!" << endl;
		return 1;
	}

	cout << "Start Surface Meshing...." << endl;
	ng_res = Ng_STL_GenerateSurfaceMesh(stl_geom, mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Surface Meshing....Aborting!!" << endl;
		return 1;
	}

	cout << "Surface Mesh successfully created....." << endl;
	cout << "Number of points = " << Ng_GetNP(mesh) << endl;
	cout << "Number of edges = " << Ng_GetNSeg_2D(mesh) << endl;

	Ng_SaveMesh(mesh, argv[3]);

	Ng_Exit();

	return 0;
}
bool StlEdgeMesh(int argc, char* argv[])
{
	// Define pointer to a new Netgen Mesh
	Ng_Mesh *mesh;

	// Define pointer to STL Geometry
	Ng_STL_Geometry *stl_geom;

	// Result of Netgen Operations
	Ng_Result ng_res;

	// Initialise the Netgen Core library
	Ng_Init();

	// Actually create the mesh structure
	mesh = Ng_NewMesh();

	int np, ne;

	// Read in the STL File
	stl_geom = Ng_STL_LoadGeometry(argv[2]);
	if (!stl_geom)
	{
		cout << "Error reading in STL File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded STL File: " << argv[2] << endl;

	// Set the Meshing Parameters to be used
	double deflection = 0;
	Ng_Meshing_Parameters mp;

	mp = ReadParameters(argv[4], deflection);
	mp.meshsize_filename = argc >= 6 ? argv[5] : NULL;

	// Add user edges if any
	if (argc >= 7)
	{
		int numOfNodes;
		double **nodes;
		ReadEdgeNodes(argv[6], numOfNodes, nodes);

		if (numOfNodes > 0)
		{
			cout << "Adding user edges...." << endl;
			for (int i = 0; i < numOfNodes / 2; i++)
			{
				Ng_STL_AddEdge(stl_geom, nodes[2 * i], nodes[2 * i + 1]);
			}

			for (int i = 0; i < numOfNodes; i++)
				delete[] nodes[i];
			delete[] nodes;
		}
	}

	cout << "Initialise the STL Geometry structure...." << endl;
	ng_res = Ng_STL_InitSTLGeometryEx(stl_geom, 1);
	if (ng_res != NG_OK)
	{
		cout << "Error Initialising the STL Geometry....Aborting!!" << endl;
		return 1;
	}

	cout << "Start Edge Meshing...." << endl;
	ng_res = Ng_STL_MakeEdges(stl_geom, mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Edge Meshing....Aborting!!" << endl;
		return 1;
	}
	cout << "Number of edges = " << Ng_GetNSeg_2D(mesh) << endl;


	ng_res = Ng_STL_GenerateEdgeMesh(stl_geom, mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Edge Meshing....Aborting!!" << endl;
		return 1;
	}

	cout << "Edge Mesh successfully created....." << endl;
	cout << "Number of points = " << Ng_GetNP(mesh) << endl;
	cout << "Number of edges = " << Ng_GetNSeg_2D(mesh) << endl;


	Ng_SaveMesh(mesh, argv[3]);

	Ng_Exit();

	return 0;
}
void ReadEdgeNodes(const char *fileName, int &numOfNodes, double** &nodes)
{
	Ng_Meshing_Parameters mp;

	ifstream File(fileName);
	string line;

	if (File)
	{
		int numOfEdges = -1;
		numOfNodes = -1;
		// check_overlapping_boundary
		getline(File, line);
		getline(File, line);
		numOfEdges = std::stoi(line);

		if (numOfEdges > 0)
		{
			numOfNodes = 2 * numOfEdges;
			nodes = new double*[numOfNodes];
			for (int i = 0; i < numOfNodes; ++i)
				nodes[i] = new double[3];

			for (int i = 0; i < numOfNodes; ++i)
			{
				getline(File, line);
				istringstream sin(line);

				sin >> nodes[i][0];
				sin >> nodes[i][1];
				sin >> nodes[i][2];
			}
		}

		File.close();
	}
}
// Occ Mesh
bool OccMesh(int argc, char* argv[])
{
	////Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;

	Ng_Mesh *occ_mesh;

	TopTools_IndexedMapOfShape FMap;

	Ng_OCC_TopTools_IndexedMapOfShape *occ_fmap = (Ng_OCC_TopTools_IndexedMapOfShape*)&FMap;

	//// Result of Netgen Operations
	Ng_Result ng_res;

	int np, ne;

	//// Initialise the Netgen Core library
	Ng_Init();

	//// Read in the OCC File
	occ_geom = Ng_OCC_Load_BREP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in BREP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded BREP File: " << argv[2] << endl;

	occ_mesh = Ng_NewMesh();

	ng_res = Ng_OCC_GetFMap(occ_geom, occ_fmap);

	cout << "ng_res = " << ng_res << endl;

	if (!FMap.Extent())
	{
		cout << "Error retrieving Face map...." << endl;
		return 1;
	}

	cout << "Successfully extracted the Face Map....:" << FMap.Extent() << endl;
	/*
	for (int i = 1; i <= FMap.Extent(); i++)
	{
	TopoDS_Face OCCface;
	OCCface = TopoDS::Face(FMap.FindKey(i));

	GProp_GProps faceProps;
	BRepGProp::SurfaceProperties(OCCface, faceProps);
	cout << "Index: " << i
	<< " :: Area: " << faceProps.Mass()
	<< " :: Hash: " << OCCface.HashCode(1e+6)
	<< endl;
	}*/


	// Set the Meshing Parameters to be used
	double deflection = 0;
	Ng_Meshing_Parameters mp;

	mp = ReadParameters(argv[4], deflection);
	mp.meshsize_filename = argv[5];

	/*mp.uselocalh = 1;
	mp.elementsperedge = 2.0;
	mp.elementspercurve = 2.0;
	mp.maxh = 10.0;
	mp.grading = 0.2;
	mp.closeedgeenable = 0;
	mp.closeedgefact = 1.0;
	mp.optsurfmeshenable = 1;*/


	// Wall-clock time of the meshing phases, reported at the end
	typedef std::chrono::steady_clock PhaseClock;
	PhaseClock::time_point phaseStart = PhaseClock::now();
	double timeLocalSize = 0, timeEdges = 0, timeSurface = 0, timeVolume = 0;
	auto phaseSeconds = [&phaseStart]() {
		PhaseClock::time_point now = PhaseClock::now();
		double seconds = std::chrono::duration<double>(now - phaseStart).count();
		phaseStart = now;
		return seconds;
	};

	cout << "Setting Local Mesh size....." << endl;
	cout << "OCC Mesh Pointer before call = " << occ_mesh << endl;
	Ng_OCC_SetLocalMeshSize(occ_geom, deflection, occ_mesh, &mp);
	cout << "Local Mesh size successfully set....." << endl;
	cout << "OCC Mesh Pointer after call = " << occ_mesh << endl;
	timeLocalSize = phaseSeconds();

	cout << "Creating Edge Mesh....." << endl;
	ng_res = Ng_OCC_GenerateEdgeMesh(occ_geom, occ_mesh, &mp);
	if (ng_res != NG_OK)
	{
		Ng_DeleteMesh(occ_mesh);
		cout << "Error creating Edge Mesh.... Aborting!!" << endl;
		return 1;
	}
	else
	{
		cout << "Edge Mesh successfully created....." << endl;
		cout << "Number of points = " << Ng_GetNP(occ_mesh) << endl;
	}
	timeEdges = phaseSeconds();

	cout << "Creating Surface Mesh....." << endl;

	ng_res = Ng_OCC_GenerateSurfaceMesh(occ_geom, occ_mesh, &mp);
	if (ng_res != NG_OK)
	{
		char fileNameWithPath[_MAX_FNAME];
		char full_path[_MAX_PATH];
		char drive[_MAX_DRIVE];
		char dir[_MAX_DIR];
		char fname[_MAX_FNAME];
		char ext[_MAX_EXT];
		_splitpath_s(argv[3], drive, dir, fname, ext);
		stringstream ss;
		ss << fname << "_error";
		_makepath_s(fileNameWithPath, drive, dir, ss.str().c_str(), ext);
		Ng_SaveMesh(occ_mesh, fileNameWithPath);
		//
		//Ng_DeleteMesh(occ_mesh);
		cout << "Error creating Surface Mesh..... Aborting!!" << endl;
		return 1;
	}
	else
	{
		cout << "Surface Mesh successfully created....." << endl;
		cout << "Number of points = " << Ng_GetNP(occ_mesh) << endl;
		cout << "Number of surface elements = " << Ng_GetNSE(occ_mesh) << endl;
	}
	timeSurface = phaseSeconds();

	cout << "Start Volume Meshing...." << endl;
	ng_res = Ng_GenerateVolumeMesh(occ_mesh, &mp);
	if (ng_res != NG_OK)
	{
		cout << "Error in Volume Meshing....Aborting!!" << endl;
		return 1;
	}
	timeVolume = phaseSeconds();

	if (mp.second_order > 0)
	{
		cout << endl << "Converting mesh to second order elements...." << endl << endl;
		Ng_OCC_Generate_SecondOrder(occ_geom, occ_mesh);
	}

	cout << "Meshing successfully completed....!!" << endl << endl;

	// volume mesh output
	np = Ng_GetNP(occ_mesh);
	cout << "Points: " << np << endl;

	ne = Ng_GetNE(occ_mesh);
	cout << "Elements: " << ne << endl;

	cout << "Phase times [s]: local size " << timeLocalSize
		<< ", edges " << timeEdges
		<< ", surface " << timeSurface
		<< ", volume " << timeVolume
		<< " (" << mp.parallel_meshing_threads << " thread(s) requested)" << endl;

	cout << "Saving Mesh as VOL file....." << endl;
	Ng_SaveMesh(occ_mesh, argv[3]);

	//nglib::Ng_Exit();

	return 0;
}
bool OccEdgeMesh(int argc, char* argv[])
{
	////Define pointer to OCC Geometry
	Ng_OCC_Geometry *occ_geom;

	Ng_Mesh *occ_mesh;

	TopTools_IndexedMapOfShape FMap;

	Ng_OCC_TopTools_IndexedMapOfShape *occ_fmap = (Ng_OCC_TopTools_IndexedMapOfShape*)&FMap;

	//// Result of Netgen Operations
	Ng_Result ng_res;

	int np, ne;

	//// Initialise the Netgen Core library
	Ng_Init();

	//// Read in the OCC File
	occ_geom = Ng_OCC_Load_BREP(argv[2]);
	if (!occ_geom)
	{
		cout << "Error reading in BREP File: " << argv[2] << endl;
		return 1;
	}
	cout << "Successfully loaded BREP File: " << argv[2] << endl;

	occ_mesh = Ng_NewMesh();

	ng_res = Ng_OCC_GetFMap(occ_geom, occ_fmap);

	cout << "ng_res = " << ng_res << endl;

	if (!FMap.Extent())
	{
		cout << "Error retrieving Face map...." << endl;
		return 1;
	}

	cout << "Successfully extracted the Face Map....:" << FMap.Extent() << endl;

	// Set the Meshing Parameters to be used
	double deflection = 0;
	Ng_Meshing_Parameters mp;

	mp = ReadParameters(argv[4], deflection);
	mp.meshsize_filename = argv[5];

	cout << "Setting Local Mesh size....." << endl;
	cout << "OCC Mesh Pointer before call = " << occ_mesh << endl;
	Ng_OCC_SetLocalMeshSize(occ_geom, deflection, occ_mesh, &mp);
	cout << "Local Mesh size successfully set....." << endl;
	cout << "OCC Mesh Pointer after call = " << occ_mesh << endl;

	cout << "Creating Edge Mesh....." << endl;
	ng_res = Ng_OCC_GenerateEdgeMesh(occ_geom, occ_mesh, &mp);
	if (ng_res != NG_OK)
	{
		Ng_DeleteMesh(occ_mesh);
		cout << "Error creating Edge Mesh..... Aborting!!" << endl;
		return 1;
	}

	cout << "Edge Mesh successfully created....." << endl;
	cout << "Number of points = " << Ng_GetNP(occ_mesh) << endl;

	Ng_SaveMesh(occ_mesh, argv[3]);

	Ng_Exit();

	return 0;
}
// Vol Mesh
bool VolVolumeMesh(int argc, char* argv[])
{
	// argv[2]	...	input vol file with the points and the closed boundary of every domain
	// argv[3]	...	output vol file
	// argv[4]	...	mesh parameters
	if (argc < 5)
	{
		cerr << "VOL_VOLUME_MESH needs an input vol file, an output vol file and a mesh parameters file." << endl;
		return 1;
	}
	//
	Ng_Init();
	//
	Ng_Mesh* mesh = Ng_LoadMesh(argv[2]);
	int numOfBoundaryPoints = Ng_GetNP(mesh);
	int numOfBoundaryElements = Ng_GetNSE(mesh);
	if (numOfBoundaryPoints == 0 || numOfBoundaryElements == 0)
	{
		cerr << "The boundary mesh " << argv[2] << " holds no points or no surface elements." << endl;
		return 1;
	}
	cout << "Boundary mesh: " << numOfBoundaryPoints << " points, " << numOfBoundaryElements
		<< " surface elements." << endl;
	//
	double deflection = 0;
	Ng_Meshing_Parameters mp = ReadParameters(argv[4], deflection);
	// The boundary is given, so there is nothing to size from a file or to raise to second order here. A face
	// shared by two domains is written once for each of them, which the overlap check would report
	mp.meshsize_filename = NULL;
	mp.second_order = 0;
	mp.check_overlapping_boundary = 0;
	//
	cout << "Start Volume Meshing...." << endl;
	Ng_Result ng_res = Ng_GenerateVolumeMesh(mesh, &mp);
	if (ng_res != NG_OK)
	{
		// What was meshed before the failure is kept beside the output, to show where it stopped
		char fileNameWithPath[_MAX_PATH];
		char drive[_MAX_DRIVE];
		char dir[_MAX_DIR];
		char fname[_MAX_FNAME];
		char ext[_MAX_EXT];
		_splitpath_s(argv[3], drive, dir, fname, ext);
		stringstream ss;
		ss << fname << "_error";
		_makepath_s(fileNameWithPath, drive, dir, ss.str().c_str(), ext);
		Ng_SaveMesh(mesh, fileNameWithPath);
		//
		cerr << "The volume could not be meshed from the boundary mesh." << endl;
		return 1;
	}
	// The boundary points are the first points of the result, in their input order, so that the caller can join
	// the volume elements to the mesh the boundary came from
	if (Ng_GetNP(mesh) < numOfBoundaryPoints)
	{
		cerr << "Volume meshing removed boundary points, so the volume mesh cannot be joined to its boundary." << endl;
		return 1;
	}
	cout << "Points: " << Ng_GetNP(mesh) << endl;
	cout << "Elements: " << Ng_GetNE(mesh) << endl;
	//
	Ng_SaveMesh(mesh, argv[3]);
	//
	return 0;
}
Ng_Meshing_Parameters ReadParameters(const char *fileName, double &deflection)
{
	//
	#pragma warning(disable:4996) // this prevents the warning for the copy string comman
	//
	Ng_Meshing_Parameters mp;
	//
	ifstream File(fileName);
	string line;
	//
	if (File)
	{
		// uselocalh
		getline(File, line);
		getline(File, line);
		mp.uselocalh = std::stoi(line);
		// maxh
		getline(File, line);
		getline(File, line);
		mp.maxh = std::stod(line);
		// minh
		getline(File, line);
		getline(File, line);
		mp.minh = std::stod(line);
		// fineness
		getline(File, line);
		getline(File, line);
		mp.fineness = std::stod(line);
		// grading
		getline(File, line);
		getline(File, line);
		mp.grading = std::stod(line);
		// elementsperedge
		getline(File, line);
		getline(File, line);
		mp.elementsperedge = std::stod(line);
		// elementspercurve
		getline(File, line);
		getline(File, line);
		mp.elementspercurve = std::stod(line);
		// closeedgeenable
		getline(File, line);
		getline(File, line);
		mp.closeedgeenable = std::stoi(line);
		// closeedgefact
		getline(File, line);
		getline(File, line);
		mp.closeedgefact = std::stod(line);
		// minedgelenenable
		getline(File, line);
		getline(File, line);
		mp.minedgelenenable = std::stoi(line);
		// minedgelen
		getline(File, line);
		getline(File, line);
		mp.minedgelen = std::stoi(line);
		// second_order
		getline(File, line);
		getline(File, line);
		mp.second_order = std::stoi(line);
		// quad_dominated
		getline(File, line);
		getline(File, line);
		mp.quad_dominated = std::stoi(line);
		// meshsize_filename
		getline(File, line);
		getline(File, line);
		int n = line.length();
		// declaring character array 
		mp.meshsize_filename = new char[n + 1];
		// copying the contents of the 
		// string to char array 
		strcpy(mp.meshsize_filename, line.c_str());
		// optsurfmeshenable
		getline(File, line);
		getline(File, line);
		mp.optsurfmeshenable = std::stoi(line);
		// optvolmeshenable
		getline(File, line);
		getline(File, line);
		mp.optvolmeshenable = std::stoi(line);
		// optsteps_3d
		getline(File, line);
		getline(File, line);
		mp.optsteps_3d = std::stoi(line);
		// optsteps_2d
		getline(File, line);
		getline(File, line);
		mp.optsteps_2d = std::stoi(line);
		// invert_tets
		getline(File, line);
		getline(File, line);
		mp.invert_tets = std::stoi(line);
		// invert_trigs
		getline(File, line);
		getline(File, line);
		mp.invert_trigs = std::stoi(line);
		// check_overlap
		getline(File, line);
		getline(File, line);
		mp.check_overlap = std::stoi(line);
		// check_overlapping_boundary
		getline(File, line);
		getline(File, line);
		mp.check_overlapping_boundary = std::stoi(line);
		// Optional OCC visualization deflection used by BREP meshing.
		if (getline(File, line) && getline(File, line) && !line.empty())
			deflection = std::stod(line);
		// Optional positive parallel meshing worker count: 1 = serial.
		if (getline(File, line) && getline(File, line) && !line.empty())
		{
			int threadCount = std::stoi(line);
			if (threadCount < 1)
				throw std::invalid_argument("parallel_meshing_threads must be larger than 0.");
			mp.parallel_meshing_threads = threadCount;
		}
		// Optional four sided faces meshed as structured triangle grids: 0 = none,
		// 1 = those whose grid is not much finer than the mesh size, 2 = all.
		if (getline(File, line) && getline(File, line) && !line.empty())
		{
			int transfiniteFaces = std::stoi(line);
			if (transfiniteFaces < 0 || transfiniteFaces > 2)
				throw std::invalid_argument("transfinite_faces must be 0, 1 or 2.");
			mp.transfinite_faces = transfiniteFaces;
		}
		// Optional corner threshold of transfinite faces in degrees: a vertex is a
		// corner where its edges meet at less than this angle.
		if (getline(File, line) && getline(File, line) && !line.empty())
			mp.transfinite_angle = std::stod(line);
		// Optional file of the structured faces PrePoMax gives, which replace those Netgen finds
		if (getline(File, line) && getline(File, line) && !line.empty())
		{
			mp.transfinite_filename = new char[line.length() + 1];
			strcpy(mp.transfinite_filename, line.c_str());
		}
		//
		File.close();
	}
	//
	return mp;
}
// The rest
bool Test(int argc, char* argv[])
{
	return 0;
}
char** ReadDataFile(int &argc, char* argv[])
{
	//
	#pragma warning(disable:4996) // this prevents the warning for the copy string comman
	//
	char* fileName = argv[1];
	ifstream File(fileName);
	string line;
	int lineLen;
	char** parameters = new char*[0];
	//
	char* command;
	//
	if (File)
	{
		// Read command
		getline(File, line);
		getline(File, line);
		lineLen = line.length();
		command = new char[lineLen + 1];
		strcpy(command, line.c_str());

		if (strcmp(command, "STL_MESH") == 0) argc = 6;
		else if (strcmp(command, "STL_SURFACE_MESH") == 0) argc = 6;
		else if (strcmp(command, "STL_EDGE_MESH") == 0) argc = 6;
		else if (strcmp(command, "STEP_ASSEMBLY_SPLIT") == 0) argc = 4;
		else if (strcmp(command, "IGES_ASSEMBLY_SPLIT") == 0) argc = 4;
		else if (strcmp(command, "BREP_ASSEMBLY_SPLIT") == 0) argc = 4;
		else if (strcmp(command, "BREP_VISUALIZATION") == 0) argc = 5;
		else if (strcmp(command, "BREP_MESH") == 0) argc = 5;
		else if (strcmp(command, "BREP_NODE_MESH") == 0) argc = 5;
		//
		parameters = new char*[argc];
		parameters[0] = argv[0];
		parameters[1] = command;
		//
		for (int i = 2; i < argc; i++)
		{
			// Read data
			line = string("");
			getline(File, line);
			getline(File, line);
			lineLen = line.length();
			parameters[i] = new char[lineLen + 1];
			strcpy(parameters[i], line.c_str());
		}
		File.close();
	}
	return parameters;
}

