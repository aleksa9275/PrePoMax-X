/**************************************************************************/
/* File:   nglib.cpp                                                      */
/* Author: Joachim Schoeberl                                              */
/* Date:   7. May. 2000                                                   */
/**************************************************************************/

/*

  Interface to the netgen meshing kernel

*/
#include <mystdlib.h>
#include <TColgp_Array1OfPnt.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <myadt.hpp>

#include <linalg.hpp>
#include <csg.hpp>
#include <stlgeom.hpp>
#include <geometry2d.hpp>
#include <meshing.hpp>
#include <../visualization/soldata.hpp>

#include <stdio.h>

#include <TColStd_Array1OfInteger.hxx>
#include <Poly_PolygonOnTriangulation.hxx>
#include <Poly_Triangulation.hxx>
#include <ShapeAnalysis_ShapeContents.hxx>
#include <iostream>
#include <OSD_Protection.hxx>
#include <OSD_File.hxx>
#include <vector> 

#ifdef OCCGEOMETRY
#include <occgeom.hpp>
#endif

#include <nginterface.h>

// By Maxx
#include <list>
#include <BOPAlgo_Builder.hxx>
#include <BRep_Builder.hxx>
#include <BRepClass3d_SolidClassifier.hxx>
#include <BRepClass_FaceClassifier.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <GCPnts_AbscissaPoint.hxx>
#include <BRep_TEdge.hxx>
#include <BRepTools.hxx>
#include <TopTools_IndexedDataMapOfShapeListOfShape.hxx>
#include <ShapeUpgrade_ShapeDivideClosed.hxx>
#include <GProp.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepLib.hxx>
#include <Precision.hxx>
#include <gp_Lin.hxx>
#include <typeinfo>
#include <map>
#include <BRepBuilderAPI_Sewing.hxx>
#include <BRepBuilderAPI_Copy.hxx>
#include <BRepOffsetAPI_MakeOffsetShape.hxx>
#include <BRepOffset_MakeSimpleOffset.hxx>
#include <ShapeUpgrade_UnifySameDomain.hxx>
#include <TopTools_MapOfShape.hxx>
#include <ShapeFix_Shape.hxx>
#include <ShapeFix_Wireframe.hxx>
#include <ShapeFix_FixSmallFace.hxx>
#include <Standard_Failure.hxx>

namespace netgen {
	extern void MeshFromSpline2D(SplineGeometry2d & geometry,
		Mesh *& mesh,
		MeshingParameters & mp);
}



#ifdef PARALLEL
#include <mpi.h>

namespace netgen
{
	// int id = 0, ntasks = 1;
	MPI_Comm mesh_comm;
}
#endif


namespace netgen
{
	int id = 0, ntasks = 1;
}



/*
// should not be needed (occ currently requires it)
namespace netgen {
#include "../libsrc/visualization/vispar.hpp"
  VisualizationParameters vispar;
  VisualizationParameters :: VisualizationParameters() { ; }
}
*/


namespace nglib {
#include "nglib.h"
}

using namespace netgen;

// constants and types:

namespace nglib
{
	// initialize, deconstruct Netgen library:
	DLL_HEADER void Ng_Init()
	{
		mycout = &cout;
		myerr = &cerr;
		// testout is Netgen's debug log and stays the null stream it starts as: written to test.out in the
		// working folder, a volume mesh whose advancing front cannot close logged every rule it tried there,
		// some 7 MB a second for as long as the run lasted
	}




	// Clean-up functions before ending usage of nglib
	DLL_HEADER void Ng_Exit()
	{
		;
	}




	// Create a new netgen mesh object
	DLL_HEADER Ng_Mesh * Ng_NewMesh()
	{
		Mesh * mesh = new Mesh;
		mesh->AddFaceDescriptor(FaceDescriptor(1, 1, 0, 1));
		return (Ng_Mesh*)(void*)mesh;
	}




	// Delete an existing netgen mesh object
	DLL_HEADER void Ng_DeleteMesh(Ng_Mesh * mesh)
	{
		if (mesh != NULL)
		{
			// Delete the Mesh structures
			((Mesh*)mesh)->DeleteMesh();

			// Now delete the Mesh class itself
			delete (Mesh*)mesh;

			// Set the Ng_Mesh pointer to NULL
			mesh = NULL;
		}
	}




	// Save a netgen mesh in the native VOL format 
	DLL_HEADER void Ng_SaveMesh(Ng_Mesh * mesh, const char* filename)
	{
		((Mesh*)mesh)->Save(filename);
	}




	// Load a netgen native VOL mesh from a given file
	DLL_HEADER Ng_Mesh * Ng_LoadMesh(const char* filename)
	{
		Mesh * mesh = new Mesh;
		mesh->Load(filename);
		return ((Ng_Mesh*)mesh);
	}




	// Merge another mesh file into the currently loaded one
	DLL_HEADER Ng_Result Ng_MergeMesh(Ng_Mesh* mesh, const char* filename)
	{
		Ng_Result status = NG_OK;

		ifstream infile(filename);
		Mesh * m = (Mesh*)mesh;

		if (!infile.good())
		{
			status = NG_FILE_NOT_FOUND;
		}

		if (!m)
		{
			status = NG_ERROR;
		}

		if (status == NG_OK)
		{
			const int num_pts = m->GetNP();
			const int face_offset = m->GetNFD();

			m->Merge(infile, face_offset);

			if (m->GetNP() > num_pts)
			{
				status = NG_OK;
			}
			else
			{
				status = NG_ERROR;
			}
		}

		return status;
	}




	// Merge another mesh file into the currently loaded one
	DLL_HEADER Ng_Result Ng_MergeMesh(Ng_Mesh* mesh1, Ng_Mesh* mesh2)
	{
		return NG_ERROR;
	}




	// Manually add a point to an existing mesh object
	DLL_HEADER void Ng_AddPoint(Ng_Mesh * mesh, double * x)
	{
		Mesh * m = (Mesh*)mesh;
		m->AddPoint(Point3d(x[0], x[1], x[2]));
	}




	// Manually add a surface element of a given type to an existing mesh object
	DLL_HEADER void Ng_AddSurfaceElement(Ng_Mesh * mesh, Ng_Surface_Element_Type et,
		int * pi)
	{
		Mesh * m = (Mesh*)mesh;
		Element2d el(3);
		el.SetIndex(1);
		el.PNum(1) = pi[0];
		el.PNum(2) = pi[1];
		el.PNum(3) = pi[2];
		m->AddSurfaceElement(el);
	}




	// Manually add a volume element of a given type to an existing mesh object
	DLL_HEADER void Ng_AddVolumeElement(Ng_Mesh * mesh, Ng_Volume_Element_Type et,
		int * pi)
	{
		Mesh * m = (Mesh*)mesh;
		Element el(4);
		el.SetIndex(1);
		el.PNum(1) = pi[0];
		el.PNum(2) = pi[1];
		el.PNum(3) = pi[2];
		el.PNum(4) = pi[3];
		m->AddVolumeElement(el);
	}




	// Obtain the number of points in the mesh
	DLL_HEADER int Ng_GetNP(Ng_Mesh * mesh)
	{
		return ((Mesh*)mesh)->GetNP();
	}




	// Obtain the number of surface elements in the mesh
	DLL_HEADER int Ng_GetNSE(Ng_Mesh * mesh)
	{
		return ((Mesh*)mesh)->GetNSE();
	}




	// Obtain the number of volume elements in the mesh
	DLL_HEADER int Ng_GetNE(Ng_Mesh * mesh)
	{
		return ((Mesh*)mesh)->GetNE();
	}




	//  Return point coordinates of a given point index in the mesh
	DLL_HEADER void Ng_GetPoint(Ng_Mesh * mesh, int num, double * x)
	{
		const Point3d & p = ((Mesh*)mesh)->Point(num);
		x[0] = p.X();
		x[1] = p.Y();
		x[2] = p.Z();
	}




	// Return the surface element at a given index "pi"
	DLL_HEADER Ng_Surface_Element_Type
		Ng_GetSurfaceElement(Ng_Mesh * mesh, int num, int * pi)
	{
		const Element2d & el = ((Mesh*)mesh)->SurfaceElement(num);
		for (int i = 1; i <= el.GetNP(); i++)
			pi[i - 1] = el.PNum(i);
		Ng_Surface_Element_Type et;
		switch (el.GetNP())
		{
		case 3: et = NG_TRIG; break;
		case 4: et = NG_QUAD; break;
		case 6:
			switch (el.GetNV())
			{
			case 3: et = NG_TRIG6; break;
			case 4: et = NG_QUAD6; break;
			default:
				et = NG_TRIG6; break;
			}
			break;
		case 8: et = NG_QUAD8; break;
		default:
			et = NG_TRIG; break; // for the compiler
		}
		return et;
	}




	// Return the volume element at a given index "pi"
	DLL_HEADER Ng_Volume_Element_Type
		Ng_GetVolumeElement(Ng_Mesh * mesh, int num, int * pi)
	{
		const Element & el = ((Mesh*)mesh)->VolumeElement(num);
		for (int i = 1; i <= el.GetNP(); i++)
			pi[i - 1] = el.PNum(i);
		Ng_Volume_Element_Type et;
		switch (el.GetNP())
		{
		case 4: et = NG_TET; break;
		case 5: et = NG_PYRAMID; break;
		case 6: et = NG_PRISM; break;
		case 10: et = NG_TET10; break;
		default:
			et = NG_TET; break; // for the compiler
		}
		return et;
	}




	// Set a global limit on the maximum mesh size allowed
	DLL_HEADER void Ng_RestrictMeshSizeGlobal(Ng_Mesh * mesh, double h)
	{
		((Mesh*)mesh)->SetGlobalH(h);
	}




	// Set a local limit on the maximum mesh size allowed around the given point
	DLL_HEADER void Ng_RestrictMeshSizePoint(Ng_Mesh * mesh, double * p, double h)
	{
		((Mesh*)mesh)->RestrictLocalH(Point3d(p[0], p[1], p[2]), h);
	}




	// Set a local limit on the maximum mesh size allowed within a given box region
	DLL_HEADER void Ng_RestrictMeshSizeBox(Ng_Mesh * mesh, double * pmin, double * pmax, double h)
	{
		for (double x = pmin[0]; x < pmax[0]; x += h)
			for (double y = pmin[1]; y < pmax[1]; y += h)
				for (double z = pmin[2]; z < pmax[2]; z += h)
					((Mesh*)mesh)->RestrictLocalH(Point3d(x, y, z), h);
	}




	/*
	  Meshing routines report a failure by throwing.  An exception that leaves
	  nglib has no handler above it and terminates the process, so every entry
	  point that meshes catches it here, names the stage and returns NG_ERROR.
	  Call from inside a catch block.
	*/
	static Ng_Result ReportMeshingException(const char * stage)
	{
		try
		{
			throw;
		}
		catch (NgException & exception)
		{
			PrintError(stage, " failed: ", exception.What().c_str());
		}
		catch (std::exception & exception)
		{
			PrintError(stage, " failed: ", exception.what());
		}
		catch (...)
		{
			PrintError(stage, " failed with an unknown error");
		}
		return NG_ERROR;
	}


	// Generates volume mesh from an existing surface mesh
	DLL_HEADER Ng_Result Ng_GenerateVolumeMesh(Ng_Mesh * mesh, Ng_Meshing_Parameters * mp)
	{
	  try
	  {
		Mesh * m = (Mesh*)mesh;

		// Philippose - 30/08/2009
		// Do not locally re-define "mparam" here... "mparam" is a global 
		// object 
		//MeshingParameters mparam;
		mp->Transfer_Parameters();

		m->CalcLocalH(mparam.grading);

		// Serial: MeshVolume + RemoveIllegalElements + OptimizeVolume.
		// With mparam.parallel_meshing_threads > 1 the independent subdomains
		// are meshed and optimized in parallel and committed in domain order.
		if (MeshVolumeAndOptimize(mparam, *m) != MESHING3_OK)
			return NG_ERROR;

		//GenerateBoundaryLayer2(*m, mparam);

		return NG_OK;
	  }
	  catch (...)
	  {
		return ReportMeshingException("Volume meshing");
	  }
	}




	/* ------------------ 2D Meshing Functions ------------------------- */
	DLL_HEADER void Ng_AddPoint_2D(Ng_Mesh * mesh, double * x)
	{
		Mesh * m = (Mesh*)mesh;

		m->AddPoint(Point3d(x[0], x[1], 0));
	}




	DLL_HEADER void Ng_AddBoundarySeg_2D(Ng_Mesh * mesh, int pi1, int pi2)
	{
		Mesh * m = (Mesh*)mesh;

		Segment seg;
		seg[0] = pi1;
		seg[1] = pi2;
		m->AddSegment(seg);
	}




	DLL_HEADER int Ng_GetNP_2D(Ng_Mesh * mesh)
	{
		Mesh * m = (Mesh*)mesh;
		return m->GetNP();
	}




	DLL_HEADER int Ng_GetNE_2D(Ng_Mesh * mesh)
	{
		Mesh * m = (Mesh*)mesh;
		return m->GetNSE();
	}




	DLL_HEADER int Ng_GetNSeg_2D(Ng_Mesh * mesh)
	{
		Mesh * m = (Mesh*)mesh;
		return m->GetNSeg();
	}




	DLL_HEADER void Ng_GetPoint_2D(Ng_Mesh * mesh, int num, double * x)
	{
		Mesh * m = (Mesh*)mesh;

		Point<3> & p = m->Point(num);
		x[0] = p(0);
		x[1] = p(1);
	}




	DLL_HEADER Ng_Surface_Element_Type
		Ng_GetElement_2D(Ng_Mesh * mesh, int num, int * pi, int * matnum)
	{
		const Element2d & el = ((Mesh*)mesh)->SurfaceElement(num);
		for (int i = 1; i <= el.GetNP(); i++)
			pi[i - 1] = el.PNum(i);

		Ng_Surface_Element_Type et;
		switch (el.GetNP())
		{
		case 3: et = NG_TRIG; break;
		case 4: et = NG_QUAD; break;
		case 6:
			switch (el.GetNV())
			{
			case 3: et = NG_TRIG6; break;
			case 4: et = NG_QUAD6; break;
			default:
				et = NG_TRIG6; break;
			}
			break;
		case 8: et = NG_QUAD8; break;
		default:
			et = NG_TRIG; break; // for the compiler
		}

		if (matnum)
			*matnum = el.GetIndex();

		return et;
	}




	DLL_HEADER void Ng_GetSegment_2D(Ng_Mesh * mesh, int num, int * pi, int * matnum)
	{
		const Segment & seg = ((Mesh*)mesh)->LineSegment(num);
		pi[0] = seg[0];
		pi[1] = seg[1];

		if (matnum)
			*matnum = seg.edgenr;
	}




	DLL_HEADER Ng_Geometry_2D * Ng_LoadGeometry_2D(const char * filename)
	{
		SplineGeometry2d * geom = new SplineGeometry2d();
		geom->Load(filename);
		return (Ng_Geometry_2D *)geom;
	}




	DLL_HEADER Ng_Result Ng_GenerateMesh_2D(Ng_Geometry_2D * geom,
		Ng_Mesh ** mesh,
		Ng_Meshing_Parameters * mp)
	{
		// use global variable mparam
		//  MeshingParameters mparam;  
		mp->Transfer_Parameters();

		Mesh * m;
		MeshFromSpline2D(*(SplineGeometry2d*)geom, m, mparam);

		cout << m->GetNSE() << " elements, " << m->GetNP() << " points" << endl;

		*mesh = (Ng_Mesh*)m;
		return NG_OK;
	}




	DLL_HEADER void Ng_HP_Refinement(Ng_Geometry_2D * geom,
		Ng_Mesh * mesh,
		int levels)
	{
		Refinement2d ref(*(SplineGeometry2d*)geom);
		HPRefinement(*(Mesh*)mesh, &ref, levels);
	}




	DLL_HEADER void Ng_HP_Refinement(Ng_Geometry_2D * geom,
		Ng_Mesh * mesh,
		int levels, double parameter)
	{
		Refinement2d ref(*(SplineGeometry2d*)geom);
		HPRefinement(*(Mesh*)mesh, &ref, levels, parameter);
	}




