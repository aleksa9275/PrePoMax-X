#ifdef OCCGEOMETRY

#include <mystdlib.h>
#include <TopTools_IndexedDataMapOfShapeListOfShape.hxx>
#include <occgeom.hpp>
#include <meshing.hpp>
#include "occparallel.hpp"
#include "occtransfinite.hpp"

#include <algorithm>
#include <vector>


namespace netgen
{

#include "occmeshsurf.hpp"

#define TCL_OK 0
#define TCL_ERROR 1

#define DIVIDEEDGESECTIONS 1000
#define IGNORECURVELENGTH 1e-4
#define VSMALL 1e-10


	bool merge_solids = 1;


	// can you please explain what you intend to compute here (JS) !!!
	double Line::Dist(Line l)
	{
		Vec<3> n = p1 - p0;
		Vec<3> q = l.p1 - l.p0;
		double nq = n * q;

		Point<3> p = p0 + 0.5*n;
		double lambda = (p - l.p0)*n / (nq + VSMALL);

		if (lambda >= 0 && lambda <= 1)
		{
			double d = (p - l.p0 - lambda * q).Length();
			//        if (d < 1e-3) d = 1e99;
			return d;
		}
		else
			return 1e99;
	}



	double Line::Length()
	{
		return (p1 - p0).Length();
	}



	inline Point<3> occ2ng(const gp_Pnt & p)
	{
		return  Point<3>(p.X(), p.Y(), p.Z());
	}



	double ComputeH(double kappa)
	{
		kappa *= mparam.curvaturesafety;
		double hret = (mparam.maxh * kappa < 1)
			? mparam.maxh
			: 1 / (kappa + VSMALL);
		return min(mparam.maxh, hret);
	}

	static double ComputeH(double kappa, double maxh, double curvature_safety)
	{
		double hret;
		kappa *= curvature_safety;

		if (maxh * kappa < 1)
			hret = maxh;
		else
			hret = 1 / (kappa + VSMALL);

		if (maxh < hret)
			hret = maxh;

		return (hret);
	}




	void CollectHTriangleRestrictions(gp_Pnt2d & par0, gp_Pnt2d & par1, gp_Pnt2d & par2,
		BRepLProp_SLProps * prop, std::vector<LocalHRestriction> & restrictions,
		double maxh, double curvature_safety, int depth, double h = 0)
	{
		int ls = -1;

		gp_Pnt pnt0, pnt1, pnt2;

		prop->SetParameters(par0.X(), par0.Y());
		pnt0 = prop->Value();

		prop->SetParameters(par1.X(), par1.Y());
		pnt1 = prop->Value();

		prop->SetParameters(par2.X(), par2.Y());
		pnt2 = prop->Value();

		double aux;
		double maxside = pnt0.Distance(pnt1);
		ls = 2;
		aux = pnt1.Distance(pnt2);
		if (aux > maxside)
		{
			maxside = aux;
			ls = 0;
		}
		aux = pnt2.Distance(pnt0);
		if (aux > maxside)
		{
			maxside = aux;
			ls = 1;
		}



		gp_Pnt2d parmid;

		parmid.SetX((par0.X() + par1.X() + par2.X()) / 3);
		parmid.SetY((par0.Y() + par1.Y() + par2.Y()) / 3);

		if (depth % 3 == 0)
		{
			double curvature = 0;

			prop->SetParameters(parmid.X(), parmid.Y());
			if (!prop->IsCurvatureDefined())
			{
				return;
			}
			curvature = max(fabs(prop->MinCurvature()),
				fabs(prop->MaxCurvature()));

			prop->SetParameters(par0.X(), par0.Y());
			if (!prop->IsCurvatureDefined())
			{
				return;
			}
			curvature = max(curvature, max(fabs(prop->MinCurvature()),
				fabs(prop->MaxCurvature())));

			prop->SetParameters(par1.X(), par1.Y());
			if (!prop->IsCurvatureDefined())
			{
				return;
			}
			curvature = max(curvature, max(fabs(prop->MinCurvature()),
				fabs(prop->MaxCurvature())));

			prop->SetParameters(par2.X(), par2.Y());
			if (!prop->IsCurvatureDefined())
			{
				return;
			}
			curvature = max(curvature, max(fabs(prop->MinCurvature()),
				fabs(prop->MaxCurvature())));

			//(*testout) << "curvature " << curvature << endl;

			if (curvature < 1e-3)
			{
				//(*testout) << "curvature too small (" << curvature << ")!" << endl;
				return;
				// return war bis 10.2.05 auskommentiert
			}



			h = ComputeH(curvature + 1e-10, maxh, curvature_safety);

			if (h < 1e-4*maxside)
				return;


			if (h > 30) return;
		}

		if (h < maxside && depth < 10)
		{
			//cout << "\r h " << h << flush;
			gp_Pnt2d pm;

			//cout << "h " << h << " maxside " << maxside << " depth " << depth << endl;
			//cout << "par0 " << par0.X() << " " << par0.Y()
			//<< " par1 " << par1.X() << " " << par1.Y()
			//   << " par2 " << par2.X() << " " << par2.Y()<< endl;

			if (ls == 0)
			{
				pm.SetX(0.5*(par1.X() + par2.X())); pm.SetY(0.5*(par1.Y() + par2.Y()));
				CollectHTriangleRestrictions(pm, par2, par0, prop, restrictions, maxh, curvature_safety, depth + 1, h);
				CollectHTriangleRestrictions(pm, par0, par1, prop, restrictions, maxh, curvature_safety, depth + 1, h);
			}
			else if (ls == 1)
			{
				pm.SetX(0.5*(par0.X() + par2.X())); pm.SetY(0.5*(par0.Y() + par2.Y()));
				CollectHTriangleRestrictions(pm, par1, par2, prop, restrictions, maxh, curvature_safety, depth + 1, h);
				CollectHTriangleRestrictions(pm, par0, par1, prop, restrictions, maxh, curvature_safety, depth + 1, h);
			}
			else if (ls == 2)
			{
				pm.SetX(0.5*(par0.X() + par1.X())); pm.SetY(0.5*(par0.Y() + par1.Y()));
				CollectHTriangleRestrictions(pm, par1, par2, prop, restrictions, maxh, curvature_safety, depth + 1, h);
				CollectHTriangleRestrictions(pm, par2, par0, prop, restrictions, maxh, curvature_safety, depth + 1, h);
			}

		}
		else
		{
			gp_Pnt pnt;
			Point3d p3d;

			prop->SetParameters(parmid.X(), parmid.Y());
			pnt = prop->Value();
			p3d = Point3d(pnt.X(), pnt.Y(), pnt.Z());
			restrictions.push_back(LocalHRestriction(p3d, h));

			p3d = Point3d(pnt0.X(), pnt0.Y(), pnt0.Z());
			restrictions.push_back(LocalHRestriction(p3d, h));

			p3d = Point3d(pnt1.X(), pnt1.Y(), pnt1.Z());
			restrictions.push_back(LocalHRestriction(p3d, h));

			p3d = Point3d(pnt2.X(), pnt2.Y(), pnt2.Z());
			restrictions.push_back(LocalHRestriction(p3d, h));

			//(*testout) << "p = " << p3d << ", h = " << h << ", maxside = " << maxside << endl;

		}
	}



	// With segments > 0 the edge gets that many segments, spaced as the local
	// mesh size would space them, instead of the number the mesh size asks for.
	void DivideEdge(const TopoDS_Edge & edge, Array<MeshPoint> & ps,
		Array<double> & params, const Mesh & mesh, int & status, int segments = 0)
	{
		status = 0;
		double s0, s1;
		double maxh = mparam.maxh;
		int nsubedges = 1;
		gp_Pnt pnt, oldpnt;
		double svalue[DIVIDEEDGESECTIONS];

		GProp_GProps system;
		BRepGProp::LinearProperties(edge, system);
		double L = system.Mass();

		Handle(Geom_Curve) c = BRep_Tool::Curve(edge, s0, s1);

		double hvalue[DIVIDEEDGESECTIONS + 1];
		hvalue[0] = 0;
		pnt = c->Value(s0);

		double olddist = 0;
		double dist = 0;

		int tmpVal = (int)(DIVIDEEDGESECTIONS);

		for (int i = 1; i <= tmpVal; i++)
		{
			oldpnt = pnt;
			pnt = c->Value(s0 + (i / double(DIVIDEEDGESECTIONS))*(s1 - s0));
			hvalue[i] = hvalue[i - 1] +
				1.0 / mesh.GetH(Point3d(pnt.X(), pnt.Y(), pnt.Z()))*
				pnt.Distance(oldpnt);

			//(*testout) << "mesh.GetH(Point3d(pnt.X(), pnt.Y(), pnt.Z())) " << mesh.GetH(Point3d(pnt.X(), pnt.Y(), pnt.Z()))
			//	   <<  " pnt.Distance(oldpnt) " << pnt.Distance(oldpnt) << endl;

			olddist = dist;
			dist = pnt.Distance(oldpnt);
		}

		//  nsubedges = int(ceil(hvalue[DIVIDEEDGESECTIONS]));
		nsubedges = max(1, int(floor(hvalue[DIVIDEEDGESECTIONS] + 0.5)));

		// A forced count may be denser than the sections, so the points are
		// interpolated within them rather than put on the section ends.
		if (segments > 0)
		{
			ps.SetSize(segments - 1);
			params.SetSize(segments + 1);
			params[0] = s0;
			params[segments] = s1;

			int section = 1;
			for (int i = 1; i < segments; i++)
			{
				const double target = hvalue[DIVIDEEDGESECTIONS] * i / segments;
				while (section < DIVIDEEDGESECTIONS && hvalue[section] < target)
					section++;
				const double dh = hvalue[section] - hvalue[section - 1];
				const double fraction = dh > 0 ? (target - hvalue[section - 1]) / dh : 1;
				params[i] = s0 + ((section - 1 + fraction) / DIVIDEEDGESECTIONS) * (s1 - s0);
				pnt = c->Value(params[i]);
				ps[i - 1] = MeshPoint(Point3d(pnt.X(), pnt.Y(), pnt.Z()));
			}
			return;
		}

		ps.SetSize(nsubedges - 1);
		params.SetSize(nsubedges + 1);

		int i = 1;
		int i1 = 0;
		do
		{
			if (hvalue[i1] / hvalue[DIVIDEEDGESECTIONS] * nsubedges >= i)
			{
				params[i] = s0 + (i1 / double(DIVIDEEDGESECTIONS))*(s1 - s0);
				pnt = c->Value(params[i]);
				ps[i - 1] = MeshPoint(Point3d(pnt.X(), pnt.Y(), pnt.Z()));
				i++;
			}
			i1++;
			if (i1 > DIVIDEEDGESECTIONS)
			{
				nsubedges = i;
				ps.SetSize(nsubedges - 1);
				params.SetSize(nsubedges + 1);
				status |= 1;
			}
		} while (i < nsubedges);

		params[0] = s0;
		params[nsubedges] = s1;

		if (params[nsubedges] <= params[nsubedges - 1])
		{
			status |= 2;
			ps.SetSize(nsubedges - 2);
			params.SetSize(nsubedges);
			params[nsubedges] = s1;
		}
	}


