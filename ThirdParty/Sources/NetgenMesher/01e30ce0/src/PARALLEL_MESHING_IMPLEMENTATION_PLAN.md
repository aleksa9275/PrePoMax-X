# Parallel OCC meshing implementation plan

## Goal and execution model

Parallelize independent OCC meshing work while preserving stable global numbering,
the existing serial behavior, and failure semantics.

The public `parallel_meshing_threads` parameter is a positive integer:

- `1`: use the legacy serial path. This remains the default.
- `>1`: use at most the requested number of workers.

Workers never mutate the destination mesh. They compute into task-local result
slots, after which the caller validates every result and commits them serially in
geometry order. This makes the parallel path deterministic for a fixed input and
worker configuration and prevents partial face commits after a worker failure.

## Milestone 1: infrastructure — implemented

- Add an `OSD_ThreadPool`-based OCC parallel context.
- Expose and transfer the worker-count parameter through `nglib`.
- Make shared low-level services safe for concurrent meshing:
  profiler bookkeeping, timestamp generation, block allocation, dynamic-memory
  registration, AD-tree traversal scratch, linear-search scratch, and diagnostic
  state.
- Keep progress reporting and the final mesh commit on the coordinator thread.

## Milestone 2: local sizing — implemented

Parallelize the read-only geometry calculations for:

- elements-per-edge restrictions;
- edge-curvature restrictions;
- face-curvature restrictions;
- close-edge proximity queries.

Each task records local-H restrictions without changing `Mesh::LocalH`. The
coordinator applies restrictions afterward in original edge/face order.

## Milestone 3: unique edges — implemented

- Build the unique OCC edge list once.
- Discretize each geometric edge once in a worker-local result.
- Preserve the serial topology walk for point de-duplication, UV data,
  orientation, warnings, and segment insertion.

## Milestone 4: faces and 2-D optimization — implemented

- Give every face its own scratch mesh and OCC surface mesher.
- Reproduce both parameter-space and plane-space boundary setup.
- Preserve the existing two-attempt projection fallback.
- Carry dynamic local-H restrictions from the first attempt into the retry.
- Run the complete face-local optimization sequence in the same worker:
  edge swapping, smoothing, element combination, and final smoothing.
- Extract only the face's interior points and elements into its result slot.
- If any face fails, report all failed face numbers and commit none of the faces.
- Otherwise, merge restrictions, points, and elements in ascending face order,
  then rebuild surface-to-node data and compress the mesh.

The parallel face mesh can differ from the legacy serial mesh because dynamic
local-H restrictions discovered while meshing one face are deliberately not fed
into simultaneously running faces. They are retained for the committed mesh and
subsequent volume meshing. Results are deterministic within the parallel path.

## Milestone 5: volume meshing of independent subdomains — implemented

Entry point: `MeshVolumeAndOptimize` (meshfunc.hpp, parallelvolume.cpp), used by
`Ng_GenerateVolumeMesh`. The serial `MeshVolume` was split into
`MeshVolumePrepare` (compress, overlap and consistency checks),
`MeshVolumeDomain` (legacy body for one subdomain) and `MeshVolumeDomains`
(legacy loop); `MeshVolume` is the composition and its output is unchanged.

- After the preparation checks, `MeshVolumeParallel` decides whether the
  parallel path applies: more than one subdomain, more than one worker, no
  volume elements yet, no identifications and no open quads. Otherwise the
  legacy serial path runs, followed by the global `RemoveIllegalElements` and
  `OptimizeVolume`.
- Every subdomain gets a private scratch mesh holding only its boundary: the
  surface elements whose face descriptor has the subdomain on either side, the
  points they reference (renumbered 1..n), the segments between those points,
  the locked points among them, all face descriptors, the global and minimal
  size, the per-domain size limits and a deep copy of the local size octree
  (`LocalH(const LocalH &)`, box order preserved, father links resolved through
  a box index instead of a hash map). The worker runs `MeshVolumeDomain`,
  `RemoveIllegalElements` and `OptimizeVolume` on the scratch mesh with a
  private `MeshingParameters` copy.
- Workers never touch the destination mesh. The worker verifies that the first
  n points are still the untouched boundary points, then extracts the new points
  and the non-deleted volume elements. If any subdomain fails, the coordinator
  reports every failed subdomain and throws; nothing is committed.
- The coordinator appends the results in subdomain order, mapping boundary
  point numbers back to the global numbers and new points behind the existing
  ones, then runs `CalcSurfacesOfNode` and `MeshQuality3d` once. The result is
  deterministic for a fixed input and independent of the worker count.
