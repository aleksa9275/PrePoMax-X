/**************************************************************************/
/* File:   parallelvolume.cpp                                             */
/* Purpose: volume meshing of independent subdomains in parallel          */
/**************************************************************************/

/*
  Every subdomain (solid) is meshed in a private scratch mesh that holds only
  the boundary of that subdomain: the surface elements whose face descriptor
  has the subdomain on either side, the points they reference (renumbered
  1..n), the segments between those points, all face descriptors, plus a deep
  copy of the local size function.  A worker runs the legacy per-subdomain
  volume meshing, the removal of illegal elements and the volume optimization
  on that scratch mesh with a private parameter set.  The workers never touch
  the destination mesh.  When all subdomains succeeded the coordinator appends
  the new points and volume elements in subdomain order, which keeps the
  numbering deterministic for a fixed input and independent of the worker
  count.

  Volume elements of different subdomains only share boundary points, the
  optimizers never move boundary points and never swap across boundary edges,
  so the per-subdomain optimization is equivalent to the global one.  What
  differs from the serial path is that a subdomain does not see the points of
  other subdomains and that local size restrictions made while block-filling
  one subdomain are not visible to the others.
*/

#include <mystdlib.h>
#include "meshing.hpp"

#include "parallelfor.hpp"

#include <algorithm>
#include <atomic>
#include <string>
#include <vector>

namespace netgen
{
  namespace
  {
    struct DomainVolumeResult
    {
      /// global point number of every scratch boundary point 1..n
      std::vector<PointIndex> boundary_points;
      /// points created for the subdomain; scratch numbers n+1, n+2, ...
      std::vector<MeshPoint> points;
      /// volume elements with scratch point numbers
      std::vector<Element> elements;
      bool success;
      std::string error;

      DomainVolumeResult() : success(false) { }
    };


    bool FaceTouchesDomain (const Mesh & mesh, int faceindex, int domain)
    {
      const FaceDescriptor & fd = mesh.GetFaceDescriptor(faceindex);
      return fd.DomainIn() == domain || fd.DomainOut() == domain;
    }


    /*
      Fills scratch with the boundary of the subdomain and returns the global
      point numbers of the scratch points (position i holds scratch point i+1).
    */
    void BuildDomainScratch (const Mesh & source, int domain, int ndomains,
                             const MeshingParameters & mp, Mesh & scratch,
                             std::vector<PointIndex> & boundary_points)
    {
      scratch.geomtype = source.geomtype;
      scratch.SetGlobalH(source.GetGlobalH());
      scratch.SetMinimalH(source.GetMinimalH());

      Array<double> maxhdomain(ndomains);
      for (int k = 1; k <= ndomains; k++)
        maxhdomain.Elem(k) = source.MaxHDomain(k);
      scratch.SetMaxHDomain(maxhdomain);

      scratch.SetLocalH(source.LocalHFunction());

      for (int i = 1; i <= source.GetNFD(); i++)
        scratch.AddFaceDescriptor(source.GetFaceDescriptor(i));

      Array<int, PointIndex::BASE> glob2loc(source.GetNP());
      glob2loc = 0;
      boundary_points.clear();

      for (SurfaceElementIndex sei = 0; sei < source.GetNSE(); sei++)
        {
          const Element2d & sel = source[sei];
          if (sel.IsDeleted() || !FaceTouchesDomain(source, sel.GetIndex(), domain))
            continue;

          Element2d el = sel;
          for (int j = 0; j < el.GetNP(); j++)
            {
              PointIndex gpi = sel[j];
              if (!glob2loc[gpi])
                {
                  const MeshPoint & point = source[gpi];
                  PointIndex lpi = scratch.AddPoint(point, point.GetLayer(), point.Type());
                  scratch.Point(lpi).Singularity(point.Singularity());
                  boundary_points.push_back(gpi);
                  glob2loc[gpi] = int(boundary_points.size());
                }
              el[j] = glob2loc[gpi];
            }
          scratch.AddSurfaceElement(el);
        }

      for (SegmentIndex si = 0; si < source.GetNSeg(); si++)
        {
          const Segment & seg = source[si];
          if (!glob2loc[seg[0]] || !glob2loc[seg[1]])
            continue;
          Segment lseg = seg;
          lseg[0] = glob2loc[seg[0]];
          lseg[1] = glob2loc[seg[1]];
          scratch.AddSegment(lseg);
        }

      const Array<PointIndex> & locked = source.LockedPoints();
      for (int i = 0; i < locked.Size(); i++)
        if (glob2loc[locked[i]])
          scratch.AddLockedPoint(glob2loc[locked[i]]);
    }


