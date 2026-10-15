# Native CAD/mesher feasibility investigation

Task 0004, 2026-10-14 (Europe/Belgrade). Source baseline:
`de8f73032a72746e3d6d9afd53d9fbd289eb310a`; research starts from c11a73d9 on
`research/native-feasibility`. Original application/native files remain unchanged.

## Outcome and measured evidence

**Verified observation:** the vendored Gmsh 4.13 C API and the plain C++
Gmsh/Q-Morph declarations compile under Apple Clang 21 on native ARM64. The
unchanged GmshCommon wrapper fails at `msclr\marshal_cppstd.h`. Its vcxproj also
declares net48/CLRSupport and Windows toolchains. This isolates a managed interop
boundary; it is not evidence that the native algorithms themselves need rewriting.

Run the offline investigation:

```sh
python3 .project/scripts/native-feasibility.py --output .project/reports/native-feasibility/macos-arm64.json
```

[Measured JSON](native-feasibility/macos-arm64.json) retains actual compiler
commands, probe sources, diagnostics, SHA-256 identities and baseline matches
for 17 source/header/notice/gateway files. All three compiler outcomes match
expectations, including the specific missing-msclr diagnostic. No linking or
native mesher execution is claimed. CMake/Ninja are absent from the current PATH;
Python's current environment has no vtk, gmsh, PySide6 or PyQt6 modules.

Forty binaries/archives were hashed and identified: primary Gmsh, NetGenMesher,
nglib and both QuadWild executables are Windows x64 PE/COFF; 29 OCCT DLLs are
also PE/COFF x64. Mmg3d is x64 but mmgs is **x86**. The four QuadMesher libraries
are ar archives; this probe does not infer the architecture of their members.
None was executed or substituted with a stock binary.

**Verified provenance discrepancy:** actual `quad_from_patches.exe` SHA-256 is
`98e0217d92e1539d9db8dffbf2f88a93a93b69e408cae128816935dfdc0c8dfe`.
It matches `Licenses/quadwild/NOTICE.md`, but not the
`445195a01b34873a111b96752c605409b187506de9c71c1ebe90ffc0b2337021`
claim in `ThirdParty/quadwild-bimdf/README.md`. Both notices agree with the
actual quadwild.exe hash. Preserve upstream notices; resolve the discrepancy
with matching source/build evidence rather than editing them to hide it.

## Matching-source and build matrix

| Component | Source evidence / access | Feasibility conclusion and next input |
|---|---|---|
| Patched Gmsh 4.13 | `Licenses/README.md` names `https://gitlab.com/MatejB/gmsh`, branch `prepomax-quadqs-transfinite`. Default shell lookup first failed sandbox DNS; an approved external `git ls-remote` reached GitLab but requested a username. The signed-in GitLab browser opened the exact branch URL and showed **404 Page not found**, with a sign-out link. Web retrieval also failed. No branch SHA obtained | Source is unavailable through this account/route; 404 does not prove whether it is private, moved or unpublished. Need accessible corresponding commit and patch/build configuration, including static OCCT 7.7.0, disabled GUI/OCAF and threading choices |
| NetGenMesher + modified Netgen 5.3.1 | `ThirdParty/netgen/README.md` names an external `C:\Pc\Programiranje\NetgenMesher` tree and describes custom CAD command protocols and pyramid/optimization patches in nglib; checkout carries runtime binaries | Need entire wrapper source, modified nglib source/base revision, exact OCCT 8.0.1 build and matched binary pair. Stock Netgen is not a protocol/behavior replacement |
| Modified QuadWild-BiMDF 0.0.2 | Local fork and `prescribed_nodes.patch` are described in `Licenses/quadwild/NOTICE.md`; neither corresponding fork nor patch is supplied here | Public upstream is accessible and offers a plausible cross-platform build route, but it cannot reproduce the prescribed-node/transfinite/quality behavior without the fork and patches |
| QuadMesher/Q-Morph | `ThirdParty/QuadMesher` supplies two headers and Debug/Release static libraries, not implementation sources. `THIRD_PARTY_NOTICES.md` describes comparison-only TQMesh/Java qmorph projects; the header describes a separate C++ port | Header declarations compile, but implementation/build/source/license identity remains unestablished. Comparison-only notices do not establish ownership of the linked implementation |

Public reference retrieval (not matching modified-source recovery):

