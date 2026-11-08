# Phase A — whole domain libraries for .NET 10

Date: 8 November 2026. Strategy: D062. Branch: `research/native-feasibility`.

## Result

The whole original assemblies now build for .NET 10 from the original source
files, with the original assembly, namespace and type names:

| Assembly | Source list | Deviations |
|---|---|---|
| CaeGlobals | original csproj | 10 WinForms/Win32 UI files excluded, 3 portable counterparts added |
| CaeMesh | original csproj | none |
| CaeModel | original csproj | 2 existing PrePoMax-X files in original folders added |
| CaeResults | original csproj | 3 PrePoMax-X files added (bounded FRD/DAT transports, test visibility) |
| CaeJob | original csproj | Windows process/WMI partials excluded, 3 portable counterparts added |
| STL, ThreeMF | original csproj | none |
| vtkControl | 4-file data subset | only data types used by CaeModel (`vtkMaxActorData`, `vtkMaxLookupTable`, `vtkRendererLayer`); rendering stays for Phase C |
| GmshCommon | C# P/Invoke port | original is C++/CLI; now calls the Gmsh 4.13 C API (`gmshc`) |
| PrePoMaxX.WinFormsCompat | new | non-visual WinForms/System.Drawing.Design API stand-ins only (enums, `UITypeEditor`, `IWin32Window`, …) |

Projects live in `X/Domain/`. `domain_sources.py` generates each
`Sources.g.props` from the original csproj Compile items plus the reviewed
deviations in `domain-sources.json` (each with a reason); `--check` fails if
they are stale. Upstream file additions therefore flow in automatically.

The previous partial slice projects (`X/Core|Analysis|Results/Cae*`,
`X/Execution/CaeJob`, `X/Feasibility/Cad/Cae*`), their hash/extraction layout
guards and the upstream-replay snapshots are deleted. All existing test hosts,
CLIs and the desktop hosts now reference `X/Domain`.

Parity inventory: 126 of 127 model/mesh features are **A**. The remaining
`WireElement.cs` is not in the original `CaeMesh.csproj` (unused upstream file).
Commands and forms belong to Phase B/C.

## Edits to original files

All edits are minimal and keep the original net48 projects compiling (C# 7.3).
`X/Domain/net48_check.py` compiles the original CaeGlobals and CaeJob csproj
lists against .NET Framework 4.8 reference assemblies on macOS: both pass.
CaeMesh/CaeModel/CaeResults need the C++/CLI GmshCommon and ActiViz, so their
net48 build is verified on Windows (pending).

- **Partial splits** (Windows/UI code moved verbatim into files listed only in
  the original csproj): `CaeGlobals` MessageBoxes/Extensions/
  DynamicTypeDescriptor/Tools → `*.WinForms.cs`; `CaeJob/AnalysisJob` →
  `AnalysisJob.Windows.cs` (WMI); `vtkControl` `vtkMaxActorData`/
  `vtkMaxLookupTable` → `*.Vtk.cs` (Kitware constructors/conversions).
- **`OrderedDictionary` qualification** in CaeMesh/CaeModel/CaeResults files:
  .NET 9+ adds `System.Collections.Generic.OrderedDictionary`, so the original
  `CaeGlobals.OrderedDictionary` is written fully qualified.
- Small using/API adjustments (`Selection.Legacy.cs`,
  `EquationLengthDefaultConverter.cs`, `CaeJob/AnalysisJob.cs`).

## Port repairs (original behaviour reproduced on Unix)

- Solver kill used WMI to find the process tree; on Unix it would never kill
  the solver. Portable implementation kills the tree via .NET.
- `Tools.GetShortPathName` called kernel32; portable version returns the path.

## Checks

`python3 X/Checks/check.py` (new `domain` area plus all suites), macOS ARM64,
59 s, all passed:

- domain: source lists current, Domain build 0 errors, net48 CaeGlobals/CaeJob
  ok. 83 distinct warnings, recorded by code in the domain report: CS0168 24,
  CA1416 17, CA2022 9, CS0219 7, NU1701 6, CS0108 5, CA2200 4, others ≤2.
  (The first run counted only 16: a parsing bug in `verify-domain.py` collapsed
  compiler warnings; fixed.)
- core: 25 mapping, 30 data (identical to the Windows reference), 95 element
  (2 known open findings, D029), 69 mesh, 9 CLI
- analysis: 58 tests + 74 static checks; execution: 49; results: 90

Four assertions encoded slice-only behaviour and were changed to the original
behaviour (see findings 1–2 and the Results FeResults/HistoryResults presence
checks). No failed check was turned into a pass.

The desktop's .NET hosts (Solve, MeshScene, InspectVis, InspectResults) build
against `X/Domain` with 0 errors. Not run in this phase: Linux ARM64 Podman,
Windows net48 full build, desktop package/DMG regeneration (next milestone).

## Findings (recorded, fix after parity — D061)

1. Original `CalCLoad` with a local coordinate system writes **global**
   directions when the CS cannot be resolved (no mesh). The slice had asserted
   a stricter behaviour; the check now asserts the original.
2. `BinaryFormatter` is disabled on .NET 10. Original `DeepClone` and the
   `Selection` copy constructor throw `NotSupportedException` until Phase B
   provides allowlisted serialization (never unrestricted).
3. `System.Drawing.Common` `Image`/`Bitmap` work only on Windows at runtime;
   reached only from UI/icon code so far.
4. Windows-only APIs reachable on every platform (CA1416/SYSLIB, will throw
   on macOS/Linux when called): `Tools.cs` registry and WMI queries,
   `AnalysisJob.IsAdministrator` (WindowsIdentity), `vtkMaxLookupTable` bitmap
   export, `DynamicTypeDescriptor` image drawing and `ReflectionOnlyLoad`, and
   **`GmshAPI` `Thread.Abort()`** in the Gmsh error path (throws
   `PlatformNotSupportedException` instead of aborting the worker). These are
   port repairs to make when Phase B exercises those paths.
5. Q-Morph quad mesher: the `QuadMesher` source is not in the repository
   (Windows `.lib` only). The port throws a clear "not available on this
   platform yet" error; a C shim (`pmx_qmorph`) is ready for when the source is
   recovered. Blocks parity for that mesher.
6. A native Gmsh 4.13 shared library is required on macOS/Linux
   (`PREPOMAXX_GMSH_LIBRARY` overrides the lookup).
7. Original GmshCommon quirks preserved: `OCC.Remove` passes `(0,0)` dim-tag
   pairs; `GetMaxNodeTag` truncates to `int`.
8. The 83 compiler/analyzer warnings (including `CS1717` self-assignment in
   `Tools.cs:293`) are reviewed with the post-parity fixes.