    void MeshDomainInScratch (const Mesh & source, const MeshingParameters & mp,
                              int domain, int ndomains, DomainVolumeResult & result)
    {
      SetThreadMessagesQuiet(true);

      try
        {
          Mesh scratch;
          BuildDomainScratch(source, domain, ndomains, mp, scratch, result.boundary_points);
          const int nlocal = int(result.boundary_points.size());

          MeshingParameters dmp;
          dmp.CopyFrom(mp);
          const double globmaxh = dmp.maxh;

          if (nlocal > 0)
            MeshVolumeDomain(dmp, scratch, domain, globmaxh);
          dmp.maxh = globmaxh;

          if (scratch.GetNE() > 0)
            {
              RemoveIllegalElements(scratch);
              OptimizeVolume(dmp, scratch);
            }

          // The boundary points must still be the first nlocal points with their
          // original coordinates, otherwise the results cannot be merged.
          if (scratch.GetNP() < nlocal)
            throw NgException("boundary points were removed from the subdomain mesh");
          for (int i = 1; i <= nlocal; i++)
            {
              const MeshPoint & a = scratch.Point(i);
              const MeshPoint & b = source[result.boundary_points[i - 1]];
              if (a(0) != b(0) || a(1) != b(1) || a(2) != b(2))
                throw NgException("a boundary point was moved in the subdomain mesh");
            }

          for (int i = nlocal + 1; i <= scratch.GetNP(); i++)
            result.points.push_back(scratch.Point(i));

          for (ElementIndex ei = 0; ei < scratch.GetNE(); ei++)
            {
              const Element & el = scratch[ei];
              if (el.IsDeleted() || el[0] <= PointIndex::BASE - 1)
                continue;
              result.elements.push_back(el);
            }

          result.success = true;
        }
      catch (NgException & exception)
        {
          result.error = exception.What();
        }
      catch (std::exception & exception)
        {
          result.error = exception.what();
        }
      catch (...)
        {
          result.error = "unknown worker exception";
        }

      SetThreadMessagesQuiet(false);
    }
  }