	struct OCCEdgeDiscretization
	{
		Array<MeshPoint> points;
		Array<double> parameters;
		bool skip;
		int status;

		OCCEdgeDiscretization()
			: skip(false), status(0)
		{
		}
	};




	// Highest vertex point within eps of p, or -1.  Reproduces the result of the
	// linear scan this replaced, which kept the last match it found.
	static int FindVertexPoint(const Mesh & mesh, const Point3dTree & tree,
		Array<int> & candidates, const Point<3> & p, double eps)
	{
		tree.GetIntersecting(Point<3>(p(0) - eps, p(1) - eps, p(2) - eps),
			Point<3>(p(0) + eps, p(1) + eps, p(2) + eps), candidates);

		int found = -1;
		for (int i = 0; i < candidates.Size(); i++)
		{
			const int pi = candidates[i];
			if (pi > found && Dist2(mesh.Point(pi), p) < eps * eps)
				found = pi;
		}
		return found;
	}


	// An edge is not made finer than this many times the segment count its own
	// mesh size asks for, plus one.
	static const int transfinite_max_refinement = 2;


	struct TransfiniteFaceSides
	{
		std::vector<int> sides[4];
	};


	// Raises the counts until the opposite sides of every face add up to the
	// same number.  The segments a side lacks go one by one to its edge that is
	// least refined for its mesh size.  Returns false if an edge reached its
	// limit first, with the faces left short marked in short_faces.
	static bool BalanceTransfiniteSides(const std::vector<TransfiniteFaceSides> & faces,
		const std::vector<char> & active, const std::vector<int> & own, const std::vector<int> & limit,
		std::vector<int> & count, std::vector<char> & short_faces)
	{
		bool changed = true;
		while (changed)
		{
			changed = false;
			for (size_t f = 0; f < faces.size(); f++)
			{
				if (!active[f])
					continue;
				for (int q = 0; q < 2; q++)
				{
					const std::vector<int> * side[2] = { &faces[f].sides[q], &faces[f].sides[q + 2] };
					int sum[2] = { 0, 0 };
					for (int s = 0; s < 2; s++)
						for (size_t k = 0; k < side[s]->size(); k++)
							sum[s] += count[(*side[s])[k]];

					const int low = sum[0] < sum[1] ? 0 : 1;
					for (int missing = sum[1 - low] - sum[low]; missing > 0; missing--)
					{
						int best = -1;
						for (size_t k = 0; k < side[low]->size(); k++)
						{
							const int i = (*side[low])[k];
							if (count[i] >= limit[i])
								continue;
							if (best < 0 || double(own[i]) * count[best] > double(own[best]) * count[i])
								best = i;
						}
						if (best < 0)
							break;
						count[best]++;
						changed = true;
					}
				}
			}
		}

		bool balanced = true;
		for (size_t f = 0; f < faces.size(); f++)
		{
			short_faces[f] = 0;
			if (!active[f])
				continue;
			for (int q = 0; q < 2; q++)
			{
				int sum[2] = { 0, 0 };
				for (int s = 0; s < 2; s++)
					for (size_t k = 0; k < faces[f].sides[q + 2 * s].size(); k++)
						sum[s] += count[faces[f].sides[q + 2 * s][k]];
				if (sum[0] != sum[1])
					short_faces[f] = 1;
			}
			if (short_faces[f])
				balanced = false;
		}
		return balanced;
	}


	// Gives the opposite sides of every face with four corners the same total
	// segment count, so the surface meshing can mesh the face as a structured
	// grid.  Counts are only raised, since a shared edge ties the faces around
	// it together, and not past transfinite_max_refinement.  A face that cannot
	// be balanced within that is dropped and the others are balanced again from
	// the counts the mesh size asks for, so no edge is refined for a face that
	// is not going to be structured.
	static void MatchTransfiniteEdgeCounts(const OCCGeometry & geom, const Mesh & mesh,
		const std::vector<TopoDS_Edge> & edges, std::vector<OCCEdgeDiscretization> & results,
		OCCParallelMeshingContext & parallel)
	{
		const int nedges = int(edges.size());

		std::vector<TransfiniteFaceSides> faces;
		for (int facenr = 1; facenr <= geom.fmap.Extent(); facenr++)
		{
			TransfiniteFaceSides face;
			if (!CollectTransfiniteSides(geom, facenr, mparam.transfinite_angle, face.sides))
				continue;

			// edge map numbers to indices; a skipped edge has no segments to count
			bool usable = true;
			for (int q = 0; q < 4; q++)
				for (size_t k = 0; k < face.sides[q].size(); k++)
					if (results[--face.sides[q][k]].skip)
						usable = false;
			if (usable)
				faces.push_back(face);
		}

		std::vector<int> own(nedges), limit(nedges), count(nedges);
		for (int i = 0; i < nedges; i++)
		{
			own[i] = results[i].points.Size() + 1;
			limit[i] = transfinite_max_refinement * own[i] + 1;
		}

		std::vector<char> active(faces.size(), 1), short_faces(faces.size(), 0);
		std::vector<int> dropped;
		for (;;)
		{
			count = own;
			if (BalanceTransfiniteSides(faces, active, own, limit, count, short_faces))
				break;
			for (size_t f = 0; f < faces.size(); f++)
				if (short_faces[f])
				{
					active[f] = 0;
					dropped.push_back(int(f));
				}
		}

		// A face is dropped with the neighbour that took a shared edge to its
		// limit, so each is tried again on top of the balanced counts.
		int restored = 0;
		for (size_t k = 0; k < dropped.size(); k++)
		{
			const std::vector<int> balanced = count;
			active[dropped[k]] = 1;
			if (BalanceTransfiniteSides(faces, active, own, limit, count, short_faces))
				restored++;
			else
			{
				active[dropped[k]] = 0;
				count = balanced;
			}
		}

		std::vector<int> redivide;
		for (int i = 0; i < nedges; i++)
			if (count[i] != own[i])
				redivide.push_back(i);

		parallel.ParallelFor(int(redivide.size()),
			[&](int, int k)
			{
				const int i = redivide[k];
				DivideEdge(edges[i], results[i].points, results[i].parameters, mesh,
					results[i].status, count[i]);
			});

		PrintMessage(3, "Transfinite faces: ", int(faces.size()), " candidates, ",
			int(dropped.size()) - restored, " dropped, ", int(redivide.size()), " edges redivided");
	}


