# Proposed migration specification

Status: draft for maintainer review. No interfaces or application code below have been implemented. Goal: preserve upstream source identity, engineering methods and command/API semantics while containing platform differences.

## Proposed boundaries

| Boundary | Proposed contract and responsibilities | Existing seam / constraint |
|---|---|---|
| Session/application service | Own FeModel/results/jobs/commands; serialize mutations, history and undo/redo; expose capabilities/state, not controls | Controller + IPython*Gateway. Keep one behavior layer; gradually replace explicit FrmMain calls with services |
| UI dispatcher | Invoke/Post on owning UI thread, busy state, cancellation and shutdown behavior | RpcUiThread BeginInvoke and FrmMain InvokeIfRequired; VTK reads/picks must execute on render thread |
| User interaction | Notifications, explicit prompts, file selection, progress; unattended decision refusal with existing error/exit semantics | MessageBoxes, ICommandWithDialog, BatchRunReport; never silently answer destructive model prompts |
| View service | Scene upload/update, visibility, fields/deformation, camera, clipping, pick/area pick and highlight/export | IPythonViewGateway/IPythonSelectionGateway, vtkMaxActorData and global IDs. Core uses domain arrays/IDs; VTK objects remain in view adapter |
| Tool/process service | Resolve immutable tool/version/capabilities; launch with executable + argument vector + cwd + env; stream stdout/stderr; asynchronous completion, timeout and whole-tree cancellation | ExecutableJobRunner, CaeJob; adapter supports Windows job objects and POSIX process containment. Avoid global cwd/env changes |
| Solver adapter | Build invocation from existing solver semantics; monitor .sta/.cvg/.dat, detect errors/output, handle partial results and continuation/wear cycles | AnalysisJob.Run_Win10/Run_OldWin; preserve statuses and OMP_NUM_THREADS; optional Abaqus/FEMaster must remain explicit capabilities |
| Native mesh/CAD adapters | Extend IMesherRunner; input parameters/model snapshots, isolated workdir, generated mesh + diagnostics + topology mapping | Preserve custom Netgen/Gmsh/MMG/QuadWild file protocols and algorithms. Keep CAD operations separate from mesh creation capability |
| Native library resolver | OS/RID/architecture lookup, explicit version/ABI probe and dependent-library diagnosis | GmshCommon replacement, lp_solve and Lib3MF P/Invoke; use C ABI and explicit ownership/marshalling |
| Paths/settings | Assets, user-private configuration, scratch/run/project-relative resolution, migration of stored foreign paths | Globals paths, Tools, SettingsContainer; never use app install path as universal writable directory |
| Serialization/clone service | Version-aware project/history/settings reader/writer; explicit bounded graph mapping and clone behavior preserving aliases | BinaryFormatter+custom binary blocks, binder, deep clones; maintain serialized type identities until proven mapping |
| Automation transport | Preserve MCP tool/schema/error contract, guide, JSON, batching/cancellation; local token/session discovery and access controls | Existing Rpc/Mcp/Python services; adapt Windows named-pipe ACL and session-file permissions, not public-network exposure |

Interfaces should express actual observed needs; do not create a giant `IFrmMain` that reproduces hundreds of UI methods. Start with notifications, paths/processes and structured view updates. Keep Windows adapters delegating to the current frontend while regression tests anchor each extraction. New project boundaries may initially link existing source rather than move it. This preserves diff locality, but linked source must not create duplicate type ownership within one process.

## Build and assembly proposal

After approval, probe a currently supported .NET LTS target (installed .NET 10 is a candidate, not a commitment). Preserve legacy net48 solution while adding isolated SDK-style feasibility projects. Test the smallest managed slice first, then the full dependency closure. Keep CaeGlobals/CaeMesh/CaeModel/CaeResults namespaces, serialized field names and assembly identities where compatibility requires them. Multi-targeting is desirable only where source and dependencies permit it; old project packaging and C++/CLI cannot simply be retargeted for macOS.

Separate presentation exports (e.g. ThreeMF actor/color conversion) from engineering exports without rewriting model calculations. Do not remove VTK integer cell types/connectivity because they have “vtk” in their name. Keep transient scene/runtime handles out of persistent domain graphs.