- Worker threads are dispatched with `std::thread` (no OpenCASCADE dependency in
  the meshing library); `0` workers means `std::thread::hardware_concurrency()`.
- Per-domain optimization equals the global one: `SwapImprove` skips boundary
  edges, `CombineImprove` and `ImproveMesh` move inner points only, and volume
  elements of different subdomains share only boundary points.
- Differences to the serial path: a subdomain does not see the points of other
  subdomains (the serial loop offered every point inside the subdomain bounding
  box to the advancing front and to Delaunay), and block-fill size restrictions
  made for one subdomain are not visible to the others. Both were
  order-dependent side effects of the serial loop.

Shared-state changes for the worker threads: `testout` is now per thread
(worker threads write to a null stream, only the thread that opened `test.out`
writes to it), `tets_in_qualclass` is per thread, worker threads set
`SetThreadMessagesQuiet` so only the coordinator prints progress (warnings and
errors always print), `MeshQuality3d` returns early on quiet threads, the
remaining function-local scratch statics in `ruler3.cpp` were removed, the
Jacobian smoothing scratch array lives in `Opti2dLocalData`, and
`BlockAllocator` keeps a free list per thread so tree-node allocation no longer
serializes on one mutex. The per-face scratch meshes of milestone 4 copy the
point array in one step instead of one time-stamped `AddPoint` per point.

Memory: every worker holds one copy of the local size octree while it works
(544,161 boxes, about 57 MB, for the 76-solid compound; below 2 GB with 32
workers) plus the boundary of its subdomain.

Validation on the 76-solid compound with the model's own parameters (32-core
workstation, wall-clock seconds of the phases printed by `NetGenMesher.exe`):

| workers | surface | volume | total | result |
|---|---|---|---|---|
| 1 | 15.0 | 53.3 | 74 | 122,763 points, 496,907 elements, byte-identical to the serial build |
| 2 | 8.3 | 22.7 | 37 | 120,886 points, 483,258 elements |
| 4 | 4.6 | 17.2 | 27 | identical file to 2 workers |
| 8 | 4.3 | 16.9 | 27 | identical file to 2 workers |

The volume phase levels off at 4 workers because the largest solid alone takes
about 15 s; finer load balancing needs intra-solid parallelism (see below).
Radius-ratio quality of the parallel mesh is on par with the serial one: mean
0.751 vs 0.748, tets below 0.2: 4,600 vs 5,353, consistent orientation, no
dangling points, all 76 material indices present. Repeated runs are
byte-identical. With the default parameters (coarser, 428,057 points,
1,877,506 elements) the parallel run also completes; the transient
"more elements on face" system messages it prints come from the advancing
front of the legacy per-subdomain code and already appeared in the serial
volume meshing of parallel surface meshes since milestone 4. The final meshes
are consistent: no duplicate surface triangles, every tetrahedron face is
shared by at most two tetrahedra, and every boundary face is a surface
element.

## Milestone 6: serial bottlenecks around the parallel work — implemented

Profiling the 76-solid compound at eight workers showed that a quarter of the
remaining time was serial work on either side of the parallel phases.

**Duplicated open-element sweeps.** `MeshVolumePrepare` looped over every
subdomain calling `Mesh::FindOpenElements` for the boundary consistency check,
and `MeshVolumeParallel` then looped over every subdomain again to find out
whether any of them has open quadrilaterals. Each call is a full pass over all
points and surface elements, so the boundary mesh was scanned 152 times.

- `Mesh::ComputeOpenElements(dom, openelems)` is the computation of
  `FindOpenElements` without its side effects. It is `const` and writes to a
  caller-owned array, so subdomains can be handled concurrently.
  `FindOpenElements` now calls it and keeps the parts that change the mesh,
  the boundary edges and the fixed point types, so every existing caller
  behaves as before.
- `Mesh::CheckConsistentBoundary(openelems)` takes the same caller-owned array.
- The preparation loop runs once, in parallel, into private arrays, and records
  the open quadrilaterals in a `VolumePrepareInfo` that the parallel path reads
  instead of sweeping again.
- The worker dispatch used by the subdomain mesher moved to `parallelfor.hpp`
  so the preparation pass can share it.

**Quadratic point lookups in edge meshing.** `OCCFindEdges` contained three
linear scans over all points added so far: vertex de-duplication, the lookup of
an edge's two end vertices, and the de-duplication of edge points. On this model
they add up to roughly six hundred million distance evaluations, and they are
serial, which is why edge meshing barely improved with more workers. All three
now use a `Point3dTree`. The tie-breaking rule of each scan is reproduced
exactly, the last match for the vertex lookup and the first for the edge points,
so the result is unchanged.