	void OCCFindEdges(OCCGeometry & geom, Mesh & mesh)
	{
		//merge_solids = 0;

		const char * savetask = multithread.task;
		multithread.task = "Edge meshing";

		(*testout) << "edge meshing" << endl;

		int nvertices = geom.vmap.Extent();
		int nedges = geom.emap.Extent();

		(*testout) << "nvertices = " << nvertices << endl;
		(*testout) << "nedges = " << nedges << endl;

		double eps = 1e-6 * geom.GetBoundingBox().Diam();

		// Vertex and edge points are looked up in spatial indices.  Scanning all
		// points that were already added made these lookups quadratic, which
		// dominated edge meshing on models with many edges.
		Box<3> searchbox = geom.GetBoundingBox();
		searchbox.Increase(searchbox.Diam() / 10 + eps);
		Point3dTree vertextree(searchbox.PMin(), searchbox.PMax());
		Point3dTree edgepointtree(searchbox.PMin(), searchbox.PMax());
		Array<int> candidates;

		for (int i = 1; i <= nvertices; i++)
		{
			gp_Pnt pnt = BRep_Tool::Pnt(TopoDS::Vertex(geom.vmap(i)));
			Point<3> p(pnt.X(), pnt.Y(), pnt.Z());
			MeshPoint mp(p);

			bool exists = 0;
			if (merge_solids)
				exists = FindVertexPoint(mesh, vertextree, candidates, p, eps) > 0;

			if (!exists)
			{
				PointIndex pi = mesh.AddPoint(mp);
				vertextree.Insert(p, pi);
			}
		}

		(*testout) << "different vertices = " << mesh.GetNP() << endl;


		int first_ep = mesh.GetNP() + 1;

		Array<int> face2solid[2];
		for (int i = 0; i < 2; i++)
		{
			face2solid[i].SetSize(geom.fmap.Extent());
			face2solid[i] = 0;
		}

		int solidnr = 0;
		for (TopExp_Explorer exp0(geom.shape, TopAbs_SOLID); exp0.More(); exp0.Next())
		{
			solidnr++;
			//TopoDS_Solid solid = TopoDS::Solid(exp0.Current());
			//solidnr = geom.somap.FindIndex(solid);
			for (TopExp_Explorer exp1(exp0.Current(), TopAbs_FACE); exp1.More(); exp1.Next())
			{
				TopoDS_Face face = TopoDS::Face(exp1.Current());
				int facenr = geom.fmap.FindIndex(face);

				if (face2solid[0][facenr - 1] == 0)
					face2solid[0][facenr - 1] = solidnr;
				else
					face2solid[1][facenr - 1] = solidnr;
			}
		}


		int total = 0;
		for (int i3 = 1; i3 <= geom.fmap.Extent(); i3++)
			for (TopExp_Explorer exp2(geom.fmap(i3), TopAbs_WIRE); exp2.More(); exp2.Next())
				for (TopExp_Explorer exp3(exp2.Current(), TopAbs_EDGE); exp3.More(); exp3.Next())
					total++;

		// Compute each topological edge only once.  The workers read the fixed
		// local-size field and write to private result slots; mesh point and
		// segment insertion below remains serial so numbering is deterministic.
		std::vector<TopoDS_Edge> unique_edges(nedges);
		std::vector<OCCEdgeDiscretization> edge_results(nedges);
		for (int i = 0; i < nedges; i++)
			unique_edges[i] = TopoDS::Edge(geom.emap(i + 1));

		OCCParallelMeshingContext parallel(mparam.parallel_meshing_threads);
		parallel.ParallelFor(nedges,
			[&](int, int edge_index)
			{
				const TopoDS_Edge & edge = unique_edges[edge_index];
				OCCEdgeDiscretization & result = edge_results[edge_index];

				if (BRep_Tool::Degenerated(edge))
				{
					result.skip = true;
					return;
				}

				if (geom.vmap.FindIndex(TopExp::FirstVertex(edge)) ==
					geom.vmap.FindIndex(TopExp::LastVertex(edge)))
				{
					GProp_GProps system;
					BRepGProp::LinearProperties(edge, system);
					if (system.Mass() < eps)
					{
						result.skip = true;
						return;
					}
				}

				DivideEdge(edge, result.points, result.parameters, mesh, result.status);
			});

		// The structured faces PrePoMax gives replace those Netgen would find
		LoadGivenTransfiniteFaces(mparam.transfinite_filename);
		if (GivenTransfiniteFaces().loaded)
		{
			std::vector<int> own(nedges), counts(nedges);
			for (int i = 0; i < nedges; i++)
				own[i] = edge_results[i].skip ? 1 : int(edge_results[i].points.Size()) + 1;
			counts = own;
			std::vector<char> borders_free_face(nedges, 0);
			for (int facenr = 1; facenr <= geom.fmap.Extent(); facenr++)
			{
				if (GivenTransfiniteFaces().sides.count(facenr)) continue;
				for (TopExp_Explorer exp(geom.fmap(facenr), TopAbs_EDGE); exp.More(); exp.Next())
				{
					const int edgenr = geom.emap.FindIndex(exp.Current());
					if (edgenr >= 1 && edgenr <= nedges) borders_free_face[edgenr - 1] = 1;
				}
			}
			BalanceGivenTransfiniteEdgeCounts(own, borders_free_face, counts);

			std::vector<int> redivide;
			for (int i = 0; i < nedges; i++)
				if (!edge_results[i].skip && counts[i] != own[i])
					redivide.push_back(i);
			parallel.ParallelFor(int(redivide.size()),
				[&](int, int k)
				{
					const int i = redivide[k];
					DivideEdge(unique_edges[i], edge_results[i].points, edge_results[i].parameters, mesh,
						edge_results[i].status, counts[i]);
				});
			PrintMessage(3, "Transfinite: ", int(redivide.size()), " edges redivided");
		}
		else if (mparam.transfinite_faces)
			MatchTransfiniteEdgeCounts(geom, mesh, unique_edges, edge_results, parallel);

		for (int i = 0; i < nedges; i++)
		{
			if (edge_results[i].skip &&
				!BRep_Tool::Degenerated(unique_edges[i]))
				cout << "ignoring edge " << i + 1
					<< ". closed edge with length < " << eps << endl;
			if (edge_results[i].status & 1)
				cout << "divide edge: local h too small" << endl;
			if (edge_results[i].status & 2)
				cout << "CORRECTED" << endl;
		}


		int facenr = 0;
		int edgenr = 0;


		(*testout) << "faces = " << geom.fmap.Extent() << endl;
		int curr = 0;

		for (int i3 = 1; i3 <= geom.fmap.Extent(); i3++)
		{
			TopoDS_Face face = TopoDS::Face(geom.fmap(i3));
			facenr = geom.fmap.FindIndex(face);       // sollte doch immer == i3 sein ??? JS

			int solidnr0 = face2solid[0][i3 - 1];
			int solidnr1 = face2solid[1][i3 - 1];

			/* auskommentiert am 3.3.05 von robert
			for (exp2.Init (geom.somap(solidnr0), TopAbs_FACE); exp2.More(); exp2.Next())
			{
			TopoDS_Face face2 = TopoDS::Face(exp2.Current());
			if (geom.fmap.FindIndex(face2) == facenr)
			{
			//		      if (face.Orientation() != face2.Orientation()) swap (solidnr0, solidnr1);
			}
			}
			*/

			mesh.AddFaceDescriptor(FaceDescriptor(facenr, solidnr0, solidnr1, 0));

			// Philippose - 06/07/2009
			// Add the face colour to the mesh data
			Quantity_Color face_colour;

			if (!(geom.face_colours.IsNull())
				&& (geom.face_colours->GetColor(face, XCAFDoc_ColorSurf, face_colour)))
			{
				mesh.GetFaceDescriptor(facenr).SetSurfColour(Vec3d(face_colour.Red(), face_colour.Green(), face_colour.Blue()));
			}
			else
			{
				mesh.GetFaceDescriptor(facenr).SetSurfColour(Vec3d(0.0, 1.0, 0.0));
			}
			// ACHTUNG! STIMMT NICHT ALLGEMEIN (RG)


			Handle(Geom_Surface) occface = BRep_Tool::Surface(face);

			for (TopExp_Explorer exp2(face, TopAbs_WIRE); exp2.More(); exp2.Next())
			{
				TopoDS_Shape wire = exp2.Current();

				for (TopExp_Explorer exp3(wire, TopAbs_EDGE); exp3.More(); exp3.Next())
				{
					curr++;
					(*testout) << "edge nr " << curr << endl;

					multithread.percent = 100 * curr / double(total);
					if (multithread.terminate) return;

					TopoDS_Edge edge = TopoDS::Edge(exp3.Current());
					int geomedgenr = geom.emap.FindIndex(edge);
					const OCCEdgeDiscretization & edge_result = edge_results[geomedgenr - 1];
					if (edge_result.skip)
						continue;

					// An external edge lies outside the face and bounds nothing.  An
					// internal one - a line drawn on the face that does not cut it
					// through - has the face on both sides, so it enters the front
					// once in each direction and the face is meshed around it.
					if (edge.Orientation() == TopAbs_EXTERNAL)
						continue;
					const bool internal_edge = edge.Orientation() == TopAbs_INTERNAL;


					Handle(Geom2d_Curve) cof;
					double s0, s1;
					cof = BRep_Tool::CurveOnSurface(edge, face, s0, s1);

					const Array<MeshPoint> & mp = edge_result.points;
					const Array<double> & params = edge_result.parameters;

					Array <int> pnums;
					pnums.SetSize(mp.Size() + 2);

					if (!merge_solids)
					{
						pnums[0] = geom.vmap.FindIndex(TopExp::FirstVertex(edge));
						pnums[pnums.Size() - 1] = geom.vmap.FindIndex(TopExp::LastVertex(edge));
					}
					else
					{
						Point<3> fp = occ2ng(BRep_Tool::Pnt(TopExp::FirstVertex(edge)));
						Point<3> lp = occ2ng(BRep_Tool::Pnt(TopExp::LastVertex(edge)));

						pnums[0] = FindVertexPoint(mesh, vertextree, candidates, fp, eps);
						pnums.Last() = FindVertexPoint(mesh, vertextree, candidates, lp, eps);
					}


					for (int i = 1; i <= mp.Size(); i++)
					{
						const Point<3> ep(mp[i - 1]);

						// Lowest matching edge point, as the former scan from
						// first_ep upwards returned.
						edgepointtree.GetIntersecting(
							Point<3>(ep(0) - eps, ep(1) - eps, ep(2) - eps),
							Point<3>(ep(0) + eps, ep(1) + eps, ep(2) + eps), candidates);

						int found = 0;
						for (int k = 0; k < candidates.Size(); k++)
						{
							const int j = candidates[k];
							if ((!found || j < found) &&
								(mesh.Point(j) - ep).Length() < eps)
								found = j;
						}

						if (found)
							pnums[i] = found;
						else
						{
							mesh.AddPoint(mp[i - 1]);
							(*testout) << "add meshpoint " << mp[i - 1] << endl;
							pnums[i] = mesh.GetNP();
							edgepointtree.Insert(ep, mesh.GetNP());
						}
					}
					(*testout) << "NP = " << mesh.GetNP() << endl;

					//(*testout) << pnums[pnums.Size()-1] << endl;

					for (int i = 1; i <= mp.Size() + 1; i++)
					{
						edgenr++;
						Segment seg;

						seg[0] = pnums[i - 1];
						seg[1] = pnums[i];
						seg.edgenr = edgenr;
						seg.si = facenr;
						seg.epgeominfo[0].dist = params[i - 1];
						seg.epgeominfo[1].dist = params[i];
						seg.epgeominfo[0].edgenr = geomedgenr;
						seg.epgeominfo[1].edgenr = geomedgenr;

						gp_Pnt2d p2d;
						p2d = cof->Value(params[i - 1]);
						//			if (i == 1) p2d = cof->Value(s0);
						seg.epgeominfo[0].u = p2d.X();
						seg.epgeominfo[0].v = p2d.Y();
						p2d = cof->Value(params[i]);
						//			if (i == mp.Size()+1) p2d = cof -> Value(s1);
						seg.epgeominfo[1].u = p2d.X();
						seg.epgeominfo[1].v = p2d.Y();

						/*
						if (occface->IsUPeriodic())
						{
						cout << "U Periodic" << endl;
						if (fabs(seg.epgeominfo[1].u-seg.epgeominfo[0].u) >
						fabs(seg.epgeominfo[1].u-
						(seg.epgeominfo[0].u-occface->UPeriod())))
						seg.epgeominfo[0].u = p2d.X()+occface->UPeriod();

						if (fabs(seg.epgeominfo[1].u-seg.epgeominfo[0].u) >
						fabs(seg.epgeominfo[1].u-
						(seg.epgeominfo[0].u+occface->UPeriod())))
						seg.epgeominfo[0].u = p2d.X()-occface->UPeriod();
						}

						if (occface->IsVPeriodic())
						{
						cout << "V Periodic" << endl;
						if (fabs(seg.epgeominfo[1].v-seg.epgeominfo[0].v) >
						fabs(seg.epgeominfo[1].v-
						(seg.epgeominfo[0].v-occface->VPeriod())))
						seg.epgeominfo[0].v = p2d.Y()+occface->VPeriod();

						if (fabs(seg.epgeominfo[1].v-seg.epgeominfo[0].v) >
						fabs(seg.epgeominfo[1].v-
						(seg.epgeominfo[0].v+occface->VPeriod())))
						seg.epgeominfo[0].v = p2d.Y()-occface->VPeriod();
						}
						*/

						if (edge.Orientation() == TopAbs_REVERSED)
						{
							swap(seg[0], seg[1]);
							swap(seg.epgeominfo[0].dist, seg.epgeominfo[1].dist);
							swap(seg.epgeominfo[0].u, seg.epgeominfo[1].u);
							swap(seg.epgeominfo[0].v, seg.epgeominfo[1].v);
						}

						mesh.AddSegment(seg);

						if (internal_edge)
						{
							edgenr++;
							seg.edgenr = edgenr;
							swap(seg[0], seg[1]);
							swap(seg.epgeominfo[0], seg.epgeominfo[1]);
							mesh.AddSegment(seg);
						}

						//edgesegments[geomedgenr-1]->Append(mesh.GetNSeg());

					}
				}
			}
		}

		//	for(i=1; i<=mesh.GetNSeg(); i++)
		//		(*testout) << "edge " << mesh.LineSegment(i).edgenr << " face " << mesh.LineSegment(i).si
		//				<< " p1 " << mesh.LineSegment(i)[0] << " p2 " << mesh.LineSegment(i)[1] << endl;
		//	exit(10);

		mesh.CalcSurfacesOfNode();
		multithread.task = savetask;
	}




