# Dependency inventory and reproducibility

The [matrix](reports/dependency-matrix.md) is the platform/integration inventory. Versions below come from project files and vendored notices, unless explicitly described as unverified. External pages were consulted on 2026-10-13; do not upgrade dependencies merely because newer releases exist.

## Managed dependencies

Packages are restored using `packages.config` with relative `../packages` HintPaths; there is no SDK-style package graph or lock file. References may use a different assembly version from the NuGet version.

| Owner | Package versions in manifests |
|---|---|
| CaeGlobals | ExtendedNumerics.BigDecimal 2025.1001.2.129, ncalc 1.3.8, Parlot 0.0.28, UnitsNet 4.89.1; Microsoft.Bcl.AsyncInterfaces 8.0.0, Microsoft.CSharp 4.7.0, NETStandard.Library 2.0.3, Microsoft.NETCore.Platforms 1.1.0; System.Buffers 4.5.1, Collections.Immutable 8.0.0, Memory 4.5.5, Numerics.Vectors 4.5.0, Runtime.CompilerServices.Unsafe 6.0.0, Threading.Tasks.Extensions 4.5.4, ValueTuple 4.5.0 |
| CaeResults | OptimizedPriorityQueue 5.1.0 (assembly PriorityQueue 5.0.0.0); Buffers 4.5.1, Memory 4.5.4, Numerics.Vectors 4.5.0, Unsafe 5.0.0 |
| CaeModel | ValueTuple 4.5.0 |
| APIs | pythonnet 3.1.0 |
| PrePoMax | CommandLineParser 2.9.1, FCTB 2.16.24, pythonnet 3.1.0, Markdig 1.3.2 (development dependency), Microsoft.CSharp 4.7.0, PrettyBin 1.1.0, Reflection.Emit 4.7.0 |
| UserControls | FCTB 2.16.24, ZedGraph 5.2.1 |
| vtkControl, non-NuGet | Kitware.VTK 5.8.0.607, Kitware.mummy.Runtime 1.0.2.599; absolute Windows install HintPaths |

WinForms/WPF/WindowsBase/System.Management, drawing and designer assemblies are framework references. Mathematical packages are candidates for reuse; package availability on modern .NET, license text, transitive graph and precise runtime behavior remain to be validated with a real restore/build in Phase 1. WinForms FCTB and ZedGraph controls cannot supply a native cross-platform GUI.

## Native source gaps

2026-10-14 follow-up: [task 0004 investigation](reports/native-feasibility.md)
retains measured headers/interop boundaries, shipped binary hashes and source
access results. Patched Gmsh's published branch returns 404 in the authenticated
browser; no corresponding SHA could be obtained. Public QuadWild v0.0.2 is pinned
as an upstream reference, not the modified fork. A QuadWild README checksum
disagrees with the actual patch executable and its license notice. Matching
custom sources/full native builds remain open; no stock tools were substituted.

`ThirdParty/netgen/README.md` says NetGenMesher is built from the author's local `C:\Pc\Programiranje\NetgenMesher`, outside this repository. It implements extensive CAD commands and modified Netgen pyramid/optimization behavior. Public Netgen supports other platforms, but does not replace this integration.

`Licenses/quadwild/NOTICE.md` describes many modifications and a `prescribed_nodes.patch` in an external local fork. Matching sources/patches are not in this checkout. Upstream QuadWild binaries are therefore not interchangeable with PrePoMax's binaries.

Patched Gmsh has a published source location: [MatejB/gmsh, prepomax-quadqs-transfinite](https://gitlab.com/MatejB/gmsh/-/tree/prepomax-quadqs-transfinite), according to `Licenses/README.md`. That branch's exact corresponding commit, subdependencies and build recipe were not independently verified; website retrieval failed. Pin and retrieve them before porting. The SDK headers/import library remain upstream while the DLL is patched. Netgen uses OCCT 8.0.1 dynamically; Gmsh uses OCCT 7.7.0 statically. Unifying those kernels is a behavior change, not housekeeping.

`GmshCommon/QMorph.h` wraps `ThirdParty/QuadMesher` headers/static Windows libraries (`qmorph_gmsh.lib`, `qmorph_static.lib`). Their implementation source/version is absent. The notices discuss comparison-only external projects and do not establish provenance for every linked static library. Resolve exact source/license ownership rather than inferring an MIT license from the name Q-Morph.

## License and distribution gate

Preserve root GPL v3 text, copyright headers and upstream links. Existing `Licenses/` notices identify NetGenMesher/QuadWild as GPL-3, Gmsh as GPL-2.0-or-later with exceptions, Netgen/OCCT/lp_solve/pthreads as LGPL variants, Mmg as LGPL-3.0-or-later and zlib under its own terms. Generated Lib3MF bindings have a BSD-2-Clause notice. This inventory is not a new legal conclusion: every exact shipped binary and transitive component needs its matching notices and source/relinking obligations reviewed before release. Modern proprietary ActiViz needs a separate GPL/open-source redistribution review; do not assume its commercial redistribution terms are sufficient.

`Licenses/README.md` says Gmsh is the sole modified binary, while QuadWild's own notice and Netgen's README also describe modifications. Treat this as an inventory inconsistency to resolve before distribution; Phase 0 leaves upstream documentation intact.

Future native manifest: component/version, repository+immutable SHA, patch set, toolchain+flags, ABI, OS/architecture, inputs/outputs, binary SHA-256, dependent libraries, license/notice/source location and capability probe. Package assets separately by RID; `.dll`/`.exe` names and Windows redistributables do not carry to macOS/Linux. macOS requires dylib install-name/rpath closure, executable permissions and eventually signing/notarization; Linux requires an explicit glibc/runtime floor. No packaging implementation was added.
