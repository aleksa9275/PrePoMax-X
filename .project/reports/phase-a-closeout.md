# Phase A verification and native dependency closeout

8 November 2026. D062 whole-code strategy; D057–D061 remain in force.
Base commit: `fdbfa457f4c2e250af621f6bdc811332b82d070e` plus this closeout.
[Compact evidence](phase-a-closeout-verification.json).

## Outcome

The whole original domain build has fresh engineering and desktop regression
evidence on macOS ARM64 and Linux ARM64. This closes the requested verification
gap, not full application/runtime parity. No engineering algorithms, expectations
or tolerances changed. Q-Morph still requires external source recovery for an
included experimental wrapper; it does not prevent Controller/Commands work in Phase B.

The retained preview application is unchanged. No new package/installer or
hosted CI run was produced. Windows/net48 full build, Linux x64 (D059), full
native mesher equivalence and release acceptance remain pending.

## Established checks rerun

| Check | macOS ARM64 | Linux ARM64 |
|---|---|---|
| Whole domain source lists/build | pass, 83 distinct warnings | pass |
| Original net48 CaeGlobals/CaeJob source compile | pass | pass |
| Mapping / Windows-reference data / elements | 25 / 30 / 95 pass | 25 / 30 / 95 pass |
| INP mesh workflows | 69 pass | 69 pass |
| Analysis / static deck / execution / results | 58 / 74 / 49 / 90 pass | 58 / 74 / 49 / 90 pass |
| Qt desktop regressions | 95 pass | 95 pass |
| Structural workflow, ten shell/membrane/beam/truss cases | 164 checks pass | 164 checks pass |
| Pinned Gmsh C# adapter | 18 checks + 7 rejection controls pass | 18 checks + 7 rejection controls pass |

CLI/refusal controls in the established verifiers also pass. The two original
D029 element correctness checks remain **failed** and `fullyAccepted=false`.
B006–B009 and the other retained diagnostics remain open. The original live
application Python/API suite still needs the original Controller/UI host.

Two fresh structural cases (`shell-tension`, `beam-centerline`) were compared
with the pinned original Windows CalculiX 2.22 under CrossOver using identical
frozen decks. Meshes match exactly; fields/histories pass the existing
`1e-6 + 1e-6*max(abs(a),abs(b))` bound. Largest field differences are
`5.735403218e-9` and `4.31681e-11`. This is reference evidence, not native
Windows acceptance or whole-product numerical acceptance.

The domain verifier now uses one MSBuild worker and disables shared compilation,
resolving the parallel-build stall observed during review. Domain lockfiles can
be redirected to the existing `NativePreviewLockRoot`, allowing read-only source
mounts on Linux. The final Mac domain build still reports the original 83 warnings.

Infrastructure failures are retained separately: the first Mac desktop attempt
could not access a display inside the sandbox; the display-enabled run passed.
Podman first failed at its gvproxy socket; a terminal-session start succeeded
without VM reconfiguration. The cached Linux image lacked Git; a separate test
image added Git/build tools. Tests run with networking disabled. The VM is
restored to its initial stopped state after the run.

## Q-Morph: exact implementation missing; original path is dormant

Tracing the introducing commit `3e5e398438904d893087e37b1ab085a6d85d264f`
and the current original sources corrects the earlier assessment:
`GmshAPI.QMorphMesh()` is private, has no callers, and is explicitly marked
"not offered yet". The commit likewise says no recombine option offers it.
Therefore this is an experimental wrapper/source-closure gap; no missing
exposed original meshing option has been established. Do not silently activate
or substitute it, or describe it as a demonstrated user-facing regression.