	static void AddTransfiniteFaceMesh(Mesh & mesh, const OCCTransfiniteFaceMesh & face_mesh)
	{
		const int point_base = mesh.GetNP();
		for (size_t i = 0; i < face_mesh.points.size(); i++)
			mesh.AddPoint(face_mesh.points[i], face_mesh.points[i].GetLayer(), face_mesh.points[i].Type());

		for (size_t i = 0; i < face_mesh.elements.size(); i++)
		{
			Element2d element = face_mesh.elements[i];
			for (int j = 1; j <= element.GetNP(); j++)
				if (int(element.PNum(j)) < 0)
					element.PNum(j) = point_base - int(element.PNum(j));
			mesh.AddSurfaceElement(element);
		}
	}


	static void OCCMeshSurfaceSerial(OCCGeometry & geom, Mesh & mesh, int perfstepsend)
	{
		int i, j, k;
		int changed;

		const char * savetask = multithread.task;
		multithread.task = "Surface meshing";

		geom.facemeshstatus = 0;

		int noldp = mesh.GetNP();

		double starttime = GetTime();

		Array<int> glob2loc(noldp);

		//int projecttype = PARAMETERSPACE;

		int projecttype = PARAMETERSPACE;

		int notrys = 1;

		int surfmesherror = 0;

		// Structured faces are kept out of the surface optimisation, which would
		// swap and smooth the grid away.
		std::vector<char> transfinite_face(mesh.GetNFD() + 1, 0);

		for (k = 1; k <= mesh.GetNFD(); k++)
		{
			if (1 == 0 && !geom.fvispar[k - 1].IsDrawable())
			{
				(*testout) << "ignoring face " << k << endl;
				cout << "ignoring face " << k << endl;
				continue;
			}

			(*testout) << "mesh face " << k << endl;
			multithread.percent = 100 * k / (mesh.GetNFD() + VSMALL);
			geom.facemeshstatus[k - 1] = -1;


			/*
			if (k != 42)
			{
			cout << "skipped" << endl;
			continue;
			}
			*/


			FaceDescriptor & fd = mesh.GetFaceDescriptor(k);

			if (GivenTransfiniteFaces().loaded && GivenTransfiniteFaces().sides.count(k))
			{
				OCCTransfiniteFaceMesh face_mesh;
				BuildGivenTransfiniteFaceMesh(geom, mesh, k, mparam.quad != 0, face_mesh);
				PrintMessage(2, "Face ", k, " / ", mesh.GetNFD(), " (transfinite)");
				AddTransfiniteFaceMesh(mesh, face_mesh);
				geom.facemeshstatus[k - 1] = 1;
				transfinite_face[k] = 1;
				continue;
			}
			if (!GivenTransfiniteFaces().loaded && mparam.transfinite_faces)
			{
				OCCTransfiniteFaceMesh face_mesh;
				if (BuildTransfiniteFaceMesh(geom, mesh, k, mparam.transfinite_angle,
					mparam.transfinite_faces == 1, face_mesh))
				{
					PrintMessage(2, "Face ", k, " / ", mesh.GetNFD(), " (transfinite)");
					AddTransfiniteFaceMesh(mesh, face_mesh);
					geom.facemeshstatus[k - 1] = 1;
					transfinite_face[k] = 1;
					continue;
				}
			}

			int oldnf = mesh.GetNSE();

			Box<3> bb = geom.GetBoundingBox();

			//      int projecttype = PLANESPACE;

			Meshing2OCCSurfaces meshing(TopoDS::Face(geom.fmap(k)), bb, projecttype, mparam);

			if (meshing.GetProjectionType() == PLANESPACE)
				PrintMessage(2, "Face ", k, " / ", mesh.GetNFD(), " (plane space projection)");
			else
				PrintMessage(2, "Face ", k, " / ", mesh.GetNFD(), " (parameter space projection)");

			if (surfmesherror)
				cout << "Surface meshing error occurred before (in " << surfmesherror << " faces)" << endl;

			//      Meshing2OCCSurfaces meshing(f2, bb);
			meshing.SetStartTime(starttime);

			//(*testout) << "Face " << k << endl << endl;


			if (meshing.GetProjectionType() == PLANESPACE)
			{
				int cntp = 0;
				glob2loc = 0;
				for (i = 1; i <= mesh.GetNSeg(); i++)
				{
					Segment & seg = mesh.LineSegment(i);
					if (seg.si == k)
					{
						for (j = 1; j <= 2; j++)
						{
							int pi = (j == 1) ? seg[0] : seg[1];
							if (!glob2loc.Get(pi))
							{
								meshing.AddPoint(mesh.Point(pi), pi);
								cntp++;
								glob2loc.Elem(pi) = cntp;
							}
						}
					}
				}

				for (i = 1; i <= mesh.GetNSeg(); i++)
				{
					Segment & seg = mesh.LineSegment(i);
					if (seg.si == k)
					{
						PointGeomInfo gi0, gi1;
						gi0.trignum = gi1.trignum = k;
						gi0.u = seg.epgeominfo[0].u;
						gi0.v = seg.epgeominfo[0].v;
						gi1.u = seg.epgeominfo[1].u;
						gi1.v = seg.epgeominfo[1].v;

						meshing.AddBoundaryElement(glob2loc.Get(seg[0]), glob2loc.Get(seg[1]), gi0, gi1);
						//(*testout) << gi0.u << " " << gi0.v << endl;
						//(*testout) << gi1.u << " " << gi1.v << endl;
					}
				}
			}
			else
			{
				int cntp = 0;

				for (i = 1; i <= mesh.GetNSeg(); i++)
					if (mesh.LineSegment(i).si == k)
						cntp += 2;


				Array< PointGeomInfo > gis;

				gis.SetAllocSize(cntp);
				gis.SetSize(0);

				for (i = 1; i <= mesh.GetNSeg(); i++)
				{
					Segment & seg = mesh.LineSegment(i);
					if (seg.si == k)
					{
						PointGeomInfo gi0, gi1;
						gi0.trignum = gi1.trignum = k;
						gi0.u = seg.epgeominfo[0].u;
						gi0.v = seg.epgeominfo[0].v;
						gi1.u = seg.epgeominfo[1].u;
						gi1.v = seg.epgeominfo[1].v;

						int locpnum[2] = { 0, 0 };

						for (j = 0; j < 2; j++)
						{
							PointGeomInfo gi = (j == 0) ? gi0 : gi1;

							int l;
							for (l = 0; l < gis.Size() && locpnum[j] == 0; l++)
							{
								double dist = sqr(gis[l].u - gi.u) + sqr(gis[l].v - gi.v);

								if (dist < 1e-10)
									locpnum[j] = l + 1;
							}

							if (locpnum[j] == 0)
							{
								int pi = (j == 0) ? seg[0] : seg[1];
								meshing.AddPoint(mesh.Point(pi), pi);

								gis.SetSize(gis.Size() + 1);
								gis[l] = gi;
								locpnum[j] = l + 1;
							}
						}

						meshing.AddBoundaryElement(locpnum[0], locpnum[1], gi0, gi1);
						//(*testout) << gi0.u << " " << gi0.v << endl;
						//(*testout) << gi1.u << " " << gi1.v << endl;

					}
				}
			}





			// Philippose - 15/01/2009
			double maxh = geom.face_maxh[k - 1];
			//double maxh = mparam.maxh;
			mparam.checkoverlap = 0;
			//      int noldpoints = mesh->GetNP();
			int noldsurfel = mesh.GetNSE();

			GProp_GProps sprops;
			BRepGProp::SurfaceProperties(TopoDS::Face(geom.fmap(k)), sprops);
			meshing.SetMaxArea(2.*sprops.Mass());

			MESHING2_RESULT res;

			try {
				res = meshing.GenerateMesh(mesh, mparam, maxh, k);
			}

			catch (SingularMatrixException)
			{
				(*myerr) << "Singular Matrix" << endl;
				res = MESHING2_GIVEUP;
			}

			catch (UVBoundsException)
			{
				(*myerr) << "UV bounds exceeded" << endl;
				res = MESHING2_GIVEUP;
			}

			projecttype = PARAMETERSPACE;

			if (res != MESHING2_OK)
			{
				if (notrys == 1)
				{
					for (int i = noldsurfel + 1; i <= mesh.GetNSE(); i++)
						mesh.DeleteSurfaceElement(i);

					mesh.Compress();

					cout << "retry Surface " << k << endl;

					k--;
					projecttype *= -1;
					notrys++;
					continue;
				}
				else
				{
					geom.facemeshstatus[k - 1] = -1;
					PrintError("Problem in Surface mesh generation");
					surfmesherror++;
					//	      throw NgException ("Problem in Surface mesh generation");
				}
			}
			else
			{
				geom.facemeshstatus[k - 1] = 1;
			}

			notrys = 1;

			for (i = oldnf + 1; i <= mesh.GetNSE(); i++)
				mesh.SurfaceElement(i).SetIndex(k);

		}

		//      ofstream problemfile("occmesh.rep");

		//      problemfile << "SURFACEMESHING" << endl << endl;

		if (surfmesherror)
		{
			cout << "WARNING! NOT ALL FACES HAVE BEEN MESHED" << endl;
			cout << "SURFACE MESHING ERROR OCCURRED IN " << surfmesherror << " FACES:" << endl;
			for (int i = 1; i <= geom.fmap.Extent(); i++)
				if (geom.facemeshstatus[i - 1] == -1)
				{
					cout << "Face " << i << endl;
					//               problemfile << "problem with face " << i << endl;
					//               problemfile << "vertices: " << endl;
					TopExp_Explorer exp0, exp1, exp2;
					for (exp0.Init(TopoDS::Face(geom.fmap(i)), TopAbs_WIRE); exp0.More(); exp0.Next())
					{
						TopoDS_Wire wire = TopoDS::Wire(exp0.Current());
						for (exp1.Init(wire, TopAbs_EDGE); exp1.More(); exp1.Next())
						{
							TopoDS_Edge edge = TopoDS::Edge(exp1.Current());
							for (exp2.Init(edge, TopAbs_VERTEX); exp2.More(); exp2.Next())
							{
								TopoDS_Vertex vertex = TopoDS::Vertex(exp2.Current());
								gp_Pnt point = BRep_Tool::Pnt(vertex);
								//                        problemfile << point.X() << " " << point.Y() << " " << point.Z() << endl;
							}
						}
					}
					//               problemfile << endl;

				}
			cout << endl << endl;
			cout << "for more information open IGES/STEP Topology Explorer" << endl;
			//            problemfile.close();
			throw NgException("Problem in Surface mesh generation");
		}
		else
		{
			//         problemfile << "OK" << endl << endl;
			//         problemfile.close();
		}




		if (multithread.terminate || perfstepsend < MESHCONST_OPTSURFACE)
			return;

		multithread.task = "Optimizing surface";

		static int timer_opt2d = NgProfiler::CreateTimer("Optimization 2D");
		NgProfiler::StartTimer(timer_opt2d);

		for (k = 1; k <= mesh.GetNFD(); k++)
		{
			//      if (k != 42) continue;
			//      if (k != 36) continue;

			//      (*testout) << "optimize face " << k << endl;
			multithread.percent = 100 * k / (mesh.GetNFD() + VSMALL);

			FaceDescriptor & fd = mesh.GetFaceDescriptor(k);

			if (transfinite_face[k])
				continue;

			PrintMessage(1, "Optimize Surface ", k);
			for (i = 1; i <= mparam.optsteps2d; i++)
			{
				//	  (*testout) << "optstep " << i << endl;
				if (multithread.terminate) return;

				{
					MeshOptimize2dOCCSurfaces meshopt(geom);
					meshopt.SetFaceIndex(k);
					meshopt.SetImproveEdges(0);
					meshopt.SetMetricWeight(mparam.elsizeweight);
					//meshopt.SetMetricWeight (0.2);
					meshopt.SetWriteStatus(0);

					//	    (*testout) << "EdgeSwapping (mesh, (i > mparam.optsteps2d/2))" << endl;
					meshopt.EdgeSwapping(mesh, (i > mparam.optsteps2d / 2));
				}

				if (multithread.terminate) return;
				{
					MeshOptimize2dOCCSurfaces meshopt(geom);
					meshopt.SetFaceIndex(k);
					meshopt.SetImproveEdges(0);
					//meshopt.SetMetricWeight (0.2);
					meshopt.SetMetricWeight(mparam.elsizeweight);
					meshopt.SetWriteStatus(0);

					//	    (*testout) << "ImproveMesh (mesh)" << endl;
					meshopt.ImproveMesh(mesh, mparam);
				}

				{
					MeshOptimize2dOCCSurfaces meshopt(geom);
					meshopt.SetFaceIndex(k);
					meshopt.SetImproveEdges(0);
					//meshopt.SetMetricWeight (0.2);
					meshopt.SetMetricWeight(mparam.elsizeweight);
					meshopt.SetWriteStatus(0);

					//	    (*testout) << "CombineImprove (mesh)" << endl;
					meshopt.CombineImprove(mesh);
				}

				if (multithread.terminate) return;
				{
					MeshOptimize2dOCCSurfaces meshopt(geom);
					meshopt.SetFaceIndex(k);
					meshopt.SetImproveEdges(0);
					//meshopt.SetMetricWeight (0.2);
					meshopt.SetMetricWeight(mparam.elsizeweight);
					meshopt.SetWriteStatus(0);

					//	    (*testout) << "ImproveMesh (mesh)" << endl;
					meshopt.ImproveMesh(mesh, mparam);
				}
			}

		}


		mesh.CalcSurfacesOfNode();
		mesh.Compress();

		NgProfiler::StopTimer(timer_opt2d);

		multithread.task = savetask;
	}


