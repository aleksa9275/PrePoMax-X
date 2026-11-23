
#ifdef OCCGEOMETRY

#include <mystdlib.h>
#include <occgeom.hpp>
#include "ShapeAnalysis_ShapeTolerance.hxx"
#include "ShapeAnalysis_ShapeContents.hxx"
#include "ShapeAnalysis_CheckSmallFace.hxx"
#include "ShapeAnalysis_DataMapOfShapeListOfReal.hxx"
#include "ShapeAnalysis_Surface.hxx"

#include "BRepCheck_Analyzer.hxx"
#include "BRepLib.hxx"
#include "ShapeBuild_ReShape.hxx"
#include "ShapeFix.hxx"
#include "ShapeFix_Edge.hxx"
#include "ShapeFix_FixSmallFace.hxx"
#include "TopoDS_Iterator.hxx"
#include "Partition_Spliter.hxx"
#include "GeomProjLib.hxx"
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepGProp_Face.hxx>
#include <BRepAlgo_NormalProjection.hxx>
#include <BRepMesh_Context.hxx>
#include <BRepMesh_EdgeDiscret.hxx>
#include <IMeshData_Edge.hxx>
#include <IMeshData_Model.hxx>
#include <IMeshData_PCurve.hxx>
#include <IMeshTools_CurveTessellator.hxx>
#include <IMeshTools_ModelAlgo.hxx>
#include <TopTools_DataMapOfShapeReal.hxx>

#include <TCollection_ExtendedString.hxx>
//By Maxx
#include <BOPAlgo_Builder.hxx>
#include <BOPTools_AlgoTools.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepBuilderAPI_GTransform.hxx>
#include <BRep_Builder.hxx>
#include <TopoDS_Compound.hxx>
#include <BRepAlgoAPI_Splitter.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <Geom_Plane.hxx>
#include <Geom_CylindricalSurface.hxx>
#include <Geom_ConicalSurface.hxx>
#include <GeomAdaptor_Surface.hxx>
#include <Geom_SphericalSurface.hxx>
#include <Geom_ToroidalSurface.hxx>
#include <TopTools_ListOfShape.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <Geom2d_Line.hxx>
#include <BRepTools.hxx>
#include <TopExp.hxx>
#include <Precision.hxx>
#include <ShapeUpgrade_UnifySameDomain.hxx>
#include <TopTools_IndexedDataMapOfShapeListOfShape.hxx>
#include <TopTools_MapOfShape.hxx>
#include <algorithm>


namespace netgen
{
	const char * shapesname[] = { " ", "CompSolids", "Solids", "Shells", "Faces", "Wires", "Edges", "Vertices" };
	const char * shapename[] = { " ", "CompSolid", "Solid", "Shell","Face", "Wire", "Edge", "Vertex" };
	const char * orientationstring[] = { "+", "-" };

	OCCParameters occparam;


	void OCCGeometry::PrintNrShapes()
	{
		TopExp_Explorer e;
		int count = 0;
		for (e.Init(shape, TopAbs_COMPSOLID); e.More(); e.Next()) count++;
		cout << "CompSolids: " << count << endl;

		cout << "Solids    : " << somap.Extent() << endl;
		cout << "Shells    : " << shmap.Extent() << endl;
		cout << "Faces     : " << fmap.Extent() << endl;
		cout << "Edges     : " << emap.Extent() << endl;
		cout << "Vertices  : " << vmap.Extent() << endl;
	}

	void PrintContents(OCCGeometry * geom)
	{
		ShapeAnalysis_ShapeContents cont;
		cont.Clear();
		cont.Perform(geom->shape);

		(*testout) << "OCC CONTENTS" << endl;
		(*testout) << "============" << endl;
		(*testout) << "SOLIDS   : " << cont.NbSolids() << endl;
		(*testout) << "SHELLS   : " << cont.NbShells() << endl;
		(*testout) << "FACES    : " << cont.NbFaces() << endl;
		(*testout) << "WIRES    : " << cont.NbWires() << endl;
		(*testout) << "EDGES    : " << cont.NbEdges() << endl;
		(*testout) << "VERTICES : " << cont.NbVertices() << endl;

		TopExp_Explorer e;
		int count = 0;
		for (e.Init(geom->shape, TopAbs_COMPOUND); e.More(); e.Next())
			count++;
		(*testout) << "Compounds: " << count << endl;

		count = 0;
		for (e.Init(geom->shape, TopAbs_COMPSOLID); e.More(); e.Next())
			count++;
		(*testout) << "CompSolids: " << count << endl;

		(*testout) << endl;

		cout << "Highest entry in topology hierarchy: " << endl;
		if (count)
			cout << count << " composite solid(s)" << endl;
		else
			if (geom->somap.Extent())
				cout << geom->somap.Extent() << " solid(s)" << endl;
			else
				if (geom->shmap.Extent())
					cout << geom->shmap.Extent() << " shells(s)" << endl;
				else
					if (geom->fmap.Extent())
						cout << geom->fmap.Extent() << " face(s)" << endl;
					else
						if (geom->wmap.Extent())
							cout << geom->wmap.Extent() << " wire(s)" << endl;
						else
							if (geom->emap.Extent())
								cout << geom->emap.Extent() << " edge(s)" << endl;
							else
								if (geom->vmap.Extent())
									cout << geom->vmap.Extent() << " vertices(s)" << endl;
								else
									cout << "no entities" << endl;

	}


	void OCCGeometry::HealGeometry()
	{
		int nrc = 0, nrcs = 0,
			nrso = somap.Extent(),
			nrsh = shmap.Extent(),
			nrf = fmap.Extent(),
			nrw = wmap.Extent(),
			nre = emap.Extent(),
			nrv = vmap.Extent();

		TopExp_Explorer exp0;
		TopExp_Explorer exp1;


		for (exp0.Init(shape, TopAbs_COMPOUND); exp0.More(); exp0.Next()) nrc++;
		for (exp0.Init(shape, TopAbs_COMPSOLID); exp0.More(); exp0.Next()) nrcs++;

		double surfacecont = 0;

		{
			Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
			rebuild->Apply(shape);
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					rebuild->Remove(edge);
			}
			shape = rebuild->Apply(shape);
		}

		BuildFMap();


		for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			TopoDS_Face face = TopoDS::Face(exp0.Current());