```sh
git ls-remote https://github.com/cgg-bern/quadwild-bimdf.git HEAD refs/tags/v0.0.2
git ls-remote https://github.com/cgg-bern/quadwild-bimdf.git 'refs/tags/v0.0.2*'
```

Observed upstream HEAD: `e722c7e961982cf61db7c10812329dd0fc7d60df`.
Annotated v0.0.2 tag: `1a24854abf7b17e5c9c0fba0f3c8c1930fd43957`;
peeled source commit: `eef4fc390f071c4194196b0bea3b6fc243893adf`.
An approved curl download retrieved its [unaltered CMakeLists](native-feasibility/quadwild-v0.0.2-CMakeLists.txt)
from the [immutable public source](https://github.com/cgg-bern/quadwild-bimdf/blob/eef4fc390f071c4194196b0bea3b6fc243893adf/CMakeLists.txt).
It requests C++20, uses subprojects and GMM FetchContent, and makes Blossom5
optional/off. A future reproducible build must pin recursive submodules,
downloads and toolchain too. No upstream QuadWild build was attempted as a
substitute for the missing modified fork. The [upstream build documentation](https://github.com/cgg-bern/quadwild-bimdf)
describes Mac/Linux support; that is a source statement, not our own build pass.

## Existing boundaries to preserve

**Verified source observations:**

- `PrePoMax/Meshing/Base/IMesherRunner.cs` already owns capability, creation and
  preview methods. Concrete runners use Controller, settings and UI reporting;
  Netgen also resolves paths through WinForms Application.StartupPath. Use this
  existing boundary when later isolating platform services.
- `PrePoMax/Common/ExecutableJobRunner.cs` provides the existing process route.
  Do not invent a second process gateway for the production meshers.
- `GmshCaller/Program.cs` loads GmshData via Tools.LoadDumpFromFile and invokes
  GmshAPI Mesh/Defeature. A separate executable is not currently a portable
  boundary: dump serialization and the managed/native closure still apply.
- `CaeMesh/Meshing/QuadWild/QuadWildRuntime.cs` builds Windows extended-length
  paths, names .exe tools and adds processes to ChildProcessJob. A source rebuild
  alone does not resolve path/process-lifetime behavior on other platforms.
- The comment-stripped GmshCommon wrapper contains 118 distinct gmsh calls.
  The JSON lists them; this is a textual wrapper inventory, not live coverage.
  Gmsh's existing C header documents gmshMalloc/gmshFree ownership, size_t tags,
  callback userdata and explicit error outputs. A future portable boundary must
  preserve those contracts and serialize access to the global model/session.

**Architectural inference:** retain the existing C# meshing algorithms and runner
semantics, and investigate a narrow native boundary around available matching
libraries. C ABI interop and process isolation remain candidates; no production
choice is made here. Q-Morph currently exposes C++ containers/virtual interfaces,
so it cannot be treated as the existing Gmsh C ABI without a separate reviewed
adapter. Independent OCCT versions must remain pinned rather than silently unified.

## Source recovery packet (prepared, not sent)

For each custom tool, obtain: accessible repository/archive and immutable base
and patched commits; complete patch history; recursive submodule identities;
build scripts/options/toolchain; dependency hashes/versions; attribution/notices;
reference binary hashes and small command fixtures/expected outputs.

Specific asks: restore access/location for patched Gmsh; supply NetGenMesher and
modified nglib as a matched pair; provide the actual QuadWild fork and
prescribed_nodes.patch/investigation notes; provide QuadMesher implementation,
prototype/algorithm notes and library provenance. No maintainer was contacted.
These inputs can be obtained independently of the Windows machine, although
that machine is useful for reference execution and binary comparison.

## Completion boundary

Task 0004's source/access/build-boundary audit is complete. **Matching native
source recovery, full native CAD/mesher builds and FEM equivalence remain open.**
Windows PMX/history compatibility remains a separate gate. F001 automatic shell
connectivity is still a proposal: current compound/imprinting support needs live
fixtures before any behavior changes.

Next bounded experiment: source-link the existing ThreeBlockMapping/Grid/count
kernel, run its existing C++ check against the 13 upstream vectors, compare C#
execution and add independently specified geometric/topological checks. This
uses existing algorithms and reference machinery, needs no third-party package,
and can finish without a native CAD engine or Windows host.