	struct OCCFaceMeshResult
	{
		std::vector<MeshPoint> points;
		std::vector<Element2d> elements;
		std::vector<LocalHRestriction> restrictions;
		bool success;
		bool retried;
		bool transfinite;
		int projection_type;
		int error_type;
		std::string error_message;

		OCCFaceMeshResult()
			: success(false), retried(false), transfinite(false), projection_type(PARAMETERSPACE), error_type(0)
		{
		}
	};


	static void InitializeFaceScratchMesh(const Mesh & source, Mesh & scratch,
		int facenr, const Box<3> & geometry_box, const MeshingParameters & mp)
	{
		scratch.geomtype = source.geomtype;
		scratch.SetGlobalH(mp.maxh);
		scratch.SetMinimalH(mp.minh);

		Box<3> size_box = geometry_box;
		size_box.Increase(size_box.Diam() / 10);
		scratch.SetLocalH(size_box.PMin(), size_box.PMax(), mp.grading);

		// one array copy instead of a time-stamped AddPoint per point
		scratch.Points() = source.Points();

		for (int i = 1; i <= source.GetNFD(); i++)
			scratch.AddFaceDescriptor(source.GetFaceDescriptor(i));

		for (int i = 1; i <= source.GetNSeg(); i++)
			if (source.LineSegment(i).si == facenr)
				scratch.AddSegment(source.LineSegment(i));
	}


	static void AddFaceBoundary(const Mesh & source, int facenr,
		Meshing2OCCSurfaces & meshing)
	{
		if (meshing.GetProjectionType() == PLANESPACE)
		{
			Array<int> glob2loc(source.GetNP());
			glob2loc = 0;
			int cntp = 0;

			for (int i = 1; i <= source.GetNSeg(); i++)
			{
				const Segment & seg = source.LineSegment(i);
				if (seg.si != facenr)
					continue;

				for (int j = 0; j < 2; j++)
				{
					int pi = seg[j];
					if (!glob2loc.Get(pi))
					{
						meshing.AddPoint(source.Point(pi), pi);
						glob2loc.Elem(pi) = ++cntp;
					}
				}
			}

			for (int i = 1; i <= source.GetNSeg(); i++)
			{
				const Segment & seg = source.LineSegment(i);
				if (seg.si != facenr)
					continue;

				PointGeomInfo gi0, gi1;
				gi0.trignum = gi1.trignum = facenr;
				gi0.u = seg.epgeominfo[0].u;
				gi0.v = seg.epgeominfo[0].v;
				gi1.u = seg.epgeominfo[1].u;
				gi1.v = seg.epgeominfo[1].v;
				meshing.AddBoundaryElement(glob2loc.Get(seg[0]), glob2loc.Get(seg[1]), gi0, gi1);
			}
			return;
		}

		int cntp = 0;
		for (int i = 1; i <= source.GetNSeg(); i++)
			if (source.LineSegment(i).si == facenr)
				cntp += 2;

		Array<PointGeomInfo> gis;
		gis.SetAllocSize(cntp);
		gis.SetSize(0);

		for (int i = 1; i <= source.GetNSeg(); i++)
		{
			const Segment & seg = source.LineSegment(i);
			if (seg.si != facenr)
				continue;

			PointGeomInfo gi[2];
			gi[0].trignum = gi[1].trignum = facenr;
			gi[0].u = seg.epgeominfo[0].u;
			gi[0].v = seg.epgeominfo[0].v;
			gi[1].u = seg.epgeominfo[1].u;
			gi[1].v = seg.epgeominfo[1].v;

			int locpnum[2] = { 0, 0 };
			for (int j = 0; j < 2; j++)
			{
				int l;
				for (l = 0; l < gis.Size() && locpnum[j] == 0; l++)
					if (sqr(gis[l].u - gi[j].u) + sqr(gis[l].v - gi[j].v) < 1e-10)
						locpnum[j] = l + 1;

				if (locpnum[j] == 0)
				{
					meshing.AddPoint(source.Point(seg[j]), seg[j]);
					gis.SetSize(gis.Size() + 1);
					gis[l] = gi[j];
					locpnum[j] = l + 1;
				}
			}

			meshing.AddBoundaryElement(locpnum[0], locpnum[1], gi[0], gi[1]);
		}
	}