	Array<STLReadTriangle> readtrias; //only before initstlgeometry
	Array<Point<3> > readedges; //only before init stlgeometry

	// loads geometry from STL file
	DLL_HEADER Ng_STL_Geometry * Ng_STL_LoadGeometry(const char * filename, int binary)
	{
		int i;
		STLGeometry geom;
		STLGeometry* geo;
		ifstream ist(filename);

		if (binary)
		{
			geo = geom.LoadBinary(ist);
		}
		else
		{
			geo = geom.Load(ist);
		}

		readtrias.SetSize(0);
		readedges.SetSize(0);

		Point3d p;
		Vec3d normal;
		double p1[3];
		double p2[3];
		double p3[3];
		double n[3];

		Ng_STL_Geometry * geo2 = Ng_STL_NewGeometry();

		for (i = 1; i <= geo->GetNT(); i++)
		{
			const STLTriangle& t = geo->GetTriangle(i);
			p = geo->GetPoint(t.PNum(1));
			p1[0] = p.X(); p1[1] = p.Y(); p1[2] = p.Z();
			p = geo->GetPoint(t.PNum(2));
			p2[0] = p.X(); p2[1] = p.Y(); p2[2] = p.Z();
			p = geo->GetPoint(t.PNum(3));
			p3[0] = p.X(); p3[1] = p.Y(); p3[2] = p.Z();
			normal = t.Normal();
			n[0] = normal.X(); n[1] = normal.Y(); n[2] = normal.Z();

			Ng_STL_AddTriangle(geo2, p1, p2, p3, n);
		}

		return geo2;
	}




	// generate new STL Geometry
	DLL_HEADER Ng_STL_Geometry * Ng_STL_NewGeometry()
	{
		return (Ng_STL_Geometry*)(void*)new STLGeometry;
	}




	// after adding triangles (and edges) initialize
	DLL_HEADER Ng_Result Ng_STL_InitSTLGeometry(Ng_STL_Geometry * geom)
	{
		return Ng_STL_InitSTLGeometryEx(geom, 0);
	}

	DLL_HEADER Ng_Result Ng_STL_InitSTLGeometryEx(Ng_STL_Geometry * geom,
		int allow_open_boundaries)
	{
		STLGeometry* geo = (STLGeometry*)geom;
		geo->SetAllowOpenBoundaries(allow_open_boundaries != 0);
		geo->InitSTLGeometry(readtrias);
		readtrias.SetSize(0);

		if (readedges.Size() != 0)
		{
			/*
			for (int i = 1; i <= readedges.Size(); i+=2)
			{
			cout << "e(" << readedges.Get(i) << "," << readedges.Get(i+1) << ")" << endl;
			}
			*/
			geo->AddEdges(readedges);
		}

		if (geo->GetStatus() == STLTopology::STL_GOOD || geo->GetStatus() == STLTopology::STL_WARNING) return NG_OK;
		return NG_SURFACE_INPUT_ERROR;
	}




	// automatically create edges:
	DLL_HEADER Ng_Result Ng_STL_MakeEdges(Ng_STL_Geometry * geom,
		Ng_Mesh* mesh,
		Ng_Meshing_Parameters * mp)
	{
		STLGeometry* stlgeometry = (STLGeometry*)geom;
		Mesh* me = (Mesh*)mesh;

		// Philippose - 27/07/2009
		// Do not locally re-define "mparam" here... "mparam" is a global 
		// object 
		//MeshingParameters mparam;
		mp->Transfer_Parameters();

		me->SetGlobalH(mparam.maxh);
		me->SetLocalH(stlgeometry->GetBoundingBox().PMin() - Vec3d(10, 10, 10),
			stlgeometry->GetBoundingBox().PMax() + Vec3d(10, 10, 10),
			0.3);

		me->LoadLocalMeshSize(mp->meshsize_filename);
		/*
		if (mp->meshsize_filename)
		{
		ifstream infile (mp->meshsize_filename);
		if (!infile.good()) return NG_FILE_NOT_FOUND;
		me -> LoadLocalMeshSize (infile);
		}
		*/

		STLMeshing(*stlgeometry, *me);

		stlgeometry->edgesfound = 1;
		stlgeometry->surfacemeshed = 0;
		stlgeometry->surfaceoptimized = 0;
		stlgeometry->volumemeshed = 0;

		return NG_OK;
	}



	// automatically generates edge mesh:
	DLL_HEADER Ng_Result Ng_STL_GenerateEdgeMesh(Ng_STL_Geometry * geom,
		Ng_Mesh* mesh,
		Ng_Meshing_Parameters * mp)
	{
		Ng_STL_MakeEdges(geom, mesh, mp);

		STLGeometry* stlgeometry = (STLGeometry*)geom;
		Mesh* me = (Mesh*)mesh;

		stlgeometry->PrepareSurfaceMeshing();

		if (me->GetNSeg() == 0) netgen::STLFindEdges(*stlgeometry, *me);

		return NG_OK;
	}




	// generates mesh, empty mesh be already created.
	DLL_HEADER Ng_Result Ng_STL_GenerateSurfaceMesh(Ng_STL_Geometry * geom,
		Ng_Mesh* mesh,
		Ng_Meshing_Parameters * mp)
	{
		STLGeometry* stlgeometry = (STLGeometry*)geom;
		Mesh* me = (Mesh*)mesh;

		// Philippose - 27/07/2009
		// Do not locally re-define "mparam" here... "mparam" is a global 
		// object
		//MeshingParameters mparam;
		mp->Transfer_Parameters();


		/*
		me -> SetGlobalH (mparam.maxh);
		me -> SetLocalH (stlgeometry->GetBoundingBox().PMin() - Vec3d(10, 10, 10),
		stlgeometry->GetBoundingBox().PMax() + Vec3d(10, 10, 10),
		0.3);
		*/
		/*
		STLMeshing (*stlgeometry, *me);

		stlgeometry->edgesfound = 1;
		stlgeometry->surfacemeshed = 0;
		stlgeometry->surfaceoptimized = 0;
		stlgeometry->volumemeshed = 0;
		*/
		int retval = STLSurfaceMeshing(*stlgeometry, *me);
		if (retval == MESHING3_OK)
		{
			(*mycout) << "Success !!!!" << endl;
			stlgeometry->surfacemeshed = 1;
			stlgeometry->surfaceoptimized = 0;
			stlgeometry->volumemeshed = 0;
		}
		else if (retval == MESHING3_OUTERSTEPSEXCEEDED)
		{
			(*mycout) << "ERROR: Give up because of too many trials. Meshing aborted!" << endl;
		}
		else if (retval == MESHING3_TERMINATE)
		{
			(*mycout) << "Meshing Stopped!" << endl;
		}
		else
		{
			(*mycout) << "ERROR: Surface meshing not successful. Meshing aborted!" << endl;
		}


		if (retval != MESHING3_OK)
			return NG_SURFACE_FAILURE;

		STLSurfaceOptimization(*stlgeometry, *me, mparam);

		return NG_OK;
	}




	// fills STL Geometry
	// positive orientation
	// normal vector may be null-pointer
	DLL_HEADER void Ng_STL_AddTriangle(Ng_STL_Geometry * geom,
		double * p1, double * p2, double * p3,
		double * nv)
	{
		Point<3> apts[3];
		apts[0] = Point<3>(p1[0], p1[1], p1[2]);
		apts[1] = Point<3>(p2[0], p2[1], p2[2]);
		apts[2] = Point<3>(p3[0], p3[1], p3[2]);

		Vec<3> n;
		if (!nv)
			n = Cross(apts[0] - apts[1], apts[0] - apts[2]);
		else
			n = Vec<3>(nv[0], nv[1], nv[2]);

		readtrias.Append(STLReadTriangle(apts, n));
	}

	// add (optional) edges:
	DLL_HEADER void Ng_STL_AddEdge(Ng_STL_Geometry * geom,
		double * p1, double * p2)
	{
		readedges.Append(Point3d(p1[0], p1[1], p1[2]));
		readedges.Append(Point3d(p2[0], p2[1], p2[2]));
	}




#ifdef OCCGEOMETRY
	// --------------------- OCC Geometry / Meshing Utility Functions -------------------
	inline const char* SurfaceTypeToString(GeomAbs_SurfaceType surfaceType)
	{
		switch (surfaceType)
		{
			case GeomAbs_Plane:   return "Plane";
			case GeomAbs_Cylinder:   return "Cylinder";
			case GeomAbs_Cone: return "Cone";
			case GeomAbs_Sphere: return "Sphere";
			case GeomAbs_Torus: return "Torus";
			case GeomAbs_BezierSurface: return "BezierSurface";
			case GeomAbs_BSplineSurface: return "BSplineSurface";
			case GeomAbs_SurfaceOfRevolution: return "SurfaceOfRevolution";
			case GeomAbs_SurfaceOfExtrusion: return "SurfaceOfExtrusion";
			case GeomAbs_OffsetSurface: return "OffsetSurface";
			case GeomAbs_OtherSurface: return "OtherSurface";
			default: return "Unknown";
		}
	}
	inline const char* CurveTypeToString(GeomAbs_CurveType curveType)
	{
		switch (curveType)
		{
			case GeomAbs_Line:   return "Line";
			case GeomAbs_Circle:   return "Circle";
			case GeomAbs_Ellipse: return "Ellipse";
			case GeomAbs_Hyperbola: return "Hyperbola";
			case GeomAbs_Parabola: return "Parabola";
			case GeomAbs_BezierCurve: return "BezierCurve";
			case GeomAbs_BSplineCurve: return "BSplineCurve";		
			case GeomAbs_OffsetCurve: return "OffsetCurve";
			case GeomAbs_OtherCurve: return "OtherCurve";
			default: return "Unknown";
		}
	}
	inline const char* OrientationToString(TopAbs_Orientation orientation)
	{
		switch (orientation)
		{
			case TopAbs_FORWARD: return "Forward";
			case TopAbs_REVERSED: return "Reversed";
			case TopAbs_INTERNAL: return "Internal";
			case TopAbs_EXTERNAL: return "External";
			default: return "Unknown";
		}
	}
	class GeometryMetadataWriter
	{
	private:
		OCCGeometry* geometry;
		ofstream& outfile;
		TopTools_IndexedDataMapOfShapeListOfShape edgeFaceMap;
		TopTools_IndexedDataMapOfShapeListOfShape faceSolidMap;
		TopTools_IndexedDataMapOfShapeListOfShape vertexEdgeMap;
		string entityLabel;