  bool MeshVolumeParallel (MeshingParameters & mp, Mesh & mesh3d,
                           const VolumePrepareInfo & info)
  {
    const int ndomains = mesh3d.GetNDomains();
    const int threads = ParallelMeshingThreads(mp, ndomains);

    if (threads <= 1 || ndomains <= 1)
      return false;
    if (mesh3d.GetNE() != 0)
      return false;
    if (!mesh3d.LocalHFunctionGenerated())
      return false;
    if (mesh3d.GetIdentifications().GetMaxNr() > 0)
      return false;

    // Open quads need the prism / pyramid rules with connected point pairs and
    // are meshed by the legacy path.  MeshVolumePrepare already looked.
    if (info.has_open_quads)
      return false;

    mesh3d.CalcSurfacesOfNode();

    PrintMessage(1, "Volume meshing of ", ndomains, " subdomains with ",
                 threads, " threads");
    PrintMessage(3, "Local size function: ", mesh3d.LocalHFunction().GetNBoxes(), " boxes");
    (*testout) << "parallel volume meshing: " << ndomains << " subdomains, "
               << threads << " threads" << endl;

    const char * savetask = multithread.task;
    multithread.task = "Volume meshing";
    multithread.percent = 0;

    std::vector<DomainVolumeResult> results(ndomains);
    std::atomic<int> completed(0);
    const Mesh & source = mesh3d;
    const MeshingParameters & parameters = mp;

    /*
      Mesh the largest subdomains first.  Work is handed out dynamically, so a
      large solid that starts late leaves the other workers idle while it
      finishes alone.  The boundary element count counted by MeshVolumePrepare
      predicts the cost of a subdomain closely, and sorting by it reaches the
      shortest possible schedule on the reference model.  Only the order of the
      work changes; results are still committed in subdomain order.
    */
    std::vector<int> order(ndomains);
    for (int i = 0; i < ndomains; i++)
      order[i] = i;

    if (info.boundary_elements.Size() == ndomains)
      {
        const Array<int> & cost = info.boundary_elements;
        std::stable_sort(order.begin(), order.end(),
          [&cost] (int a, int b) { return cost[a] > cost[b]; });
      }

    ParallelForItems(ndomains, threads,
      [&] (int item)
      {
        const int index = order[item];
        MeshDomainInScratch(source, parameters, index + 1, ndomains, results[index]);
        multithread.percent = 100.0 * (++completed) / ndomains;
      });

    multithread.task = savetask;

    if (multithread.terminate)
      return true;

    int failed = 0;
    for (int k = 1; k <= ndomains; k++)
      if (!results[k - 1].success)
        failed++;

    if (failed)
      {
        PrintError("Volume meshing failed in ", failed, " of ", ndomains, " subdomains:");
        for (int k = 1; k <= ndomains; k++)
          if (!results[k - 1].success)
            PrintError("  subdomain ", k, ": ", results[k - 1].error.c_str());
        throw NgException("Stop meshing since volume meshing of a subdomain failed");
      }

    // Commit in subdomain order: new points first, then the elements with the
    // scratch point numbers mapped to the destination mesh.
    for (int k = 1; k <= ndomains; k++)
      {
        const DomainVolumeResult & result = results[k - 1];
        const int nlocal = int(result.boundary_points.size());
        const int point_base = mesh3d.GetNP();

        for (size_t i = 0; i < result.points.size(); i++)
          {
            const MeshPoint & point = result.points[i];
            PointIndex pi = mesh3d.AddPoint(point, point.GetLayer(), point.Type());
            mesh3d.Point(pi).Singularity(point.Singularity());
          }

        for (size_t i = 0; i < result.elements.size(); i++)
          {
            Element el = result.elements[i];
            for (int j = 1; j <= el.GetNP(); j++)
              {
                const int pnum = el.PNum(j);
                if (pnum <= nlocal)
                  el.PNum(j) = result.boundary_points[pnum - 1];
                else
                  el.PNum(j) = point_base + (pnum - nlocal);
              }
            el.SetIndex(k);
            mesh3d.AddVolumeElement(el);
          }

        PrintMessage(2, MyStr("Subdomain ") + MyStr(k) + MyStr(" of ") + MyStr(ndomains)
                     + MyStr(": ") + MyStr((int) result.points.size()) + MyStr(" points, ")
                     + MyStr((int) result.elements.size()) + MyStr(" elements"));
      }

    mesh3d.CalcSurfacesOfNode();
    mesh3d.mglevels = 1;

    MeshQuality3d(mesh3d);
    ReportVolumeMeshingResult(mesh3d);

    return true;
  }



  MESHING3_RESULT MeshVolumeAndOptimize (MeshingParameters & mp, Mesh & mesh3d)
  {
    VolumePrepareInfo info;
    MeshVolumePrepare(mp, mesh3d, &info);

    if (MeshVolumeParallel(mp, mesh3d, info))
      return MESHING3_OK;

    MESHING3_RESULT result = MeshVolumeDomains(mp, mesh3d);
    if (result != MESHING3_OK)
      return result;

    RemoveIllegalElements(mesh3d);
    OptimizeVolume(mp, mesh3d);

    // The parallel path reports inside MeshVolumeParallel, where the workers
    // have already optimized; the serial path is only final here.
    ReportVolumeMeshingResult(mesh3d);

    return MESHING3_OK;
  }
}