**Largest subdomain first.** Subdomains were handed out in index order. Work is
taken dynamically, so a large solid that starts late finishes alone while the
other workers idle. `MeshVolumePrepare` already counts the boundary elements of
every subdomain, so that count is carried in `VolumePrepareInfo` and the
subdomain mesher sorts its dispatch order by it, descending, stable so equal
costs keep subdomain order. Only the order of the work changes; results are
still committed in subdomain order, and the mesh is byte-identical.

The boundary element count predicts the cost well: its correlation with the
number of tetrahedra a subdomain receives is 0.996 on the reference model, where
one solid holds 36 per cent of all tetrahedra. A schedule simulation over the
real subdomain sizes predicted a 7.4 per cent shorter volume phase at four
workers and 2.8 per cent at eight, and reached the theoretical optimum in both
cases. Measured, with everything else held constant:

| workers | index order | largest first |
|---|---|---|
| 4 | 11.70, 11.75 | 10.82, 10.77 |
| 8 | 10.95, 11.51 | 10.75, 10.66 |

That is 7.5 per cent at four workers against 7.4 predicted. The gain is bounded
by the largest solid, so it matters most on models with several large solids and
cannot exceed the critical path.

Phase times in seconds on the 76-solid compound:

| phase | 1 worker before | 1 worker after | 8 workers before | 8 workers after |
|---|---|---|---|---|
| local mesh size | 1.85 | 1.87 | 1.14 | 1.15 |
| edges | 2.73 | 0.89 | 2.28 | 0.38 |
| surface | 15.74 | 16.05 | 3.24 | 3.19 |
| volume | 52.42 | 49.39 | 15.06 | 11.67 |

Total wall time at eight workers fell from 23 to 18 seconds. The meshes are
byte-identical to the previous build at one and at eight workers, a repeated run
is byte-identical, and four unrelated single-part and compound geometries mesh
byte-identically as well. A fifth geometry fails on both builds in the same way
and writes the same error mesh, so the failure path is unchanged too.

## Meshing output

Two long-standing Netgen diagnostics reached the console without context. With
many workers they interleave and look like failures, although neither reports a
defect of the finished mesh.

- `BFGS update error1` / `error2` (bfgs.cpp) fire when the rank-one update of
  the approximate Hessian in the point smoother is not positive definite. The
  routine then restores the starting point, so the smoothing step for that one
  point is discarded and nothing else changes. The two `cerr` writes were
  removed; the event is still recorded in `test.out`. The original
  pre-parallel build printed these too.
- `more elements on face` (`Mesh::FindOpenElements`) means that a face was
  claimed by more than two volume elements of one subdomain at that moment.
  The advancing front produces such a configuration occasionally and the repair
  loop removes it. It is no longer printed as a system error; `NoteNonManifoldFace`
  counts it and the detail still goes to `test.out` on the coordinator thread.
  The message appears only with a parallel surface mesh, since milestone 4, and
  never in a fully serial run.

The verdict is now made on the finished mesh instead of on an intermediate
state. When the counter is non-zero, `CountNonManifoldVolumeFaces` sorts the
face point triples of the final mesh and reports either

    Repaired N transient face conflict(s) reported by the advancing front

or, if a face really is shared by more than two elements, an error naming the
count. The check costs nothing when the front never complained.

Both paths close the phase with

    Volume meshing finished: X points, Y elements in Z subdomain(s)

and the parallel path prints one commit line per subdomain instead of two.

## A meshing failure terminated the process

Three records for `NetGenMesher.exe` appeared in the Windows application log
within two minutes of each other, all with exception code `0xc0000409` in
`ucrtbase.dll` at the same fault offset. That code is the runtime's fail-fast
path and the faulting module is the C runtime rather than the mesher, which is
the signature of `abort` rather than a bad memory access. A test run also died
during volume meshing leaving no output file and no message.

The cause is not memory corruption. Netgen reports a meshing failure by
throwing `NgException`. `Ng_OCC_GenerateSurfaceMesh` caught it, but
`Ng_GenerateVolumeMesh`, `Ng_OCC_SetLocalMeshSize` and
`Ng_OCC_GenerateEdgeMesh` did not, and neither did the executable, so an
exception left `main` and the runtime terminated the process. Nothing was
printed because the reason travels in the exception and standard output was
still buffered.

- Every nglib entry point that meshes now catches, names the stage and returns
  `NG_ERROR` after printing the message, so the reason reaches the caller.