		void BeginEntity(const char* entityType, int id)
		{
			if (strcmp(entityType, "solid") == 0) entityLabel = "Solid";
			else if (strcmp(entityType, "shell") == 0) entityLabel = "Shell";
			else if (strcmp(entityType, "face") == 0) entityLabel = "Face";
			else if (strcmp(entityType, "edge") == 0) entityLabel = "Edge";
			else if (strcmp(entityType, "vertex") == 0) entityLabel = "Vertex";
			else entityLabel = entityType;
			outfile << entityLabel << " number: " << id << endl;
		}
		void EndEntity()
		{
			outfile << endl;
			entityLabel.clear();
		}
		void PropertyName(const char* name)
		{
			outfile << entityLabel << " " << name << ":";
		}
		void Property(const char* name, double value)
		{
			PropertyName(name);
			outfile << " " << value << endl;
		}
		void Property(const char* name, int value)
		{
			PropertyName(name);
			outfile << " " << value << endl;
		}
		void Property(const char* name, const char* value)
		{
			PropertyName(name);
			outfile << " " << value << endl;
		}
		void Property(const char* name, const gp_Pnt& point)
		{
			PropertyName(name);
			outfile << " " << point.X() << " " << point.Y() << " " << point.Z() << endl;
		}
		void Property(const char* name, const gp_Dir& direction)
		{
			PropertyName(name);
			outfile << " " << direction.X() << " " << direction.Y() << " "
				    << direction.Z() << endl;
		}
		void AxisProperty(const gp_Ax1& axis)
		{
			const gp_Pnt& location = axis.Location();
			const gp_Dir& direction = axis.Direction();
			PropertyName("axis");
			outfile << " " << location.X() << " " << location.Y() << " " << location.Z() << " "
				    << direction.X() << " " << direction.Y() << " " << direction.Z() << endl;
		}
		void PositionProperties(const gp_Ax2& position)
		{
			AxisProperty(position.Axis());
			Property("x_direction", position.XDirection());
			Property("y_direction", position.YDirection());
		}
		void PositionProperties(const gp_Ax3& position)
		{
			AxisProperty(position.Axis());
			Property("x_direction", position.XDirection());
			Property("y_direction", position.YDirection());
		}
		void BoundingBoxProperty(const TopoDS_Shape& shape)
		{
			Bnd_Box box;
			BRepBndLib::Add(shape, box, Standard_False);
			if (box.IsVoid()) return;
			//
			double xMin;
			double yMin;
			double zMin;
			double xMax;
			double yMax;
			double zMax;
			box.Get(xMin, yMin, zMin, xMax, yMax, zMax);
			PropertyName("bounding_box");
			outfile << " " << xMin << " " << xMax << " " << yMin << " " << yMax << " "
				    << zMin << " " << zMax << endl;
		}
		void InertiaProperty(const GProp_GProps& properties)
		{
			gp_Mat inertia = properties.MatrixOfInertia();
			PropertyName("inertia_at_center_of_mass");
			outfile << " "
				    << inertia(1, 1) << " " << inertia(1, 2) << " " << inertia(1, 3) << " "
				    << inertia(2, 1) << " " << inertia(2, 2) << " " << inertia(2, 3) << " "
				    << inertia(3, 1) << " " << inertia(3, 2) << " " << inertia(3, 3) << endl;
		}
		void ShapeIdsProperty(const char* name, const TopoDS_Shape& shape, TopAbs_ShapeEnum shapeType,
		                      const TopTools_IndexedMapOfShape& globalMap)
		{
			TopTools_IndexedMapOfShape localMap;
			TopExp::MapShapes(shape, shapeType, localMap);
			PropertyName(name);
			for (int i = 1; i <= localMap.Extent(); i++)
			{
				int id = globalMap.FindIndex(localMap(i));
				if (id > 0) outfile << " " << id;
			}
			outfile << endl;
		}
		bool GetSingleParentSolid(const TopoDS_Face& face, TopoDS_Solid& solid)
		{
			if (!faceSolidMap.Contains(face)) return false;
			TopTools_IndexedMapOfShape parentSolids;
			const TopTools_ListOfShape& solids = faceSolidMap.FindFromKey(face);
			for (TopTools_ListIteratorOfListOfShape it(solids); it.More(); it.Next()) parentSolids.Add(it.Value());
			if (parentSolids.Extent() != 1) return false;
			solid = TopoDS::Solid(parentSolids(1));
			return true;
		}
		// A face bounds its solid from one side only when the solid always uses it the same way; a face used both
		// ways has material on both of its sides
		bool GetOrientationInSolid(const TopoDS_Face& face, const TopoDS_Solid& solid, TopAbs_Orientation& orientation)
		{
			bool found = false;
			for (TopExp_Explorer explorer(solid, TopAbs_FACE); explorer.More(); explorer.Next())
			{
				if (!explorer.Current().IsSame(face)) continue;
				TopAbs_Orientation current = explorer.Current().Orientation();
				if (current != TopAbs_FORWARD && current != TopAbs_REVERSED) return false;
				if (found && current != orientation) return false;
				orientation = current;
				found = true;
			}
			return found;
		}
		const char* CylinderConvexity(const TopoDS_Face& face, const BRepAdaptor_Surface& surface,
		                                const gp_Cylinder& cylinder)
		{
			TopoDS_Solid solid;
			if (!GetSingleParentSolid(face, solid)) return nullptr;
			// Find a point inside the trimmed face, away from its boundary. The outward normal there points
			// away from the material, which states on which radial side the material is. Classifying points
			// against the whole solid states the same and costs tens of milliseconds a point on a solid with
			// spline faces, so it is kept for a face with a mirroring location only: a mirror reverses the
			// parametric normal of the transformed surface, and Forward/Reversed then means the opposite.
			double uMin;
			double uMax;
			double vMin;
			double vMax;
			BRepTools::UVBounds(face, uMin, uMax, vMin, vMax);
			if (Precision::IsInfinite(uMin) || Precision::IsInfinite(uMax) ||
				Precision::IsInfinite(vMin) || Precision::IsInfinite(vMax)) return nullptr;
			const double fractions[] = { 0.5, 0.25, 0.75, 0.125, 0.875 };
			gp_Pnt point;
			gp_Vec uDerivative;
			gp_Vec vDerivative;
			bool pointFound = false;
			for (double uFraction : fractions)
			{
				for (double vFraction : fractions)
				{
					double u = uMin + uFraction * (uMax - uMin);
					double v = vMin + vFraction * (vMax - vMin);
					BRepClass_FaceClassifier classifier(face, gp_Pnt2d(u, v), Precision::Confusion());
					if (classifier.State() == TopAbs_IN)
					{
						surface.D1(u, v, point, uDerivative, vDerivative);
						pointFound = true;
						break;
					}
				}
				if (pointFound) break;
			}
			if (!pointFound) return nullptr;
			// The radial direction points away from the cylinder axis.
			gp_Vec axis(cylinder.Axis().Direction());
			gp_Vec radial(cylinder.Axis().Location(), point);
			radial -= axis.Multiplied(radial.Dot(axis));
			if (radial.SquareMagnitude() <= Precision::SquareConfusion()) return nullptr;
			radial.Normalize();
			if (!face.Location().Transformation().IsNegative())
			{
				TopAbs_Orientation orientation;
				if (!GetOrientationInSolid(face, solid, orientation)) return nullptr;
				gp_Vec normal = uDerivative.Crossed(vDerivative);
				if (normal.SquareMagnitude() <= Precision::SquareConfusion()) return nullptr;
				normal.Normalize();
				if (orientation == TopAbs_REVERSED) normal.Reverse();
				double radialComponent = normal.Dot(radial);
				if (radialComponent > 0.5) return "Convex";
				if (radialComponent < -0.5) return "Concave";
				return nullptr;
			}
			double offset = std::max(100.0 * Precision::Confusion(), cylinder.Radius() * 1e-6);
			BRepClass3d_SolidClassifier classifier(solid);
			classifier.Perform(point.Translated(radial.Multiplied(-offset)), Precision::Confusion());
			TopAbs_State towardAxis = classifier.State();
			classifier.Perform(point.Translated(radial.Multiplied(offset)), Precision::Confusion());
			TopAbs_State awayFromAxis = classifier.State();
			if (towardAxis == TopAbs_IN && awayFromAxis == TopAbs_OUT) return "Convex";
			if (towardAxis == TopAbs_OUT && awayFromAxis == TopAbs_IN) return "Concave";
			return nullptr;
		}
		void WriteSolid(int id, const TopoDS_Shape& solid)
		{
			BeginEntity("solid", id);
			Property("orientation", OrientationToString(solid.Orientation()));
			BoundingBoxProperty(solid);
			//
			GProp_GProps volumeProperties;
			BRepGProp::VolumeProperties(solid, volumeProperties);
			Property("volume", volumeProperties.Mass());
			Property("center_of_mass", volumeProperties.CentreOfMass());
			InertiaProperty(volumeProperties);
			//
			GProp_GProps surfaceProperties;
			BRepGProp::SurfaceProperties(solid, surfaceProperties);
			Property("surface_area", surfaceProperties.Mass());
			ShapeIdsProperty("shell_ids", solid, TopAbs_SHELL, geometry->shmap);
			ShapeIdsProperty("face_ids", solid, TopAbs_FACE, geometry->fmap);
			EndEntity();
		}
		void WriteShell(int id, const TopoDS_Shape& shell)
		{
			BeginEntity("shell", id);
			Property("orientation", OrientationToString(shell.Orientation()));
			Property("closed", shell.Closed() ? 1 : 0);
			BoundingBoxProperty(shell);
			//
			GProp_GProps properties;
			BRepGProp::SurfaceProperties(shell, properties);
			Property("area", properties.Mass());
			Property("centroid", properties.CentreOfMass());
			ShapeIdsProperty("face_ids", shell, TopAbs_FACE, geometry->fmap);
			EndEntity();
		}
		void WriteSurfaceProperties(const TopoDS_Face& face, const BRepAdaptor_Surface& surface,
		                            GeomAbs_SurfaceType surfaceType)
		{
			switch (surfaceType)
			{
				case GeomAbs_Plane:
					PositionProperties(surface.Plane().Position());
					break;
				case GeomAbs_Cylinder:
				{
					gp_Cylinder cylinder = surface.Cylinder();
					PositionProperties(cylinder.Position());
					Property("radius", cylinder.Radius());
					const char* convexity = CylinderConvexity(face, surface, cylinder);
					if (convexity != nullptr) Property("convexity", convexity);
					break;
				}
				case GeomAbs_Cone:
				{
					gp_Cone cone = surface.Cone();
					PositionProperties(cone.Position());
					Property("apex", cone.Apex());
					Property("reference_radius", cone.RefRadius());
					Property("semi_angle_rad", cone.SemiAngle());
					break;
				}
				case GeomAbs_Sphere:
				{
					gp_Sphere sphere = surface.Sphere();
					PositionProperties(sphere.Position());
					Property("center", sphere.Location());
					Property("radius", sphere.Radius());
					break;
				}
				case GeomAbs_Torus:
				{
					gp_Torus torus = surface.Torus();
					PositionProperties(torus.Position());
					Property("center", torus.Location());
					Property("major_radius", torus.MajorRadius());
					Property("minor_radius", torus.MinorRadius());
					break;
				}
				case GeomAbs_SurfaceOfRevolution:
					AxisProperty(surface.AxeOfRevolution());
					break;
				case GeomAbs_SurfaceOfExtrusion:
					Property("extrusion_direction", surface.Direction());
					break;
			}
		}
		void WriteFace(int id, const TopoDS_Face& face)
		{
			BRepAdaptor_Surface surface(face, Standard_True);
			GeomAbs_SurfaceType surfaceType = surface.GetType();
			BeginEntity("face", id);
			Property("orientation", OrientationToString(face.Orientation()));
			Property("type", SurfaceTypeToString(surfaceType));
			BoundingBoxProperty(face);
			//
			GProp_GProps properties;
			BRepGProp::SurfaceProperties(face, properties);
			Property("area", properties.Mass());
			Property("centroid", properties.CentreOfMass());
			ShapeIdsProperty("edge_ids", face, TopAbs_EDGE, geometry->emap);
			WriteSurfaceProperties(face, surface, surfaceType);
			EndEntity();
		}
		void WriteCurveProperties(const BRepAdaptor_Curve& curve, GeomAbs_CurveType curveType)
		{
			switch (curveType)
			{
				case GeomAbs_Line:
					AxisProperty(curve.Line().Position());
					break;
				case GeomAbs_Circle:
				{
					gp_Circ circle = curve.Circle();
					PositionProperties(circle.Position());
					Property("center", circle.Location());
					Property("radius", circle.Radius());
					Property("closed", curve.IsClosed() ? 1 : 0);
					Property("sweep_angle_rad", std::abs(curve.LastParameter() - curve.FirstParameter()));
					break;
				}
				case GeomAbs_Ellipse:
				{
					gp_Elips ellipse = curve.Ellipse();
					PositionProperties(ellipse.Position());
					Property("center", ellipse.Location());
					Property("major_radius", ellipse.MajorRadius());
					Property("minor_radius", ellipse.MinorRadius());
					break;
				}
				case GeomAbs_Hyperbola:
				{
					gp_Hypr hyperbola = curve.Hyperbola();
					PositionProperties(hyperbola.Position());
					Property("center", hyperbola.Location());
					Property("major_radius", hyperbola.MajorRadius());
					Property("minor_radius", hyperbola.MinorRadius());
					break;
				}
				case GeomAbs_Parabola:
				{
					gp_Parab parabola = curve.Parabola();
					PositionProperties(parabola.Position());
					Property("vertex", parabola.Location());
					Property("focal_length", parabola.Focal());
					break;
				}
				default:
					WriteStraightCurveAxis(curve);
					break;
			}
		}
		// A curve that was drawn straight and arrives as a spline - which is what a STEP file and a
		// boolean operation both leave behind - still runs in one direction, and a reader asking for
		// the direction of an edge means that direction whatever curve carries it. So a non analytic
		// curve that stays on the line through its ends reports that line as its axis. The type stays
		// what the curve really is: the axis says the curve is straight, not that it is a line.
		void WriteStraightCurveAxis(const BRepAdaptor_Curve& curve)
		{
			double first = curve.FirstParameter();
			double last = curve.LastParameter();
			if (last <= first) return;
			//
			gp_Pnt start = curve.Value(first);
			gp_Pnt end = curve.Value(last);
			double chord = start.Distance(end);
			if (chord <= Precision::Confusion()) return;
			//
			gp_Dir direction(gp_Vec(start, end));
			gp_Lin line(start, direction);
			// The ends of a curve lie on the line through them whatever the curve does between them, so
			// the curve is sampled over its whole parameter range and every sample has to sit on it too
			double tolerance = chord * 1.0e-6;
			if (tolerance < Precision::Confusion()) tolerance = Precision::Confusion();
			const int numOfSamples = 32;
			for (int i = 1; i < numOfSamples; i++)
			{
				gp_Pnt point = curve.Value(first + (last - first) * i / numOfSamples);
				if (line.Distance(point) > tolerance) return;
			}
			// A curve that runs out along the line and back again sits on the line at every sample, so
			// the length it covers has to be the length of the chord as well
			if (GCPnts_AbscissaPoint::Length(curve) - chord > tolerance) return;
			//
			AxisProperty(gp_Ax1(start, direction));
		}
		void WriteEdge(int id, const TopoDS_Edge& edge)
		{
			BRepAdaptor_Curve curve(edge);
			GeomAbs_CurveType curveType = curve.GetType();
			BeginEntity("edge", id);
			Property("orientation", OrientationToString(edge.Orientation()));
			Property("type", CurveTypeToString(curveType));
			Property("degenerated", BRep_Tool::Degenerated(edge) ? 1 : 0);
			BoundingBoxProperty(edge);
			//
			GProp_GProps properties;
			BRepGProp::LinearProperties(edge, properties);
			Property("length", properties.Mass());
			Property("centroid", properties.CentreOfMass());
			// The point half way along the edge, which is what a user means by its midpoint. It is not
			// the centroid: the centroid of an arc does not lie on the arc.
			if (!BRep_Tool::Degenerated(edge))
			{
				double curveLength = GCPnts_AbscissaPoint::Length(curve);
				if (curveLength > 0)
				{
					GCPnts_AbscissaPoint midpoint(curve, curveLength / 2, curve.FirstParameter());
					if (midpoint.IsDone()) Property("midpoint", curve.Value(midpoint.Parameter()));
				}
			}
			ShapeIdsProperty("vertex_ids", edge, TopAbs_VERTEX, geometry->vmap);
			//
			TopTools_IndexedMapOfShape parentFaces;
			int faceUseCount = 0;
			if (edgeFaceMap.Contains(edge))
			{
				const TopTools_ListOfShape& faces = edgeFaceMap.FindFromKey(edge);
				for (TopTools_ListIteratorOfListOfShape it(faces); it.More(); it.Next())
				{
					parentFaces.Add(it.Value());
					faceUseCount++;
				}
			}
			PropertyName("face_ids");
			for (int i = 1; i <= parentFaces.Extent(); i++)
			{
				int faceId = geometry->fmap.FindIndex(parentFaces(i));
				if (faceId > 0) outfile << " " << faceId;
			}
			outfile << endl;
			Property("face_use_count", faceUseCount);
			WriteCurveProperties(curve, curveType);
			EndEntity();
		}
		void WriteVertex(int id, const TopoDS_Vertex& vertex)
		{
			BeginEntity("vertex", id);
			Property("orientation", OrientationToString(vertex.Orientation()));
			Property("coordinates", BRep_Tool::Pnt(vertex));
			PropertyName("edge_ids");
			if (vertexEdgeMap.Contains(vertex))
			{
				TopTools_IndexedMapOfShape parentEdges;
				const TopTools_ListOfShape& edges = vertexEdgeMap.FindFromKey(vertex);
				for (TopTools_ListIteratorOfListOfShape it(edges); it.More(); it.Next()) parentEdges.Add(it.Value());
				for (int i = 1; i <= parentEdges.Extent(); i++)
				{
					int edgeId = geometry->emap.FindIndex(parentEdges(i));
					if (edgeId > 0) outfile << " " << edgeId;
				}
			}
			outfile << endl;
			EndEntity();
		}