## First feasibility experiment: .NET and compatibility

Build a source-linked managed slice covering STL, Vec3D/Matrix, equations/units, representative element/material/step and input-output readers. Record exact required dependency exclusions/adapters and failed APIs. Compare parsed nodes/connectivity, material values and solver deck semantics against Windows. A subset build proves only that subset.

In parallel inspect real PMX/PMH payloads produced by pinned Windows versions. Inventory every serialized type/assembly and custom block. Evaluate safe NRBF record reading/explicit construction, compatible writing and clone replacements. [Microsoft's NRBF guidance](https://learn.microsoft.com/en-us/dotnet/standard/serialization/binaryformatter-migration-guide/read-nrbf-payloads) distinguishes decoding records from constructing application instances; this is not a ready-made PrePoMax reader/writer. Acceptance: import into candidate native runtime, preserve topology/equations/history/results, export a file opened correctly in the same-baseline Windows reference. Reading only a flattened new format fails the requirement. A converter may aid fixture capture but is not final native file compatibility. No implementation is authorized yet.

## Smallest meaningful VTK proof of concept

Separate research executable; no production changes or frontend commitment. Compare one feasible open-source binding route with supported ActiViz only if licensing permits evaluation. Start on this Mac ARM64, then Windows x64/Linux x64/macOS x64 before choosing a production host.

Use a fixture with two distinguishable parts, triangular/quadrilateral faces, at least one second-order cell, explicit FEM node/element/face IDs and nodal scalar values. Preserve mapping through a deformed result view. Embed in a resizable GUI candidate with a real native render surface and event loop.

Acceptance checklist:

1. Orbit/pan/zoom, resize, hide/show/dispose/recreate and Retina/DPI scaling work; repeated lifetime cycles release resources.
2. Click a face, edge and node and return exact domain IDs, not just a local VTK cell index. Test occlusion, deformed coordinates and modifier keys.
3. Rectangle selection returns expected IDs and highlights the same entities. Verify camera/viewport transformations and tolerance behavior at 1x/2x scale.
4. Scalar contour + legend, clipping/section and camera reset remain coherent; picks on clipped/deformed actors resolve consistently.
5. Capture screenshot and export machine-readable pick/camera/scene results. Run synthetic automation picks and actual pointer interaction on render thread.
6. Repeat at least 100 host recreation cycles and 1,000 deterministic picks with no stale mapping, native exception or unbounded memory trend; record hardware/backend and timings against a declared fixture budget.

A static triangle or screenshot is insufficient. On Mac record native ARM64 dylibs, actual render window/backend, OpenGL/Cocoa limits and separate Metal/WebGPU capability. On Linux test X11 first, then explicitly report Wayland/XWayland support instead of assuming it. VTK pipeline/backend parity and embedding/input parity are separate tests.

## Process/solver acceptance contract

Use resolved executable paths and argument arrays, separate stdout/stderr drains, per-run cwd/env and unique job directories. Preserve configurable user solver arguments and existing default job basename convention. Completion records exit code, application status, errors, warnings, produced files and detected solver version/hash. Exit 0 does not guarantee valid results; parsed diagnostics and expected outputs matter. Partial FRD/DAT can coexist with failed/cancelled status and must not be labeled success.

Cancel/timeout must stop descendants, finish output draining, avoid orphan workers and distinguish cancellation from timeout/error. Test before/during/after launch and shutdown. Preserve multiple increments/runs and OMP_NUM_THREADS; parallel reproducibility testing uses a pinned single-thread reference first. File extension checks must permit native executables without `.exe` on Unix; batch-shell execution is an explicit adapter behavior.

## Exit gates and non-goals

Go/no-go review after core/file compatibility and interactive VTK gates, plus source recovery for native dependencies. A platform may report an unavailable experimental tool capability during development, but public parity release requires all required capabilities or an explicitly approved documented limitation. No algorithm rewrite, automatic dependency upgrade, new file format default, renderer replacement, GUI selection or native binary substitution is part of Phase 0.