	static void OptimizeFaceScratchMesh(const OCCGeometry & geom, Mesh & scratch,
		int facenr, const MeshingParameters & mp)
	{
		scratch.CalcSurfacesOfNode();
		for (int i = 1; i <= mp.optsteps2d; i++)
		{
			{
				MeshOptimize2dOCCSurfaces meshopt(geom);
				meshopt.SetFaceIndex(facenr);
				meshopt.SetImproveEdges(0);
				meshopt.SetMetricWeight(mp.elsizeweight);
				meshopt.SetWriteStatus(0);
				meshopt.EdgeSwapping(scratch, (i > mp.optsteps2d / 2));
			}
			{
				MeshOptimize2dOCCSurfaces meshopt(geom);
				meshopt.SetFaceIndex(facenr);
				meshopt.SetImproveEdges(0);
				meshopt.SetMetricWeight(mp.elsizeweight);
				meshopt.SetWriteStatus(0);
				meshopt.ImproveMesh(scratch, mp);
			}
			{
				MeshOptimize2dOCCSurfaces meshopt(geom);
				meshopt.SetFaceIndex(facenr);
				meshopt.SetImproveEdges(0);
				meshopt.SetMetricWeight(mp.elsizeweight);
				meshopt.SetWriteStatus(0);
				meshopt.CombineImprove(scratch);
			}
			{
				MeshOptimize2dOCCSurfaces meshopt(geom);
				meshopt.SetFaceIndex(facenr);
				meshopt.SetImproveEdges(0);
				meshopt.SetMetricWeight(mp.elsizeweight);
				meshopt.SetWriteStatus(0);
				meshopt.ImproveMesh(scratch, mp);
			}
		}
	}


	// A scratch mesh starts with every point of the source mesh, so those points keep their numbers. The
	// optimisation of a face with quadrilaterals compresses the mesh it works on, which drops the points the face
	// does not use and keeps the order of the rest: its boundary then comes first, in the order of the numbers
	// of the source mesh. Read as numbered like the source mesh, the elements of every face but the first joined
	// points of other faces. Such a mesh is compressed once more after the optimisation, which changes nothing
	// when the optimisation compressed it already, and the numbers of its first points are returned
	static std::vector<int> GetSourcePointNumbers(const Mesh & source, Mesh & scratch, int facenr, bool quad)
	{
		std::vector<int> source_points;
		if (!quad)
		{
			for (int i = 1; i <= source.GetNP(); i++)
				source_points.push_back(i);
			return source_points;
		}

		for (int i = 1; i <= source.GetNSeg(); i++)
		{
			const Segment & seg = source.LineSegment(i);
			if (seg.si != facenr)
				continue;
			source_points.push_back(seg[0]);
			source_points.push_back(seg[1]);
		}
		std::sort(source_points.begin(), source_points.end());
		source_points.erase(std::unique(source_points.begin(), source_points.end()), source_points.end());

		scratch.Compress();
		if (scratch.GetNP() < int(source_points.size()))
			throw NgException("The surface mesh of a face lost points of its boundary");
		for (size_t i = 0; i < source_points.size(); i++)
			if (Dist2(scratch.Point(int(i) + 1), source.Point(source_points[i])) != 0)
				throw NgException("The surface mesh of a face lost points of its boundary");
		return source_points;
	}


	static void ExtractFaceResult(const Mesh & scratch, const std::vector<int> & source_points,
		int facenr, OCCFaceMeshResult & result)
	{
		const int boundary_point_count = int(source_points.size());
		std::vector<int> point_map(scratch.GetNP() + 1, 0);

		for (int i = 1; i <= scratch.GetNSE(); i++)
		{
			const Element2d & source_element = scratch.SurfaceElement(i);
			if (source_element.IsDeleted() || source_element.GetIndex() != facenr)
				continue;

			Element2d element = source_element;
			for (int j = 1; j <= element.GetNP(); j++)
			{
				int pi = element.PNum(j);
				if (pi <= boundary_point_count)
				{
					element.PNum(j) = source_points[pi - 1];
					continue;
				}

				if (point_map[pi] == 0)
				{
					result.points.push_back(scratch.Point(pi));
					point_map[pi] = int(result.points.size());
				}
				element.PNum(j) = -point_map[pi];
			}
			result.elements.push_back(element);
		}
	}


	static void GenerateFaceMesh(const OCCGeometry & geom, const Mesh & source,
		const Box<3> & geometry_box, int facenr, int perfstepsend,
		double starttime, OCCFaceMeshResult & result)
	{
		if (GivenTransfiniteFaces().loaded && GivenTransfiniteFaces().sides.count(facenr))
		{
			OCCTransfiniteFaceMesh face_mesh;
			BuildGivenTransfiniteFaceMesh(geom, source, facenr, mparam.quad != 0, face_mesh);
			result.points.swap(face_mesh.points);
			result.elements.swap(face_mesh.elements);
			result.transfinite = true;
			result.success = true;
			return;
		}
		if (!GivenTransfiniteFaces().loaded && mparam.transfinite_faces)
		{
			OCCTransfiniteFaceMesh face_mesh;
			if (BuildTransfiniteFaceMesh(geom, source, facenr, mparam.transfinite_angle,
				mparam.transfinite_faces == 1, face_mesh))
			{
				result.points.swap(face_mesh.points);
				result.elements.swap(face_mesh.elements);
				result.transfinite = true;
				result.success = true;
				return;
			}
		}

		MeshingParameters face_mp;
		face_mp.CopyFrom(mparam);
		face_mp.checkoverlap = 0;

		Array<LocalHRestriction> accumulated_restrictions;

		for (int attempt = 0; attempt < 2; attempt++)
		{
			const int projection_type = attempt == 0 ? PARAMETERSPACE : PLANESPACE;
			Mesh scratch;
			InitializeFaceScratchMesh(source, scratch, facenr, geometry_box, face_mp);
			for (int i = 0; i < accumulated_restrictions.Size(); i++)
				scratch.RestrictLocalH(accumulated_restrictions[i].point,
					accumulated_restrictions[i].h);

			Meshing2OCCSurfaces meshing(TopoDS::Face(geom.fmap(facenr)), geometry_box,
				projection_type, face_mp);
			meshing.SetStartTime(starttime);
			AddFaceBoundary(source, facenr, meshing);

			GProp_GProps sprops;
			BRepGProp::SurfaceProperties(TopoDS::Face(geom.fmap(facenr)), sprops);
			meshing.SetMaxArea(2.*sprops.Mass());

			Array<LocalHRestriction> attempt_restrictions;
			MESHING2_RESULT mesh_result = MESHING2_GIVEUP;
			try
			{
				mesh_result = meshing.GenerateMesh(scratch, face_mp,
					geom.face_maxh[facenr - 1], facenr, &source,
					&attempt_restrictions, false);
			}
			catch (SingularMatrixException)
			{
				result.error_type = 1;
			}
			catch (UVBoundsException)
			{
				result.error_type = 2;
			}

			for (int i = 0; i < attempt_restrictions.Size(); i++)
				accumulated_restrictions.Append(attempt_restrictions[i]);

			if (mesh_result != MESHING2_OK)
			{
				result.retried = true;
				continue;
			}

			if (perfstepsend >= MESHCONST_OPTSURFACE)
				OptimizeFaceScratchMesh(geom, scratch, facenr, face_mp);

			std::vector<int> source_points = GetSourcePointNumbers(source, scratch, facenr, face_mp.quad != 0);
			ExtractFaceResult(scratch, source_points, facenr, result);
			for (int i = 0; i < accumulated_restrictions.Size(); i++)
				result.restrictions.push_back(accumulated_restrictions[i]);
			result.projection_type = projection_type;
			result.success = true;
			return;
		}
	}


	static void OCCMeshSurfaceParallel(OCCGeometry & geom, Mesh & mesh,
		int perfstepsend, OCCParallelMeshingContext & parallel)
	{
		const char * savetask = multithread.task;
		multithread.task = "Surface meshing";
		geom.facemeshstatus = 0;

		const int face_count = mesh.GetNFD();
		const double starttime = GetTime();
		const Box<3> geometry_box = geom.GetBoundingBox();
		std::vector<OCCFaceMeshResult> results(face_count);

		parallel.ParallelFor(face_count,
			[&](int, int face_index)
			{
				try
				{
					GenerateFaceMesh(geom, mesh, geometry_box, face_index + 1, perfstepsend,
						starttime, results[face_index]);
				}
				catch (const NgException & exception)
				{
					results[face_index].error_message = exception.What();
				}
				catch (const std::exception & exception)
				{
					results[face_index].error_message = exception.what();
				}
				catch (...)
				{
					results[face_index].error_message = "unknown worker exception";
				}
			});

		int error_count = 0;
		for (int face_index = 0; face_index < face_count; face_index++)
		{
			const OCCFaceMeshResult & result = results[face_index];
			const int facenr = face_index + 1;
			if (!result.success)
			{
				geom.facemeshstatus[face_index] = -1;
				error_count++;
				continue;
			}

			geom.facemeshstatus[face_index] = 1;
			if (result.retried)
				cout << "retry Surface " << facenr << endl;
			if (result.transfinite)
				PrintMessage(2, "Face ", facenr, " / ", face_count, " (transfinite)");
			else if (result.projection_type == PLANESPACE)
				PrintMessage(2, "Face ", facenr, " / ", face_count,
					" (plane space projection)");
			else
				PrintMessage(2, "Face ", facenr, " / ", face_count,
					" (parameter space projection)");
		}

		if (error_count)
		{
			cout << "WARNING! NOT ALL FACES HAVE BEEN MESHED" << endl;
			cout << "SURFACE MESHING ERROR OCCURRED IN " << error_count << " FACES:" << endl;
			for (int i = 0; i < face_count; i++)
				if (!results[i].success)
				{
					cout << "Face " << i + 1;
					if (!results[i].error_message.empty())
						cout << ": " << results[i].error_message;
					else if (results[i].error_type == 1)
						cout << ": Singular Matrix";
					else if (results[i].error_type == 2)
						cout << ": UV bounds exceeded";
					cout << endl;
				}
			multithread.task = savetask;
			throw NgException("Problem in parallel Surface mesh generation");
		}

		// Commit only after every worker succeeded.  Face order fixes global point
		// and element numbering independently of task completion order.
		for (int face_index = 0; face_index < face_count; face_index++)
		{
			const OCCFaceMeshResult & result = results[face_index];
			for (size_t i = 0; i < result.restrictions.size(); i++)
				mesh.RestrictLocalH(result.restrictions[i].point, result.restrictions[i].h);

			const int point_base = mesh.GetNP();
			for (size_t i = 0; i < result.points.size(); i++)
			{
				const MeshPoint & point = result.points[i];
				PointIndex pi = mesh.AddPoint(point, point.GetLayer(), point.Type());
				mesh.Point(pi).Singularity(point.Singularity());
			}

			for (size_t i = 0; i < result.elements.size(); i++)
			{
				Element2d element = result.elements[i];
				for (int j = 1; j <= element.GetNP(); j++)
					if (int(element.PNum(j)) < 0)
						element.PNum(j) = point_base - int(element.PNum(j));
				element.SetIndex(face_index + 1);
				mesh.AddSurfaceElement(element);
			}

			multithread.percent = 100 * (face_index + 1) / (face_count + VSMALL);
		}

		mesh.CalcSurfacesOfNode();
		mesh.Compress();
		multithread.task = savetask;
	}