	public:
		GeometryMetadataWriter(OCCGeometry* geometry, ofstream& outfile)
			: geometry(geometry), outfile(outfile)
		{
			TopExp::MapShapesAndAncestors(geometry->shape, TopAbs_EDGE, TopAbs_FACE, edgeFaceMap);
			TopExp::MapShapesAndAncestors(geometry->shape, TopAbs_FACE, TopAbs_SOLID, faceSolidMap);
			TopExp::MapShapesAndAncestors(geometry->shape, TopAbs_VERTEX, TopAbs_EDGE, vertexEdgeMap);
		}
		void Write()
		{
			// Every geometry entity is defined once before the tessellation. Each property is independent;
			// readers ignore unknown names, and a missing line means that the property is unavailable.
			outfile << "VIS file format: 2" << endl;
			outfile << "Coordinate system: global" << endl;
			outfile << "Length unit: model" << endl << endl;
			outfile << "**********" << endl;
			outfile << "Geometry" << endl;
			outfile << "**********" << endl << endl;
			outfile.precision(17);
			//
			outfile << "Number of solids: " << geometry->somap.Extent() << endl << endl;
			for (int i = 1; i <= geometry->somap.Extent(); i++) WriteSolid(i, geometry->somap(i));
			outfile << "Number of shells: " << geometry->shmap.Extent() << endl << endl;
			for (int i = 1; i <= geometry->shmap.Extent(); i++) WriteShell(i, geometry->shmap(i));
			outfile << "Number of faces: " << geometry->fmap.Extent() << endl << endl;
			for (int i = 1; i <= geometry->fmap.Extent(); i++) WriteFace(i, TopoDS::Face(geometry->fmap(i)));
			outfile << "Number of edges: " << geometry->emap.Extent() << endl << endl;
			for (int i = 1; i <= geometry->emap.Extent(); i++) WriteEdge(i, TopoDS::Edge(geometry->emap(i)));
			outfile << "Number of vertices: " << geometry->vmap.Extent() << endl << endl;
			for (int i = 1; i <= geometry->vmap.Extent(); i++) WriteVertex(i, TopoDS::Vertex(geometry->vmap(i)));
			outfile << "**********" << endl;
			outfile << "Visualization" << endl;
			outfile << "**********" << endl << endl;
		}
	};
	void ExportVisualizationVertices(OCCGeometry* occgeom, ofstream& outfile)
	{
		// The coordinates are written in full: a point picked on the visualization is handed back to the
		// modelling kernel, and six decimals put a vertex a fraction of a micron off the geometry it lies on
		outfile.precision(17);
		outfile << "Number of visualization vertices: " << occgeom->vmap.Extent() << " (Id, X, Y, Z)" << endl;
		for (int i = 1; i <= occgeom->vmap.Extent(); i++)
		{
			gp_Pnt point = BRep_Tool::Pnt(TopoDS::Vertex(occgeom->vmap(i)));
			outfile << i << " " << point.X() << " " << point.Y() << " " << point.Z() << "\n";
		}
		outfile << endl;
	}
	void ExportItemVisualization(OCCGeometry * occgeom, TopAbs_ShapeEnum TopAbs_Shape, ofstream &outfile,
	                             int &numOfEdges, int &numOfFallbackEdges, int &numOfFacesWithoutTriangulation)
	{
		TopLoc_Location aLocation;
		Standard_Integer nId;
		gp_Pnt aPnt1;
		int facenr;
		int edgenr;
		Standard_Integer N1;
		Standard_Integer N2;
		Standard_Integer N3;
		//
		TopAbs_ShapeEnum ToAvoid;
		if (TopAbs_Shape == TopAbs_SOLID) ToAvoid = TopAbs_SHAPE;
		else if (TopAbs_Shape == TopAbs_SHELL) ToAvoid = TopAbs_SOLID;
		else if (TopAbs_Shape == TopAbs_FACE) ToAvoid = TopAbs_SHELL;
		//
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_Shape, ToAvoid); exp0.More(); exp0.Next())
		{
			for (TopExp_Explorer exp1(exp0.Current(), TopAbs_FACE); exp1.More(); exp1.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp1.Current());
				facenr = occgeom->fmap.FindIndex(face);
				//
				BRepAdaptor_Surface faceElementAdaptor(face, Standard_True);
				GeomAbs_SurfaceType surfaceType = faceElementAdaptor.GetType();
				//
				outfile << "**********" << endl;
				outfile << "Face mesh number: " << facenr << endl;
				//
				Handle(Poly_Triangulation) aTr = BRep_Tool::Triangulation(face, aLocation);
				// If this triangulation is not NULL
				if (!aTr.IsNull())
				{
					// Takes the array of nodes for this triangulation:
					// const TColgp_Array1OfPnt& aNodes = aTr->Node();
					// Create array of node points in absolute coordinate system
					TColgp_Array1OfPnt aPoints(1, aTr->NbNodes());
					for (Standard_Integer i = 1; i <= aTr->NbNodes(); i++)
					{
						aPoints(i) = aTr->Node(i).Transformed(aLocation);
					}
					// Nodes
					outfile << "**********" << endl;
					outfile << "Number of nodes: " << aPoints.Length() << " (Id, X, Y, Z)" << endl;
					//
					for (Standard_Integer i = 1; i <= aPoints.Length(); i++)
					{
						outfile << i << " " << aPoints(i).X() << " " << aPoints(i).Y() << " " << aPoints(i).Z() << "\n";
					}
					// Triangles
					const Poly_Array1OfTriangle& triangles = aTr->Triangles();
					outfile << "**********" << endl;
					outfile << "Number of triangles: " << aTr->NbTriangles() << " (Id, N1, N2, N3)" << endl;
					for (Standard_Integer i = 1; i <= triangles.Length(); i++)
					{
						triangles(i).Get(N1, N2, N3);
						outfile << i << " " << N1 << " " << N2 << " " << N3 << "\n";
					}
					// Edges
					TopTools_IndexedMapOfShape edges;
					TopExp::MapShapes(exp1.Current(), TopAbs_EDGE, edges);
					outfile << "**********" << endl;
					outfile << "Number of edge polylines: " << edges.Extent() << " (Edge Id, N1, N2, N3 ...)" << endl;
					//
					bool searchNodeByNode;
					GProp_GProps system;
					double eps = 1E-9;
					TopoDS_Vertex v1;
					TopoDS_Vertex v2;
					BRepExtrema_DistShapeShape extrema;
					extrema.SetDeflection(eps);
					//
					for (TopExp_Explorer exp2(exp1.Current(), TopAbs_EDGE); exp2.More(); exp2.Next())
					{
						TopoDS_Edge edge = TopoDS::Edge(exp2.Current());
						edgenr = occgeom->emap.FindIndex(edge);
						numOfEdges++;
						//
						// If this edge is not NULL
						if (!edge.IsNull())
						{
							// Takes the polygon associated to the edge aEdge.
							// The (triangulation, location) pair identifies the stored
							// representation, so the location must be the one the face
							// triangulation was retrieved with - not the edge's own.
							Handle(Poly_PolygonOnTriangulation) aPol = BRep_Tool::PolygonOnTriangulation(edge, aTr, aLocation);
							// If this polygon is not NULL
							searchNodeByNode = aPol.IsNull();
							if (!searchNodeByNode)
							{
								// The polygon's node indices are, by construction, indices into
								// this face's triangulation and lie on this edge, so they are
								// written out directly - no per-node verification needed.
								const TColStd_Array1OfInteger& aNodesOfPol = aPol->Nodes();
								{
									outfile << "Edge polyline: " << edgenr;
									// Takes the array of nodes for this polygon (indexes in the array of nodes for triangulation of theFace)
									for (Standard_Integer i = 1; i <= aNodesOfPol.Length(); i++)
									{
										nId = aNodesOfPol.Value(i);
										outfile << " " << nId;
									}
									outfile << endl;
								}
							}
							// The polygon is NULL
							if (searchNodeByNode)
							{
								// Kept for geometry that genuinely has no polygon on this
								// face's triangulation. It is orders of magnitude more
								// expensive than the path above, so it is counted and
								// reported: a non-zero count means real degenerate geometry,
								// not a lookup that silently failed.
								numOfFallbackEdges++;
								// Find points on triangulation
								BRepGProp::LinearProperties(edge, system);
								if (system.Mass() < eps) continue;
								//
								int startId = -1;
								int endId = -1;
								int minId = -1;
								double min = 1E100;
								//
								v1 = TopExp::FirstVertex(edge);
								extrema.LoadS1(v1);
								for (Standard_Integer i = 1; i <= aPoints.Length(); i++)
								{
									v2 = BRepBuilderAPI_MakeVertex(aPoints(i));
									extrema.LoadS2(v2);
									extrema.Perform();
									//
									if (extrema.IsDone() == 1)
									{
										if (extrema.Value() < eps)
										{
											startId = i;
											break;
										}
										if (extrema.Value() < min)
										{
											min = extrema.Value();
											minId = i;
										}
									}
								}
								if (startId == -1) startId = minId;
								//
								min = 1E100;
								minId = -1;
								v1 = TopExp::LastVertex(edge);
								extrema.LoadS1(v1);
								for (Standard_Integer i = 1; i <= aPoints.Length(); i++)
								{
									v2 = BRepBuilderAPI_MakeVertex(aPoints(i));
									extrema.LoadS2(v2);
									extrema.Perform();
									//
									if (extrema.IsDone() == 1)
									{
										if (extrema.Value() < eps)
										{
											endId = i;
											break;
										}
										if (extrema.Value() < min)
										{
											min = extrema.Value();
											minId = i;
										}
									}
								}
								if (endId == -1) endId = minId;
								//
								outfile << "Edge polyline: " << edgenr;
								outfile << " " << startId;
								//
								extrema.LoadS1(edge);
								for (Standard_Integer i = 1; i <= aPoints.Length(); i++)
								{
									if (i == startId || i == endId) continue;
									//
									v2 = BRepBuilderAPI_MakeVertex(aPoints(i));
									extrema.LoadS2(v2);
									extrema.Perform();
									//
									if (extrema.IsDone() == 1 && extrema.Value() < eps)
									{
										outfile << " " << i;
									}
								}
								//
								outfile << " " << endId;
								outfile << endl;
							}
						}
					}
				}
				else
				{
					// The face is written without its nodes, triangles and edges, so it reaches
					// PrePoMax as a hole in the part. Say so instead of letting it pass unnoticed.
					numOfFacesWithoutTriangulation++;
					// The caller is mid-way through its "Exporting ..." line, so start a new one
					cout << endl << "WARNING: face " << facenr << " (" << SurfaceTypeToString(surfaceType)
						 << ") could not be triangulated and is missing from the visualization." << endl;
				}
			}
		}
	}
	void SearchConnectedShapes(int currShapeNr, list<int> * connection, list<int> * connectedShapes, int * shapesToVisit)
	{
		bool found = (std::find(connection->begin(), connection->end(), currShapeNr) != connection->end());
		if (found) return;
		//
		connection->push_back(currShapeNr);
		shapesToVisit[currShapeNr] = 0;
		//
		list<int> connectedShape = connectedShapes[currShapeNr];
		if (connectedShape.size() > 0)
		{
			for (std::list<int>::iterator it = connectedShape.begin(); it != connectedShape.end(); it++)
			{
				SearchConnectedShapes(*it, connection, connectedShapes, shapesToVisit);
			}
			connectedShapes[currShapeNr].clear();
		}
	}
	TopoDS_Shape ReverseFaceOrientation(const TopoDS_Shape& shape, const TopoDS_Face& face)
	{
		//
		// https://www.opencascade.com/content/reverse-face-orientation
		//
		Handle(BRepTools_ReShape) rebuild = new BRepTools_ReShape();
		//rebuild->e ->ModeConsiderOrientation() = Standard_True;
		TopoDS_Shape newface = face.Complemented();
		rebuild->Replace(face, newface);
		TopoDS_Shape newshape = rebuild->Apply(shape, TopAbs_FACE);
		return newshape;
	}
	OCCGeometry * ReverseBrepFaceOrientations(Ng_OCC_Geometry * geom, int * faceIds, int numOfIds)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		//
		int facenr;
		bool faceFound;
		TopoDS_Face face;
		//
		for (int i = 0; i < numOfIds; i++)
		{
			faceFound = false;
			//
			for (TopExp_Explorer exp0(occgeom->shape, TopAbs_FACE); exp0.More(); exp0.Next())
			{
				face = TopoDS::Face(exp0.Current());
				facenr = occgeom->fmap.FindIndex(face);
				//
				if (facenr == faceIds[i])
				{
					faceFound = true;
					break;
				}
			}
			if (faceFound) occgeom->shape = ReverseFaceOrientation(occgeom->shape, face);
		}
		//
		return occgeom;
	}
	// Everything that is offset goes into one shell, and so comes back as one part. The faces of a
	// connected patch keep the edges they share, and a selection that falls apart into several patches is
	// still one shell, because it was one selection
	int AddFacesToShell(const TopoDS_Shape & shape, BRep_Builder & builder, TopoDS_Shell & shell)
	{
		int numOfFaces = 0;
		for (TopExp_Explorer exp0(shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			builder.Add(shell, exp0.Current());
			numOfFaces++;
		}
		return numOfFaces;
	}
	TopoDS_Shape OffsetShell(const TopoDS_Shape & shell, double offset, double tolerance)
	{
		try
		{
			BRepOffsetAPI_MakeOffsetShape makeOffset;
			makeOffset.PerformByJoin(shell, offset, tolerance, BRepOffset_Skin, Standard_False,
			                         Standard_False, GeomAbs_Intersection, Standard_False);
			if (makeOffset.IsDone() && !makeOffset.Shape().IsNull()) return makeOffset.Shape();
		}
		catch (Standard_Failure &)
		{
		}
		// The joining offset intersects the offset surfaces with each other and gives up where they
		// cannot be intersected. The simple offset only moves them, which is enough for a patch whose
		// faces meet smoothly and is the case a mid surface is usually taken from
		try
		{
			BRepOffset_MakeSimpleOffset simpleOffset(shell, offset);
			simpleOffset.SetBuildSolidFlag(Standard_False);
			simpleOffset.Perform();
			if (simpleOffset.IsDone() && !simpleOffset.GetResultShape().IsNull())
				return simpleOffset.GetResultShape();
		}
		catch (Standard_Failure &)
		{
		}
		//
		return TopoDS_Shape();
	}
	// The faces the ids name, lifted out of the shape that carries them and sewn into shells, so that a
	// selection covering a connected patch comes back as one body instead of as loose faces. An offset
	// other than zero moves each patch along its own normals, which is what a mid surface is made of.
	// The ids arrive grouped the way a shell split sends them: targetFaceCounts[i] of them are numbered
	// inside solid targetSolids[i], and a solid of zero numbers them in the shape itself. That is what a
	// compound needs - the faces of each of its sub parts are numbered inside the solid the sub part was
	// written out of - and what lets the faces of several sub parts be sewn into one body.
	OCCGeometry * OffsetFaces(Ng_OCC_Geometry * geom, int * targetSolids, int * targetFaceCounts,
	                          int numOfTargetGroups, int * faceIds, double offset)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		//
		TopTools_IndexedMapOfShape faces;
		if (!GetTargetFaces(occgeom, targetSolids, targetFaceCounts, numOfTargetGroups, faceIds, faces))
		{
			cout << "None of the selected surfaces was found in the geometry." << endl;
			return NULL;
		}
		// The faces of one body share their edges, so any tolerance that covers the edges covers the
		// sewing; the edge tolerances are what an imported geometry actually carries
		double tolerance = Precision::Confusion();
		for (int i = 1; i <= faces.Extent(); i++)
		{
			for (TopExp_Explorer exp0(faces.FindKey(i), TopAbs_EDGE); exp0.More(); exp0.Next())
			{
				double edgeTolerance = BRep_Tool::Tolerance(TopoDS::Edge(exp0.Current()));
				if (edgeTolerance > tolerance) tolerance = edgeTolerance;
			}
		}
		//
		BRepBuilderAPI_Sewing sewing(2 * tolerance);
		for (int i = 1; i <= faces.Extent(); i++) sewing.Add(faces.FindKey(i));
		sewing.Perform();
		TopoDS_Shape sewedShape = sewing.SewedShape();
		if (sewedShape.IsNull())
		{
			cout << "The selected surfaces could not be sewn into a shell." << endl;
			return NULL;
		}
		// A selection that falls into several patches gives several shells, and each of them is offset on
		// its own, because an offset follows the surface and not the selection
		std::vector<TopoDS_Shape> patches;
		BRep_Builder builder;
		//
		for (TopExp_Explorer exp0(sewedShape, TopAbs_SHELL); exp0.More(); exp0.Next())
			patches.push_back(exp0.Current());
		for (TopExp_Explorer exp0(sewedShape, TopAbs_FACE, TopAbs_SHELL); exp0.More(); exp0.Next())
		{
			TopoDS_Shell shell;
			builder.MakeShell(shell);
			builder.Add(shell, exp0.Current());
			patches.push_back(shell);
		}
		//
		// Each patch is a shell of its own, so that a patch that shares no edge with the others is written
		// out as a part of its own and carries only its own faces
		TopoDS_Compound compound;
		builder.MakeCompound(compound);
		int numOfOffsetFaces = 0;
		//
		for (size_t i = 0; i < patches.size(); i++)
		{
			TopoDS_Shell shell;
			builder.MakeShell(shell);
			int numOfPatchFaces = 0;
			//
			if (offset == 0) numOfPatchFaces = AddFacesToShell(patches[i], builder, shell);
			else
			{
				TopoDS_Shape offsetShape = OffsetShell(patches[i], offset, tolerance);
				// A surface that lands somewhere other than where it was asked to go is worse than no
				// surface at all, so a failed offset fails the whole face offset
				if (offsetShape.IsNull())
				{
					cout << "The surface could not be offset by " << offset << "." << endl;
					return NULL;
				}
				numOfPatchFaces = AddFacesToShell(offsetShape, builder, shell);
			}
			if (numOfPatchFaces > 0) builder.Add(compound, shell);
			numOfOffsetFaces += numOfPatchFaces;
		}
		if (numOfOffsetFaces == 0)
		{
			cout << "The face offset left no surface at all." << endl;
			return NULL;
		}
		//
		OCCGeometry * newoccgeo = new OCCGeometry;
		newoccgeo->shape = compound;
		newoccgeo->changed = 1;
		newoccgeo->BuildFMap();
		//
		return newoccgeo;
	}
	static bool ShapeHoldsAnyFace(const TopoDS_Shape & shape, const TopTools_IndexedMapOfShape & faces)
	{
		for (TopExp_Explorer exp0(shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			if (faces.Contains(exp0.Current())) return true;
		}
		return false;
	}
	// The faces a shape keeps, each with the orientation it had in it, so that the edges they share stay shared
	// and the normals point where they pointed
	static int AddKeptFaces(const TopoDS_Shape & shape, const TopTools_IndexedMapOfShape & removedFaces,
	                        BRep_Builder & builder, TopoDS_Shell & keptShell)
	{
		int numOfKeptFaces = 0;
		for (TopExp_Explorer exp0(shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			if (removedFaces.Contains(exp0.Current())) continue;
			builder.Add(keptShell, exp0.Current());
			numOfKeptFaces++;
		}
		return numOfKeptFaces;
	}
	// The named faces are taken out and nothing is put in their place. A solid that loses a face is no
	// longer closed, so what is left of it is written as one shell; a solid, a shell or a face that loses
	// nothing is written as it was, so a neighbour keeps the very faces and edges it shared. The solids that
	// are kept come first, in the order they had, and the shells of the opened solids follow in the same
	// order, so a caller that is told which solids were opened can tell the pieces of the result apart;
	// openedSolids receives their numbers, counted the way the explorer walks the solids, and may be NULL.
	// A solid that loses every face is gone and leaves nothing in the result; removedSolids receives its
	// number.
	// What is left may no longer touch; the caller decides what the pieces become.
	// The ids arrive grouped the way a face offset sends them: targetFaceCounts[i] of them are numbered
	// inside solid targetSolids[i], and a solid of zero numbers them in the shape itself.
	OCCGeometry * RemoveFaces(Ng_OCC_Geometry * geom, int * targetSolids, int * targetFaceCounts,
	                          int numOfTargetGroups, int * faceIds, int * openedSolids, int maxOpenedSolids,
	                          int * numOfOpenedSolids, int * removedSolids, int * numOfRemovedSolids)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		if (numOfOpenedSolids != NULL) *numOfOpenedSolids = 0;
		if (numOfRemovedSolids != NULL) *numOfRemovedSolids = 0;
		//
		TopTools_IndexedMapOfShape removedFaces;
		if (!GetTargetFaces(occgeom, targetSolids, targetFaceCounts, numOfTargetGroups, faceIds, removedFaces))
		{
			cout << "None of the selected faces was found in the geometry." << endl;
			return NULL;
		}
		//
		BRep_Builder builder;
		TopoDS_Compound result;
		builder.MakeCompound(result);
		int numOfKeptFaces = 0;
		vector<TopoDS_Shape> openedShells;
		vector<int> openedSolidNumbers;
		vector<int> removedSolidNumbers;
		//
		int solidNumber = 0;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			solidNumber++;
			if (!ShapeHoldsAnyFace(exp0.Current(), removedFaces))
			{
				builder.Add(result, exp0.Current());
				numOfKeptFaces++;
				continue;
			}
			TopoDS_Shell keptShell;
			builder.MakeShell(keptShell);
			int numOfSolidFaces = AddKeptFaces(exp0.Current(), removedFaces, builder, keptShell);
			if (numOfSolidFaces == 0)
			{
				removedSolidNumbers.push_back(solidNumber);
				continue;
			}
			keptShell.Closed(BRep_Tool::IsClosed(keptShell));
			openedShells.push_back(keptShell);
			openedSolidNumbers.push_back(solidNumber);
			numOfKeptFaces += numOfSolidFaces;
		}
		for (size_t i = 0; i < openedShells.size(); i++) builder.Add(result, openedShells[i]);
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			if (!ShapeHoldsAnyFace(exp0.Current(), removedFaces))
			{
				builder.Add(result, exp0.Current());
				numOfKeptFaces++;
				continue;
			}
			TopoDS_Shell keptShell;
			builder.MakeShell(keptShell);
			int numOfShellFaces = AddKeptFaces(exp0.Current(), removedFaces, builder, keptShell);
			if (numOfShellFaces == 0) continue;
			keptShell.Closed(BRep_Tool::IsClosed(keptShell));
			builder.Add(result, keptShell);
			numOfKeptFaces += numOfShellFaces;
		}
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_FACE, TopAbs_SHELL); exp0.More(); exp0.Next())
		{
			if (removedFaces.Contains(exp0.Current())) continue;
			builder.Add(result, exp0.Current());
			numOfKeptFaces++;
		}
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_EDGE, TopAbs_FACE); exp0.More(); exp0.Next())
			builder.Add(result, exp0.Current());
		//
		if (numOfKeptFaces == 0 && removedSolidNumbers.size() == 0)
		{
			cout << "Deleting the selected faces would leave no face at all." << endl;
			return NULL;
		}
		if ((openedSolids != NULL && (int)openedSolidNumbers.size() > maxOpenedSolids) ||
		    (removedSolids != NULL && (int)removedSolidNumbers.size() > maxOpenedSolids))
		{
			cout << "More solids were opened than the caller has room for." << endl;
			return NULL;
		}
		for (size_t i = 0; openedSolids != NULL && i < openedSolidNumbers.size(); i++)
			openedSolids[i] = openedSolidNumbers[i];
		if (numOfOpenedSolids != NULL) *numOfOpenedSolids = (int)openedSolidNumbers.size();
		for (size_t i = 0; removedSolids != NULL && i < removedSolidNumbers.size(); i++)
			removedSolids[i] = removedSolidNumbers[i];
		if (numOfRemovedSolids != NULL) *numOfRemovedSolids = (int)removedSolidNumbers.size();
		//
		OCCGeometry * newoccgeo = new OCCGeometry;
		newoccgeo->shape = result;
		newoccgeo->changed = 1;
		newoccgeo->BuildFMap();
		//
		return newoccgeo;
	}
	static int CountSubShapes(const TopoDS_Shape & shape, TopAbs_ShapeEnum type)
	{
		TopTools_IndexedMapOfShape subShapes;
		TopExp::MapShapes(shape, type, subShapes);
		return subShapes.Extent();
	}
	// Two faces may only become one when they bound the same solids, or a solid would hold a face its
	// neighbour does not and the two would no longer meet
	static bool BoundSameSolids(const TopoDS_Shape & first, const TopoDS_Shape & second,
	                            const TopTools_IndexedDataMapOfShapeListOfShape & faceSolids)
	{
		TopTools_MapOfShape firstSolids;
		TopTools_MapOfShape secondSolids;
		int index = faceSolids.FindIndex(first);
		if (index > 0)
			for (TopTools_ListOfShape::Iterator it(faceSolids(index)); it.More(); it.Next()) firstSolids.Add(it.Value());
		index = faceSolids.FindIndex(second);
		if (index > 0)
			for (TopTools_ListOfShape::Iterator it(faceSolids(index)); it.More(); it.Next()) secondSolids.Add(it.Value());
		//
		if (firstSolids.Extent() != secondSolids.Extent()) return false;
		for (TopTools_MapOfShape::Iterator it(firstSolids); it.More(); it.Next())
			if (!secondSolids.Contains(it.Value())) return false;
		return true;
	}
	// The named faces are made one across the edges they share, where the faces on both sides lie on one
	// surface. An edge is only taken out when both of its faces are named and bound the same solids, and a
	// seam only when its face is named, so every other edge stays where it is and the shape is never moved.
	// The edges are then joined at the vertices of the edges taken out, which takes out the points a split
	// left on the edges it crossed. Answers the number of faces that were fused away, zero when there was
	// nothing to fuse, and -1 when the result is not a valid shape of the same bodies, which is not used.
	static int FuseFacesOfShape(const TopoDS_Shape & shape, const TopTools_IndexedMapOfShape & fusableFaces,
	                            TopoDS_Shape & result)
	{
		result = shape;
		//
		TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
		TopExp::MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
		TopTools_IndexedDataMapOfShapeListOfShape faceSolids;
		TopExp::MapShapesAndAncestors(shape, TopAbs_FACE, TopAbs_SOLID, faceSolids);
		//
		TopTools_MapOfShape keepEdges;
		TopTools_IndexedMapOfShape fusedEdgeVertices;
		int numOfFusableEdges = 0;
		for (int i = 1; i <= edgeFaces.Extent(); i++)
		{
			const TopoDS_Shape & edge = edgeFaces.FindKey(i);
			TopTools_IndexedMapOfShape faces;
			for (TopTools_ListOfShape::Iterator it(edgeFaces(i)); it.More(); it.Next()) faces.Add(it.Value());
			//
			bool fusable = faces.Extent() == 1 || faces.Extent() == 2;
			for (int j = 1; fusable && j <= faces.Extent(); j++) fusable = fusableFaces.Contains(faces(j));
			if (fusable && faces.Extent() == 1)
				fusable = BRep_Tool::IsClosed(TopoDS::Edge(edge), TopoDS::Face(faces(1)));
			if (fusable && faces.Extent() == 2) fusable = BoundSameSolids(faces(1), faces(2), faceSolids);
			//
			if (!fusable) keepEdges.Add(edge);
			else if (faces.Extent() == 2)
			{
				numOfFusableEdges++;
				TopExp::MapShapes(edge, TopAbs_VERTEX, fusedEdgeVertices);
			}
		}
		if (numOfFusableEdges == 0) return 0;
		//
		int numOfFacesBefore = CountSubShapes(shape, TopAbs_FACE);
		int numOfSolidsBefore = CountSubShapes(shape, TopAbs_SOLID);
		int numOfShellsBefore = CountSubShapes(shape, TopAbs_SHELL);
		bool validBefore = BRepCheck_Analyzer(shape).IsValid() == Standard_True;
		// The edges that stay keep their identity, so a face that is not fused still shares them
		ShapeUpgrade_UnifySameDomain unifyFaces(shape, Standard_False, Standard_True, Standard_False);
		unifyFaces.KeepShapes(keepEdges);
		unifyFaces.SetSafeInputMode(false);
		unifyFaces.Build();
		TopoDS_Shape fused = unifyFaces.Shape();
		//
		TopTools_MapOfShape keepVertices;
		TopTools_IndexedMapOfShape vertices;
		TopExp::MapShapes(fused, TopAbs_VERTEX, vertices);
		for (int i = 1; i <= vertices.Extent(); i++)
			if (!fusedEdgeVertices.Contains(vertices(i))) keepVertices.Add(vertices(i));
		ShapeUpgrade_UnifySameDomain unifyEdges(fused, Standard_True, Standard_False, Standard_False);
		unifyEdges.KeepShapes(keepVertices);
		unifyEdges.SetSafeInputMode(false);
		unifyEdges.Build();
		fused = unifyEdges.Shape();
		//
		int numOfFacesAfter = CountSubShapes(fused, TopAbs_FACE);
		if (numOfFacesAfter >= numOfFacesBefore) return 0;
		if (CountSubShapes(fused, TopAbs_SOLID) != numOfSolidsBefore ||
		    CountSubShapes(fused, TopAbs_SHELL) != numOfShellsBefore ||
		    (validBefore && !BRepCheck_Analyzer(fused).IsValid())) return -1;
		//
		result = fused;
		return numOfFacesBefore - numOfFacesAfter;
	}
	// The ids arrive grouped the way a face offset sends them: targetFaceCounts[i] of them are numbered
	// inside solid targetSolids[i], and a solid of zero numbers them in the shape itself.
	OCCGeometry * FuseFaces(Ng_OCC_Geometry * geom, int * targetSolids, int * targetFaceCounts,
	                        int numOfTargetGroups, int * faceIds)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		//
		TopTools_IndexedMapOfShape faces;
		if (!GetTargetFaces(occgeom, targetSolids, targetFaceCounts, numOfTargetGroups, faceIds, faces))
		{
			cout << "None of the selected faces was found in the geometry." << endl;
			return NULL;
		}
		if (faces.Extent() < 2)
		{
			cout << "Fusing faces needs at least two faces that share an edge." << endl;
			return NULL;
		}
		//
		TopoDS_Shape result;
		int numOfFusedFaces = FuseFacesOfShape(occgeom->shape, faces, result);
		if (numOfFusedFaces < 0)
		{
			cout << "The fused faces do not make a valid shape, so the geometry was left as it was." << endl;
			return NULL;
		}
		if (numOfFusedFaces == 0)
		{
			cout << "None of the selected faces could be fused. Faces are fused across an edge they share, " <<
			        "when they lie on one surface and bound the same solids." << endl;
			return NULL;
		}
		cout << "Fuse faces: " << faces.Extent() << " selected faces became " << faces.Extent() - numOfFusedFaces
		     << "." << endl;
		//
		OCCGeometry * newoccgeo = new OCCGeometry;
		newoccgeo->shape = result;
		newoccgeo->changed = 1;
		newoccgeo->BuildFMap();
		//
		return newoccgeo;
	}
	static void WriteRepairStep(const char * step, const TopoDS_Shape & before, const TopoDS_Shape & after)
	{
		cout << "Repair - " << step << ": faces " << CountSubShapes(before, TopAbs_FACE) << " -> " <<
		        CountSubShapes(after, TopAbs_FACE) << ", edges " << CountSubShapes(before, TopAbs_EDGE) <<
		        " -> " << CountSubShapes(after, TopAbs_EDGE) << ", vertices " <<
		        CountSubShapes(before, TopAbs_VERTEX) << " -> " << CountSubShapes(after, TopAbs_VERTEX) << endl;
	}
	// The repairs the options name run in a fixed order, each on what the one before left: sewing first,
	// since the fixes need faces that are connected, then the shape fixes, the small faces and the small
	// edges, which leave faces and edges on one surface or curve that the fusing and joining take out. A
	// repair never adds or removes a solid, and a result that is no longer valid when the input was is not
	// used, so a repair that cannot help leaves the geometry as it was.
	OCCGeometry * RepairShape(Ng_OCC_Geometry * geom, int options, double tolerance)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		TopoDS_Shape shape = occgeom->shape;
		if (tolerance <= 0) tolerance = Precision::Confusion();
		//
		int numOfSolidsBefore = CountSubShapes(shape, TopAbs_SOLID);
		bool validBefore = BRepCheck_Analyzer(shape).IsValid() == Standard_True;
		TopoDS_Shape before;
		//
		if (options & NG_OCC_REPAIR_SEW_FACES)
		{
			if (numOfSolidsBefore > 0) cout << "Repair - sew faces: skipped, the geometry holds solids." << endl;
			else
			{
				before = shape;
				BRepBuilderAPI_Sewing sewing(tolerance);
				sewing.Add(shape);
				sewing.Perform();
				if (!sewing.SewedShape().IsNull()) shape = sewing.SewedShape();
				WriteRepairStep("sew faces", before, shape);
			}
		}
		if (options & NG_OCC_REPAIR_FIX_SHAPE)
		{
			before = shape;
			Handle(ShapeFix_Shape) shapeFix = new ShapeFix_Shape;
			shapeFix->Init(shape);
			shapeFix->SetPrecision(Precision::Confusion());
			shapeFix->SetMaxTolerance(tolerance);
			shapeFix->Perform();
			if (shapeFix->Status(ShapeExtend_DONE)) shape = shapeFix->Shape();
			WriteRepairStep(shapeFix->Status(ShapeExtend_DONE) ? "fix shape" : "fix shape (nothing to fix)",
			                before, shape);
		}
		if (options & NG_OCC_REPAIR_SMALL_FACES)
		{
			before = shape;
			Handle(ShapeFix_FixSmallFace) smallFaceFix = new ShapeFix_FixSmallFace();
			smallFaceFix->Init(shape);
			smallFaceFix->SetPrecision(tolerance);
			smallFaceFix->SetMaxTolerance(tolerance);
			smallFaceFix->Perform();
			shape = smallFaceFix->FixShape();
			WriteRepairStep("remove small faces", before, shape);
		}
		if (options & NG_OCC_REPAIR_SMALL_EDGES)
		{
			before = shape;
			Handle(ShapeFix_Wireframe) wireframeFix = new ShapeFix_Wireframe(shape);
			wireframeFix->SetPrecision(tolerance);
			wireframeFix->SetMaxTolerance(tolerance);
			wireframeFix->ModeDropSmallEdges() = Standard_True;
			wireframeFix->FixSmallEdges();
			// Closing the wire gaps of a valid shape can break it, and in place: on a split part with no gap it
			// reoriented two faces no small edge touches and gave a shared vertex a tolerance of 70 mm
			if (!BRepCheck_Analyzer(wireframeFix->Shape()).IsValid()) wireframeFix->FixWireGaps();
			shape = wireframeFix->Shape();
			WriteRepairStep("remove small edges", before, shape);
		}
		if (options & NG_OCC_REPAIR_FUSE_FACES)
		{
			before = shape;
			TopTools_IndexedMapOfShape faces;
			TopExp::MapShapes(shape, TopAbs_FACE, faces);
			TopoDS_Shape fused;
			if (FuseFacesOfShape(shape, faces, fused) < 0)
				cout << "Repair - fuse faces: skipped, the fused faces do not make a valid shape." << endl;
			else shape = fused;
			WriteRepairStep("fuse faces", before, shape);
		}
		if (options & NG_OCC_REPAIR_JOIN_EDGES)
		{
			before = shape;
			ShapeUpgrade_UnifySameDomain unifyEdges(shape, Standard_True, Standard_False, Standard_False);
			unifyEdges.Build();
			shape = unifyEdges.Shape();
			WriteRepairStep("join edges", before, shape);
		}
		//
		if (CountSubShapes(shape, TopAbs_FACE) == 0)
		{
			cout << "The repair left no face, so the geometry was left as it was." << endl;
			return NULL;
		}
		if (CountSubShapes(shape, TopAbs_SOLID) != numOfSolidsBefore)
		{
			cout << "The repair changed the number of solids from " << numOfSolidsBefore << " to " <<
			        CountSubShapes(shape, TopAbs_SOLID) << ", so the geometry was left as it was." << endl;
			return NULL;
		}
		bool validAfter = BRepCheck_Analyzer(shape).IsValid() == Standard_True;
		if (validBefore && !validAfter)
		{
			cout << "The repaired geometry is not valid, so the geometry was left as it was." << endl;
			return NULL;
		}
		if (!validBefore)
			cout << (validAfter ? "The geometry was not valid and is valid after the repair." :
			                      "The geometry was not valid and is still not valid after the repair.") << endl;
		//
		OCCGeometry * newoccgeo = new OCCGeometry;
		newoccgeo->shape = shape;
		newoccgeo->changed = 1;
		newoccgeo->BuildFMap();
		//
		return newoccgeo;
	}
	// A vertex a CAD system wrote a hair past the seam of a periodic face - a mirrored part has had the vertices of
	// its bores 2e-9 rad past it - is cut off by the divider as an edge shorter than any tolerance, and the faces
	// that edge bounds are invalid. Moving the vertex onto the seam would reshape the pcurves, and recomputing them
	// breaks the edges on the neighbouring faces. Dropping such edges after the split gives back the faces the
	// divider meant, so it is done only to a result that is invalid.
	void DropSmallEdgesOfInvalidShape(TopoDS_Shape& shape, const char* filename)
	{
		if (BRepCheck_Analyzer(shape).IsValid()) return;
		try
		{
			ShapeFix_Wireframe fixer(shape);
			fixer.SetPrecision(1e-6);
			fixer.SetMaxTolerance(1e-4);
			fixer.ModeDropSmallEdges() = Standard_True;
			fixer.FixSmallEdges();
			fixer.FixWireGaps();
			TopoDS_Shape fixedShape = fixer.Shape();
			if (BRepCheck_Analyzer(fixedShape).IsValid())
			{
				shape = fixedShape;
				return;
			}
		}
		catch (Standard_Failure& ex)
		{
			cout << endl << "WARNING: dropping the small edges of " << filename << " failed ("
				 << typeid(ex).name() << ")." << endl;
		}
		cout << endl << "WARNING: the periodic face split of " << filename << " is not a valid shape." << endl;
	}
	bool WriteShapeToBrepFile(const TopoDS_Shape& shape, const char* filename, int numOfSplitFaces)
	{
		bool result = false;
		TopoDS_Shape splitShape = shape;
		//
		if (numOfSplitFaces > 1)
		{
			// Faces a boolean operation cut from one face share its surface, so an edge between two of
			// them carries a single pcurve that serves both. Dividing one of the faces removes that pcurve
			// from the edges it splits, and the other face is left with edges it cannot be divided along:
			// it comes back as an empty face holding them and two pieces that miss them. A copy gives every
			// face a surface and pcurves of its own.
			BRepBuilderAPI_Copy copier(shape, Standard_True);
			ShapeUpgrade_ShapeDivideClosed divider = ShapeUpgrade_ShapeDivideClosed(copier.Shape());
			//divider.SetPrecision(0.01);
			//divider.SetMinTolerance(0.1 * 0.01);
			//divider.SetMaxTolerance(0.01);
			divider.SetNbSplitPoints(numOfSplitFaces - 1);
			if (divider.Perform())
			{
				splitShape = divider.Result();
				// The divider rebuilds the pcurves of the edges it touches but leaves their
				// SameParameter and SameRange flags set, so the flags no longer describe the
				// edge. BRepMesh trusts them and drops the triangulation of the affected faces,
				// which then arrive in PrePoMax as holes in the part. Recomputing the flags
				// here keeps the written file valid. The divided shape must not be copied again -
				// BRepBuilderAPI_Copy of a freshly divided shape makes SameParameter throw.
				try
				{
					BRepLib::SameParameter(splitShape, Precision::Confusion(), Standard_True);
				}
				catch (Standard_Failure& ex)
				{
					cout << endl << "WARNING: the edges of " << filename << " could not be repaired after the"
						 << " periodic face split (" << typeid(ex).name() << ")."
						 << " The geometry is written unrepaired and may be invalid." << endl;
				}
				DropSmallEdgesOfInvalidShape(splitShape, filename);
			}
		}
		//
		BRepTools::Write(splitShape, filename, Message_ProgressRange());
		return result;
	}
	void ExtractBodies(const TopoDS_Shape& shape, BRep_Builder& builder, TopoDS_Compound& faceCompound, TopoDS_Compound& shellCompound,	
					   TopoDS_Compound& solidCompound, bool closeShells)
	{
		TopoDS_Shell shell;
		//
		for (TopExp_Explorer exp0(shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			builder.Add(solidCompound, exp0.Current());
		}
		//
		for (TopExp_Explorer exp0(shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			shell = TopoDS::Shell(exp0.Current());
			//
			if (closeShells && BRep_Tool::IsClosed(shell))
			{
				// Try to convert it into a solid
				TopoDS_Solid solid;
				BRepBuilderAPI_MakeSolid solidMaker;
				solidMaker.Add(shell);
				solid = solidMaker.Solid();
				// Optional: check if the resulting solid is valid
				BRepCheck_Analyzer analyzer(solid);
				if (analyzer.IsValid())
				{
					std::cout << "Successfully built solid from shell." << std::endl;
					// Use or store the solid as needed
					builder.Add(solidCompound, solid);
				}
				else
				{
					// Solid is invalid
					builder.Add(shellCompound, shell);
				}
			}
			else
			{
				// Shell is not closed and cannot be converted to a solid
				builder.Add(shellCompound, shell);
			}
		}
		//
		for (TopExp_Explorer exp0(shape, TopAbs_FACE, TopAbs_SHELL); exp0.More(); exp0.Next())
		{
			builder.MakeShell(shell);			// create the shell
			builder.Add(shell, exp0.Current()); // add the face to the shell
			builder.Add(shellCompound, shell);
		}
	}
	int WriteAssemblyAsSolidCompounds(OCCGeometry* occgeom, int countStart, const char* filename, int numOfSplitFaces)
	{
		// occgeom->RebuildGeometry();
		// Search for shared surfaces
		int numOfFaces = occgeom->fmap.Extent();
		Array<int> face2solid[2];
		for (int i = 0; i < 2; i++)
		{
			face2solid[i].SetSize(numOfFaces);
			face2solid[i] = -1;
		}
		int numOfSolids;
		int facenr;
		int currSolidnr = 0;
		int solidnr0 = 0;
		TopoDS_Solid solid;
		TopoDS_Solid * solids;
		list<int> * connectedSolids;	// for each solidId store a list of connected solids
		//
		numOfSolids = occgeom->somap.Extent();
		solids = new TopoDS_Solid[numOfSolids];
		connectedSolids = new list<int>[numOfSolids];
		//
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			currSolidnr++;
			solid = TopoDS::Solid(exp0.Current());
			solids[currSolidnr - 1] = solid;
			//
			for (TopExp_Explorer exp1(solid, TopAbs_FACE); exp1.More(); exp1.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp1.Current());
				facenr = occgeom->fmap.FindIndex(face);
				// First solid
				if (face2solid[0][facenr - 1] == -1)
					face2solid[0][facenr - 1] = currSolidnr - 1;
				// Second solid
				else
				{
					face2solid[1][facenr - 1] = currSolidnr - 1;
					//
					solidnr0 = face2solid[0][facenr - 1];
					connectedSolids[solidnr0].push_back(currSolidnr - 1);
					connectedSolids[currSolidnr - 1].push_back(solidnr0);
				}
			}
		}
		// Find connected parts
		int * solidsToVisit;
		solidsToVisit = new int[numOfSolids];
		for (int i = 0; i < numOfSolids; i++) solidsToVisit[i] = 1;
		list<int> * connection;
		list<list<int>> allConnections;
		//
		for (int i = 0; i < numOfSolids; i++)
		{
			if (solidsToVisit[i] == 1)
			{
				connection = new list<int>();
				SearchConnectedShapes(i, connection, connectedSolids, solidsToVisit);
				//
				allConnections.push_back(*connection);
			}
		}
		// Export																									
		char solidFileNameWithPath[_MAX_FNAME];
		char shellFileNameWithPath[_MAX_FNAME];
		char full_path[_MAX_PATH];
		char drive[_MAX_DRIVE];
		char dir[_MAX_DIR];
		char fname[_MAX_FNAME];
		char ext[_MAX_EXT];
		//
		_splitpath_s(filename, drive, dir, fname, ext);
		// Export Solids
		currSolidnr = countStart;
		for (std::list<list<int>>::iterator it1 = allConnections.begin(); it1 != allConnections.end(); it1++)
		{
			stringstream ss;
			list<int>& oneConnection = *it1;
			if (oneConnection.size() == 1)
			{
				//ss << fname << "_solid_" << currSolidnr;
				ss << fname << "_solid_" << std::setfill('0') << std::setw(4) << currSolidnr;
				//
				_makepath_s(solidFileNameWithPath, drive, dir, ss.str().c_str(), ext);
				WriteShapeToBrepFile(solids[*oneConnection.begin()], solidFileNameWithPath, numOfSplitFaces);
				//BRepTools::Write(solids[*oneConnection.begin()], solidFileNameWithPath, Message_ProgressRange());
			}
			else if (oneConnection.size() > 1)
			{
				BOPAlgo_Builder aBuilder;
				aBuilder.SetRunParallel(Standard_True);
				//
				for (std::list<int>::iterator it2 = oneConnection.begin(); it2 != oneConnection.end(); it2++)
				{
					aBuilder.AddArgument(solids[*it2]);
				}
				//
				aBuilder.Perform();
				if (aBuilder.HasErrors()) continue;
				//
				const TopoDS_Shape& aRes = aBuilder.Shape();
				//
				//ss << fname << "_compound_solid_" << currSolidnr;
				ss << fname << "_compound_solid_" << std::setfill('0') << std::setw(4) << currSolidnr;
				//
				_makepath_s(solidFileNameWithPath, drive, dir, ss.str().c_str(), ext);
				WriteShapeToBrepFile(aRes, solidFileNameWithPath, numOfSplitFaces);
				//BRepTools::Write(aRes, solidFileNameWithPath, Message_ProgressRange());
			}
			currSolidnr++;
		}
		//
		delete[] solids;
		delete[] connectedSolids;
		delete[] solidsToVisit;
		//
		return currSolidnr;
	}
	int WriteAssemblyAsShellCompounds(OCCGeometry* occgeom, int countStart, const char* filename, int numOfSplitFaces)
	{
		// Search for shared edges
		int numOfEdges = occgeom->emap.Extent();
		list<int> oneEdgeShells;
		list<int> * edgeShells;
		edgeShells = new list<int>[numOfEdges];
		list<int> visitedEdges;
		//
		int numOfShells;
		int edgeNr;
		int currShellNr = 0;
		TopoDS_Shell shell;
		TopoDS_Shell * shells;
		list<int> * connectedShells;	// for each shellId store a list of connected shells
		//
		//numOfShells = occgeom->shmap.Extent();
		// Count shells that are not solids
		numOfShells = 0;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			numOfShells++;
		}
		shells = new TopoDS_Shell[numOfShells];
		connectedShells = new list<int>[numOfShells];
		//
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			currShellNr++;
			shell = TopoDS::Shell(exp0.Current());
			shells[currShellNr - 1] = shell;
			//
			visitedEdges.clear();
			//
			for (TopExp_Explorer exp1(shell, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				edgeNr = occgeom->emap.FindIndex(edge);
				// Check if edge was visited: a shell contains multiple faces sharing the same edge more than once
				bool found = (std::find(visitedEdges.begin(), visitedEdges.end(), edgeNr) != visitedEdges.end());
				if (!found)
				{
					// Add edge
					visitedEdges.push_back(edgeNr);
					// First shell
					if (edgeShells[edgeNr - 1].size() == 0)
						edgeShells[edgeNr - 1].push_back(currShellNr - 1);
					// The rest of the shells
					else
					{
						oneEdgeShells = edgeShells[edgeNr - 1];
						for (std::list<int>::iterator it = oneEdgeShells.begin(); it != oneEdgeShells.end(); it++)
						{
							connectedShells[*it].push_back(currShellNr - 1);
							connectedShells[currShellNr - 1].push_back(*it);
						}
						edgeShells[edgeNr - 1].push_back(currShellNr - 1);	// must not be oneEdgeShell
					}
				}
			}
		}
		// Find connected shells
		int * shellsToVisit;
		shellsToVisit = new int[numOfShells];
		for (int i = 0; i < numOfShells; i++) shellsToVisit[i] = 1;
		list<int> * connection;
		list<list<int>> allConnections;
		//
		for (int i = 0; i < numOfShells; i++)
		{
			if (shellsToVisit[i] == 1)
			{
				connection = new list<int>();
				SearchConnectedShapes(i, connection, connectedShells, shellsToVisit);
				//
				allConnections.push_back(*connection);
			}
		}
		// Export																									
		char shellFileNameWithPath[_MAX_FNAME];
		char full_path[_MAX_PATH];
		char drive[_MAX_DRIVE];
		char dir[_MAX_DIR];
		char fname[_MAX_FNAME];
		char ext[_MAX_EXT];
		//
		_splitpath_s(filename, drive, dir, fname, ext);
		// Shells
		int shellNr = countStart;
		for (std::list<list<int>>::iterator it1 = allConnections.begin(); it1 != allConnections.end(); it1++)
		{
			stringstream ss;
			list<int>& oneConnection = *it1;
			if (oneConnection.size() == 1)
			{
				//ss << fname << "_shell_" << shellNr;
				ss << fname << "_shell_" << std::setfill('0') << std::setw(4) << shellNr;
				//
				_makepath_s(shellFileNameWithPath, drive, dir, ss.str().c_str(), ext);
				//BRepTools::Write(shells[*oneConnection.begin()], shellFileNameWithPath, Message_ProgressRange());
				WriteShapeToBrepFile(shells[*oneConnection.begin()], shellFileNameWithPath, numOfSplitFaces);
			}
			else if (oneConnection.size() > 1)
			{
				BOPAlgo_Builder aBuilder;
				aBuilder.SetRunParallel(Standard_True);
				//
				for (std::list<int>::iterator it2 = oneConnection.begin(); it2 != oneConnection.end(); it2++)
				{
					aBuilder.AddArgument(shells[*it2]);
				}
				//
				aBuilder.Perform();
				if (aBuilder.HasErrors()) continue;
				//
				const TopoDS_Shape& aRes = aBuilder.Shape();
				//
				//ss << fname << "_shell_" << shellNr;
				ss << fname << "_shell_" << std::setfill('0') << std::setw(4) << shellNr;
				//
				_makepath_s(shellFileNameWithPath, drive, dir, ss.str().c_str(), ext);
				//
				//BRepTools::Write(aRes, shellFileNameWithPath, Message_ProgressRange());
				WriteShapeToBrepFile(aRes, shellFileNameWithPath, numOfSplitFaces);
			}
			shellNr++;
		}
		delete[] edgeShells;
		delete[] shells;
		delete[] connectedShells;
		delete[] shellsToVisit;
		//
		return shellNr;
	}
	void DumpShapeTopology(const TopoDS_Shape& shape)
	{
		std::map<TopAbs_ShapeEnum, int> counts;
		//
		for (TopExp_Explorer exp(shape, TopAbs_SHAPE); exp.More(); exp.Next())
		{
			counts[exp.Current().ShapeType()]++;
		}
		//
		std::cout << "=== Topology summary ===\n";
		for (int i = TopAbs_COMPOUND; i <= TopAbs_VERTEX; ++i)
		{
			auto type = static_cast<TopAbs_ShapeEnum>(i);
			std::cout << TopAbs::ShapeTypeToString(type)
				<< ": " << counts[type] << "\n";
		}
	}

	
	
	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_NewGeometry()
	{
		return (Ng_OCC_Geometry*)(void*)new OCCGeometry;
	}

	// Delete the OCC Geometry Object
	DLL_HEADER Ng_Result Ng_OCC_DeleteGeometry(Ng_OCC_Geometry * geom)
	{
		if (geom != NULL)
		{
			delete (OCCGeometry*)geom;
			geom = NULL;
			return NG_OK;
		}

		return NG_ERROR;
	}

	// Loads geometry from STEP File
	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_Load_STEP(const char * filename)
	{
		// Call the STEP File Load function. Note.. the geometry class 
		// is created and instantiated within the load function
		OCCGeometry * occgeom = LoadOCC_STEP(filename);

		//TopoDS_Shape top_shape = occgeom->shape;
		//DumpShapeTopology(top_shape);

		return ((Ng_OCC_Geometry *)occgeom);
	}

	// Loads geometry from IGES File
	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_Load_IGES(const char * filename)
	{
		// Call the IGES File Load function. Note.. the geometry class 
		// is created and instantiated within the load function
		OCCGeometry * occgeom = LoadOCC_IGES(filename);

		return ((Ng_OCC_Geometry *)occgeom);
	}

	// Loads geometry from BREP File
	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_Load_BREP(const char * filename)
	{
		// Call the BREP File Load function. Note.. the geometry class 
		// is created and instantiated within the load function
		OCCGeometry * occgeom = LoadOCC_BREP(filename);

		return ((Ng_OCC_Geometry *)occgeom);
	}

	// Save geometry to STEP File
	DLL_HEADER Ng_Result Ng_OCC_Save_STEP(Ng_OCC_Geometry * geom, const char * filename)
	{
		// Call the STEP File Load function. Note.. the geometry class 
		// is created and instantiated within the load function
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		//
		STEPControl_Writer aWriter;
		IFSelect_ReturnStatus aStat = aWriter.Transfer(occgeom->shape, STEPControl_AsIs);
		aStat = aWriter.Write(filename);
		if (aStat != IFSelect_RetDone)
		{
			cout << "Writing error" << endl;
			return(NG_ERROR);
		}
		else
			return(NG_OK);
	}
	
	// Save geometry to BREP File
	DLL_HEADER Ng_Result Ng_OCC_Save_BREP(Ng_OCC_Geometry * geom, const char * filename)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		//
		BRepTools::Write(occgeom->shape, filename, Message_ProgressRange());
		//
		return(NG_OK);
	}

	// Locally limit the size of the mesh to be generated at various points based on the topology of the geometry
	DLL_HEADER Ng_Result Ng_OCC_SetLocalMeshSize(Ng_OCC_Geometry * geom, double deflection, Ng_Mesh * mesh, Ng_Meshing_Parameters * mp)
	{
	  try
	  {
		// Variables
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		Mesh * me = (Mesh*)mesh;
		// Set geometry type
		me->geomtype = Mesh::GEOM_OCC;
		// Load mp to global variable mparam
		mp->Transfer_Parameters();
		//
		occparam.resthcloseedgeenable = mp->closeedgeenable;
		occparam.resthcloseedgefac = mp->closeedgefact;
		// Delete the mesh structures in order to start with a clean slate
		me->DeleteMesh();
		// Build visualization
		occgeom->BuildVisualizationMesh(deflection);
		// Set local mesh size
		OCCSetLocalMeshSize(*occgeom, *me);
		//
		return(NG_OK);
	  }
	  catch (...)
	  {
		return ReportMeshingException("Setting the local mesh size");
	  }
	}

	// Mesh the edges and add Face descriptors to prepare for surface meshing
	DLL_HEADER Ng_Result Ng_OCC_GenerateEdgeMesh(Ng_OCC_Geometry * geom, Ng_Mesh * mesh, Ng_Meshing_Parameters * mp)
	{
	  try
	  {
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		Mesh * me = (Mesh*)mesh;

		mp->Transfer_Parameters();

		OCCFindEdges(*occgeom, *me);

		if ((me->GetNP()) && (me->GetNFD()))
		{
			return NG_OK;
		}
		else
		{
			return NG_ERROR;
		}
	  }
	  catch (...)
	  {
		return ReportMeshingException("Edge meshing");
	  }
	}

	// Mesh the edges and add Face descriptors to prepare for surface meshing
	DLL_HEADER Ng_Result Ng_OCC_GenerateSurfaceMesh(Ng_OCC_Geometry * geom, Ng_Mesh * mesh, Ng_Meshing_Parameters * mp)
	{
		try 
		{
			int numpoints = 0;

			OCCGeometry * occgeom = (OCCGeometry*)geom;
			Mesh * me = (Mesh*)mesh;

			// Set the internal meshing parameters structure from the nglib meshing 
			// parameters structure
			mp->Transfer_Parameters();


			// Only go into surface meshing if the face descriptors have already been added
			if (!me->GetNFD())
				return NG_ERROR;

			numpoints = me->GetNP();

			// Initially set up only for surface meshing without any optimisation
			int perfstepsend = MESHCONST_MESHSURFACE;

			// Check and if required, enable surface mesh optimisation step
			if (mp->optsurfmeshenable)
			{
				perfstepsend = MESHCONST_OPTSURFACE;
			}

			OCCMeshSurface(*occgeom, *me, perfstepsend);

			me->CalcSurfacesOfNode();

			if (me->GetNP() < numpoints)	// Added for support of coarse meshes - cube
				return NG_ERROR;

			if (me->GetNSE() <= 0)
				return NG_ERROR;

			return NG_OK;
		}
		catch (...)
		{
			return ReportMeshingException("Surface meshing");
		}
	}
	// Extract the face map from the OCC geometry
	// The face map basically gives an index to each face in the geometry, 
	// which can be used to access a specific face
	DLL_HEADER Ng_Result Ng_OCC_GetFMap(Ng_OCC_Geometry * geom, Ng_OCC_TopTools_IndexedMapOfShape * FMap)
	{
		OCCGeometry* occgeom = (OCCGeometry*)geom;
		TopTools_IndexedMapOfShape *occfmap = (TopTools_IndexedMapOfShape *)FMap;

		// Copy the face map from the geometry to the given variable
		occfmap->Assign(occgeom->fmap);

		if (occfmap->Extent())
		{
			return NG_OK;
		}
		else
		{
			return NG_ERROR;
		}
	}

	DLL_HEADER Ng_Result Ng_OCC_ExportVisualization(Ng_OCC_Geometry * geom, double deflection, const char* filename)
	{
		return Ng_OCC_ExportVisualization(geom, deflection, true, 0.5, filename);
	}
	
	DLL_HEADER Ng_Result Ng_OCC_ExportVisualization(Ng_OCC_Geometry* geom, double linearDeflection, bool relative, double angularDeflection, const char* filename)
	{
		OCCGeometry* occgeom = (OCCGeometry*)geom;

		//occgeom->RebuildGeometry();

		// Build visualization		
		cout << "Building visualization mesh:" << endl;
		occgeom->BuildVisualizationMesh(linearDeflection, relative, angularDeflection);
		//
		TopLoc_Location aLocation;
		Standard_Integer nId;
		gp_Pnt aPnt1;
		int facenr;
		int edgenr;
		int solidnr = 0;
		int shellnr = 0;
		Standard_Integer N1;
		Standard_Integer N2;
		Standard_Integer N3;
		//
		const string& stringName = filename;
		ofstream outfile(stringName.c_str());
		// How many edges took the expensive node-by-node fallback. Should be 0 for
		// well-formed geometry; anything else is worth looking at.
		int numOfEdges = 0;
		int numOfFallbackEdges = 0;
		// Faces BRepMesh could not triangulate. They are written without any nodes,
		// triangles or edges, so PrePoMax silently ends up with a part full of holes.
		int numOfFacesWithoutTriangulation = 0;
		cout << "Exporting geometry definitions:";
		GeometryMetadataWriter metadataWriter(occgeom, outfile);
		metadataWriter.Write();
		ExportVisualizationVertices(occgeom, outfile);
		cout << " ... done" << endl;
		// Free Solids
		int numOfSolids = occgeom->somap.Extent();
		if (numOfSolids > 0)
		{
			cout << "Exporting solids: " << numOfSolids;
			ExportItemVisualization(occgeom, TopAbs_SOLID, outfile, numOfEdges, numOfFallbackEdges, numOfFacesWithoutTriangulation);
			cout << " ... done" << endl;
		}

		// Free Shells
		int numOfShells = 0;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			numOfShells++;
		}
		if (numOfShells > 0)
		{
			cout << "Exporting shells: " << numOfShells;
			ExportItemVisualization(occgeom, TopAbs_SHELL, outfile, numOfEdges, numOfFallbackEdges, numOfFacesWithoutTriangulation);
			cout << " ... done" << endl;
		}
		// Free Faces
		int numOfFaces = 0;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_FACE, TopAbs_SHELL); exp0.More(); exp0.Next())
		{
			numOfFaces++;
		}
		if (numOfFaces > 0)
		{
			cout << "Exporting free faces: " << numOfFaces;
			ExportItemVisualization(occgeom, TopAbs_FACE, outfile, numOfEdges, numOfFallbackEdges, numOfFacesWithoutTriangulation);
			cout << " ... done" << endl;
		}
		cout << "Edges: " << numOfEdges << " total, " << numOfFallbackEdges
			 << " needed the node-by-node fallback" << endl;
		if (numOfFacesWithoutTriangulation > 0)
			cout << "WARNING: " << numOfFacesWithoutTriangulation
				 << " face(s) could not be triangulated. The geometry is incomplete and most likely invalid." << endl;
		cout << "Closing visualization file.";
		outfile.close();
		cout << " ... done" << endl;
		//
		return(NG_OK);
	}

	DLL_HEADER Ng_Result Ng_OCC_WriteAssemblyAsCompounds(Ng_OCC_Geometry * geom, const char* filename, int numOfSplitFaces, bool closeShells)
	{
		// Call the STEP File Load function. Note.. the geometry class 
		// is created and instantiated within the load function
		//OCCGeometry* occgeom1 = LoadOCC_STEP("C:\\Temp\\PTCmodels\\Test1.stp");
		//TopoDS_Shape top_shape1 = occgeom1->shape;
		//DumpShapeTopology(top_shape1);

		int count = 1;
		OCCGeometry* newoccgeo;
		OCCGeometry* occgeom = (OCCGeometry*)geom;
		TopoDS_Shape top_shape = occgeom->shape;
		// Extract shapes - build a solid from a closed shape
		BRep_Builder builder;
		TopoDS_Compound faceCompound;
		TopoDS_Compound shellCompound;
		TopoDS_Compound solidCompound;
		builder.MakeCompound(faceCompound);
		builder.MakeCompound(shellCompound);
		builder.MakeCompound(solidCompound);
		ExtractBodies(top_shape, builder, faceCompound, shellCompound, solidCompound, closeShells);
		// Solids
		newoccgeo = new OCCGeometry;
		newoccgeo->shape = solidCompound;
		newoccgeo->changed = 1;
		newoccgeo->BuildFMap();
		//newoccgeo->CalcBoundingBox();
		count = WriteAssemblyAsSolidCompounds(newoccgeo, count, filename, numOfSplitFaces);
		// Shells
		newoccgeo = new OCCGeometry;
		newoccgeo->shape = shellCompound;
		newoccgeo->changed = 1;
		newoccgeo->BuildFMap();
		//newoccgeo->CalcBoundingBox();
		count = WriteAssemblyAsShellCompounds(newoccgeo, count, filename, numOfSplitFaces);
		// Free faces
		char shellFileNameWithPath[_MAX_FNAME];
		char full_path[_MAX_PATH];
		char drive[_MAX_DRIVE];
		char dir[_MAX_DIR];
		char fname[_MAX_FNAME];
		char ext[_MAX_EXT];
		//
		_splitpath_s(filename, drive, dir, fname, ext);
		// Export free faces
		int faceNr = count;
		for (TopExp_Explorer exp0(faceCompound, TopAbs_FACE, TopAbs_SHELL); exp0.More(); exp0.Next())
		{
			faceNr++;
			//
			stringstream ss;
			ss << fname << "_face_" << faceNr;
			//
			_makepath_s(shellFileNameWithPath, drive, dir, ss.str().c_str(), ext);
			//
			TopoDS_Face face = TopoDS::Face(exp0.Current());
			//
			//BRepTools::Write(face, shellFileNameWithPath, Message_ProgressRange());
			WriteShapeToBrepFile(face, shellFileNameWithPath, numOfSplitFaces);
		}
		//
		return NG_OK;
	}

	// The whole shape is divided at once, so that a face two solids share is divided in both and they
	// still meet on it. Dividing a solid on its own, which is what writing the parts does, gives each
	// of them a face of its own and a numbering the shape they came from does not have.
	DLL_HEADER Ng_Result Ng_OCC_SaveBrepWithSplitClosedFaces(Ng_OCC_Geometry * geom, const char* filename,
	                                                         int numOfSplitFaces)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			WriteShapeToBrepFile(occgeom->shape, filename, numOfSplitFaces);
			return NG_OK;
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_SaveBrepWithSplitClosedFaces.");
		}
		return NG_ERROR;
	}

	DLL_HEADER int Ng_OCC_WriteAssemblyAsSolidParts(Ng_OCC_Geometry * geom, int countStart, const char* filename, int numOfSplitFaces)
	{
		OCCGeometry * occgeom = (OCCGeometry*)geom;
		// Export
		char solidFileNameWithPath[_MAX_FNAME];
		char full_path[_MAX_PATH];
		char drive[_MAX_DRIVE];
		char dir[_MAX_DIR];
		char fname[_MAX_FNAME];
		char ext[_MAX_EXT];
		//
		_splitpath_s(filename, drive, dir, fname, ext);
		//
		int solidNr = countStart;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			solidNr++;
			//
			stringstream ss;
			//ss << fname << "_solid_" << solidNr;
			ss << fname << "_solid_" << std::setfill('0') << std::setw(4) << solidNr;
			//
			_makepath_s(solidFileNameWithPath, drive, dir, ss.str().c_str(), ext);
			//
			TopoDS_Solid solid = TopoDS::Solid(exp0.Current());
			//
			//BRepTools::Write(solid, solidFileNameWithPath, Message_ProgressRange());
			WriteShapeToBrepFile(solid, solidFileNameWithPath, numOfSplitFaces);
		}
		//
		return solidNr;
	}

	DLL_HEADER int Ng_OCC_WriteAssemblyAsShellParts(Ng_OCC_Geometry * geom, int countStart, const char* filename, int numOfSplitFaces)
	{
		countStart = WriteAssemblyAsShellCompounds((OCCGeometry*)geom, countStart, filename, numOfSplitFaces);
		return countStart;
	}

	DLL_HEADER Ng_Result Ng_OCC_CreateCompoundFromBrep(int argc, char* argv[])
	{
		try
		{
			if (CreateCompoundFromBrep(argc, argv))
				return NG_OK;
			else
			{
				PrintMessage(1, "An error occurred in CreateCompoundFromBrep.");
				return NG_ERROR;
			}
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_CreateCompoundFromBrep.");
		}
	}

	DLL_HEADER Ng_Result Ng_OCC_CreateAssemblyFromBrep(int argc, char* argv[], bool saveAsStep)
	{
		try
		{
			if (CreateAssemblyFromBrep(argc, argv, saveAsStep))
				return NG_OK;
			else
			{
				PrintMessage(1, "An error occurred in CreateAssemblyFromBrep.");
				return NG_ERROR;
			}
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_CreateAssemblyFromBrep.");
			return NG_ERROR;
		}
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_ScaleGeometry(Ng_OCC_Geometry * geom, double Tx, double Ty, double Tz, double sx, double sy, double sz)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			occgeom = ScaleGeometry(occgeom, Tx, Ty, Tz, sx, sy, sz);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_ScaleGeometry.");
		}
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_ReverseFaceOrientations(Ng_OCC_Geometry * geom, int * faceIds, int numOfIds)
	{
		try
		{			
			OCCGeometry * occgeom = ReverseBrepFaceOrientations(geom, faceIds, numOfIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_ReverseFaceOrientations.");
		}
	}
	
	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_SplitAFaceUsingTwoPoints(Ng_OCC_Geometry * geom, int faceId, double x1, double y1, double z1, double x2, double y2, double z2)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			occgeom = SplitAFaceUsingTwoPoints(occgeom, faceId, x1, y1, z1, x2, y2, z2);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_SplitAFaceUsingTwoPoints.");
		}
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_RemoveSolids(Ng_OCC_Geometry * geom, int * solidIds, int numOfSolidIds)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			occgeom = RemoveSolids(occgeom, solidIds, numOfSolidIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_RemoveSolids.");
		}
		return geom;
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_MergeSolids(Ng_OCC_Geometry * geom, int * solidIds, int numOfSolidIds)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			occgeom = MergeSolids(occgeom, solidIds, numOfSolidIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_MergeSolids.");
		}
		return geom;
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_SplitWithPlane(Ng_OCC_Geometry * geom, double * origin, double * normal,
	                                                   double * extent, double fuzzyValue, int * solidIds,
	                                                   int numOfSolidIds, int * targetSolids,
	                                                   int * targetFaceCounts, int numOfTargetGroups,
	                                                   int * targetFaceIds)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			occgeom = SplitWithPlane(occgeom, origin, normal, extent, fuzzyValue, solidIds, numOfSolidIds,
			                         targetSolids, targetFaceCounts, numOfTargetGroups, targetFaceIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_SplitWithPlane.");
		}
		return geom;
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_SplitWithExtendedFace(Ng_OCC_Geometry * geom,
	                                                          Ng_OCC_Geometry ** sourceGeoms, int * faceIdCounts,
	                                                          int numOfSources, int * faceIds, double * extent,
	                                                          double offset, double fuzzyValue, int * solidIds,
	                                                          int numOfSolidIds, int * targetSolids,
	                                                          int * targetFaceCounts, int numOfTargetGroups,
	                                                          int * targetFaceIds)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			OCCGeometry ** sourceoccgeoms = (OCCGeometry**)sourceGeoms;
			occgeom = SplitWithExtendedFace(occgeom, sourceoccgeoms, faceIdCounts, numOfSources, faceIds,
			                               extent, offset, fuzzyValue, solidIds, numOfSolidIds, targetSolids,
			                               targetFaceCounts, numOfTargetGroups, targetFaceIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_SplitWithExtendedFace.");
		}
		return geom;
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_SplitWithExtrudedEdges(Ng_OCC_Geometry * geom,
	                                                           Ng_OCC_Geometry ** sourceGeoms, int * edgeIdCounts,
	                                                           int numOfSources, int * edgeIds, double * offset,
	                                                           double * vector, double fuzzyValue, int * solidIds,
	                                                           int numOfSolidIds, int * targetSolids,
	                                                           int * targetFaceCounts, int numOfTargetGroups,
	                                                           int * targetFaceIds)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			OCCGeometry ** sourceoccgeoms = (OCCGeometry**)sourceGeoms;
			occgeom = SplitWithExtrudedEdges(occgeom, sourceoccgeoms, edgeIdCounts, numOfSources, edgeIds,
			                                offset, vector, fuzzyValue, solidIds, numOfSolidIds, targetSolids,
			                                targetFaceCounts, numOfTargetGroups, targetFaceIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_SplitWithExtrudedEdges.");
		}
		return geom;
	}

	DLL_HEADER Ng_OCC_Geometry * Ng_OCC_SplitWithSurfaceLine(Ng_OCC_Geometry * geom, double * firstPoint,
	                                                         double * secondPoint, double fuzzyValue,
	                                                         int * targetSolids, int * targetFaceCounts,
	                                                         int numOfTargetGroups, int * targetFaceIds)
	{
		try
		{
			OCCGeometry * occgeom = (OCCGeometry*)geom;
			occgeom = SplitWithSurfaceLine(occgeom, firstPoint, secondPoint, fuzzyValue, targetSolids,
			                               targetFaceCounts, numOfTargetGroups, targetFaceIds);
			return ((Ng_OCC_Geometry *)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_SplitWithSurfaceLine.");
		}
		return geom;
	}

	DLL_HEADER Ng_OCC_Geometry* Ng_OCC_ConvertToShell(Ng_OCC_Geometry* geom)
	{
		try
		{
			OCCGeometry* occgeom = (OCCGeometry*)geom;
			//
			BRep_Builder builder;
			TopoDS_Compound shellCompound;
			builder.MakeCompound(shellCompound);
			//
			for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
			{
				for (TopExp_Explorer exp1(exp0.Current(), TopAbs_SHELL); exp1.More(); exp1.Next())
				{
					builder.Add(shellCompound, exp1.Current());
				}
			}
			//
			OCCGeometry* newoccgeo;
			newoccgeo = new OCCGeometry;
			newoccgeo->shape = shellCompound;
			newoccgeo->changed = 1;
			newoccgeo->BuildFMap();
			//
			return ((Ng_OCC_Geometry*)newoccgeo);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_ConvertToShell.");
		}
	}
	
	DLL_HEADER Ng_OCC_Geometry* Ng_OCC_ConvertToSolid(Ng_OCC_Geometry* geom)
	{
		try
		{
			OCCGeometry* occgeom = (OCCGeometry*)geom;
			//
			BRep_Builder builder;
			TopoDS_Shell shell;
			TopoDS_Compound solidCompound;
			builder.MakeCompound(solidCompound);
			//
			for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
			{
				shell = TopoDS::Shell(exp0.Current());
				//
				if (BRep_Tool::IsClosed(shell))
				{
					// Try to convert it into a solid
					TopoDS_Solid solid;
					BRepBuilderAPI_MakeSolid solidMaker;
					solidMaker.Add(shell);
					solid = solidMaker.Solid();
					// Optional: check if the resulting solid is valid
					BRepCheck_Analyzer analyzer(solid);
					if (analyzer.IsValid())
					{
						std::cout << "Successfully built solid from shell." << std::endl;
						// Use or store the solid as needed
						builder.Add(solidCompound, solid);
					}
				}
			}
			//
			OCCGeometry* newoccgeo;
			newoccgeo = new OCCGeometry;
			newoccgeo->shape = solidCompound;
			newoccgeo->changed = 1;
			newoccgeo->BuildFMap();
			//
			return ((Ng_OCC_Geometry*)newoccgeo);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_ConvertToSolid.");
		}
	}


	DLL_HEADER Ng_OCC_Geometry* Ng_OCC_OffsetFaces(Ng_OCC_Geometry* geom, int* targetSolids,
	                                               int* targetFaceCounts, int numOfTargetGroups,
	                                               int* faceIds, double offset)
	{
		try
		{
			OCCGeometry* occgeom = OffsetFaces(geom, targetSolids, targetFaceCounts, numOfTargetGroups,
			                                   faceIds, offset);
			return ((Ng_OCC_Geometry*)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_OffsetFaces.");
		}
		return NULL;
	}

	DLL_HEADER Ng_OCC_Geometry* Ng_OCC_RemoveFaces(Ng_OCC_Geometry* geom, int* targetSolids,
	                                               int* targetFaceCounts, int numOfTargetGroups, int* faceIds,
	                                               int* openedSolids, int maxOpenedSolids, int* numOfOpenedSolids,
	                                               int* removedSolids, int* numOfRemovedSolids)
	{
		try
		{
			OCCGeometry* occgeom = RemoveFaces(geom, targetSolids, targetFaceCounts, numOfTargetGroups, faceIds,
			                                   openedSolids, maxOpenedSolids, numOfOpenedSolids, removedSolids,
			                                   numOfRemovedSolids);
			return ((Ng_OCC_Geometry*)occgeom);
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_RemoveFaces.");
		}
		return NULL;
	}

	DLL_HEADER Ng_OCC_Geometry* Ng_OCC_FuseFaces(Ng_OCC_Geometry* geom, int* targetSolids, int* targetFaceCounts,
	                                             int numOfTargetGroups, int* faceIds)
	{
		try
		{
			OCCGeometry* occgeom = FuseFaces(geom, targetSolids, targetFaceCounts, numOfTargetGroups, faceIds);
			return ((Ng_OCC_Geometry*)occgeom);
		}
		catch (Standard_Failure & ex)
		{
			cout << "Fusing the faces failed: " << ex.GetMessageString() << endl;
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_FuseFaces.");
		}
		return NULL;
	}

	DLL_HEADER Ng_OCC_Geometry* Ng_OCC_RepairShape(Ng_OCC_Geometry* geom, int options, double tolerance)
	{
		try
		{
			OCCGeometry* occgeom = RepairShape(geom, options, tolerance);
			return ((Ng_OCC_Geometry*)occgeom);
		}
		catch (Standard_Failure & ex)
		{
			cout << "Repairing the geometry failed: " << ex.GetMessageString() << endl;
		}
		catch (exception ex)
		{
			PrintMessage(1, "An error occurred in Ng_OCC_RepairShape.");
		}
		return NULL;
	}


	// ------------------ End - OCC Geometry / Meshing Utility Functions ----------------
#endif




   // ------------------ Begin - Meshing Parameters related functions ------------------
   // Constructor for the local nglib meshing parameters class
	DLL_HEADER Ng_Meshing_Parameters::Ng_Meshing_Parameters()
	{
		uselocalh = 1;

		maxh = 1000;
		minh = 0.0;

		fineness = 0.5;
		grading = 0.3;

		elementsperedge = 2.0;
		elementspercurve = 2.0;

		closeedgeenable = 0;
		closeedgefact = 2.0;

		minedgelenenable = 0;
		minedgelen = 1e-4;

		second_order = 0;
		quad_dominated = 0;

		meshsize_filename = 0;

		optsurfmeshenable = 1;
		optvolmeshenable = 1;

		optsteps_2d = 3;
		optsteps_3d = 3;

		invert_tets = 0;
		invert_trigs = 0;

		check_overlap = 1;
		check_overlapping_boundary = 1;
		parallel_meshing_threads = 1;
		transfinite_faces = 0;
		transfinite_angle = 135;
		transfinite_filename = 0;
	}




	// Reset the local meshing parameters to the default values
	DLL_HEADER void Ng_Meshing_Parameters::Reset_Parameters()
	{
		uselocalh = 1;

		maxh = 1000;
		minh = 0;

		fineness = 0.5;
		grading = 0.3;

		elementsperedge = 2.0;
		elementspercurve = 2.0;

		closeedgeenable = 0;
		closeedgefact = 2.0;

		minedgelenenable = 0;
		minedgelen = 1e-4;

		second_order = 0;
		quad_dominated = 0;

		meshsize_filename = 0;

		optsurfmeshenable = 1;
		optvolmeshenable = 1;

		optsteps_2d = 3;
		optsteps_3d = 3;

		invert_tets = 0;
		invert_trigs = 0;

		check_overlap = 1;
		check_overlapping_boundary = 1;
		parallel_meshing_threads = 1;
		transfinite_faces = 0;
		transfinite_angle = 135;
		transfinite_filename = 0;
	}




	// 
	DLL_HEADER void Ng_Meshing_Parameters::Transfer_Parameters()
	{
		mparam.uselocalh = uselocalh;

		mparam.maxh = maxh;
		mparam.minh = minh;

		mparam.grading = grading;
		mparam.curvaturesafety = elementspercurve;
		mparam.segmentsperedge = elementsperedge;

		mparam.secondorder = second_order;
		mparam.quad = quad_dominated;

		mparam.meshsizefilename = meshsize_filename;

		mparam.optsteps2d = optsteps_2d;
		mparam.optsteps3d = optsteps_3d;

		mparam.inverttets = invert_tets;
		mparam.inverttrigs = invert_trigs;

		mparam.checkoverlap = check_overlap;
		mparam.checkoverlappingboundary = check_overlapping_boundary;
		mparam.parallel_meshing_threads = parallel_meshing_threads > 0 ? parallel_meshing_threads : 1;
		mparam.transfinite_faces = transfinite_faces;
		mparam.transfinite_angle = transfinite_angle;
		mparam.transfinite_filename = transfinite_filename ? transfinite_filename : "";
	}
	// ------------------ End - Meshing Parameters related functions --------------------




	// ------------------ Begin - Second Order Mesh generation functions ----------------
	DLL_HEADER void Ng_Generate_SecondOrder(Ng_Mesh * mesh)
	{
		Refinement ref;
		ref.MakeSecondOrder(*(Mesh*)mesh);
	}




	DLL_HEADER void Ng_2D_Generate_SecondOrder(Ng_Geometry_2D * geom,
		Ng_Mesh * mesh)
	{
		((SplineGeometry2d*)geom)->GetRefinement().MakeSecondOrder(*(Mesh*)mesh);
	}




	DLL_HEADER void Ng_STL_Generate_SecondOrder(Ng_STL_Geometry * geom,
		Ng_Mesh * mesh)
	{
		((STLGeometry*)geom)->GetRefinement().MakeSecondOrder(*(Mesh*)mesh);
	}




	DLL_HEADER void Ng_CSG_Generate_SecondOrder(Ng_CSG_Geometry * geom,
		Ng_Mesh * mesh)
	{
		((CSGeometry*)geom)->GetRefinement().MakeSecondOrder(*(Mesh*)mesh);
	}




#ifdef OCCGEOMETRY
	DLL_HEADER void Ng_OCC_Generate_SecondOrder(Ng_OCC_Geometry * geom,
		Ng_Mesh * mesh)
	{
		((OCCGeometry*)geom)->GetRefinement().MakeSecondOrder(*(Mesh*)mesh);
	}
#endif
	// ------------------ End - Second Order Mesh generation functions ------------------




	// ------------------ Begin - Uniform Mesh Refinement functions ---------------------
	DLL_HEADER void Ng_Uniform_Refinement(Ng_Mesh * mesh)
	{
		Refinement ref;
		ref.Refine(*(Mesh*)mesh);
	}




	DLL_HEADER void Ng_2D_Uniform_Refinement(Ng_Geometry_2D * geom,
		Ng_Mesh * mesh)
	{
		((SplineGeometry2d*)geom)->GetRefinement().Refine(*(Mesh*)mesh);
	}




	DLL_HEADER void Ng_STL_Uniform_Refinement(Ng_STL_Geometry * geom,
		Ng_Mesh * mesh)
	{
		((STLGeometry*)geom)->GetRefinement().Refine(*(Mesh*)mesh);
	}




	DLL_HEADER void Ng_CSG_Uniform_Refinement(Ng_CSG_Geometry * geom,
		Ng_Mesh * mesh)
	{
		((CSGeometry*)geom)->GetRefinement().Refine(*(Mesh*)mesh);
	}




#ifdef OCCGEOMETRY
	DLL_HEADER void Ng_OCC_Uniform_Refinement(Ng_OCC_Geometry * geom,
		Ng_Mesh * mesh)
	{
		((OCCGeometry*)geom)->GetRefinement().Refine(*(Mesh*)mesh);
	}
#endif
	// ------------------ End - Uniform Mesh Refinement functions -----------------------
} // End of namespace nglib




// compatibility functions:
namespace netgen
{
	char geomfilename[255];

	DLL_HEADER void MyError(const char * ch)
	{
		cerr << ch;
	}




	//Destination for messages, errors, ...
	DLL_HEADER void Ng_PrintDest(const char * s)
	{
#ifdef PARALLEL
		int id = 0;
		MPI_Comm_rank(MPI_COMM_WORLD, &id);
		if (id != 0) return;
#endif
		(*mycout) << s << flush;
	}




	DLL_HEADER double GetTime()
	{
		return 0;
	}




	void ResetTime()
	{
		;
	}




	void MyBeep(int i)
	{
		;
	}




	void Render()
	{
		;
	}
} // End of namespace netgen




void Ng_Redraw() { ; }
void Ng_ClearSolutionData() { ; }
void Ng_SetSolutionData(Ng_SolutionData * soldata)
{
	delete soldata->solclass;
}
void Ng_InitSolutionData(Ng_SolutionData * soldata) { ; }