- `Ng_GenerateVolumeMesh` also honours the `MESHING3_RESULT` it used to discard,
  which previously let a failed volume mesh report success.
- `Ng_OCC_GenerateSurfaceMesh` used to catch silently; it now prints the reason
  as well.
- The executable runs every command under a backstop handler that reports the
  failure and exits with code 1.

Verified with a library that throws deep inside volume meshing: the process
prints the stage and the reason, exits 1, and writes no crash record. The
meshes of the reference compound at one and eight workers and of four smaller
geometries are unchanged.

This does not make a model that cannot be meshed succeed. It turns a silent
termination into a reported failure, so the next occurrence names its cause.

## Validation completed

- Debug and Release OCC library builds pass.
- Debug and Release test-application builds pass.
- Five repeated four-worker edge runs produced byte-identical output.
- Seven repeated four-worker face-generation runs produced 2,927 surface points
  and 5,866 surface elements every time.
- Six repeated four-worker face-generation plus 2-D-optimization runs produced
  2,907 surface points and 5,826 surface elements every time.
- The serial compatibility run reproduced 2,925 surface points and 5,862 surface
  elements.
- All complete surface tests continued through successful volume meshing.

## Further parallelization opportunities

Edges, faces and independent solids are parallel, and the serial work around
them has been cut. At eight workers the volume phase is about 11.7 s of a 16.4 s
total, and its parallel part is bounded by the single largest solid. Remaining
targets, in the order they are worth doing:

1. **Tetrahedral generation inside one solid.** This is now the critical path
   and the only way to speed up a model made of one large solid. Measure the
   split between front generation and optimization first, by meshing with
   `optsteps_3d` set to zero. If optimization dominates, the per-solid passes
   can run concurrently over independent sets of elements chosen by a
   deterministic colouring. If generation dominates, the interior has to be
   partitioned with a frozen conforming interface, which is a separate
   architectural milestone.
2. **Boundary validation and quality analysis.** The remaining overlap,
   legality, element quality and statistics passes can use read-only per-element
   reductions. `CheckOverlappingBoundary` is still serial inside the volume
   preparation.
3. **Geometry preparation.** Bounding boxes, face properties, curvature samples
   and some OCC triangulation preparation can be parallelized once any lazy OCC
   caches are initialized safely.
4. **Import, export and conversion.** The result file is written and read back
   through unbuffered streams, which is seconds on large models.
5. **Memory of the subdomain workers.** The per-worker copy of the local size
   octree could be replaced by a shared read-only tree plus per-worker flag
   arrays and a per-worker overlay for block-fill restrictions, if very large
   models with many workers run short of memory.

## Regression fixes after the first PrePoMax deployment

A 76-solid compound (`kontejner_to_mesh.pmx`, 4,430 faces, 11,612 edges) meshed
with the pre-parallel build but crashed with `parallel_meshing_threads = 1` in the
new build (access violation in `nglib.dll`, `FindInnerPoint`, findip.hpp:93),
while two or more workers succeeded. Two independent defects were involved.

1. **Serial local sizing was not legacy-identical.** The parallel
   elements-per-edge pass initialised the per-edge limit with `mparam.maxh`. The
   legacy loop limited the edge size only by `geom.face_maxh`, which is set from
   the global default (1e10) when the geometry is loaded, so the edge size was
   effectively uncapped. Capping it changed the local-H octree refinement and the
   1.2-factor early return in `LocalH::SetH`, which moved edge subdivision points
   and changed the surface mesh. The limit is now initialised with a large value
   again; the serial edge mesh is byte-identical to the old build.
2. **Latent Netgen 5.3.1 bug in `AdFront3::GetGroup`.** The point loop tested
   `points.Get(i).Valid()` with `i` being the stale face counter from the previous
   loop instead of `points[pi].Valid()`. Whether the group was built correctly
   therefore depended on an arbitrary, possibly deleted or out-of-range point.
   When it was not, `FindInnerPoint` read garbage point indices and crashed.
   The old build only survived by luck of mesh and heap layout. Fixed to test the
   visited point.

Validation on the compound with the model's own parameters: 1 worker reproduces
the old build exactly (122,763 points, 496,907 elements); 2 workers succeed
(121,710 points, 491,273 elements); the `GetGroup` fix alone also removes the
crash on the previously failing mesh.

Known remaining deviation: with `closeedgeenable = 1` the search box of every
line is now sized from the local-H field before any close-edge restriction is
applied, whereas the legacy loop interleaved sizing and restriction. PrePoMax
never enables this option.