The supplied [uhweili/Q-Morph](https://github.com/uhweili/Q-Morph/tree/5e113a0e4cd1c7cbdce2d4223258ab85068f3d00)
is a different implementation of the same algorithm. Its OpenMesh/FrontsManager
interface does not implement PrePoMax's `qm::qmorph` or
`qmg::makeFaceNodeCountsEven`, `setBackgroundAlgorithms`, `quadMeshSurfaces`.
The local headers describe a C++ port of separate Python prototypes. A native
link of the prepared C shim fails on precisely the missing three `qmg::` functions.
Windows `.lib` archives do not supply ARM64/macOS/Linux implementations.

Needed from the original QuadMesher project: `cpp/src` (including `qmorph.cpp`
and the Gmsh integration), matching headers/revision, CMake/build configuration,
license/ownership notices, dependencies, and representative fixtures/prototypes.
The static archive records `C:\Pc\Programiranje\QuadMesher\cpp\...` build paths.
The checked-in notices label the other named MIT meshers **comparison only**;
they do not establish the license of these linked libraries. No alternative
algorithm was substituted and no external maintainer was contacted.

At the maintainer's request, public GitHub/GitLab searches covered QuadMesher,
Q-Morph/qmorph, the exact API/header names, the PrePoMax GitHub organization,
and MatejB's public GitLab project list. No matching implementation was found.
The GitHub organization exposes PrePoMax, NetgenMesher, Gmsh and QuadWild;
MatejB's GitLab list exposes PrePoMax, PrePoMax-Models and OptiMax. GitLab's
QuadMesher folder still contains only the known headers/notices/Windows
archives. Other Q-Morph repositories are algorithm references, not recovered
matching sources. The inspected HGL2533/quadMesher archive is a cross-field/libQEx
tool; GuDuJian-J-Zhang/QMorph_2D uses a different QuadMesh API. Neither contains
the required Gmsh integration symbols. Some additional GitHub API tree/search
requests returned HTTP 504; archive inspection provided the source checks above.
Public discovery cannot rule out private/unindexed sources.

## Gmsh: pinned baseline, explicit upgrade candidate

Recovered and hash-pinned [PrePoMax's patched 4.13.0 source](https://github.com/PrePoMax/Gmsh/tree/4156db5d5647087b1575c3f4b8a65a891b81102b)
and OCCT 7.7.0. The [offline native build recipe](../../X/Build/Gmsh/README.md)
builds the original three-patch mesher with static OCCT; Netgen keeps OCCT 8.0.1.
Both libraries are native ARM64; the Mac library links only system C++/OS libraries. Runtime tests
cover prescribed curve counts/16-quad meshing, nested C arrays, physical groups,
Unicode STEP exchange, volume geometry, callback lifetime, quadratic tetrahedra
with positive scaled Jacobians, MSH reopen and native error propagation.
These bounded tests do not verify every original mesher/patch/geometry workflow.

The loader requires an absolute override or app-local library and an adjacent
build profile. It checks version, exact patched source revision, OCCT version
and library SHA-256 before loading, then checks the reported runtime version.
Unversioned system-library fallback is removed. Wrong source/version/kernel,
wrong hash, missing manifest, relative overrides and implicit lookup are refused.

[Gmsh 4.15.2](https://gmsh.info/src/) is pinned as an **unadopted candidate**.
All three PrePoMax patches apply cleanly, and all 118 C functions used by the
adapter retain their declarations (including the deprecated `getType` alias).
The [release history](https://gmsh.info/doc/texinfo/#Version-history) reports
useful fixes/improvements, but this closeout does not demonstrate an improvement
on PrePoMax models or establish unchanged meshing/defaults. Keep 4.13.0 as the
reference and evaluate a patched 4.15.2 build against it before adopting it.
Archive hashes/build inputs and the candidate patch are retained; full source
distribution and Windows/native build equivalence remain open.

## Inventory and next step

The inventory now checks original Compile items, reads declared class names,
excludes abstract bases/enums/the unused WireElement file, and names
`TimeIncrementationStepControlParameter` and `DampingRatioAndRange` correctly.
It has **108 selected source entries at A**, 237 command files and 72 forms at
zero B/C/V. The smaller denominator removes counting artifacts, not functionality.
It explicitly excludes any whole-product completion percentage and identifies
missing coverage of results, utilities, persistence, automation and distribution.

Phase B is next: original Controller/Commands, allowlisted original PMX/clone
serialization, and reached platform API repairs. Keep Q-Morph as an unresolved
experimental native-source dependency. Original numerical bugs and ordinary warning cleanup remain
post-parity work under D061; required port repairs are not deferred as warnings.