			GProp_GProps system;
			BRepGProp::SurfaceProperties(face, system);
			surfacecont += system.Mass();
		}


		cout << "Starting geometry healing procedure (tolerance: " << tolerance << ")" << endl
			<< "-----------------------------------" << endl;

		{
			cout << endl << "- repairing faces" << endl;

			Handle(ShapeFix_Face) sff;
			Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
			rebuild->Apply(shape);


			for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
			{
				// Variable to hold the colour (if there exists one) of 
				// the current face being processed
				Quantity_Color face_colour;

				TopoDS_Face face = TopoDS::Face(exp0.Current());

				if (face_colours.IsNull()
					|| (!(face_colours->GetColor(face, XCAFDoc_ColorSurf, face_colour))))
				{
					// Set the default face colour to green (Netgen Standard)
					// if no colour has been defined for the face
					face_colour = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB);
				}

				sff = new ShapeFix_Face(face);
				sff->FixAddNaturalBoundMode() = Standard_True;
				sff->FixSmallAreaWireMode() = Standard_True;
				sff->Perform();

				if (sff->Status(ShapeExtend_DONE1) ||
					sff->Status(ShapeExtend_DONE2) ||
					sff->Status(ShapeExtend_DONE3) ||
					sff->Status(ShapeExtend_DONE4) ||
					sff->Status(ShapeExtend_DONE5))
				{
					cout << "repaired face " << fmap.FindIndex(face) << " ";
					if (sff->Status(ShapeExtend_DONE1))
						cout << "(some wires are fixed)" << endl;
					else if (sff->Status(ShapeExtend_DONE2))
						cout << "(orientation of wires fixed)" << endl;
					else if (sff->Status(ShapeExtend_DONE3))
						cout << "(missing seam added)" << endl;
					else if (sff->Status(ShapeExtend_DONE4))
						cout << "(small area wire removed)" << endl;
					else if (sff->Status(ShapeExtend_DONE5))
						cout << "(natural bounds added)" << endl;
					TopoDS_Face newface = sff->Face();

					rebuild->Replace(face, newface);
				}

				// Set the original colour of the face to the newly created 
				// face (after the healing process)
				face = TopoDS::Face(exp0.Current());
				if (!face_colours.IsNull())
					face_colours->SetColor(face, face_colour, XCAFDoc_ColorSurf);
			}
			shape = rebuild->Apply(shape);
		}


		{
			Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
			rebuild->Apply(shape);
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					rebuild->Remove(edge);
			}
			shape = rebuild->Apply(shape);
		}


		if (fixsmalledges)
		{
			cout << endl << "- fixing small edges" << endl;

			Handle(ShapeFix_Wire) sfw;
			Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
			rebuild->Apply(shape);


			for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp0.Current());

				for (exp1.Init(face, TopAbs_WIRE); exp1.More(); exp1.Next())
				{
					TopoDS_Wire oldwire = TopoDS::Wire(exp1.Current());
					sfw = new ShapeFix_Wire(oldwire, face, tolerance);
					sfw->ModifyTopologyMode() = Standard_True;

					sfw->ClosedWireMode() = Standard_True;

					bool replace = false;

					replace = sfw->FixReorder() || replace;

					replace = sfw->FixConnected() || replace;



					if (sfw->FixSmall(Standard_False, tolerance) && !(sfw->StatusSmall(ShapeExtend_FAIL1) ||
						sfw->StatusSmall(ShapeExtend_FAIL2) ||
						sfw->StatusSmall(ShapeExtend_FAIL3)))
					{
						cout << "Fixed small edge in wire " << wmap.FindIndex(oldwire) << endl;
						replace = true;

					}
					else if (sfw->StatusSmall(ShapeExtend_FAIL1))
						cerr << "Failed to fix small edge in wire " << wmap.FindIndex(oldwire)
						<< ", edge cannot be checked (no 3d curve and no pcurve)" << endl;
					else if (sfw->StatusSmall(ShapeExtend_FAIL2))
						cerr << "Failed to fix small edge in wire " << wmap.FindIndex(oldwire)
						<< ", edge is null-length and has different vertives at begin and end, and lockvtx is True or ModifiyTopologyMode is False" << endl;
					else if (sfw->StatusSmall(ShapeExtend_FAIL3))
						cerr << "Failed to fix small edge in wire " << wmap.FindIndex(oldwire)
						<< ", CheckConnected has failed" << endl;

					replace = sfw->FixEdgeCurves() || replace;

					replace = sfw->FixDegenerated() || replace;

					replace = sfw->FixSelfIntersection() || replace;

					replace = sfw->FixLacking(Standard_True) || replace;

					if (replace)
					{
						TopoDS_Wire newwire = sfw->Wire();
						rebuild->Replace(oldwire, newwire);
					}

					//delete sfw; sfw = NULL;

				}
			}

			shape = rebuild->Apply(shape);



			{
				BuildFMap();
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);

				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (vmap.FindIndex(TopExp::FirstVertex(edge)) ==
						vmap.FindIndex(TopExp::LastVertex(edge)))
					{
						GProp_GProps system;
						BRepGProp::LinearProperties(edge, system);
						if (system.Mass() < tolerance)
						{
							cout << "removing degenerated edge " << emap.FindIndex(edge)
								<< " from vertex " << vmap.FindIndex(TopExp::FirstVertex(edge))
								<< " to vertex " << vmap.FindIndex(TopExp::LastVertex(edge)) << endl;
							rebuild->Remove(edge);
						}
					}
				}
				shape = rebuild->Apply(shape);

				//delete rebuild; rebuild = NULL;
			}



			{
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						rebuild->Remove(edge);
				}
				shape = rebuild->Apply(shape);
			}




			Handle(ShapeFix_Wireframe) sfwf = new ShapeFix_Wireframe;
			sfwf->SetPrecision(tolerance);
			sfwf->Load(shape);
			sfwf->ModeDropSmallEdges() = Standard_True;

			sfwf->SetPrecision(boundingbox.Diam());

			if (sfwf->FixWireGaps())
			{
				cout << endl << "- fixing wire gaps" << endl;
				if (sfwf->StatusWireGaps(ShapeExtend_OK)) cout << "no gaps found" << endl;
				if (sfwf->StatusWireGaps(ShapeExtend_DONE1)) cout << "some 2D gaps fixed" << endl;
				if (sfwf->StatusWireGaps(ShapeExtend_DONE2)) cout << "some 3D gaps fixed" << endl;
				if (sfwf->StatusWireGaps(ShapeExtend_FAIL1)) cout << "failed to fix some 2D gaps" << endl;
				if (sfwf->StatusWireGaps(ShapeExtend_FAIL2)) cout << "failed to fix some 3D gaps" << endl;
			}

			sfwf->SetPrecision(tolerance);


			{
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						cout << "degenerated edge at position 4" << endl;
				}
			}



			if (sfwf->FixSmallEdges())
			{
				cout << endl << "- fixing wire frames" << endl;
				if (sfwf->StatusSmallEdges(ShapeExtend_OK)) cout << "no small edges found" << endl;
				if (sfwf->StatusSmallEdges(ShapeExtend_DONE1)) cout << "some small edges fixed" << endl;
				if (sfwf->StatusSmallEdges(ShapeExtend_FAIL1)) cout << "failed to fix some small edges" << endl;
			}



			shape = sfwf->Shape();

			//delete sfwf; sfwf = NULL;
			//delete rebuild; rebuild = NULL;

		}





		{
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					cout << "degenerated edge at position 5" << endl;
			}
		}




		if (fixspotstripfaces)
		{

			cout << endl << "- fixing spot and strip faces" << endl;
			Handle(ShapeFix_FixSmallFace) sffsm = new ShapeFix_FixSmallFace();
			sffsm->Init(shape);
			sffsm->SetPrecision(tolerance);
			sffsm->Perform();

			shape = sffsm->FixShape();
			//delete sffsm; sffsm = NULL;
		}


		{
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					cout << "degenerated edge at position 6" << endl;
			}
		}



		if (sewfaces)
		{
			cout << endl << "- sewing faces" << endl;

			BRepOffsetAPI_Sewing sewedObj(tolerance);

			for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp0.Current());
				sewedObj.Add(face);
			}

			sewedObj.Perform();

			if (!sewedObj.SewedShape().IsNull())
				shape = sewedObj.SewedShape();
			else
				cout << " not possible";
		}



		{
			Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
			rebuild->Apply(shape);
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					rebuild->Remove(edge);
			}
			shape = rebuild->Apply(shape);
		}


		if (makesolids)
		{
			cout << endl << "- making solids" << endl;

			BRepBuilderAPI_MakeSolid ms;
			int count = 0;
			for (exp0.Init(shape, TopAbs_SHELL); exp0.More(); exp0.Next())
			{
				count++;
				ms.Add(TopoDS::Shell(exp0.Current()));
			}

			if (!count)
			{
				cout << " not possible (no shells)" << endl;
			}
			else
			{
				BRepCheck_Analyzer ba(ms);
				if (ba.IsValid())
				{
					Handle(ShapeFix_Shape) sfs = new ShapeFix_Shape;
					sfs->Init(ms);
					sfs->SetPrecision(tolerance);
					sfs->SetMaxTolerance(tolerance);
					sfs->Perform();
					shape = sfs->Shape();

					for (exp0.Init(shape, TopAbs_SOLID); exp0.More(); exp0.Next())
					{
						TopoDS_Solid solid = TopoDS::Solid(exp0.Current());
						TopoDS_Solid newsolid = solid;
						BRepLib::OrientClosedSolid(newsolid);
						Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
						//		  rebuild->Apply(shape);
						rebuild->Replace(solid, newsolid);
						TopoDS_Shape newshape = rebuild->Apply(shape, TopAbs_COMPSOLID);//, 1);
						//		  TopoDS_Shape newshape = rebuild->Apply(shape);
						shape = newshape;
					}

					//delete sfs; sfs = NULL;
				}
				else
					cout << " not possible" << endl;
			}
		}



		if (splitpartitions)
		{
			cout << "- running SALOME partition splitter" << endl;

			TopExp_Explorer e2;
			Partition_Spliter ps;
			int count = 0;

			for (e2.Init(shape, TopAbs_SOLID);
				e2.More(); e2.Next())
			{
				count++;
				ps.AddShape(e2.Current());
			}

			ps.Compute();
			shape = ps.Shape();

			cout << " before: " << count << " solids" << endl;

			count = 0;
			for (e2.Init(shape, TopAbs_SOLID);
				e2.More(); e2.Next()) count++;

			cout << " after : " << count << " solids" << endl;
		}

		BuildFMap();



		{
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					cout << "degenerated edge at position 8" << endl;
			}
		}


		double newsurfacecont = 0;


		for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			TopoDS_Face face = TopoDS::Face(exp0.Current());
			GProp_GProps system;
			BRepGProp::SurfaceProperties(face, system);
			newsurfacecont += system.Mass();
		}


		int nnrc = 0, nnrcs = 0,
			nnrso = somap.Extent(),
			nnrsh = shmap.Extent(),
			nnrf = fmap.Extent(),
			nnrw = wmap.Extent(),
			nnre = emap.Extent(),
			nnrv = vmap.Extent();

		for (exp0.Init(shape, TopAbs_COMPOUND); exp0.More(); exp0.Next()) nnrc++;
		for (exp0.Init(shape, TopAbs_COMPSOLID); exp0.More(); exp0.Next()) nnrcs++;

		cout << "-----------------------------------" << endl;
		cout << "Compounds       : " << nnrc << " (" << nrc << ")" << endl;
		cout << "Composite solids: " << nnrcs << " (" << nrcs << ")" << endl;
		cout << "Solids          : " << nnrso << " (" << nrso << ")" << endl;
		cout << "Shells          : " << nnrsh << " (" << nrsh << ")" << endl;
		cout << "Wires           : " << nnrw << " (" << nrw << ")" << endl;
		cout << "Faces           : " << nnrf << " (" << nrf << ")" << endl;
		cout << "Edges           : " << nnre << " (" << nre << ")" << endl;
		cout << "Vertices        : " << nnrv << " (" << nrv << ")" << endl;
		cout << endl;
		cout << "Totol surface area : " << newsurfacecont << " (" << surfacecont << ")" << endl;
		cout << endl;
	}

	// This is a copy of Heal Geometry for testing
	void OCCGeometry::RebuildGeometry()
	{
		int nrc = 0,
			nrcs = 0,
			nrso = somap.Extent(),
			nrsh = shmap.Extent(),
			nrf = fmap.Extent(),
			nrw = wmap.Extent(),
			nre = emap.Extent(),
			nrv = vmap.Extent();

		TopExp_Explorer exp0;
		TopExp_Explorer exp1;


		for (exp0.Init(shape, TopAbs_COMPOUND); exp0.More(); exp0.Next()) nrc++;
		for (exp0.Init(shape, TopAbs_COMPSOLID); exp0.More(); exp0.Next()) nrcs++;

		double surfacecont = 0;



		if (false)
		{
			{
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						rebuild->Remove(edge);
				}
				shape = rebuild->Apply(shape);
			}

			BuildFMap();


			for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp0.Current());

				GProp_GProps system;
				BRepGProp::SurfaceProperties(face, system);
				surfacecont += system.Mass();
			}

			cout << "Starting geometry healing procedure (tolerance: " << tolerance << ")" << endl
				<< "-----------------------------------" << endl;

			{
				cout << endl << "- repairing faces" << endl;

				Handle(ShapeFix_Face) sff;
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);


				for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
				{
					// Variable to hold the colour (if there exists one) of 
					// the current face being processed
					Quantity_Color face_colour;

					TopoDS_Face face = TopoDS::Face(exp0.Current());

					if (face_colours.IsNull()
						|| (!(face_colours->GetColor(face, XCAFDoc_ColorSurf, face_colour))))
					{
						// Set the default face colour to green (Netgen Standard)
						// if no colour has been defined for the face
						face_colour = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB);
					}

					sff = new ShapeFix_Face(face);
					sff->FixAddNaturalBoundMode() = Standard_True;
					sff->FixSmallAreaWireMode() = Standard_True;
					sff->Perform();

					if (sff->Status(ShapeExtend_DONE1) ||
						sff->Status(ShapeExtend_DONE2) ||
						sff->Status(ShapeExtend_DONE3) ||
						sff->Status(ShapeExtend_DONE4) ||
						sff->Status(ShapeExtend_DONE5))
					{
						cout << "repaired face " << fmap.FindIndex(face) << " ";
						if (sff->Status(ShapeExtend_DONE1))
							cout << "(some wires are fixed)" << endl;
						else if (sff->Status(ShapeExtend_DONE2))
							cout << "(orientation of wires fixed)" << endl;
						else if (sff->Status(ShapeExtend_DONE3))
							cout << "(missing seam added)" << endl;
						else if (sff->Status(ShapeExtend_DONE4))
							cout << "(small area wire removed)" << endl;
						else if (sff->Status(ShapeExtend_DONE5))
							cout << "(natural bounds added)" << endl;
						TopoDS_Face newface = sff->Face();

						rebuild->Replace(face, newface);
					}

					// Set the original colour of the face to the newly created 
					// face (after the healing process)
					face = TopoDS::Face(exp0.Current());
					if (!face_colours.IsNull())
						face_colours->SetColor(face, face_colour, XCAFDoc_ColorSurf);
				}
				shape = rebuild->Apply(shape);
			}


			{
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						rebuild->Remove(edge);
				}
				shape = rebuild->Apply(shape);
			}


			if (fixsmalledges)
			{
				cout << endl << "- fixing small edges" << endl;

				Handle(ShapeFix_Wire) sfw;
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);


				for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
				{
					TopoDS_Face face = TopoDS::Face(exp0.Current());

					for (exp1.Init(face, TopAbs_WIRE); exp1.More(); exp1.Next())
					{
						TopoDS_Wire oldwire = TopoDS::Wire(exp1.Current());
						sfw = new ShapeFix_Wire(oldwire, face, tolerance);
						sfw->ModifyTopologyMode() = Standard_True;

						sfw->ClosedWireMode() = Standard_True;

						bool replace = false;

						replace = sfw->FixReorder() || replace;

						replace = sfw->FixConnected() || replace;



						if (sfw->FixSmall(Standard_False, tolerance) && !(sfw->StatusSmall(ShapeExtend_FAIL1) ||
							sfw->StatusSmall(ShapeExtend_FAIL2) ||
							sfw->StatusSmall(ShapeExtend_FAIL3)))
						{
							cout << "Fixed small edge in wire " << wmap.FindIndex(oldwire) << endl;
							replace = true;

						}
						else if (sfw->StatusSmall(ShapeExtend_FAIL1))
							cerr << "Failed to fix small edge in wire " << wmap.FindIndex(oldwire)
							<< ", edge cannot be checked (no 3d curve and no pcurve)" << endl;
						else if (sfw->StatusSmall(ShapeExtend_FAIL2))
							cerr << "Failed to fix small edge in wire " << wmap.FindIndex(oldwire)
							<< ", edge is null-length and has different vertives at begin and end, and lockvtx is True or ModifiyTopologyMode is False" << endl;
						else if (sfw->StatusSmall(ShapeExtend_FAIL3))
							cerr << "Failed to fix small edge in wire " << wmap.FindIndex(oldwire)
							<< ", CheckConnected has failed" << endl;

						replace = sfw->FixEdgeCurves() || replace;

						replace = sfw->FixDegenerated() || replace;

						replace = sfw->FixSelfIntersection() || replace;

						replace = sfw->FixLacking(Standard_True) || replace;

						if (replace)
						{
							TopoDS_Wire newwire = sfw->Wire();
							rebuild->Replace(oldwire, newwire);
						}

						//delete sfw; sfw = NULL;

					}
				}

				shape = rebuild->Apply(shape);



				{
					BuildFMap();
					Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
					rebuild->Apply(shape);

					for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
					{
						TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
						if (vmap.FindIndex(TopExp::FirstVertex(edge)) ==
							vmap.FindIndex(TopExp::LastVertex(edge)))
						{
							GProp_GProps system;
							BRepGProp::LinearProperties(edge, system);
							if (system.Mass() < tolerance)
							{
								cout << "removing degenerated edge " << emap.FindIndex(edge)
									<< " from vertex " << vmap.FindIndex(TopExp::FirstVertex(edge))
									<< " to vertex " << vmap.FindIndex(TopExp::LastVertex(edge)) << endl;
								rebuild->Remove(edge);
							}
						}
					}
					shape = rebuild->Apply(shape);

					//delete rebuild; rebuild = NULL;
				}



				{
					Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
					rebuild->Apply(shape);
					for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
					{
						TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
						if (BRep_Tool::Degenerated(edge))
							rebuild->Remove(edge);
					}
					shape = rebuild->Apply(shape);
				}




				Handle(ShapeFix_Wireframe) sfwf = new ShapeFix_Wireframe;
				sfwf->SetPrecision(tolerance);
				sfwf->Load(shape);
				sfwf->ModeDropSmallEdges() = Standard_True;

				sfwf->SetPrecision(boundingbox.Diam());

				if (sfwf->FixWireGaps())
				{
					cout << endl << "- fixing wire gaps" << endl;
					if (sfwf->StatusWireGaps(ShapeExtend_OK)) cout << "no gaps found" << endl;
					if (sfwf->StatusWireGaps(ShapeExtend_DONE1)) cout << "some 2D gaps fixed" << endl;
					if (sfwf->StatusWireGaps(ShapeExtend_DONE2)) cout << "some 3D gaps fixed" << endl;
					if (sfwf->StatusWireGaps(ShapeExtend_FAIL1)) cout << "failed to fix some 2D gaps" << endl;
					if (sfwf->StatusWireGaps(ShapeExtend_FAIL2)) cout << "failed to fix some 3D gaps" << endl;
				}

				sfwf->SetPrecision(tolerance);


				{
					for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
					{
						TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
						if (BRep_Tool::Degenerated(edge))
							cout << "degenerated edge at position 4" << endl;
					}
				}



				if (sfwf->FixSmallEdges())
				{
					cout << endl << "- fixing wire frames" << endl;
					if (sfwf->StatusSmallEdges(ShapeExtend_OK)) cout << "no small edges found" << endl;
					if (sfwf->StatusSmallEdges(ShapeExtend_DONE1)) cout << "some small edges fixed" << endl;
					if (sfwf->StatusSmallEdges(ShapeExtend_FAIL1)) cout << "failed to fix some small edges" << endl;
				}



				shape = sfwf->Shape();

				//delete sfwf; sfwf = NULL;
				//delete rebuild; rebuild = NULL;

			}





			{
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						cout << "degenerated edge at position 5" << endl;
				}
			}




			if (fixspotstripfaces)
			{

				cout << endl << "- fixing spot and strip faces" << endl;
				Handle(ShapeFix_FixSmallFace) sffsm = new ShapeFix_FixSmallFace();
				sffsm->Init(shape);
				sffsm->SetPrecision(tolerance);
				sffsm->Perform();

				shape = sffsm->FixShape();
				//delete sffsm; sffsm = NULL;
			}


			{
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						cout << "degenerated edge at position 6" << endl;
				}
			}



			if (sewfaces)
			{
				cout << endl << "- sewing faces" << endl;

				BRepOffsetAPI_Sewing sewedObj(tolerance);

				for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
				{
					TopoDS_Face face = TopoDS::Face(exp0.Current());
					sewedObj.Add(face);
				}

				sewedObj.Perform();

				if (!sewedObj.SewedShape().IsNull())
					shape = sewedObj.SewedShape();
				else
					cout << " not possible";
			}



			{
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Apply(shape);
				for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
					if (BRep_Tool::Degenerated(edge))
						rebuild->Remove(edge);
				}
				shape = rebuild->Apply(shape);
			}


			if (makesolids)
			{
				cout << endl << "- making solids" << endl;

				BRepBuilderAPI_MakeSolid ms;
				int count = 0;
				for (exp0.Init(shape, TopAbs_SHELL); exp0.More(); exp0.Next())
				{
					count++;
					ms.Add(TopoDS::Shell(exp0.Current()));
				}

				if (!count)
				{
					cout << " not possible (no shells)" << endl;
				}
				else
				{
					BRepCheck_Analyzer ba(ms);
					if (ba.IsValid())
					{
						Handle(ShapeFix_Shape) sfs = new ShapeFix_Shape;
						sfs->Init(ms);
						sfs->SetPrecision(tolerance);
						sfs->SetMaxTolerance(tolerance);
						sfs->Perform();
						shape = sfs->Shape();

						for (exp0.Init(shape, TopAbs_SOLID); exp0.More(); exp0.Next())
						{
							TopoDS_Solid solid = TopoDS::Solid(exp0.Current());
							TopoDS_Solid newsolid = solid;
							BRepLib::OrientClosedSolid(newsolid);
							Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
							//		  rebuild->Apply(shape);
							rebuild->Replace(solid, newsolid);
							TopoDS_Shape newshape = rebuild->Apply(shape, TopAbs_COMPSOLID);//, 1);
							//		  TopoDS_Shape newshape = rebuild->Apply(shape);
							shape = newshape;
						}

						//delete sfs; sfs = NULL;
					}
					else
						cout << " not possible" << endl;
				}
			}

		}

		if (splitpartitions)
		{
			cout << "- running SALOME partition splitter" << endl;

			TopExp_Explorer e2;
			Partition_Spliter ps;
			int count = 0;

			for (e2.Init(shape, TopAbs_SOLID);
				e2.More(); e2.Next())
			{
				count++;
				ps.AddShape(e2.Current());
			}

			ps.Compute();
			shape = ps.Shape();

			cout << " before: " << count << " solids" << endl;

			count = 0;
			for (e2.Init(shape, TopAbs_SOLID);
				e2.More(); e2.Next()) count++;

			cout << " after : " << count << " solids" << endl;
		}

		BuildFMap();
		return;


		{
			for (exp1.Init(shape, TopAbs_EDGE); exp1.More(); exp1.Next())
			{
				TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
				if (BRep_Tool::Degenerated(edge))
					cout << "degenerated edge at position 8" << endl;
			}
		}


		double newsurfacecont = 0;


		for (exp0.Init(shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			TopoDS_Face face = TopoDS::Face(exp0.Current());
			GProp_GProps system;
			BRepGProp::SurfaceProperties(face, system);
			newsurfacecont += system.Mass();
		}


		int nnrc = 0, nnrcs = 0,
			nnrso = somap.Extent(),
			nnrsh = shmap.Extent(),
			nnrf = fmap.Extent(),
			nnrw = wmap.Extent(),
			nnre = emap.Extent(),
			nnrv = vmap.Extent();

		for (exp0.Init(shape, TopAbs_COMPOUND); exp0.More(); exp0.Next()) nnrc++;
		for (exp0.Init(shape, TopAbs_COMPSOLID); exp0.More(); exp0.Next()) nnrcs++;

		cout << "-----------------------------------" << endl;
		cout << "Compounds       : " << nnrc << " (" << nrc << ")" << endl;
		cout << "Composite solids: " << nnrcs << " (" << nrcs << ")" << endl;
		cout << "Solids          : " << nnrso << " (" << nrso << ")" << endl;
		cout << "Shells          : " << nnrsh << " (" << nrsh << ")" << endl;
		cout << "Wires           : " << nnrw << " (" << nrw << ")" << endl;
		cout << "Faces           : " << nnrf << " (" << nrf << ")" << endl;
		cout << "Edges           : " << nnre << " (" << nre << ")" << endl;
		cout << "Vertices        : " << nnrv << " (" << nrv << ")" << endl;
		cout << endl;
		cout << "Totol surface area : " << newsurfacecont << " (" << surfacecont << ")" << endl;
		cout << endl;
	}


	bool CreateCompoundFromBrep(int argc, char* argv[])
	{
		// argv[0]		...	exe					
		// argv[1]		...	function			
		// argv[2]		...	input brep file name
		// argv[3]		...	input brep file name
		// ...									
		// argv[n-1]	...	input brep file name
		// argv[n]		...	output file name	
		//
		//https://www.opencascade.com/content/partition-operation-done-programatically
		//
		BOPAlgo_Builder aBuilder;
		// The general fuse is single threaded by default and its cost grows sharply with the
		// number of arguments, so it is run in parallel - the resulting shape is the same
		aBuilder.SetRunParallel(Standard_True);
		OCCGeometry * occgeom;
		int numOfFiles = argc - 3;
		//
		for (int i = 0; i < numOfFiles; i++)
		{
			occgeom = LoadOCC_BREP(argv[i + 2]);
			if (!occgeom)
			{
				//occgeom->HealGeometry();
				stringstream ss;
				ss << argv[i + 2];
				//
				PrintMessage(1, "The file " + ss.str() + " is empty of not found.");
				return false;
			}
			aBuilder.AddArgument(occgeom->shape);
		}
		aBuilder.Perform();
		//
		if (aBuilder.HasErrors())
		{
			PrintMessage(1, "The partition command failed.");
			return false;
		}
		//
		//https://documentation.help/Open-Cascade/occt_user_guides__shape_healing.html
		/*Handle(ShapeFix_FixSmallFace) sfss = new ShapeFix_FixSmallFace;
		sfss->Init(aBuilder.Shape());

		sfss->SetPrecision(1e-3);
		sfss->SetMaxTolerance(1e-3);

		sfss->Perform();

		TopoDS_Shape shape = sfss->FixShape();*/
		
		//
		BRepTools::Write(aBuilder.Shape(), argv[argc - 1], Message_ProgressRange());
		//
		return true;		
	}
	
	bool CreateAssemblyFromBrep(int argc, char* argv[], bool saveAsStep)
	{
		// argv[0]		...	exe					
		// argv[1]		...	function			
		// argv[2]		...	input brep file name
		// argv[3]		...	input brep file name
		// ...									
		// argv[n-1]	...	input brep file name
		// argv[n]		...	output file name	
		//
		// The shapes are gathered into a compound without a boolean operation, so that every part
		// keeps the geometry it was written with
		BRep_Builder builder;
		TopoDS_Compound compound;
		OCCGeometry * occgeom;
		int numOfFiles = argc - 3;
		//
		builder.MakeCompound(compound);
		//
		for (int i = 0; i < numOfFiles; i++)
		{
			occgeom = LoadOCC_BREP(argv[i + 2]);
			if (!occgeom)
			{
				stringstream ss;
				ss << argv[i + 2];
				//
				PrintMessage(1, "The file " + ss.str() + " is empty or not found.");
				return false;
			}
			builder.Add(compound, occgeom->shape);
		}
		//
		if (saveAsStep)
		{
			STEPControl_Writer writer;
			writer.Transfer(compound, STEPControl_AsIs);
			if (writer.Write(argv[argc - 1]) != IFSelect_RetDone)
			{
				PrintMessage(1, "Writing the STEP file failed.");
				return false;
			}
		}
		else BRepTools::Write(compound, argv[argc - 1], Message_ProgressRange());
		//
		return true;
	}
	
	OCCGeometry * SplitAFaceUsingTwoPoints(OCCGeometry * occgeom, int faceId, double x1, double y1, double z1, double x2, double y2, double z2)
	{
		int facenr;
		bool faceFound;
		TopoDS_Face face;
		//
		faceFound = false;
		//
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_FACE); exp0.More(); exp0.Next())
		{
			face = TopoDS::Face(exp0.Current());
			facenr = occgeom->fmap.FindIndex(face);
			//
			if (facenr == faceId)
			{
				faceFound = true;
				break;
			}
		}
		if (faceFound)
		{
			TopoDS_Edge edge;
			TopoDS_Vertex ver1, ver2;
			//
			ver1 = BRepBuilderAPI_MakeVertex(gp_Pnt(x1, y1, z1));
			ver2 = BRepBuilderAPI_MakeVertex(gp_Pnt(x2, y2, z2));
			//
			edge = BRepBuilderAPI_MakeEdge(ver1, ver2).Edge();
			//BRepTools::Write(edge1, "C:\\Temp\\edge1.brep");
			//
			BRepAlgo_NormalProjection projector = BRepAlgo_NormalProjection(face);
			projector.Add(edge);
			projector.Build();
			//BRepTools::Write(projector.Projection(), "C:\\Temp\\projection.brep");
			//
			BOPAlgo_Builder aBuilder;
			aBuilder.SetRunParallel(Standard_True);
			aBuilder.AddArgument(occgeom->shape);
			aBuilder.AddArgument(projector.Projection());
			aBuilder.Perform();
			if (aBuilder.HasErrors())
			{
				PrintMessage(1, "The split face command failed.");
			}
			else
			{
				//BRepTools::Write(aBuilder.Shape(), "C:\\Temp\\builder.brep");
				occgeom->shape = aBuilder.Shape();
			}
		}
		//
		return occgeom;
	}

	// A splitting tool has to be larger than everything it cuts, and the same tool is applied to every
	// part of a region, so the caller passes the extent it must cover as x_min x_max y_min y_max z_min z_max
	// rather than letting each part size a tool of its own.
	static bool GetToolSurfaceParameterRange(const Handle(Geom_Surface) & surface, const double * extent,
	                                         double & uMin, double & uMax, double & vMin, double & vMax)
	{
		double u1, u2, v1, v2;
		surface->Bounds(u1, u2, v1, v2);
		//
		bool uPeriodic = surface->IsUPeriodic() == Standard_True;
		bool vPeriodic = surface->IsVPeriodic() == Standard_True;
		bool uInfinite = Precision::IsInfinite(u1) || Precision::IsInfinite(u2);
		bool vInfinite = Precision::IsInfinite(v1) || Precision::IsInfinite(v2);
		//
		if (uPeriodic) { uMin = u1; uMax = u1 + surface->UPeriod(); }
		else if (!uInfinite) { uMin = u1; uMax = u2; }
		if (vPeriodic) { vMin = v1; vMax = v1 + surface->VPeriod(); }
		else if (!vInfinite) { vMin = v1; vMax = v2; }
		// An infinite direction is trimmed to the projection of the extent box, padded so that the tool
		// reaches past the geometry instead of ending exactly on it
		if ((uInfinite && !uPeriodic) || (vInfinite && !vPeriodic))
		{
			double uLow = 1e100, uHigh = -1e100, vLow = 1e100, vHigh = -1e100;
			ShapeAnalysis_Surface analysis(surface);
			for (int i = 0; i < 8; i++)
			{
				gp_Pnt corner(extent[i & 1], extent[2 + ((i >> 1) & 1)], extent[4 + ((i >> 2) & 1)]);
				gp_Pnt2d uv = analysis.ValueOfUV(corner, Precision::Confusion());
				uLow = min2(uLow, uv.X()); uHigh = max2(uHigh, uv.X());
				vLow = min2(vLow, uv.Y()); vHigh = max2(vHigh, uv.Y());
			}
			double diagonal = sqrt((extent[1] - extent[0]) * (extent[1] - extent[0]) +
			                       (extent[3] - extent[2]) * (extent[3] - extent[2]) +
			                       (extent[5] - extent[4]) * (extent[5] - extent[4]));
			if (diagonal <= 0) return false;
			//
			if (uInfinite && !uPeriodic)
			{
				double pad = max2(0.1 * (uHigh - uLow), 0.05 * diagonal);
				uMin = uLow - pad; uMax = uHigh + pad;
			}
			if (vInfinite && !vPeriodic)
			{
				double pad = max2(0.1 * (vHigh - vLow), 0.05 * diagonal);
				vMin = vLow - pad; vMax = vHigh + pad;
			}
		}
		//
		return uMax > uMin && vMax > vMin;
	}
	static TopoDS_Shape MakeToolFaceFromSurface(const Handle(Geom_Surface) & surface, const double * extent)
	{
		double uMin, uMax, vMin, vMax;
		if (!GetToolSurfaceParameterRange(surface, extent, uMin, uMax, vMin, vMax)) return TopoDS_Shape();
		//
		BRepBuilderAPI_MakeFace faceMaker(surface, uMin, uMax, vMin, vMax, Precision::Confusion());
		if (!faceMaker.IsDone()) return TopoDS_Shape();
		//
		return faceMaker.Face();
	}
	// The general fuse would keep the fragments of the tool itself in the result, so a splitting
	// operation uses the splitter, which splits the arguments and drops what is left of the tools
	static bool SplitOneShapeWithTool(const TopoDS_Shape & shape, const TopoDS_Shape & tool, double fuzzyValue,
	                                  TopoDS_Shape & result)
	{
		TopTools_ListOfShape arguments;
		TopTools_ListOfShape tools;
		arguments.Append(shape);
		tools.Append(tool);
		//
		BRepAlgoAPI_Splitter splitter;
		splitter.SetArguments(arguments);
		splitter.SetTools(tools);
		splitter.SetRunParallel(Standard_True);
		splitter.SetNonDestructive(Standard_True);
		if (fuzzyValue > 0) splitter.SetFuzzyValue(fuzzyValue);
		splitter.Build();
		//
		if (splitter.HasErrors()) return false;
		//
		result = splitter.Shape();
		return true;
	}
	// A compound is cut solid by solid so that the solids the caller did not name come through untouched,
	// and everything is gathered back into one compound. Cutting a solid on its own rebuilds the faces of
	// that solid, so a face it shared with a solid the caller did not name comes back twice - once rebuilt
	// and once as it was - wherever the tool reaches that face, and the two sides no longer meet on one
	// face. The pieces are therefore put back through a general fuse at the end, which imprints them on
	// each other again.
	static OCCGeometry * SplitSolidsWithTool(OCCGeometry * occgeom, const TopoDS_Shape & tool, double fuzzyValue,
	                                        int * solidIds, int numOfSolidIds)
	{
		BRep_Builder builder;
		TopoDS_Compound result;
		builder.MakeCompound(result);
		//
		int solidNumber = 0;
		int numOfSplitSolids = 0;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			solidNumber++;
			//
			bool split = false;
			for (int i = 0; i < numOfSolidIds; i++) if (solidIds[i] == solidNumber) { split = true; break; }
			//
			TopoDS_Shape piece = exp0.Current();
			if (split)
			{
				TopoDS_Shape cut;
				if (SplitOneShapeWithTool(piece, tool, fuzzyValue, cut)) { piece = cut; numOfSplitSolids++; }
				else PrintMessage(1, "The split command failed on one of the solids.");
			}
			// The splitter answers with a compound of the pieces, which is flattened so that the result
			// holds solids and not compounds inside a compound
			bool added = false;
			for (TopExp_Explorer exp1(piece, TopAbs_SOLID); exp1.More(); exp1.Next())
			{
				builder.Add(result, exp1.Current());
				added = true;
			}
			if (!added) builder.Add(result, piece);
		}
		if (solidNumber == 0 || numOfSplitSolids == 0)
		{
			PrintMessage(1, "None of the named solids was split.");
			return occgeom;
		}
		// The pieces are imprinted on each other again, so that a face shared with a solid that was not
		// cut is one face and not two coincident ones. A cut that reached no shared face is left as it is
		TopoDS_Shape joined = result;
		BOPAlgo_Builder aBuilder;
		aBuilder.SetRunParallel(Standard_True);
		for (TopExp_Explorer exp2(result, TopAbs_SOLID); exp2.More(); exp2.Next())
			aBuilder.AddArgument(exp2.Current());
		aBuilder.Perform();
		if (aBuilder.HasErrors())
			PrintMessage(1, "The pieces of the split could not be imprinted on each other. The parts that "
			                "were cut may not share their faces with the parts that were not.");
		else joined = aBuilder.Shape();
		//
		occgeom->shape = joined;
		occgeom->changed = 1;
		occgeom->BuildFMap();
		//
		return occgeom;
	}
	// The imprint answers with the body and the curves that were imprinted on it side by side. The
	// curves are already in the faces they divided, so what is kept is the bodies alone - a single one
	// as itself, several gathered into a compound, which is the shape the geometry had to begin with.
	static TopoDS_Shape KeepSplitBodies(const TopoDS_Shape & shape)
	{
		TopTools_ListOfShape bodies;
		for (TopExp_Explorer exp0(shape, TopAbs_SOLID); exp0.More(); exp0.Next())
			bodies.Append(exp0.Current());
		for (TopExp_Explorer exp0(shape, TopAbs_SHELL, TopAbs_SOLID); exp0.More(); exp0.Next())
			bodies.Append(exp0.Current());
		for (TopExp_Explorer exp0(shape, TopAbs_FACE, TopAbs_SHELL); exp0.More(); exp0.Next())
			bodies.Append(exp0.Current());
		//
		if (bodies.Extent() == 0) return shape;
		if (bodies.Extent() == 1) return bodies.First();
		//
		BRep_Builder builder;
		TopoDS_Compound result;
		builder.MakeCompound(result);
		for (TopTools_ListOfShape::Iterator it(bodies); it.More(); it.Next()) builder.Add(result, it.Value());
		//
		return result;
	}
	// The faces a group of ids names, which is what a shell split divides and what a surface extraction
	// takes. A face id says the place of the face in the shape it was picked on, and for a compound that
	// is one of its solids, so the ids arrive grouped: targetFaceCounts[i] of them are numbered inside
	// solid targetSolids[i]. A solid of zero numbers them in the shape itself. The faces of a solid are
	// walked here the way the face map walks them, which is the order the solid was written out of the
	// compound in, so the numbers mean the same thing on both sides.
	bool GetTargetFaces(OCCGeometry * occgeom, int * targetSolids, int * targetFaceCounts,
	                    int numOfTargetGroups, int * targetFaceIds,
	                    TopTools_IndexedMapOfShape & targetFaces)
	{
		int index = 0;
		for (int group = 0; group < numOfTargetGroups; group++)
		{
			TopTools_IndexedMapOfShape solidFaces;
			const TopTools_IndexedMapOfShape * groupFaces = &occgeom->fmap;
			int solidNumber = targetSolids == NULL ? 0 : targetSolids[group];
			if (solidNumber > 0)
			{
				int number = 0;
				for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
				{
					if (++number != solidNumber) continue;
					TopExp::MapShapes(exp0.Current(), TopAbs_FACE, solidFaces);
					break;
				}
				groupFaces = &solidFaces;
			}
			//
			for (int i = 0; i < targetFaceCounts[group]; i++, index++)
			{
				int faceId = targetFaceIds[index];
				if (faceId < 1 || faceId > groupFaces->Extent()) continue;
				targetFaces.Add((*groupFaces)(faceId));
			}
		}
		return targetFaces.Extent() > 0;
	}
	// The curves are imprinted on the whole shape rather than on the faces they were found on, so that
	// a face next to a divided one is rebuilt with the edge that was divided with it. Imprinting the
	// faces on their own would leave the neighbour holding the edge it had, and the two would no longer
	// meet. A curve cannot separate a body, so the solid, the shell and the compound come back as they
	// were, with more faces.
	static OCCGeometry * ImprintEdgesOnShape(OCCGeometry * occgeom,
	                                        const TopTools_IndexedMapOfShape & imprintEdges, double fuzzyValue)
	{
		BOPAlgo_Builder imprint;
		imprint.SetRunParallel(Standard_True);
		if (fuzzyValue > 0) imprint.SetFuzzyValue(fuzzyValue);
		imprint.AddArgument(occgeom->shape);
		for (int i = 1; i <= imprintEdges.Extent(); i++) imprint.AddArgument(imprintEdges(i));
		imprint.Perform();
		if (imprint.HasErrors())
		{
			PrintMessage(1, "The selected surfaces could not be split.");
			return occgeom;
		}
		//
		occgeom->shape = KeepSplitBodies(imprint.Shape());
		occgeom->changed = 1;
		occgeom->BuildFMap();
		//
		return occgeom;
	}
	// A shell split divides the faces it is given without cutting the body they belong to. The tool
	// cannot do that itself - handed to the splitter, a tool face separates a solid in two - so it is
	// only used to find where it crosses the picked faces, and those curves, not the tool, are what is
	// imprinted. A curve cannot separate a solid, so the solid, the shell and the compound above the
	// faces come back as they were, with more faces.
	static OCCGeometry * SplitFacesWithTool(OCCGeometry * occgeom, const TopoDS_Shape & tool, double fuzzyValue,
	                                        const TopTools_IndexedMapOfShape & targetFaces)
	{
		// Both shapes are arguments of a general fuse rather than argument and tool, so that the picked
		// faces come back divided whether the tool crosses them or lies in them. It can lie in them: an
		// edge swept along the plane of the face it was picked on gives a tool face in that same plane.
		BOPAlgo_Builder crossing;
		crossing.SetRunParallel(Standard_True);
		if (fuzzyValue > 0) crossing.SetFuzzyValue(fuzzyValue);
		for (int i = 1; i <= targetFaces.Extent(); i++) crossing.AddArgument(targetFaces(i));
		crossing.AddArgument(tool);
		crossing.Perform();
		if (crossing.HasErrors())
		{
			PrintMessage(1, "The splitting tool could not be crossed with the selected surfaces.");
			return occgeom;
		}
		// What the shape already has stays as it is; only what the crossing added is imprinted
		TopTools_IndexedMapOfShape oldEdges;
		TopExp::MapShapes(occgeom->shape, TopAbs_EDGE, oldEdges);
		//
		TopTools_IndexedMapOfShape imprintEdges;
		for (int i = 1; i <= targetFaces.Extent(); i++)
		{
			const TopTools_ListOfShape & pieces = crossing.Modified(targetFaces(i));
			for (TopTools_ListOfShape::Iterator it(pieces); it.More(); it.Next())
			{
				for (TopExp_Explorer exp0(it.Value(), TopAbs_EDGE); exp0.More(); exp0.Next())
				{
					if (oldEdges.FindIndex(exp0.Current()) < 1) imprintEdges.Add(exp0.Current());
				}
			}
		}
		if (imprintEdges.Extent() == 0)
		{
			PrintMessage(1, "The splitting tool does not cross any of the selected surfaces.");
			return occgeom;
		}
		return ImprintEdgesOnShape(occgeom, imprintEdges, fuzzyValue);
	}
	static OCCGeometry * SplitWithTool(OCCGeometry * occgeom, const TopoDS_Shape & tool, double fuzzyValue,
	                                   int * solidIds, int numOfSolidIds, int * targetSolids,
	                                   int * targetFaceCounts, int numOfTargetGroups, int * targetFaceIds)
	{
		if (tool.IsNull())
		{
			PrintMessage(1, "The splitting tool could not be created.");
			return occgeom;
		}
		// Only the faces the caller names are divided, and the bodies they belong to stay whole
		if (numOfTargetGroups > 0)
		{
			TopTools_IndexedMapOfShape targetFaces;
			if (!GetTargetFaces(occgeom, targetSolids, targetFaceCounts, numOfTargetGroups,
			                    targetFaceIds, targetFaces))
			{
				PrintMessage(1, "None of the surfaces to split exists.");
				return occgeom;
			}
			return SplitFacesWithTool(occgeom, tool, fuzzyValue, targetFaces);
		}
		// Only some of the solids are cut when the caller names them
		if (solidIds != NULL && numOfSolidIds > 0)
			return SplitSolidsWithTool(occgeom, tool, fuzzyValue, solidIds, numOfSolidIds);
		//
		TopTools_ListOfShape arguments;
		TopTools_ListOfShape tools;
		arguments.Append(occgeom->shape);
		tools.Append(tool);
		//
		BRepAlgoAPI_Splitter splitter;
		splitter.SetArguments(arguments);
		splitter.SetTools(tools);
		splitter.SetRunParallel(Standard_True);
		splitter.SetNonDestructive(Standard_True);
		if (fuzzyValue > 0) splitter.SetFuzzyValue(fuzzyValue);
		splitter.Build();
		//
		if (splitter.HasErrors())
		{
			PrintMessage(1, "The split command failed.");
			return occgeom;
		}
		//
		occgeom->shape = splitter.Shape();
		occgeom->changed = 1;
		occgeom->BuildFMap();
		//
		return occgeom;
	}
	// The solids are numbered the way every other command numbers them, by the order the explorer walks
	// them, so the caller names the same solid here as it does when it says which ones to split. What is
	// left is gathered into a compound again and the shapes are not touched, so a solid that stays keeps
	// the faces, edges and vertices it had, imprints on its neighbours included.
	OCCGeometry * RemoveSolids(OCCGeometry * occgeom, int * solidIds, int numOfSolidIds)
	{
		if (solidIds == NULL || numOfSolidIds <= 0)
		{
			PrintMessage(1, "No solid to remove was named.");
			return occgeom;
		}
		//
		BRep_Builder builder;
		TopoDS_Compound result;
		builder.MakeCompound(result);
		//
		int solidNumber = 0;
		int numOfRemovedSolids = 0;
		int numOfKeptSolids = 0;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			solidNumber++;
			//
			bool remove = false;
			for (int i = 0; i < numOfSolidIds; i++) if (solidIds[i] == solidNumber) { remove = true; break; }
			//
			if (remove) numOfRemovedSolids++;
			else
			{
				builder.Add(result, exp0.Current());
				numOfKeptSolids++;
			}
		}
		if (numOfRemovedSolids == 0)
		{
			PrintMessage(1, "None of the named solids exists.");
			return occgeom;
		}
		if (numOfKeptSolids == 0)
		{
			PrintMessage(1, "Removing the named solids would leave nothing.");
			return occgeom;
		}
		//
		occgeom->shape = result;
		occgeom->changed = 1;
		occgeom->BuildFMap();
		//
		return occgeom;
	}
	// An edge that has the same face on both sides, the seam of a closed surface, separates nothing
	static bool IsSeamEdge(const TopoDS_Shape & edge, const TopTools_IndexedDataMapOfShapeListOfShape & edgeFaces)
	{
		const TopTools_ListOfShape & faces = edgeFaces.FindFromKey(edge);
		for (TopTools_ListIteratorOfListOfShape it(faces); it.More(); it.Next())
		{
			if (BRep_Tool::IsClosed(TopoDS::Edge(edge), TopoDS::Face(it.Value()))) return true;
		}
		return false;
	}
	// Heals away the edges the removed faces of a merge leave on the outside of the merged solid, where the
	// faces on both sides lie on one surface, which gives back the faces a split divided. The faces are
	// merged first, across the edges of removed faces only, so the faces the model had before the split
	// stay as they were. The edges are joined next, only at the vertices of removed faces, which takes out
	// the points the cut left on the edges it crossed. Nothing the merged solid shares with another solid
	// is touched, and a result that is not one valid solid still holding all of that is not used.
	static TopoDS_Shape UnifyMergedSolid(const TopoDS_Shape & mergedSolid,
	                                     const TopTools_IndexedMapOfShape & interfaceEdges,
	                                     const TopTools_IndexedMapOfShape & interfaceVertices,
	                                     const TopTools_IndexedMapOfShape & otherShapes)
	{
		TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
		TopExp::MapShapesAndAncestors(mergedSolid, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
		TopTools_MapOfShape keepEdges;
		for (int i = 1; i <= edgeFaces.Extent(); i++)
		{
			const TopoDS_Shape & edge = edgeFaces.FindKey(i);
			if (otherShapes.Contains(edge) || (!interfaceEdges.Contains(edge) && !IsSeamEdge(edge, edgeFaces)))
				keepEdges.Add(edge);
		}
		ShapeUpgrade_UnifySameDomain unifyFaces(mergedSolid, Standard_False, Standard_True, Standard_False);
		unifyFaces.KeepShapes(keepEdges);
		// The faces a merge keeps from another solid share its edges, which only gain a curve on the merged face;
		// copied instead, as the safe mode copies what it touches, they would no longer be the edges shared
		unifyFaces.SetSafeInputMode(false);
		unifyFaces.Build();
		//
		TopTools_MapOfShape keepVertices;
		TopTools_IndexedMapOfShape shapes;
		TopExp::MapShapes(unifyFaces.Shape(), TopAbs_VERTEX, shapes);
		for (int i = 1; i <= shapes.Extent(); i++)
		{
			if (!interfaceVertices.Contains(shapes(i)) || otherShapes.Contains(shapes(i))) keepVertices.Add(shapes(i));
		}
		shapes.Clear();
		TopExp::MapShapes(unifyFaces.Shape(), TopAbs_EDGE, shapes);
		for (int i = 1; i <= shapes.Extent(); i++) if (otherShapes.Contains(shapes(i))) keepVertices.Add(shapes(i));
		ShapeUpgrade_UnifySameDomain unifyEdges(unifyFaces.Shape(), Standard_True, Standard_False, Standard_False);
		unifyEdges.KeepShapes(keepVertices);
		unifyEdges.SetSafeInputMode(false);
		unifyEdges.Build();
		//
		TopoDS_Shape unified = unifyEdges.Shape();
		TopExp_Explorer solidExplorer(unified, TopAbs_SOLID);
		if (!solidExplorer.More()) return mergedSolid;
		TopoDS_Shape unifiedSolid = solidExplorer.Current();
		solidExplorer.Next();
		if (solidExplorer.More()) return mergedSolid;
		if (!BRepCheck_Analyzer(unifiedSolid).IsValid()) return mergedSolid;
		//
		TopTools_IndexedMapOfShape unifiedShapes;
		TopExp::MapShapes(unifiedSolid, unifiedShapes);
		TopTools_IndexedMapOfShape mergedShapes;
		TopExp::MapShapes(mergedSolid, mergedShapes);
		for (int i = 1; i <= mergedShapes.Extent(); i++)
		{
			if (otherShapes.Contains(mergedShapes(i)) && !unifiedShapes.Contains(mergedShapes(i)))
				return mergedSolid;
		}
		return unifiedSolid;
	}
	static int FindMergeGroup(vector<int> & groups, int i)
	{
		while (groups[i] != i)
		{
			groups[i] = groups[groups[i]];
			i = groups[i];
		}
		return i;
	}
	// The named solids become one. The faces two of them share lie inside the result and are left out, and
	// every other face is taken as it is, so a solid that is not named keeps the very faces, edges and
	// vertices it shares with the result and the compound stays conformal. The solids are numbered by the
	// order the explorer walks them, as for RemoveSolids, and the result takes the place of the first named
	// one. Solids that do not share faces cannot become one solid and are refused.
	OCCGeometry * MergeSolids(OCCGeometry * occgeom, int * solidIds, int numOfSolidIds)
	{
		if (solidIds == NULL || numOfSolidIds < 2)
		{
			PrintMessage(1, "At least two solids to merge must be named.");
			return occgeom;
		}
		//
		vector<TopoDS_Shape> solids;
		for (TopExp_Explorer exp0(occgeom->shape, TopAbs_SOLID); exp0.More(); exp0.Next())
			solids.push_back(exp0.Current());
		//
		vector<bool> merged(solids.size(), false);
		vector<int> mergedIndices;
		for (int i = 0; i < numOfSolidIds; i++)
		{
			int index = solidIds[i] - 1;
			if (index < 0 || index >= (int)solids.size() || merged[index]) continue;
			merged[index] = true;
			mergedIndices.push_back(index);
		}
		if (mergedIndices.size() < 2)
		{
			PrintMessage(1, "Fewer than two of the named solids exist.");
			return occgeom;
		}
		int firstIndex = *std::min_element(mergedIndices.begin(), mergedIndices.end());
		// Which of the named solids hold each of their faces
		TopTools_IndexedDataMapOfShapeListOfShape faceSolids;
		TopTools_IndexedMapOfShape mergedSolidMap;
		for (size_t k = 0; k < mergedIndices.size(); k++)
		{
			const TopoDS_Shape & solid = solids[mergedIndices[k]];
			mergedSolidMap.Add(solid);
			TopTools_IndexedMapOfShape solidFaces;
			TopExp::MapShapes(solid, TopAbs_FACE, solidFaces);
			for (int i = 1; i <= solidFaces.Extent(); i++)
			{
				if (!faceSolids.Contains(solidFaces(i))) faceSolids.Add(solidFaces(i), TopTools_ListOfShape());
				faceSolids.ChangeFromKey(solidFaces(i)).Append(solid);
			}
		}
		// The named solids must be connected through the faces they share
		vector<int> groups(mergedSolidMap.Extent() + 1);
		for (int i = 1; i <= mergedSolidMap.Extent(); i++) groups[i] = i;
		for (int i = 1; i <= faceSolids.Extent(); i++)
		{
			const TopTools_ListOfShape & holders = faceSolids(i);
			if (holders.Extent() < 2) continue;
			int first = FindMergeGroup(groups, mergedSolidMap.FindIndex(holders.First()));
			for (TopTools_ListIteratorOfListOfShape it(holders); it.More(); it.Next())
				groups[FindMergeGroup(groups, mergedSolidMap.FindIndex(it.Value()))] = first;
		}
		for (int i = 2; i <= mergedSolidMap.Extent(); i++)
		{
			if (FindMergeGroup(groups, i) != FindMergeGroup(groups, 1))
			{
				PrintMessage(1, "The named solids do not all share faces, so they cannot become one solid.");
				return occgeom;
			}
		}
		// What the solids that are not named hold must stay exactly as it is
		TopTools_IndexedMapOfShape otherShapes;
		for (size_t i = 0; i < solids.size(); i++) if (!merged[i]) TopExp::MapShapes(solids[i], otherShapes);
		// The faces of the result, oriented as their own solid holds them
		BRep_Builder builder;
		TopoDS_Compound faceCompound;
		builder.MakeCompound(faceCompound);
		TopTools_IndexedMapOfShape interfaceEdges;
		TopTools_IndexedMapOfShape interfaceVertices;
		for (size_t k = 0; k < mergedIndices.size(); k++)
		{
			for (TopExp_Explorer exp0(solids[mergedIndices[k]], TopAbs_FACE); exp0.More(); exp0.Next())
			{
				if (faceSolids.FindFromKey(exp0.Current()).Extent() > 1)
				{
					TopExp::MapShapes(exp0.Current(), TopAbs_EDGE, interfaceEdges);
					TopExp::MapShapes(exp0.Current(), TopAbs_VERTEX, interfaceVertices);
				}
				else builder.Add(faceCompound, exp0.Current());
			}
		}
		// A shell for every set of faces joined by edges: the outer boundary and one for every void
		TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
		TopExp::MapShapesAndAncestors(faceCompound, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
		TopTools_IndexedMapOfShape resultFaces;
		vector<TopoDS_Shape> orientedFaces(1);
		for (TopoDS_Iterator it(faceCompound); it.More(); it.Next())
		{
			resultFaces.Add(it.Value());
			orientedFaces.push_back(it.Value());
		}
		vector<int> faceShells(resultFaces.Extent() + 1, 0);
		vector<TopoDS_Shell> shells;
		for (int start = 1; start <= resultFaces.Extent(); start++)
		{
			if (faceShells[start] != 0) continue;
			TopoDS_Shell shell;
			builder.MakeShell(shell);
			int shellNumber = (int)shells.size() + 1;
			vector<int> stack(1, start);
			faceShells[start] = shellNumber;
			while (stack.size() > 0)
			{
				int faceIndex = stack.back();
				stack.pop_back();
				builder.Add(shell, orientedFaces[faceIndex]);
				for (TopExp_Explorer exp0(orientedFaces[faceIndex], TopAbs_EDGE); exp0.More(); exp0.Next())
				{
					const TopTools_ListOfShape & neighbours = edgeFaces.FindFromKey(exp0.Current());
					for (TopTools_ListIteratorOfListOfShape it(neighbours); it.More(); it.Next())
					{
						int neighbour = resultFaces.FindIndex(it.Value());
						if (neighbour > 0 && faceShells[neighbour] == 0)
						{
							faceShells[neighbour] = shellNumber;
							stack.push_back(neighbour);
						}
					}
				}
			}
			shell.Closed(BRep_Tool::IsClosed(shell));
			shells.push_back(shell);
		}
		if (shells.size() == 0)
		{
			PrintMessage(1, "The named solids leave no faces when merged.");
			return occgeom;
		}
		// The outer boundary is the shell with the largest box and goes first
		int outerShell = 0;
		double largestExtent = -1;
		for (size_t i = 0; i < shells.size(); i++)
		{
			Bnd_Box box;
			BRepBndLib::Add(shells[i], box);
			double extent = box.IsVoid() ? 0 : box.SquareExtent();
			if (extent > largestExtent)
			{
				largestExtent = extent;
				outerShell = (int)i;
			}
		}
		TopoDS_Solid mergedSolid;
		builder.MakeSolid(mergedSolid);
		builder.Add(mergedSolid, shells[outerShell]);
		for (size_t i = 0; i < shells.size(); i++) if ((int)i != outerShell) builder.Add(mergedSolid, shells[i]);
		if (!BRepCheck_Analyzer(mergedSolid).IsValid())
		{
			PrintMessage(1, "The named solids do not give a valid solid when merged.");
			return occgeom;
		}
		//
		TopoDS_Shape resultSolid = UnifyMergedSolid(mergedSolid, interfaceEdges, interfaceVertices, otherShapes);
		//
		TopoDS_Compound result;
		builder.MakeCompound(result);
		for (size_t i = 0; i < solids.size(); i++)
		{
			if ((int)i == firstIndex) builder.Add(result, resultSolid);
			else if (!merged[i]) builder.Add(result, solids[i]);
		}
		//
		occgeom->shape = result;
		occgeom->changed = 1;
		occgeom->BuildFMap();
		//
		return occgeom;
	}
	OCCGeometry * SplitWithPlane(OCCGeometry * occgeom, double * origin, double * normal, double * extent,
	                             double fuzzyValue, int * solidIds, int numOfSolidIds, int * targetSolids,
	                             int * targetFaceCounts, int numOfTargetGroups, int * targetFaceIds)
	{
		gp_Vec direction(normal[0], normal[1], normal[2]);
		if (direction.Magnitude() <= Precision::Confusion())
		{
			PrintMessage(1, "The splitting plane normal is zero.");
			return occgeom;
		}
		//
		gp_Pln plane(gp_Pnt(origin[0], origin[1], origin[2]), gp_Dir(direction));
		Handle(Geom_Plane) surface = new Geom_Plane(plane);
		//
		return SplitWithTool(occgeom, MakeToolFaceFromSurface(surface, extent), fuzzyValue, solidIds,
		                     numOfSolidIds, targetSolids, targetFaceCounts, numOfTargetGroups,
		                     targetFaceIds);
	}
	// A surface moved along its own normal. Every surface that continues past its face is one of five
	// kinds, and each of them offsets exactly into another surface of the same kind, so an offset tool
	// is still a plane, a cylinder, a cone, a sphere or a torus and not a surface the modelling kernel
	// has to approximate. A positive offset moves a plane along its normal and grows the radius of the
	// others; one that would leave no surface at all - a radius at or below zero, a torus that would
	// close on itself - is refused, and the face it came from is left out of the tool.
	// The surface is always rebuilt from its kind, also when the offset is zero. A face a split left holds
	// its surface trimmed to the face - a periodic face divided in halves holds a half cylinder, and the
	// whole band of the stem it lies on is its parameter range - and a tool made from that surface is only
	// as large as the face. It then lies exactly on the face it was picked on and never continues past its
	// boundary, so it divides nothing. The untrimmed surface of the same kind is the one the face lies on.
	static bool OffsetSplitToolSurface(const Handle(Geom_Surface) & surface, double offset,
	                                   Handle(Geom_Surface) & offsetSurface)
	{
		// The kind is read through the adaptor, as the geometry metadata reads it, so a surface a face
		// holds inside a trimmed surface - as a split leaves it - is offset as the cylinder or plane the
		// symbol showed, instead of being refused as a kind that cannot be offset
		GeomAdaptor_Surface adaptor(surface);
		switch (adaptor.GetType())
		{
			case GeomAbs_Plane:
			{
				gp_Pln plane = adaptor.Plane();
				if (offset != 0) plane.Translate(gp_Vec(plane.Axis().Direction()) * offset);
				offsetSurface = new Geom_Plane(plane);
				return true;
			}
			case GeomAbs_Cylinder:
			{
				gp_Cylinder cylinder = adaptor.Cylinder();
				double radius = cylinder.Radius() + offset;
				if (radius <= Precision::Confusion()) return false;
				offsetSurface = new Geom_CylindricalSurface(cylinder.Position(), radius);
				return true;
			}
			case GeomAbs_Cone:
			{
				gp_Cone cone = adaptor.Cone();
				double radius = cone.RefRadius();
				if (offset != 0)
				{
					double cosine = cos(cone.SemiAngle());
					if (fabs(cosine) <= Precision::Confusion()) return false;
					// The offset is measured along the normal and the radius across the axis, and the two
					// stand at the half angle of the cone to each other
					radius += offset / cosine;
					if (radius < 0) return false;
				}
				offsetSurface = new Geom_ConicalSurface(cone.Position(), cone.SemiAngle(), radius);
				return true;
			}
			case GeomAbs_Sphere:
			{
				gp_Sphere sphere = adaptor.Sphere();
				double radius = sphere.Radius() + offset;
				if (radius <= Precision::Confusion()) return false;
				offsetSurface = new Geom_SphericalSurface(sphere.Position(), radius);
				return true;
			}
			case GeomAbs_Torus:
			{
				gp_Torus torus = adaptor.Torus();
				double minorRadius = torus.MinorRadius() + offset;
				if (offset != 0 && (minorRadius <= Precision::Confusion() || minorRadius >= torus.MajorRadius()))
					return false;
				offsetSurface = new Geom_ToroidalSurface(torus.Position(), torus.MajorRadius(), minorRadius);
				return true;
			}
			default:
				// A surface of no analytic kind has no continuation to rebuild, so without an offset it is
				// the tool as the face holds it
				if (offset != 0) return false;
				offsetSurface = surface;
				return true;
		}
	}
	// Several faces may be extended at once, and they may sit on several shapes - a compound is split
	// as a whole while its pieces are what the faces are picked on - so the ids arrive grouped:
	// faceIdCounts[i] of them belong to sourcegeoms[i]. Each becomes a tool face of its own and they
	// cut together, as one compound tool.
	OCCGeometry * SplitWithExtendedFace(OCCGeometry * occgeom, OCCGeometry ** sourcegeoms,
	                                    int * faceIdCounts, int numOfSources, int * faceIds,
	                                    double * extent, double offset, double fuzzyValue,
	                                    int * solidIds, int numOfSolidIds, int * targetSolids,
	                                    int * targetFaceCounts, int numOfTargetGroups, int * targetFaceIds)
	{
		BRep_Builder builder;
		TopoDS_Compound tool;
		builder.MakeCompound(tool);
		//
		int numOfToolFaces = 0;
		int index = 0;
		for (int source = 0; source < numOfSources; source++)
		{
			OCCGeometry * sourcegeom = sourcegeoms == NULL || sourcegeoms[source] == NULL ?
			                           occgeom : sourcegeoms[source];
			for (int i = 0; i < faceIdCounts[source]; i++, index++)
			{
				if (faceIds[index] < 1 || faceIds[index] > sourcegeom->fmap.Extent()) continue;
				//
				TopoDS_Face face = TopoDS::Face(sourcegeom->fmap(faceIds[index]));
				Handle(Geom_Surface) surface = BRep_Tool::Surface(face);
				if (surface.IsNull()) continue;
				// The face is continued past its boundary as the surface it lies on, moved along its own
				// normal when an offset is asked for
				Handle(Geom_Surface) offsetSurface;
				if (!OffsetSplitToolSurface(surface, offset, offsetSurface)) continue;
				//
				TopoDS_Shape toolFace = MakeToolFaceFromSurface(offsetSurface, extent);
				if (toolFace.IsNull()) continue;
				//
				builder.Add(tool, toolFace);
				numOfToolFaces++;
			}
		}
		if (numOfToolFaces == 0)
		{
			PrintMessage(1, "None of the faces to extend could be continued past its boundary.");
			return occgeom;
		}
		//
		return SplitWithTool(occgeom, tool, fuzzyValue, solidIds, numOfSolidIds, targetSolids,
		                     targetFaceCounts, numOfTargetGroups, targetFaceIds);
	}
	// The edges may come from more than one shape, because a compound is split as a whole while the
	// edges are picked on its pieces, and an edge id means nothing outside the shape it was read from.
	// So the ids arrive grouped: edgeIdCounts[i] of them belong to sourcegeoms[i].
	OCCGeometry * SplitWithExtrudedEdges(OCCGeometry * occgeom, OCCGeometry ** sourcegeoms,
	                                     int * edgeIdCounts, int numOfSources, int * edgeIds,
	                                     double * offset, double * vector, double fuzzyValue,
	                                     int * solidIds, int numOfSolidIds, int * targetSolids,
	                                     int * targetFaceCounts, int numOfTargetGroups,
	                                     int * targetFaceIds)
	{
		gp_Vec extrusion(vector[0], vector[1], vector[2]);
		if (extrusion.Magnitude() <= Precision::Confusion())
		{
			PrintMessage(1, "The extrusion vector is zero.");
			return occgeom;
		}
		//
		BRep_Builder builder;
		TopoDS_Compound profile;
		builder.MakeCompound(profile);
		//
		int numOfEdges = 0;
		int index = 0;
		for (int source = 0; source < numOfSources; source++)
		{
			OCCGeometry * sourcegeom = sourcegeoms == NULL || sourcegeoms[source] == NULL ?
			                           occgeom : sourcegeoms[source];
			for (int i = 0; i < edgeIdCounts[source]; i++, index++)
			{
				if (edgeIds[index] < 1 || edgeIds[index] > sourcegeom->emap.Extent()) continue;
				builder.Add(profile, sourcegeom->emap(edgeIds[index]));
				numOfEdges++;
			}
		}
		if (numOfEdges == 0)
		{
			PrintMessage(1, "The edges to extrude do not exist.");
			return occgeom;
		}
		//
		TopoDS_Shape shifted = profile;
		if (offset[0] != 0 || offset[1] != 0 || offset[2] != 0)
		{
			gp_Trsf trsf;
			trsf.SetTranslation(gp_Vec(offset[0], offset[1], offset[2]));
			shifted = BRepBuilderAPI_Transform(profile, trsf, true).Shape();
		}
		//
		BRepPrimAPI_MakePrism prismMaker(shifted, extrusion);
		if (!prismMaker.IsDone())
		{
			PrintMessage(1, "The extruded splitting tool could not be created.");
			return occgeom;
		}
		//
		return SplitWithTool(occgeom, prismMaker.Shape(), fuzzyValue, solidIds, numOfSolidIds,
		                     targetSolids, targetFaceCounts, numOfTargetGroups, targetFaceIds);
	}
	// The parameter interval over which a line crosses a box, or false when it misses it. The line of a
	// two point split is drawn across the parameter box of the face rather than between the two points,
	// so that it reaches the boundary and actually divides the face; clipping it to the box is what keeps
	// a periodic surface from being cut a second time where the line comes round again.
	static bool ClipParameterLineToBox(const gp_Pnt2d & origin, const gp_Dir2d & direction,
	                                   double uMin, double uMax, double vMin, double vMax,
	                                   double & first, double & last)
	{
		first = -1e100;
		last = 1e100;
		double denominators[4] = { -direction.X(), direction.X(), -direction.Y(), direction.Y() };
		double distances[4] = { origin.X() - uMin, uMax - origin.X(), origin.Y() - vMin, vMax - origin.Y() };
		for (int i = 0; i < 4; i++)
		{
			if (fabs(denominators[i]) < 1e-12)
			{
				if (distances[i] < 0) return false;
				continue;
			}
			double parameter = distances[i] / denominators[i];
			if (denominators[i] < 0) { if (parameter > first) first = parameter; }
			else { if (parameter < last) last = parameter; }
		}
		return last > first;
	}
	// The line between two points, drawn in the parameter space of the face they lie on. Nothing is
	// projected: the points are located on the surface and the line is built from their parameters, so
	// there is no projection direction that can be undefined - which is what a straight edge projected
	// onto a cylinder meets when the two points face each other across the axis.
	static bool MakeSurfaceLineEdge(const TopoDS_Face & face, const gp_Pnt & firstPoint,
	                                const gp_Pnt & secondPoint, double tolerance, TopoDS_Edge & edge)
	{
		Handle(Geom_Surface) surface = BRep_Tool::Surface(face);
		if (surface.IsNull()) return false;
		//
		ShapeAnalysis_Surface analysis(surface);
		gp_Pnt2d firstUV = analysis.ValueOfUV(firstPoint, Precision::Confusion());
		gp_Pnt2d secondUV = analysis.ValueOfUV(secondPoint, Precision::Confusion());
		// A point that is not on this surface would be drawn to the nearest place on it without saying so
		if (surface->Value(firstUV.X(), firstUV.Y()).Distance(firstPoint) > tolerance) return false;
		if (surface->Value(secondUV.X(), secondUV.Y()).Distance(secondPoint) > tolerance) return false;
		// A periodic direction is walked the short way round
		if (surface->IsUPeriodic())
		{
			double period = surface->UPeriod();
			while (secondUV.X() - firstUV.X() > 0.5 * period) secondUV.SetX(secondUV.X() - period);
			while (firstUV.X() - secondUV.X() > 0.5 * period) secondUV.SetX(secondUV.X() + period);
		}
		if (surface->IsVPeriodic())
		{
			double period = surface->VPeriod();
			while (secondUV.Y() - firstUV.Y() > 0.5 * period) secondUV.SetY(secondUV.Y() - period);
			while (firstUV.Y() - secondUV.Y() > 0.5 * period) secondUV.SetY(secondUV.Y() + period);
		}
		//
		gp_Vec2d along(firstUV, secondUV);
		if (along.Magnitude() <= Precision::PConfusion()) return false;
		//
		double uMin, uMax, vMin, vMax;
		BRepTools::UVBounds(face, uMin, uMax, vMin, vMax);
		double first, last;
		gp_Dir2d direction(along);
		if (!ClipParameterLineToBox(firstUV, direction, uMin, uMax, vMin, vMax, first, last)) return false;
		//
		Handle(Geom2d_Line) line = new Geom2d_Line(firstUV, direction);
		BRepBuilderAPI_MakeEdge edgeMaker(line, surface, first, last);
		if (!edgeMaker.IsDone()) return false;
		//
		edge = edgeMaker.Edge();
		BRepLib::BuildCurves3d(edge);
		//
		return true;
	}
	// Divides the named faces along the line between two points that lie on them. The line belongs to
	// the surface, so this tool has no shape of its own and no extent: it goes straight to the imprint.
	OCCGeometry * SplitWithSurfaceLine(OCCGeometry * occgeom, double * firstPoint, double * secondPoint,
	                                   double fuzzyValue, int * targetSolids, int * targetFaceCounts,
	                                   int numOfTargetGroups, int * targetFaceIds)
	{
		TopTools_IndexedMapOfShape targetFaces;
		if (!GetTargetFaces(occgeom, targetSolids, targetFaceCounts, numOfTargetGroups, targetFaceIds,
	                    targetFaces))
		{
			PrintMessage(1, "None of the surfaces to split exists.");
			return occgeom;
		}
		//
		gp_Pnt first(firstPoint[0], firstPoint[1], firstPoint[2]);
		gp_Pnt second(secondPoint[0], secondPoint[1], secondPoint[2]);
		// The points were read from the picked geometry, so they sit on the surface as accurately as that
		// geometry carries them, and the check is only there to catch a point picked somewhere else
		double tolerance = max2(1e-3 * first.Distance(second), Precision::Confusion());
		//
		TopTools_IndexedMapOfShape imprintEdges;
		for (int i = 1; i <= targetFaces.Extent(); i++)
		{
			TopoDS_Edge edge;
			if (MakeSurfaceLineEdge(TopoDS::Face(targetFaces(i)), first, second, tolerance, edge))
				imprintEdges.Add(edge);
		}
		if (imprintEdges.Extent() == 0)
		{
			PrintMessage(1, "The line between the two points could not be drawn on the selected surfaces.");
			return occgeom;
		}
		//
		return ImprintEdgesOnShape(occgeom, imprintEdges, fuzzyValue);
	}
	OCCGeometry * ScaleGeometry(OCCGeometry * occgeom, double Tx, double Ty, double Tz, double sx, double sy, double sz)
	{
		if (sx == sy && sy == sz)
		{
			gp_Trsf trsf;
			trsf.SetScale(gp_XYZ(Tx, Ty, Tz), sx);
			//
			BRepBuilderAPI_Transform myBRepTransformation = BRepBuilderAPI_Transform(occgeom->shape, trsf, true);
			occgeom->shape = myBRepTransformation.Shape();
		}
		else
		{
			gp_Trsf toZero;
			toZero.SetTranslation(gp_XYZ(Tx, Ty, Tz), gp_XYZ(0, 0, 0));
			gp_GTrsf gToZero = gp_GTrsf(toZero);
			//
			gp_GTrsf gScale;
			gScale.SetValue(1, 1, sx);
			gScale.SetValue(2, 2, sy);
			gScale.SetValue(3, 3, sz);
			//
			gp_Trsf toPoint;
			toPoint.SetTranslation(gp_XYZ(0, 0, 0), gp_XYZ(Tx, Ty, Tz));
			gp_GTrsf gToPoint = gp_GTrsf(toPoint);
			// Invert the sequence
			gp_GTrsf gTrsf = gToPoint * gScale * gToZero;
			//
			BRepBuilderAPI_GTransform myBRepGTransformation = BRepBuilderAPI_GTransform(occgeom->shape, gTrsf, true);
			occgeom->shape = myBRepGTransformation.Shape();
		}
		//
		return occgeom;
	}

	void OCCGeometry::BuildFMap()
	{
		somap.Clear();
		shmap.Clear();
		fmap.Clear();
		wmap.Clear();
		emap.Clear();
		vmap.Clear();

		TopExp_Explorer exp0, exp1, exp2, exp3, exp4, exp5;

		for (exp0.Init(shape, TopAbs_COMPOUND);
			exp0.More(); exp0.Next())
		{
			TopoDS_Compound compound = TopoDS::Compound(exp0.Current());
			(*testout) << "compound" << endl;
			int i = 0;
			for (exp1.Init(compound, TopAbs_SHELL);
				exp1.More(); exp1.Next())
			{
				(*testout) << "shell " << ++i << endl;
			}
		}

		for (exp0.Init(shape, TopAbs_SOLID);
			exp0.More(); exp0.Next())
		{
			TopoDS_Solid solid = TopoDS::Solid(exp0.Current());

			if (somap.FindIndex(solid) < 1)
			{
				somap.Add(solid);

				for (exp1.Init(solid, TopAbs_SHELL);
					exp1.More(); exp1.Next())
				{
					TopoDS_Shell shell = TopoDS::Shell(exp1.Current());
					if (shmap.FindIndex(shell) < 1)
					{
						shmap.Add(shell);

						for (exp2.Init(shell, TopAbs_FACE);
							exp2.More(); exp2.Next())
						{
							TopoDS_Face face = TopoDS::Face(exp2.Current());
							if (fmap.FindIndex(face) < 1)
							{
								fmap.Add(face);
								(*testout) << "face " << fmap.FindIndex(face) << " ";
								(*testout) << ((face.Orientation() == TopAbs_REVERSED) ? "-" : "+") << ", ";
								(*testout) << ((exp2.Current().Orientation() == TopAbs_REVERSED) ? "-" : "+") << endl;
								for (exp3.Init(exp2.Current(), TopAbs_WIRE);
									exp3.More(); exp3.Next())
								{
									TopoDS_Wire wire = TopoDS::Wire(exp3.Current());
									if (wmap.FindIndex(wire) < 1)
									{
										wmap.Add(wire);

										for (exp4.Init(exp3.Current(), TopAbs_EDGE);
											exp4.More(); exp4.Next())
										{
											TopoDS_Edge edge = TopoDS::Edge(exp4.Current());
											if (emap.FindIndex(edge) < 1)
											{
												emap.Add(edge);
												for (exp5.Init(exp4.Current(), TopAbs_VERTEX);
													exp5.More(); exp5.Next())
												{
													TopoDS_Vertex vertex = TopoDS::Vertex(exp5.Current());
													if (vmap.FindIndex(vertex) < 1)
														vmap.Add(vertex);
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}

		// Free Shells
		for (exp1.Init(shape, TopAbs_SHELL, TopAbs_SOLID); exp1.More(); exp1.Next())
		{
			TopoDS_Shell shell = TopoDS::Shell(exp1.Current());
			if (shmap.FindIndex(shell) < 1)
			{
				shmap.Add(shell);

				(*testout) << "shell " << shmap.FindIndex(shell) << " ";
				(*testout) << ((shell.Orientation() == TopAbs_REVERSED) ? "-" : "+") << ", ";
				(*testout) << ((exp1.Current().Orientation() == TopAbs_REVERSED) ? "-" : "+") << endl;

				for (exp2.Init(shell, TopAbs_FACE); exp2.More(); exp2.Next())
				{
					TopoDS_Face face = TopoDS::Face(exp2.Current());
					if (fmap.FindIndex(face) < 1)
					{
						fmap.Add(face);

						for (exp3.Init(face, TopAbs_WIRE); exp3.More(); exp3.Next())
						{
							TopoDS_Wire wire = TopoDS::Wire(exp3.Current());
							if (wmap.FindIndex(wire) < 1)
							{
								wmap.Add(wire);

								for (exp4.Init(wire, TopAbs_EDGE); exp4.More(); exp4.Next())
								{
									TopoDS_Edge edge = TopoDS::Edge(exp4.Current());
									if (emap.FindIndex(edge) < 1)
									{
										emap.Add(edge);
										for (exp5.Init(edge, TopAbs_VERTEX); exp5.More(); exp5.Next())
										{
											TopoDS_Vertex vertex = TopoDS::Vertex(exp5.Current());
											if (vmap.FindIndex(vertex) < 1)
												vmap.Add(vertex);
										}
									}
								}
							}
						}
					}
				}
			}
		}


		// Free Faces

		for (exp2.Init(shape, TopAbs_FACE, TopAbs_SHELL); exp2.More(); exp2.Next())
		{
			TopoDS_Face face = TopoDS::Face(exp2.Current());
			if (fmap.FindIndex(face) < 1)
			{
				fmap.Add(face);

				for (exp3.Init(exp2.Current(), TopAbs_WIRE); exp3.More(); exp3.Next())
				{
					TopoDS_Wire wire = TopoDS::Wire(exp3.Current());
					if (wmap.FindIndex(wire) < 1)
					{
						wmap.Add(wire);

						for (exp4.Init(exp3.Current(), TopAbs_EDGE); exp4.More(); exp4.Next())
						{
							TopoDS_Edge edge = TopoDS::Edge(exp4.Current());
							if (emap.FindIndex(edge) < 1)
							{
								emap.Add(edge);
								for (exp5.Init(exp4.Current(), TopAbs_VERTEX); exp5.More(); exp5.Next())
								{
									TopoDS_Vertex vertex = TopoDS::Vertex(exp5.Current());
									if (vmap.FindIndex(vertex) < 1)
										vmap.Add(vertex);
								}
							}
						}
					}
				}
			}
		}


		// Free Wires

		for (exp3.Init(shape, TopAbs_WIRE, TopAbs_FACE); exp3.More(); exp3.Next())
		{
			TopoDS_Wire wire = TopoDS::Wire(exp3.Current());
			if (wmap.FindIndex(wire) < 1)
			{
				wmap.Add(wire);

				for (exp4.Init(exp3.Current(), TopAbs_EDGE); exp4.More(); exp4.Next())
				{
					TopoDS_Edge edge = TopoDS::Edge(exp4.Current());
					if (emap.FindIndex(edge) < 1)
					{
						emap.Add(edge);
						for (exp5.Init(exp4.Current(), TopAbs_VERTEX); exp5.More(); exp5.Next())
						{
							TopoDS_Vertex vertex = TopoDS::Vertex(exp5.Current());
							if (vmap.FindIndex(vertex) < 1)
								vmap.Add(vertex);
						}
					}
				}
			}
		}


		// Free Edges

		for (exp4.Init(shape, TopAbs_EDGE, TopAbs_WIRE); exp4.More(); exp4.Next())
		{
			TopoDS_Edge edge = TopoDS::Edge(exp4.Current());
			if (emap.FindIndex(edge) < 1)
			{
				emap.Add(edge);
				for (exp5.Init(exp4.Current(), TopAbs_VERTEX); exp5.More(); exp5.Next())
				{
					TopoDS_Vertex vertex = TopoDS::Vertex(exp5.Current());
					if (vmap.FindIndex(vertex) < 1)
						vmap.Add(vertex);
				}
			}
		}


		// Free Vertices

		for (exp5.Init(shape, TopAbs_VERTEX, TopAbs_EDGE); exp5.More(); exp5.Next())
		{
			TopoDS_Vertex vertex = TopoDS::Vertex(exp5.Current());
			if (vmap.FindIndex(vertex) < 1)
				vmap.Add(vertex);
		}




		facemeshstatus.DeleteAll();
		facemeshstatus.SetSize(fmap.Extent());
		facemeshstatus = 0;

		// Philippose - 15/01/2009
		face_maxh.DeleteAll();
		face_maxh.SetSize(fmap.Extent());
		face_maxh = mparam.maxh;

		// Philippose - 15/01/2010      
		face_maxh_modified.DeleteAll();
		face_maxh_modified.SetSize(fmap.Extent());
		face_maxh_modified = 0;


		// Philippose - 17/01/2009
		face_sel_status.DeleteAll();
		face_sel_status.SetSize(fmap.Extent());
		face_sel_status = 0;

		fvispar.SetSize(fmap.Extent());
		evispar.SetSize(emap.Extent());
		vvispar.SetSize(vmap.Extent());

		fsingular.SetSize(fmap.Extent());
		esingular.SetSize(emap.Extent());
		vsingular.SetSize(vmap.Extent());

		fsingular = esingular = vsingular = false;
	}

	void OCCGeometry::SewFaces()
	{
		(*testout) << "Trying to sew faces ..." << endl;
		cout << "Trying to sew faces ..." << flush;

		BRepOffsetAPI_Sewing sewedObj(1);

		for (int i = 1; i <= fmap.Extent(); i++)
		{
			TopoDS_Face face = TopoDS::Face(fmap(i));
			sewedObj.Add(face);
		}

		sewedObj.Perform();

		if (!sewedObj.SewedShape().IsNull())
		{
			shape = sewedObj.SewedShape();
			cout << " done" << endl;
		}
		else
			cout << " not possible";
	}

	void OCCGeometry::MakeSolid()
	{
		TopExp_Explorer exp0;

		(*testout) << "Trying to build solids ..." << endl;
		cout << "Trying to build solids ..." << flush;

		BRepBuilderAPI_MakeSolid ms;
		int count = 0;
		for (exp0.Init(shape, TopAbs_SHELL); exp0.More(); exp0.Next())
		{
			count++;
			ms.Add(TopoDS::Shell(exp0.Current()));
		}

		if (!count)
		{
			cout << " not possible (no shells)" << endl;
			return;
		}

		BRepCheck_Analyzer ba(ms);
		if (ba.IsValid())
		{
			Handle(ShapeFix_Shape) sfs = new ShapeFix_Shape;
			sfs->Init(ms);

			sfs->SetPrecision(1e-5);
			sfs->SetMaxTolerance(1e-5);

			sfs->Perform();

			shape = sfs->Shape();

			for (exp0.Init(shape, TopAbs_SOLID); exp0.More(); exp0.Next())
			{
				TopoDS_Solid solid = TopoDS::Solid(exp0.Current());
				TopoDS_Solid newsolid = solid;
				BRepLib::OrientClosedSolid(newsolid);
				Handle(ShapeBuild_ReShape) rebuild = new ShapeBuild_ReShape;
				rebuild->Replace(solid, newsolid);

				TopoDS_Shape newshape = rebuild->Apply(shape, TopAbs_SHAPE, 1);
				shape = newshape;
			}

			cout << " done" << endl;
		}
		else
			cout << " not possible" << endl;
	}

	void OCCGeometry::BuildVisualizationMesh(double deflection)
	{
		BuildVisualizationMesh(deflection, true, 0.5);
	}
	
	// Discretizes the edges as BRepMesh does, then discretizes again, with the deflections scaled by the given
	// factor, every given edge. The edges are shared by the faces in the discrete model, so every face of such an
	// edge is meshed against the same finer polyline and the triangulations stay conforming. The other edges keep
	// the polylines the faces that are not meshed again already have.
	class RefiningEdgeDiscret : public IMeshTools_ModelAlgo
	{
	public:
		RefiningEdgeDiscret(const TopTools_DataMapOfShapeReal& edgeFactors, const TopTools_MapOfShape& edgesToDivide)
			: edgeFactors(edgeFactors), edgesToDivide(edgesToDivide) {}

	protected:
		bool performInternal(const Handle(IMeshData_Model)& model, const IMeshTools_Parameters& parameters,
							 const Message_ProgressRange& range) override
		{
			Handle(BRepMesh_EdgeDiscret) edgeDiscret = new BRepMesh_EdgeDiscret();
			if (!edgeDiscret->Perform(model, parameters, range)) return false;
			//
			for (int i = 0; i < model->EdgesNb(); i++)
			{
				const IMeshData::IEdgeHandle& dEdge = model->GetEdge(i);
				const double* factor = edgeFactors.Seek(dEdge->GetEdge());
				if (factor == nullptr || !edgesToDivide.Contains(dEdge->GetEdge()) || dEdge->GetDegenerated() ||
					dEdge->IsFree()) continue;
				//
				dEdge->SetDeflection(dEdge->GetDeflection() * *factor);
				dEdge->SetAngularDeflection(dEdge->GetAngularDeflection() * sqrt(*factor));
				IMeshTools_Parameters edgeParameters = parameters;
				edgeParameters.Relative = false;
				edgeParameters.Deflection = dEdge->GetDeflection();
				edgeParameters.Angle = dEdge->GetAngularDeflection();
				//
				const IMeshData::IPCurveHandle& pCurve = dEdge->GetPCurve(0);
				Handle(IMeshTools_CurveTessellator) tessellator =
					BRepMesh_EdgeDiscret::CreateEdgeTessellator(dEdge, pCurve->GetOrientation(), pCurve->GetFace(),
																edgeParameters);
				if (tessellator.IsNull()) continue;
				dEdge->Clear(false);
				BRepMesh_EdgeDiscret::Tessellate3d(dEdge, tessellator, true);
				BRepMesh_EdgeDiscret::Tessellate2d(dEdge, true);
			}
			return true;
		}

	private:
		TopTools_DataMapOfShapeReal edgeFactors;
		TopTools_MapOfShape edgesToDivide;
	};

	// BRepMesh leaves a face triangulated in part when the polylines of its edges cross in the parameter space of
	// the face - a thin face along long curved edges, discretized for their length rather than the width of the
	// face. The triangles then cover a small part of the face, while a coarse but whole triangulation of a curved
	// face is off its area by a fraction only.
	// The nodes on the edges past the crossing belong to no triangle, which is quick to find, so the area of the
	// face is computed only then.
	static double GetTriangulatedAreaFraction(const TopoDS_Face& face, TopTools_DataMapOfShapeReal& faceAreas)
	{
		TopLoc_Location location;
		Handle(Poly_Triangulation) triangulation = BRep_Tool::Triangulation(face, location);
		if (triangulation.IsNull() || triangulation->NbTriangles() == 0) return 0;
		//
		std::vector<bool> usedNodes(triangulation->NbNodes() + 1, false);
		Standard_Integer n1, n2, n3;
		for (Standard_Integer i = 1; i <= triangulation->NbTriangles(); i++)
		{
			triangulation->Triangle(i).Get(n1, n2, n3);
			usedNodes[n1] = true;
			usedNodes[n2] = true;
			usedNodes[n3] = true;
		}
		if (std::find(usedNodes.begin() + 1, usedNodes.end(), false) == usedNodes.end()) return 1;
		//
		const double* cachedArea = faceAreas.Seek(face);
		double faceArea;
		if (cachedArea != nullptr) faceArea = *cachedArea;
		else
		{
			GProp_GProps properties;
			BRepGProp::SurfaceProperties(face, properties);
			faceArea = properties.Mass();
			faceAreas.Bind(face, faceArea);
		}
		if (faceArea <= 0) return 1;
		//
		double triangulationArea = 0;
		for (Standard_Integer i = 1; i <= triangulation->NbTriangles(); i++)
		{
			triangulation->Triangle(i).Get(n1, n2, n3);
			gp_Vec v1(triangulation->Node(n1), triangulation->Node(n2));
			gp_Vec v2(triangulation->Node(n1), triangulation->Node(n3));
			triangulationArea += 0.5 * v1.Crossed(v2).Magnitude();
		}
		return triangulationArea / faceArea;
	}

	void OCCGeometry::BuildVisualizationMesh(double linearDeflection, bool relative, double angularDeflection)
	{
		cout << "Preparing visualization (linear deflection = " << linearDeflection <<
				", relative = " << std::boolalpha << relative <<
				", angular deflection = " << angularDeflection << ") ... " << flush;

		BRepTools::Clean(shape);
		//BRepMesh_IncrementalMesh(shape, deflection, true);
		BRepMesh_IncrementalMesh(shape, linearDeflection, relative, angularDeflection, true);	// parallel
		cout << "done" << endl;
		// Mesh again with the edges of every face triangulated in part divided finer, until its edge polylines
		// no longer cross. The other edges are divided as before, so the rest of the mesh does not change. A face
		// whose triangles cover no more of it after a refinement is not helped by one, and its edges are divided as
		// before again, so its neighbours are not meshed finer for nothing.
		const int maxRefinements = 3;
		const double minPartialFraction = 0.5;
		const double refinementFactor = 0.25;
		NCollection_DataMap<TopoDS_Shape, int, TopTools_ShapeMapHasher> faceLevels;
		TopTools_DataMapOfShapeReal faceFractions;
		TopTools_MapOfShape hopelessFaces;
		TopTools_DataMapOfShapeReal appliedEdgeFactors;
		TopTools_DataMapOfShapeReal faceAreas;
		TopTools_IndexedDataMapOfShapeListOfShape edgeFaces;
		TopExp::MapShapesAndAncestors(shape, TopAbs_EDGE, TopAbs_FACE, edgeFaces);
		stringstream faceIds;
		for (int refinement = 0; refinement <= maxRefinements; refinement++)
		{
			bool changed = false;
			faceIds.str("");
			stringstream refinedFaceIds;
			TopTools_MapOfShape faces;
			for (TopExp_Explorer exp(shape, TopAbs_FACE); exp.More(); exp.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp.Current());
				if (!faces.Add(face)) continue;
				double fraction = GetTriangulatedAreaFraction(face, faceAreas);
				if (fraction >= minPartialFraction) continue;
				faceIds << " " << fmap.FindIndex(face);
				if (hopelessFaces.Contains(face)) continue;
				//
				const double* previousFraction = faceFractions.Seek(face);
				if (previousFraction != nullptr && fraction <= *previousFraction + 0.01)
				{
					hopelessFaces.Add(face);
					faceLevels.UnBind(face);
					changed = true;
				}
				else if (refinement < maxRefinements)
				{
					faceFractions.Bind(face, fraction);
					int* level = faceLevels.ChangeSeek(face);
					if (level != nullptr) (*level)++;
					else faceLevels.Bind(face, 1);
					refinedFaceIds << " " << fmap.FindIndex(face);
					changed = true;
				}
			}
			if (!changed) break;
			//
			TopTools_DataMapOfShapeReal edgeFactors;
			for (NCollection_DataMap<TopoDS_Shape, int, TopTools_ShapeMapHasher>::Iterator it(faceLevels);
				 it.More(); it.Next())
			{
				double faceFactor = pow(refinementFactor, it.Value());
				for (TopExp_Explorer expEdge(it.Key(), TopAbs_EDGE); expEdge.More(); expEdge.Next())
				{
					const TopoDS_Shape& edge = expEdge.Current();
					if (BRep_Tool::Degenerated(TopoDS::Edge(edge))) continue;
					double* factor = edgeFactors.ChangeSeek(edge);
					if (factor == nullptr) edgeFactors.Bind(edge, faceFactor);
					else if (faceFactor < *factor) *factor = faceFactor;
				}
			}
			//
			// Only the faces of the edges divided differently than in the last meshing are meshed again
			TopTools_MapOfShape changedEdges;
			for (TopTools_DataMapOfShapeReal::Iterator it(edgeFactors); it.More(); it.Next())
			{
				const double* appliedFactor = appliedEdgeFactors.Seek(it.Key());
				if (appliedFactor == nullptr || *appliedFactor != it.Value()) changedEdges.Add(it.Key());
			}
			for (TopTools_DataMapOfShapeReal::Iterator it(appliedEdgeFactors); it.More(); it.Next())
			{
				if (!edgeFactors.IsBound(it.Key())) changedEdges.Add(it.Key());
			}
			TopTools_MapOfShape facesToMesh;
			for (TopTools_MapOfShape::Iterator it(changedEdges); it.More(); it.Next())
			{
				for (TopTools_ListOfShape::Iterator itFace(edgeFaces.FindFromKey(it.Key())); itFace.More(); itFace.Next())
					facesToMesh.Add(itFace.Value());
			}
			// An edge keeps its finer polyline from a face that is not meshed again, and is divided again only when
			// all of its faces are
			TopTools_MapOfShape edgesToDivide;
			for (TopTools_DataMapOfShapeReal::Iterator it(edgeFactors); it.More(); it.Next())
			{
				bool allFacesToMesh = true;
				for (TopTools_ListOfShape::Iterator itFace(edgeFaces.FindFromKey(it.Key())); itFace.More(); itFace.Next())
				{
					if (!facesToMesh.Contains(itFace.Value())) allFacesToMesh = false;
				}
				if (allFacesToMesh) edgesToDivide.Add(it.Key());
			}
			appliedEdgeFactors = edgeFactors;
			//
			if (refinedFaceIds.str().empty())
				cout << "Dividing the edges of the face(s) a refinement did not help as before ... " << flush;
			else
				cout << "Dividing the edges of the face(s) triangulated in part finer:" << refinedFaceIds.str() << " ... "
					 << flush;
			BRep_Builder builder;
			for (TopTools_MapOfShape::Iterator it(facesToMesh); it.More(); it.Next())
				builder.UpdateFace(TopoDS::Face(it.Value()), Handle(Poly_Triangulation)());
			BRepMesh_IncrementalMesh mesher;
			mesher.SetShape(shape);
			mesher.ChangeParameters().Deflection = linearDeflection;
			mesher.ChangeParameters().Angle = angularDeflection;
			mesher.ChangeParameters().Relative = relative;
			mesher.ChangeParameters().InParallel = true;
			Handle(BRepMesh_Context) context = new BRepMesh_Context();
			context->SetEdgeDiscret(new RefiningEdgeDiscret(edgeFactors, edgesToDivide));
			mesher.Perform(context);
			cout << "done" << endl;
		}
		if (!faceLevels.IsEmpty() || !hopelessFaces.IsEmpty())
		{
			faceIds.str("");
			TopTools_MapOfShape faces;
			for (TopExp_Explorer exp(shape, TopAbs_FACE); exp.More(); exp.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp.Current());
				if (faces.Add(face) && GetTriangulatedAreaFraction(face, faceAreas) < minPartialFraction)
					faceIds << " " << fmap.FindIndex(face);
			}
			if (!faceIds.str().empty())
				cout << "WARNING: face(s)" << faceIds.str() << " are still triangulated only in part." << endl;
		}
	}

	void OCCGeometry::CalcBoundingBox()
	{
		Bnd_Box b;

		// SDS Not defined !

		BRepBndLib::Add((const TopoDS_Shape)shape, b, (Standard_Boolean)true);

		// SDS
		double x1, y1, z1, x2, y2, z2;
		b.Get(x1, y1, z1, x2, y2, z2);
		Point<3> p1 = Point<3>(x1, y1, z1);
		Point<3> p2 = Point<3>(x2, y2, z2);

		(*testout) << "Bounding Box = [" << p1 << " - " << p2 << "]" << endl;
		boundingbox = Box<3>(p1, p2);
		SetCenter();
	}


	void OCCGeometry::Project(int surfi, Point<3> & p) const
	{
		static int cnt = 0;
		if (++cnt % 1000 == 0) cout << "Project cnt = " << cnt << endl;

		gp_Pnt pnt(p(0), p(1), p(2));

		double u, v;
		Handle(Geom_Surface) thesurf = BRep_Tool::Surface(TopoDS::Face(fmap(surfi)));
		Handle(ShapeAnalysis_Surface) su = new ShapeAnalysis_Surface(thesurf);
		gp_Pnt2d suval = su->ValueOfUV(pnt, BRep_Tool::Tolerance(TopoDS::Face(fmap(surfi))));
		suval.Coord(u, v);
		pnt = thesurf->Value(u, v);


		p = Point<3>(pnt.X(), pnt.Y(), pnt.Z());

	}

	bool OCCGeometry::FastProject(int surfi, Point<3> & ap, double& u, double& v) const
	{
		gp_Pnt p(ap(0), ap(1), ap(2));

		Handle(Geom_Surface) surface = BRep_Tool::Surface(TopoDS::Face(fmap(surfi)));

		gp_Pnt x = surface->Value(u, v);

		if (p.SquareDistance(x) <= sqr(PROJECTION_TOLERANCE)) return true;

		gp_Vec du, dv;

		surface->D1(u, v, x, du, dv);

		int count = 0;

		gp_Pnt xold;
		gp_Vec n;
		double det, lambda, mu;

		do {
			count++;

			n = du ^ dv;

			det = Det3(n.X(), du.X(), dv.X(),
				n.Y(), du.Y(), dv.Y(),
				n.Z(), du.Z(), dv.Z());

			if (det < 1e-15) return false;

			lambda = Det3(n.X(), p.X() - x.X(), dv.X(),
				n.Y(), p.Y() - x.Y(), dv.Y(),
				n.Z(), p.Z() - x.Z(), dv.Z()) / det;

			mu = Det3(n.X(), du.X(), p.X() - x.X(),
				n.Y(), du.Y(), p.Y() - x.Y(),
				n.Z(), du.Z(), p.Z() - x.Z()) / det;

			u += lambda;
			v += mu;

			xold = x;
			surface->D1(u, v, x, du, dv);

		} while (xold.SquareDistance(x) > sqr(PROJECTION_TOLERANCE) && count < 50);

		//    (*testout) << "FastProject count: " << count << endl;

		if (count == 50) return false;

		ap = Point<3>(x.X(), x.Y(), x.Z());

		return true;
	}


	void OCCGeometry::WriteOCC_STL(char * filename)
	{
		cout << "writing stl..."; cout.flush();
		StlAPI_Writer writer;
		//      writer.RelativeMode() = Standard_False;

		//      writer.SetDeflection(0.02);
		writer.Write(shape, filename);

		cout << "done" << endl;
	}

	// Philippose - 23/02/2009
	/* Special IGES File load function including the ability
	to extract individual surface colours via the extended
	OpenCascade XDE and XCAF Feature set.
	*/
	OCCGeometry * LoadOCC_IGES(const char *filename)
	{
		OCCGeometry *occgeo;
		occgeo = new OCCGeometry;

		// Initiate a dummy XCAF Application to handle the IGES XCAF Document
		static Handle(XCAFApp_Application) dummy_app = XCAFApp_Application::GetApplication();

		// Create an XCAF Document to contain the IGES file itself
		Handle(TDocStd_Document) iges_doc;

		// Check if a IGES File is already open under this handle, if so, close it to prevent
		// Segmentation Faults when trying to create a new document
		if (dummy_app->NbDocuments() > 0)
		{
			dummy_app->GetDocument(1, iges_doc);
			dummy_app->Close(iges_doc);
		}
		dummy_app->NewDocument("IGES-XCAF", iges_doc);

		IGESCAFControl_Reader reader;

		Standard_Integer stat = reader.ReadFile((char*)filename);

		if (stat != IFSelect_RetDone)
		{
			delete occgeo;
			return NULL;
		}

		// Enable transfer of colours
		reader.SetColorMode(Standard_True);

		reader.Transfer(iges_doc);

		// Read in the shape(s) and the colours present in the IGES File
		Handle(XCAFDoc_ShapeTool) iges_shape_contents = XCAFDoc_DocumentTool::ShapeTool(iges_doc->Main());
		Handle(XCAFDoc_ColorTool) iges_colour_contents = XCAFDoc_DocumentTool::ColorTool(iges_doc->Main());

		TDF_LabelSequence iges_shapes;
		iges_shape_contents->GetShapes(iges_shapes);

		// List out the available colours in the IGES File as Colour Names
		TDF_LabelSequence all_colours;
		iges_colour_contents->GetColors(all_colours);
		PrintMessage(1, "Number of colours in IGES File: ", all_colours.Length());
		for (int i = 1; i <= all_colours.Length(); i++)
		{
			Quantity_Color col;
			stringstream col_rgb;
			iges_colour_contents->GetColor(all_colours.Value(i), col);
			col_rgb << " : (" << col.Red() << "," << col.Green() << "," << col.Blue() << ")";
			PrintMessage(1, "Colour [", i, "] = ", col.StringName(col.Name()), col_rgb.str());
		}


		// For the IGES Reader, all the shapes can be exported as one compund shape 
		// using the "OneShape" member
		occgeo->shape = reader.OneShape();
		occgeo->face_colours = iges_colour_contents;
		occgeo->changed = 1;
		occgeo->BuildFMap();

		occgeo->CalcBoundingBox();
		PrintContents(occgeo);

		return occgeo;
	}

	// Philippose - 29/01/2009
	/* Special STEP File load function including the ability
	to extract individual surface colours via the extended
	OpenCascade XDE and XCAF Feature set.
	*/

	//void ExtractSolidsRecursive(const TopoDS_Shape& shape, BRep_Builder& builder, TopoDS_Compound& solidCompound)
	//{
	//	TopAbs_ShapeEnum type = shape.ShapeType();

	//	if (type == TopAbs_SOLID)
	//	{
	//		builder.Add(solidCompound, shape);
	//	}
	//	else if (type == TopAbs_COMPOUND || type == TopAbs_COMPSOLID)
	//	{
	//		for (TopoDS_Iterator it(shape); it.More(); it.Next())
	//		{
	//			ExtractSolidsRecursive(it.Value(), builder, solidCompound);
	//		}
	//	}
	//	// else ignore (e.g. SHELL, FACE, EDGE)
	//}

	void ExtractSolidsRecursive(const TopoDS_Shape& shape, BRep_Builder& builder, TopoDS_Compound& targetCompound)
	{
		TopAbs_ShapeEnum type = shape.ShapeType();
		//
		if (type == TopAbs_SHELL)
		{
			TopoDS_Shell shell = TopoDS::Shell(shape);
			//
			if (BRep_Tool::IsClosed(shell))
			{
				std::cout << "Found closed shell." << std::endl;
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
					builder.Add(targetCompound, solid);
				}
				else
				{
					std::cout << "Solid is invalid." << std::endl;
					builder.Add(targetCompound, shell);
				}
			}
			else
			{
				std::cout << "Shell is not closed and cannot be converted to a solid." << std::endl;
				builder.Add(targetCompound, shell);
			}
		}
		//
		else if (type == TopAbs_SOLID)
		{
			builder.Add(targetCompound, shape);
		}
		else if (type == TopAbs_COMPOUND || type == TopAbs_COMPSOLID)
		{
			for (TopoDS_Iterator it(shape); it.More(); it.Next())
			{
				ExtractSolidsRecursive(it.Value(), builder, targetCompound);
			}
		}
	}

	void AddShapeRecursive(const Handle(XCAFDoc_ShapeTool)& shapeTool, const TDF_Label& label,
						   const TopLoc_Location& parentLoc, BRep_Builder& builder, TopoDS_Compound& result)
	{
		TopLoc_Location loc = parentLoc * shapeTool->GetLocation(label);
		//
		if (shapeTool->IsAssembly(label))
		{
			TDF_LabelSequence components;
			shapeTool->GetComponents(label, components);
			//
			for (Standard_Integer i = 1; i <= components.Length(); ++i)
			{
				AddShapeRecursive(shapeTool, components.Value(i), loc, builder, result);
			}
		}
		else
		{
			TopoDS_Shape shape = shapeTool->GetShape(label);
			if (shape.IsNull()) return;
			//
			TopoDS_Shape locatedShape = shape.Located(loc);
			builder.Add(result, locatedShape);
		}
	}

	OCCGeometry * LoadOCC_STEP_old(const char * filename)
	{
		//STEPControl_Reader o_step_reader;
		//o_step_reader.ReadFile(s_file_name);
		//DeclareAndCast(StepData_StepModel, po_model, o_step_reader.Model());

		//for (int i = 1; i < po_model->NbEntities(); i++)
		//{
		//	if (po_model->Entity(i)->IsKind(STANDARD_TYPE(StepBasic_LengthMeasureWithUnit)))
		//	{
		//		DeclareAndCast(StepBasic_LengthMeasureWithUnit, po_lmwu, po_model->Entity(i));

		//		if (po_lmwu->ValueComponent() == 25.4)
		//		{
		//			//INCHES
		//		}
		//		break;
		//	}
		//}

		OCCGeometry * occgeo;
		occgeo = new OCCGeometry;

		// Initiate a dummy XCAF Application to handle the STEP XCAF Document
		static Handle(XCAFApp_Application) dummy_app = XCAFApp_Application::GetApplication();

		// Create an XCAF Document to contain the STEP file itself
		Handle(TDocStd_Document) step_doc;

		// Check if a STEP File is already open under this handle, if so, close it to prevent
		// Segmentation Faults when trying to create a new document
		if (dummy_app->NbDocuments() > 0)
		{
			dummy_app->GetDocument(1, step_doc);
			dummy_app->Close(step_doc);
		}
		dummy_app->NewDocument("STEP-XCAF", step_doc);

		STEPCAFControl_Reader reader;

		// Enable transfer of colours
		reader.SetColorMode(Standard_True);

		// Unicode strings
		Standard_CString path = (char*)filename;
		//
		PrintMessage(0, "Reading STEP file: ", path);
		//	  
		Standard_Integer stat = reader.ReadFile(path);
		//Standard_Integer stat = reader.ReadFile((char*)filename);

		if (stat != IFSelect_RetDone)
		{
			delete occgeo;
			return NULL;
		}

		reader.Transfer(step_doc);

		// Read in the shape(s) and the colours present in the STEP File
		Handle(XCAFDoc_ShapeTool) step_shape_contents = XCAFDoc_DocumentTool::ShapeTool(step_doc->Main());
		Handle(XCAFDoc_ColorTool) step_colour_contents = XCAFDoc_DocumentTool::ColorTool(step_doc->Main());

		TDF_LabelSequence step_shapes;
		step_shape_contents->GetShapes(step_shapes);

		// List out the available colours in the STEP File as Colour Names
		TDF_LabelSequence all_colours;
		step_colour_contents->GetColors(all_colours);
		PrintMessage(1, "Number of colours in STEP File: ", all_colours.Length());
		for (int i = 1; i <= all_colours.Length(); i++)
		{
			Quantity_Color col;
			stringstream col_rgb;
			step_colour_contents->GetColor(all_colours.Value(i), col);
			col_rgb << " : (" << col.Red() << "," << col.Green() << "," << col.Blue() << ")";
			PrintMessage(1, "Colour [", i, "] = ", col.StringName(col.Name()), col_rgb.str());
		}

		// Added to take care of multiple shapes without the compound - ChatGPT
		// If there is an assembly in assembly the first shape is the main compound
		// and the following shapes are sub-compounds and then parts
		// But some models have multiple shapes that are not compounds
		TopoDS_Shape shape = step_shape_contents->GetShape(step_shapes.Value(1));
		if (step_shapes.Length() > 1 && shape.ShapeType() != TopAbs_COMPOUND)
		{
			BRep_Builder builder;
			TopoDS_Compound compound;
			builder.MakeCompound(compound);
			//
			for (Standard_Integer i = 1; i <= step_shapes.Length(); ++i)
			{
				shape = step_shape_contents->GetShape(step_shapes.Value(i));
				if (!shape.IsNull())
					builder.Add(compound, shape);
			}
			occgeo->shape = compound;
		}
		else
		{
			// For the STEP File Reader in OCC, the 1st Shape contains the entire 
			// compound geometry as one shape
			occgeo->shape = shape;
		}
		
		occgeo->face_colours = step_colour_contents;
		occgeo->changed = 1;
		occgeo->BuildFMap();

		occgeo->CalcBoundingBox();
		PrintContents(occgeo);

		return occgeo;
	}

	OCCGeometry* LoadOCC_STEP(const char* filename)
	{
		// Created by Chat GPT
		OCCGeometry* occgeo = new OCCGeometry;
		//
		static Handle(XCAFApp_Application) app = XCAFApp_Application::GetApplication();
		Handle(TDocStd_Document) doc;
		//
		if (app->NbDocuments() > 0)
		{
			app->GetDocument(1, doc);
			app->Close(doc);
		}
		//
		app->NewDocument("STEP-XCAF", doc);
		//
		STEPCAFControl_Reader reader;
		reader.SetColorMode(Standard_True);
		reader.SetNameMode(Standard_True);
		reader.SetLayerMode(Standard_True);
		//
		if (reader.ReadFile(filename) != IFSelect_RetDone)
		{
			delete occgeo;
			return nullptr;
		}
		//
		reader.Transfer(doc);
		//
		Handle(XCAFDoc_ShapeTool) shapeTool = XCAFDoc_DocumentTool::ShapeTool(doc->Main());
		Handle(XCAFDoc_ColorTool) colorTool = XCAFDoc_DocumentTool::ColorTool(doc->Main());
		//
		TDF_LabelSequence freeShapes;
		shapeTool->GetFreeShapes(freeShapes);
		//
		if (freeShapes.Length() == 0)
		{
			delete occgeo;
			return nullptr;
		}
		// List out the available colours in the STEP File as Colour Names
		TDF_LabelSequence all_colours;
		colorTool->GetColors(all_colours);
		PrintMessage(1, "Number of colours in STEP File: ", all_colours.Length());
		for (int i = 1; i <= all_colours.Length(); i++)
		{
			Quantity_Color col;
			stringstream col_rgb;
			colorTool->GetColor(all_colours.Value(i), col);
			col_rgb << " : (" << col.Red() << "," << col.Green() << "," << col.Blue() << ")";
			PrintMessage(1, "Colour [", i, "] = ", col.StringName(col.Name()), col_rgb.str());
		}
		//
		BRep_Builder builder;
		TopoDS_Compound compound;
		builder.MakeCompound(compound);
		//
		for (Standard_Integer i = 1; i <= freeShapes.Length(); ++i)
		{
			AddShapeRecursive(shapeTool, freeShapes.Value(i), TopLoc_Location(), builder, compound);
		}
		//
		occgeo->shape = compound;
		occgeo->face_colours = colorTool;
		occgeo->changed = 1;
		occgeo->BuildFMap();
		occgeo->CalcBoundingBox();
		//
		PrintContents(occgeo);
		//
		return occgeo;
	}


	OCCGeometry * LoadOCC_BREP(const char *filename)
	{
		OCCGeometry * occgeo;
		occgeo = new OCCGeometry;
		cout << "Highest entry in topology hierarchy: " << endl;
		BRep_Builder aBuilder;
		Standard_Boolean result = BRepTools::Read(occgeo->shape, const_cast<char*> (filename), aBuilder);

		if (!result)
		{
			delete occgeo;
			return NULL;
		}

		// Philippose - 23/02/2009
		// Fixed a bug in the OpenCascade XDE Colour handling when 
		// opening BREP Files, since BREP Files have no colour data.
		// Hence, the face_colours Handle needs to be created as a NULL handle.
		occgeo->face_colours = Handle(XCAFDoc_ColorTool)();
		occgeo->face_colours.Nullify();
		occgeo->changed = 1;
		occgeo->BuildFMap();

		occgeo->CalcBoundingBox();
		PrintContents(occgeo);

		return occgeo;
	}


	void OCCGeometry::Save(string sfilename) const
	{
		const char * filename = sfilename.c_str();
		if (strlen(filename) < 4)
			throw NgException("illegal filename");

		if (strcmp(&filename[strlen(filename) - 3], "igs") == 0)
		{
			IGESControl_Writer writer("millimeters", 1);
			writer.AddShape(shape);
			writer.Write(filename);
		}
		else if (strcmp(&filename[strlen(filename) - 3], "stp") == 0)
		{
			STEPControl_Writer writer;
			writer.Transfer(shape, STEPControl_AsIs);
			writer.Write(filename);
		}
		else if (strcmp(&filename[strlen(filename) - 3], "stl") == 0)
		{
			StlAPI_Writer writer;
			writer.ASCIIMode() = Standard_True;
			writer.Write(shape, filename);
		}
		else if (strcmp(&filename[strlen(filename) - 4], "stlb") == 0)
		{
			StlAPI_Writer writer;
			writer.ASCIIMode() = Standard_False;
			writer.Write(shape, filename);
		}
	}


	void OCCGeometry::RecursiveTopologyTree(const TopoDS_Shape & sh, stringstream & str, TopAbs_ShapeEnum l, bool isfree, const char * lname)
	{
		if (l > TopAbs_VERTEX) return;

		TopExp_Explorer e;
		int count = 0;
		int count2 = 0;

		if (isfree)
			e.Init(sh, l, TopAbs_ShapeEnum(l - 1));
		else
			e.Init(sh, l);

		for (; e.More(); e.Next())
		{
			count++;

			stringstream lname2;
			lname2 << lname << "/" << shapename[l] << count;
			str << lname2.str() << " ";

			switch (e.Current().ShapeType())
			{
			case TopAbs_SOLID:
				count2 = somap.FindIndex(TopoDS::Solid(e.Current())); break;
			case TopAbs_SHELL:
				count2 = shmap.FindIndex(TopoDS::Shell(e.Current())); break;
			case TopAbs_FACE:
				count2 = fmap.FindIndex(TopoDS::Face(e.Current())); break;
			case TopAbs_WIRE:
				count2 = wmap.FindIndex(TopoDS::Wire(e.Current())); break;
			case TopAbs_EDGE:
				count2 = emap.FindIndex(TopoDS::Edge(e.Current())); break;
			case TopAbs_VERTEX:
				count2 = vmap.FindIndex(TopoDS::Vertex(e.Current())); break;
			default:
				cout << "RecursiveTopologyTree: Case " << e.Current().ShapeType() << " not handeled" << endl;
			}

			int nrsubshapes = 0;

			if (l <= TopAbs_WIRE)
			{
				TopExp_Explorer e2;
				for (e2.Init(e.Current(), TopAbs_ShapeEnum(l + 1));
					e2.More(); e2.Next())
					nrsubshapes++;
			}

			str << "{" << shapename[l] << " " << count2;

			if (l <= TopAbs_EDGE)
			{
				str << " (" << orientationstring[e.Current().Orientation()];
				if (nrsubshapes != 0) str << ", " << nrsubshapes;
				str << ") } ";
			}
			else
				str << " } ";

			RecursiveTopologyTree(e.Current(), str, TopAbs_ShapeEnum(l + 1),
				false, (char*)lname2.str().c_str());

		}
	}

	void OCCGeometry::GetTopologyTree(stringstream & str)
	{
		cout << "Building topology tree ... " << flush;
		RecursiveTopologyTree(shape, str, TopAbs_COMPSOLID, false, "CompSolids");
		RecursiveTopologyTree(shape, str, TopAbs_SOLID, true, "FreeSolids");
		RecursiveTopologyTree(shape, str, TopAbs_SHELL, true, "FreeShells");
		RecursiveTopologyTree(shape, str, TopAbs_FACE, true, "FreeFaces");
		RecursiveTopologyTree(shape, str, TopAbs_WIRE, true, "FreeWires");
		RecursiveTopologyTree(shape, str, TopAbs_EDGE, true, "FreeEdges");
		RecursiveTopologyTree(shape, str, TopAbs_VERTEX, true, "FreeVertices");
		str << flush;
		//  cout << "done" << endl;
	}


	void OCCGeometry::CheckIrregularEntities(stringstream & str)
	{
		ShapeAnalysis_CheckSmallFace csm;

		csm.SetTolerance(1e-6);

		TopTools_DataMapOfShapeListOfShape mapEdges;
		ShapeAnalysis_DataMapOfShapeListOfReal mapParam;
		TopoDS_Compound theAllVert;

		int spotfaces = 0;
		int stripsupportfaces = 0;
		int singlestripfaces = 0;
		int stripfaces = 0;
		int facessplitbyvertices = 0;
		int stretchedpinfaces = 0;
		int smoothpinfaces = 0;
		int twistedfaces = 0;
		// int edgessamebutnotidentified = 0;

		cout << "checking faces ... " << flush;

		int i;
		for (i = 1; i <= fmap.Extent(); i++)
		{
			TopoDS_Face face = TopoDS::Face(fmap(i));
			TopoDS_Edge e1, e2;

			if (csm.CheckSpotFace(face))
			{
				if (!spotfaces++)
					str << "SpotFace {Spot face} ";

				(*testout) << "Face " << i << " is a spot face" << endl;
				str << "SpotFace/Face" << i << " ";
				str << "{Face " << i << " } ";
			}

			if (csm.IsStripSupport(face))
			{
				if (!stripsupportfaces++)
					str << "StripSupportFace {Strip support face} ";

				(*testout) << "Face " << i << " has strip support" << endl;
				str << "StripSupportFace/Face" << i << " ";
				str << "{Face " << i << " } ";
			}

			if (csm.CheckSingleStrip(face, e1, e2))
			{
				if (!singlestripfaces++)
					str << "SingleStripFace {Single strip face} ";

				(*testout) << "Face " << i << " is a single strip (edge " << emap.FindIndex(e1)
					<< " and edge " << emap.FindIndex(e2) << " are identical)" << endl;
				str << "SingleStripFace/Face" << i << " ";
				str << "{Face " << i << " (edge " << emap.FindIndex(e1)
					<< " and edge " << emap.FindIndex(e2) << " are identical)} ";
			}

			if (csm.CheckStripFace(face, e1, e2))
			{
				if (!stripfaces++)
					str << "StripFace {Strip face} ";

				(*testout) << "Face " << i << " is a strip (edge " << emap.FindIndex(e1)
					<< " and edge " << emap.FindIndex(e2)
					<< " are identical)" << endl;
				str << "StripFace/Face" << i << " ";
				str << "{Face " << i << " (edge " << emap.FindIndex(e1)
					<< " and edge " << emap.FindIndex(e2) << " are identical)} ";
			}

			if (int count = csm.CheckSplittingVertices(face, mapEdges, mapParam, theAllVert))
			{
				if (!facessplitbyvertices++)
					str << "FaceSplitByVertices {Face split by vertices} ";

				(*testout) << "Face " << i << " is split by " << count
					<< " vertex/vertices " << endl;
				str << "FaceSplitByVertices/Face" << i << " ";
				str << "{Face " << i << " (split by " << count << "vertex/vertices)} ";
			}

			int whatrow, sens;
			if (int type = csm.CheckPin(face, whatrow, sens))
			{
				if (type == 1)
				{
					if (!smoothpinfaces++)
						str << "SmoothPinFace {Smooth pin face} ";

					(*testout) << "Face " << i << " is a smooth pin" << endl;
					str << "SmoothPinFace/Face" << i << " ";
					str << "{Face " << i << " } ";
				}
				else
				{
					if (!stretchedpinfaces++)
						str << "StretchedPinFace {Stretched pin face} ";

					(*testout) << "Face " << i << " is a streched pin" << endl;
					str << "StretchedPinFace/Face" << i << " ";
					str << "{Face " << i << " } ";
				}
			}

			double paramu, paramv;
			if (csm.CheckTwisted(face, paramu, paramv))
			{
				if (!twistedfaces++)
					str << "TwistedFace {Twisted face} ";

				(*testout) << "Face " << i << " is twisted" << endl;
				str << "TwistedFace/Face" << i << " ";
				str << "{Face " << i << " } ";
			}
		}

		cout << "done" << endl;
		cout << "checking edges ... " << flush;

		// double dmax;
		// int cnt = 0;
		Array <double> edgeLengths;
		Array <int> order;
		edgeLengths.SetSize(emap.Extent());
		order.SetSize(emap.Extent());

		for (i = 1; i <= emap.Extent(); i++)
		{
			TopoDS_Edge edge1 = TopoDS::Edge(emap(i));
			GProp_GProps system;
			BRepGProp::LinearProperties(edge1, system);
			edgeLengths[i - 1] = system.Mass();
		}

		Sort(edgeLengths, order);

		str << "ShortestEdges {Shortest edges} ";
		for (i = 1; i <= min(20, emap.Extent()); i++)
		{
			str << "ShortestEdges/Edge" << i;
			str << " {Edge " << order[i - 1] << " (L=" << edgeLengths[order[i - 1] - 1] << ")} ";
		}

		str << flush;

		cout << "done" << endl;
	}

	void OCCGeometry::GetUnmeshedFaceInfo(stringstream & str)
	{
		for (int i = 1; i <= fmap.Extent(); i++)
		{
			if (facemeshstatus[i - 1] == -1)
				str << "Face" << i << " {Face " << i << " } ";
		}
		str << flush;
	}


	void OCCGeometry::GetNotDrawableFaces(stringstream & str)
	{
		for (int i = 1; i <= fmap.Extent(); i++)
		{
			if (!fvispar[i - 1].IsDrawable())
				str << "Face" << i << " {Face " << i << " } ";
		}
		str << flush;
	}

	bool OCCGeometry::ErrorInSurfaceMeshing()
	{
		for (int i = 1; i <= fmap.Extent(); i++)
			if (facemeshstatus[i - 1] == -1)
				return true;

		return false;
	}


	int OCCGeometry::GenerateMesh(Mesh*& mesh, MeshingParameters & mparam, int perfstepsstart, int perfstepsend)
	{
		return OCCGenerateMesh(*this, mesh, mparam, perfstepsstart, perfstepsend);
	}

	const Refinement & OCCGeometry::GetRefinement() const
	{
		return *new OCCRefinementSurfaces(*this);
	}


	OCCParameters::OCCParameters()
	{
		resthcloseedgefac = 1;
		resthcloseedgeenable = 1;
		resthminedgelen = 0.001;
		resthminedgelenenable = 1;
	}

	void OCCParameters::Print(ostream & ost) const
	{
		ost << "OCC Parameters:" << endl
			<< "close edges: " << resthcloseedgeenable
			<< ", fac = " << resthcloseedgefac << endl
			<< "minimum edge length: " << resthminedgelenenable
			<< ", min len = " << resthminedgelen << endl;
	}
}


#endif