	void OCCMeshSurface(OCCGeometry & geom, Mesh & mesh, int perfstepsend)
	{
		OCCParallelMeshingContext parallel(mparam.parallel_meshing_threads);
		if (!parallel.IsParallel(mesh.GetNFD()))
		{
			OCCMeshSurfaceSerial(geom, mesh, perfstepsend);
			return;
		}

		if (multithread.terminate)
			return;
		OCCMeshSurfaceParallel(geom, mesh, perfstepsend, parallel);
	}



	void OCCSetLocalMeshSize(OCCGeometry & geom, Mesh & mesh)
	{
		mesh.SetGlobalH(mparam.maxh);
		mesh.SetMinimalH(mparam.minh);

		Array<double> maxhdom;
		maxhdom.SetSize(geom.NrSolids());
		maxhdom = mparam.maxh;

		mesh.SetMaxHDomain(maxhdom);

		Box<3> bb = geom.GetBoundingBox();
		bb.Increase(bb.Diam() / 10);

		mesh.SetLocalH(bb.PMin(), bb.PMax(), 0.5);

		if (mparam.uselocalh)
		{
			const char * savetask = multithread.task;
			multithread.percent = 0;

			mesh.SetLocalH(bb.PMin(), bb.PMax(), mparam.grading);

			int nedges = geom.emap.Extent();
			OCCParallelMeshingContext parallel(mparam.parallel_meshing_threads);
			std::vector<TopoDS_Edge> edges(nedges);
			for (int i = 0; i < nedges; i++)
				edges[i] = TopoDS::Edge(geom.emap(i + 1));

			double mincurvelength = IGNORECURVELENGTH;
			double maxedgelen = 0;
			double minedgelen = 1e99;

			if (occparam.resthminedgelenenable)
			{
				mincurvelength = occparam.resthminedgelen;
				if (mincurvelength < IGNORECURVELENGTH) mincurvelength = IGNORECURVELENGTH;
			}

			multithread.task = "Setting local mesh size (elements per edge)";

			// setting elements per edge: compute independently, commit in edge order
			TopTools_IndexedDataMapOfShapeListOfShape edge_face_map;
			TopExp::MapShapesAndAncestors(geom.shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map);
			// Legacy behaviour: the edge size is only limited by the per-face limit of
			// the parent faces (geom.face_maxh, initialised from the global default at
			// load time), not by mparam.maxh.  Capping it here changes the local size
			// field and therefore the serial mesh.
			std::vector<double> edge_face_maxh(nedges, 1e99);
			for (int i = 0; i < nedges; i++)
			{
				const TopTools_ListOfShape& parent_faces = edge_face_map.FindFromKey(edges[i]);
				for (TopTools_ListIteratorOfListOfShape it(parent_faces); it.More(); it.Next())
				{
					const int face_index = geom.fmap.FindIndex(TopoDS::Face(it.Value()));
					if (face_index >= 1)
						edge_face_maxh[i] = min(edge_face_maxh[i], geom.face_maxh[face_index - 1]);
				}
			}

			std::vector<double> edge_lengths(nedges, 0.0);
			std::vector<std::vector<LocalHRestriction> > edge_size_restrictions(nedges);
			parallel.ParallelFor(nedges, [&] (int, int edge_index)
			{
				const TopoDS_Edge & e = edges[edge_index];
				if (BRep_Tool::Degenerated(e))
					return;

				GProp_GProps system;
				BRepGProp::LinearProperties(e, system);
				const double len = system.Mass();
				edge_lengths[edge_index] = len;
				if (len < mincurvelength)
					return;

				double localh = min(len / mparam.segmentsperedge, edge_face_maxh[edge_index]);
				double s0, s1;
				Handle(Geom_Curve) c = BRep_Tool::Curve(e, s0, s1);
				const int maxj = max((int)ceil(len / localh), 2);
				std::vector<LocalHRestriction> & result = edge_size_restrictions[edge_index];
				result.reserve(maxj + 1);
				for (int j = 0; j <= maxj; j++)
				{
					gp_Pnt pnt = c->Value(s0 + double(j) / maxj * (s1 - s0));
					result.push_back(LocalHRestriction(
						Point3d(pnt.X(), pnt.Y(), pnt.Z()), localh));
				}
			});

			for (int i = 0; i < nedges && !multithread.terminate; i++)
			{
				multithread.percent = 100 * i / double(nedges);
				if (edge_lengths[i] > 0)
				{
					maxedgelen = max(maxedgelen, edge_lengths[i]);
					minedgelen = min(minedgelen, edge_lengths[i]);
				}
				for (size_t j = 0; j < edge_size_restrictions[i].size(); j++)
					mesh.RestrictLocalH(edge_size_restrictions[i][j].point,
						edge_size_restrictions[i][j].h);
			}

			multithread.task = "Setting local mesh size (edge curvature)";

			// setting edge curvature

			int nsections = 20;

			std::vector<std::vector<LocalHRestriction> > edge_curvature_restrictions(nedges);
			parallel.ParallelFor(nedges, [&] (int, int edge_index)
			{
				const TopoDS_Edge & edge = edges[edge_index];
				if (BRep_Tool::Degenerated(edge))
					return;
				double s0, s1;
				Handle(Geom_Curve) c = BRep_Tool::Curve(edge, s0, s1);
				BRepAdaptor_Curve brepc(edge);
				BRepLProp_CLProps prop(brepc, 2, 1e-5);
				std::vector<LocalHRestriction> & result = edge_curvature_restrictions[edge_index];
				result.reserve(nsections);

				for (int j = 1; j <= nsections; j++)
				{
					const double s = s0 + j / (double)nsections * (s1 - s0);
					prop.SetParameter(s);
					const double curvature = prop.Curvature();
					if (curvature >= 1e99)
						continue;
					gp_Pnt pnt = c->Value(s);
					result.push_back(LocalHRestriction(
						Point3d(pnt.X(), pnt.Y(), pnt.Z()),
						ComputeH(fabs(curvature), mparam.maxh, mparam.curvaturesafety)));
				}
			});

			for (int i = 0; i < nedges && !multithread.terminate; i++)
			{
				multithread.percent = 100 * i / double(nedges);
				for (size_t j = 0; j < edge_curvature_restrictions[i].size(); j++)
					mesh.RestrictLocalH(edge_curvature_restrictions[i][j].point,
						edge_curvature_restrictions[i][j].h);
			}

			multithread.task = "Setting local mesh size (face curvature)";

			// setting face curvature

			int nfaces = geom.fmap.Extent();
			std::vector<TopoDS_Face> faces(nfaces);
			for (int i = 0; i < nfaces; i++)
				faces[i] = TopoDS::Face(geom.fmap(i + 1));

			std::vector<std::vector<LocalHRestriction> > face_curvature_restrictions(nfaces);
			parallel.ParallelFor(nfaces, [&] (int, int face_index)
			{
				const TopoDS_Face & face = faces[face_index];
				TopLoc_Location loc;
				Handle(Poly_Triangulation) triangulation = BRep_Tool::Triangulation(face, loc);
				if (triangulation.IsNull())
					return;

				BRepAdaptor_Surface sf(face, Standard_True);
				BRepLProp_SLProps prop(sf, 2, 1e-5);
				std::vector<LocalHRestriction> & result =
					face_curvature_restrictions[face_index];

				const int ntriangles = triangulation->NbTriangles();
				for (int j = 1; j <= ntriangles; j++)
				{
					gp_Pnt2d par[3];
					for (int k = 1; k <= 3; k++)
					{
						const int n = triangulation->Triangles()(j)(k);
						par[k - 1] = triangulation->UVNode(n);
					}
					CollectHTriangleRestrictions(par[0], par[1], par[2], &prop,
						result, mparam.maxh, mparam.curvaturesafety, 0);
				}
			});

			for (int i = 0; i < nfaces && !multithread.terminate; i++)
			{
				multithread.percent = 100 * i / double(nfaces);
				for (size_t j = 0; j < face_curvature_restrictions[i].size(); j++)
					mesh.RestrictLocalH(face_curvature_restrictions[i][j].point,
						face_curvature_restrictions[i][j].h);
			}

			// setting close edges

			if (occparam.resthcloseedgeenable)
			{
				multithread.task = "Setting local mesh size (close edges)";

				int sections = 100;

				Array<Line> lines(sections*nedges);

				Box3dTree* searchtree =
					new Box3dTree(bb.PMin(), bb.PMax());

				int nlines = 0;
				for (int i = 1; i <= nedges && !multithread.terminate; i++)
				{
					TopoDS_Edge edge = TopoDS::Edge(geom.emap(i));
					if (BRep_Tool::Degenerated(edge)) continue;

					double s0, s1;
					Handle(Geom_Curve) c = BRep_Tool::Curve(edge, s0, s1);
					BRepAdaptor_Curve brepc(edge);
					BRepLProp_CLProps prop(brepc, 1, 1e-5);
					prop.SetParameter(s0);

					gp_Vec d0 = prop.D1().Normalized();
					double s_start = s0;
					int count = 0;
					for (int j = 1; j <= sections; j++)
					{
						double s = s0 + (s1 - s0)*(double)j / (double)sections;
						prop.SetParameter(s);
						gp_Vec d1 = prop.D1().Normalized();
						double cosalpha = fabs(d0*d1);
						if ((j == sections) || (cosalpha < cos(10.0 / 180.0*M_PI)))
						{
							count++;
							gp_Pnt p0 = c->Value(s_start);
							gp_Pnt p1 = c->Value(s);
							lines[nlines].p0 = Point<3>(p0.X(), p0.Y(), p0.Z());
							lines[nlines].p1 = Point<3>(p1.X(), p1.Y(), p1.Z());

							Box3d box;
							box.SetPoint(Point3d(lines[nlines].p0));
							box.AddPoint(Point3d(lines[nlines].p1));

							searchtree->Insert(box.PMin(), box.PMax(), nlines + 1);
							nlines++;

							s_start = s;
							d0 = d1;
						}
					}
				}

				std::vector<double> line_min_distances(nlines, 1e99);
				parallel.ParallelFor(nlines, [&] (int, int line_index)
				{
					Line & line = lines[line_index];
					Box3d box;
					box.SetPoint(Point3d(line.p0));
					box.AddPoint(Point3d(line.p1));
					const double maxhline = max(mesh.GetH(box.PMin()),
						mesh.GetH(box.PMax()));
					box.Increase(maxhline);

					Array<int> linenums;
					searchtree->GetIntersecting(box.PMin(), box.PMax(), linenums);
					double mindist = 1e99;
					for (int j = 0; j < linenums.Size(); j++)
					{
						const int num = linenums[j] - 1;
						if (line_index == num) continue;
						if ((line.p0 - lines[num].p0).Length2() < 1e-15) continue;
						if ((line.p0 - lines[num].p1).Length2() < 1e-15) continue;
						if ((line.p1 - lines[num].p0).Length2() < 1e-15) continue;
						if ((line.p1 - lines[num].p1).Length2() < 1e-15) continue;
						mindist = min(mindist, line.Dist(lines[num]));
					}
					line_min_distances[line_index] =
						mindist / (occparam.resthcloseedgefac + VSMALL);
				});

				for (int i = 0; i < nlines && !multithread.terminate; i++)
				{
					multithread.percent = (100 * i) / double(nlines);
					double mindist = line_min_distances[i];
					if (mindist < 1e-3)
					{
						(*testout) << "extremely small local h: " << mindist
							<< " --> setting to 1e-3" << endl;
						(*testout) << "somewhere near " << lines[i].p0 << " - " << lines[i].p1 << endl;
						mindist = 1e-3;
					}
					mesh.RestrictLocalHLine(lines[i].p0, lines[i].p1, mindist);
				}

				delete searchtree;
			}

			multithread.task = savetask;

		}

		// Philippose - 09/03/2009
		// Added the capability to load the mesh size from a 
		// file also for OpenCascade Geometry
		// Note: 
		// ** If the "uselocalh" option is ticked in 
		// the "mesh options...insider" menu, the mesh 
		// size will be further modified by the topology 
		// analysis routines.
		// ** To use the mesh size file as the sole source 
		// for defining the mesh size, uncheck the "uselocalh"
		// option.
		mesh.LoadLocalMeshSize(mparam.meshsizefilename);
	}



	int OCCGenerateMesh(OCCGeometry & geom, Mesh *& mesh, MeshingParameters & mparam,
		int perfstepsstart, int perfstepsend)
	{
		multithread.percent = 0;

		if (perfstepsstart <= MESHCONST_ANALYSE)
		{
			delete mesh;
			mesh = new Mesh();
			mesh->geomtype = Mesh::GEOM_OCC;

			OCCSetLocalMeshSize(geom, *mesh);
		}

		if (multithread.terminate || perfstepsend <= MESHCONST_ANALYSE)
			return TCL_OK;

		if (perfstepsstart <= MESHCONST_MESHEDGES)
		{
			OCCFindEdges(geom, *mesh);

			/*
			cout << "Removing redundant points" << endl;

			int i, j;
			int np = mesh->GetNP();
			Array<int> equalto;

			equalto.SetSize (np);
			equalto = 0;

			for (i = 1; i <= np; i++)
			{
			for (j = i+1; j <= np; j++)
			{
			if (!equalto[j-1] && (Dist2 (mesh->Point(i), mesh->Point(j)) < 1e-12))
			equalto[j-1] = i;
			}
			}

			for (i = 1; i <= np; i++)
			if (equalto[i-1])
			{
			cout << "Point " << i << " is equal to Point " << equalto[i-1] << endl;
			for (j = 1; j <= mesh->GetNSeg(); j++)
			{
			Segment & seg = mesh->LineSegment(j);
			if (seg[0] == i) seg[0] = equalto[i-1];
			if (seg[1] == i) seg[1] = equalto[i-1];
			}
			}

			cout << "Removing degenerated segments" << endl;
			for (j = 1; j <= mesh->GetNSeg(); j++)
			{
			Segment & seg = mesh->LineSegment(j);
			if (seg[0] == seg[1])
			{
			mesh->DeleteSegment(j);
			cout << "Deleting Segment " << j << endl;
			}
			}

			mesh->Compress();
			*/

			/*
			for (int i = 1; i <= geom.fmap.Extent(); i++)
			{
			Handle(Geom_Surface) hf1 =
			BRep_Tool::Surface(TopoDS::Face(geom.fmap(i)));
			for (int j = i+1; j <= geom.fmap.Extent(); j++)
			{
			Handle(Geom_Surface) hf2 =
			BRep_Tool::Surface(TopoDS::Face(geom.fmap(j)));
			if (hf1 == hf2) cout << "face " << i << " and face " << j << " lie on same surface" << endl;
			}
			}
			*/

#ifdef LOG_STREAM
			(*logout) << "Edges meshed" << endl
				<< "time = " << GetTime() << " sec" << endl
				<< "points: " << mesh->GetNP() << endl;
#endif
		}

		if (multithread.terminate || perfstepsend <= MESHCONST_MESHEDGES)
			return TCL_OK;

		if (perfstepsstart <= MESHCONST_MESHSURFACE)
		{
			OCCMeshSurface(geom, *mesh, perfstepsend);
			if (multithread.terminate) return TCL_OK;

#ifdef LOG_STREAM
			(*logout) << "Surfaces meshed" << endl
				<< "time = " << GetTime() << " sec" << endl
				<< "points: " << mesh->GetNP() << endl;
#endif

#ifdef STAT_STREAM
			(*statout) << mesh->GetNSeg() << " & "
				<< mesh->GetNSE() << " & - &"
				<< GetTime() << " & " << endl;
#endif

			//      MeshQuality2d (*mesh);
			mesh->CalcSurfacesOfNode();
		}

		if (multithread.terminate || perfstepsend <= MESHCONST_OPTSURFACE)
			return TCL_OK;

		if (perfstepsstart <= MESHCONST_MESHVOLUME)
		{
			multithread.task = "Volume meshing";

			MESHING3_RESULT res = MeshVolume(mparam, *mesh);

			/*
					 ofstream problemfile("occmesh.rep",ios_base::app);

					 problemfile << "VOLUMEMESHING" << endl << endl;
					 if(res != MESHING3_OK)
						problemfile << "ERROR" << endl << endl;
					 else
						problemfile << "OK" << endl
						<< mesh->GetNE() << " elements" << endl << endl;

					 problemfile.close();
			*/

			if (res != MESHING3_OK) return TCL_ERROR;

			if (multithread.terminate) return TCL_OK;

			RemoveIllegalElements(*mesh);
			if (multithread.terminate) return TCL_OK;

			MeshQuality3d(*mesh);

#ifdef STAT_STREAM
			(*statout) << GetTime() << " & ";
#endif

#ifdef LOG_STREAM
			(*logout) << "Volume meshed" << endl
				<< "time = " << GetTime() << " sec" << endl
				<< "points: " << mesh->GetNP() << endl;
#endif
		}

		if (multithread.terminate || perfstepsend <= MESHCONST_MESHVOLUME)
			return TCL_OK;

		if (perfstepsstart <= MESHCONST_OPTVOLUME)
		{
			multithread.task = "Volume optimization";

			OptimizeVolume(mparam, *mesh);
			if (multithread.terminate) return TCL_OK;

#ifdef STAT_STREAM
			(*statout) << GetTime() << " & "
				<< mesh->GetNE() << " & "
				<< mesh->GetNP() << " " << '\\' << '\\' << " \\" << "hline" << endl;
#endif

#ifdef LOG_STREAM
			(*logout) << "Volume optimized" << endl
				<< "time = " << GetTime() << " sec" << endl
				<< "points: " << mesh->GetNP() << endl;
#endif

			// cout << "Optimization complete" << endl;

		}

		(*testout) << "NP: " << mesh->GetNP() << endl;
		for (int i = 1; i <= mesh->GetNP(); i++)
			(*testout) << mesh->Point(i) << endl;

		(*testout) << endl << "NSegments: " << mesh->GetNSeg() << endl;
		for (int i = 1; i <= mesh->GetNSeg(); i++)
			(*testout) << mesh->LineSegment(i) << endl;

		return TCL_OK;
	}
}

#endif
