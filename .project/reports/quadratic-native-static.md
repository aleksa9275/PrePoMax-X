# Native C3D10 calculations and desktop integration

Tasks 0087/0088 implement native **C3D10 linear-static calculation**, including
curved CAD meshes, original configuration, solver execution and ten-node FRD
results. They supersede tasks 0084–0086's blanket quadratic solver refusal.
[Verification receipt](quadratic-native-static-verification.json).

The maintainer's requirement is **IDENTICAL PrePoMax 3.0.0 functionality, every
mesh type and calculation, except unavailable solvers** (D060). Static-solid and
preview boundaries describe intermediate implementation, never a smaller final
product. [Required breadth](../PARITY.md) explicitly retains all other element,
mesher, analysis, material/load, model/results and persistence workflows.

## Calculation boundary

`StaticAnalysisDeckWriter` admits C3D10 alongside C3D4/C3D8 and retains original
CalElement ordering and keyword writers. Positive corner orientation is checked
with the original linear tetrahedron helper; the failing quadratic PrePoMax
measurement/integration path is never used to authorize a solver job.
`AnalysisFiles.Build` delegates admission to that writer instead of imposing an
unrelated measurement call. Original CalculiX 2.22 `e_c3d.f` calls `shape10tet`
and rejects nonpositive integration-point Jacobians itself. These solver sources
and original PrePoMax quadrature are unchanged. The original FRD reader already
constructs `ParabolicTetraElement`; its portable result boundary now retains it.

The curved fixture exposed **B005**: G17 lossless exchange coordinates can exceed
CalculiX's numeric-field width. Solver node blocks now use the shared **original
CalNode E8 formatter**, as original PrePoMax and the checked CAD PMX path do.
Standalone mesh export remains G17 and retains exact node/connectivity readback.
The failed deck/exit 201 and correction are retained. Every affected PMX deck
consumer must be rebuilt; a stale cached C3D8 validator initially caused a hash
comparison failure, and rebuilding it restores the strict comparison.

The original affine integral still fails at **26.794910717854155 versus 28**;
the original quadratic-pyramid classifier also remains false. The measurement
command still refuses quadratic tetrahedra. Neither original failure is hidden,
fixed by a tolerance change, or evidence that CalculiX C3D10 is unavailable.
General curved-element quality certification remains open; solver integration-
point checks are not a global positive-Jacobian proof.

## Actual numerical evidence

Native Mac and Linux ARM64 each pass **12 calculation checks**:

- A force-driven unit tetrahedron has ten original nodes, one C3D10 element and
  four free axial unknowns. Consistent nodal forces on its sloping quadratic face
  give the analytical affine displacement and unit axial stress. The real DAT
  request also exercises the history-required output contract.
- The curved L-bracket has **2,548 nodes, 1,154 C3D10 elements, 694 free interior
  nodes (2,082 unknown DOFs)** and 33 curved-edge incidences. Manufactured affine
  boundary displacements leave the interior to the native solver. Original FRD
  IDs/connectivity and all ten nodes per cell survive.
- A deliberately moved midside node leaves positive corner orientation but
  inverts a curved element. Native CalculiX refuses it with a nonpositive-Jacobian
  diagnostic and failed job; it never becomes a completed result.

The new curved fixture's fixed bounds account for original E8 input formatting,
CalculiX extrapolation and stored FRD precision: 2e-7 axial displacement, 2e-8
lateral displacement, 1e-4 stress and 1e-4 force resultant in mm/N/MPa. Observed
Mac maxima are 1.3e-7 / 1.41954e-8 / 6.1e-5 / 7.09478e-5 respectively. The unit
force fixture uses tighter bounds recorded in the receipt. No existing test's
expectation/tolerance or numerical implementation was changed.

The **same solver decks** also run through the fingerprint-checked original
Windows CalculiX 2.22 executable and five runtime DLLs in the existing isolated
CrossOver bottle. IDs/connectivity/coordinates match exactly. The largest curved
field differences from native Mac are displacement ~2e-16, stress ~4.96701e-9,
strain ~6.41238e-12 and force ~1e-11. The inverted fixture fails there too, exit
201. This is Windows binary reference execution through CrossOver, not native
Windows acceptance, original GUI/PMX readback or exact field equality.

## Desktop and regression evidence

The real CAD order dialog offers **Quadratic C3D10** and enables Configure/Run.
The model tree displays materials, sections, supports and loads for quadratic
meshes. Native quadratic mesh receipts and frozen jobs record order 2 and static
analysis eligibility. Midside regions and mesh-only export/reopen are preserved.
The probe rejects an invalid material through the original C# validator before
accepting the real definition and running the native solver. It then checks
quadratic VTK cells/contours, CAD/results switching, immutable job hashes and
reopened INP calculation controls.

Source Mac and Linux ARM64 each pass **37 desktop workflow checks** and **52
unit tests**. Native Linux also passes 11 CAD mesh/topology/frozen-input checks,
the 91-check edited-six-body linear workflow and CAD/C3D8 PMX regressions **28/17**.
Mac ownership/build guards pass **12/9**. Current Mac analysis/results checks
pass, including 73 static checks and all 78 result checks. All four current Mac engineering suites pass. The copied app passes **37 checks
in each viewport mode**, 12 numerical checks, the 91-check linear workflow and
**28/17** CAD/C3D8 PMX regressions. Both result screenshots show quadratic
contours; all 2,422 copied payload hashes, 2,276 symlink targets and the ad-hoc
signature verify.
The first sandboxed Mac offscreen test could not create OpenGL and exited 139;
the actual native graphics run passes all 52 tests. Both diagnostics remain.

Mac/Linux native curved meshes still differ in coordinates/connectivity; exact
native mesh/deck/field parity is open. Do not compare positional field arrays
from different meshes. Neither the analytical tests nor the original-Windows
comparison closes full formulation/analysis, general PMX or release acceptance.

## Publication and current candidate

Implementation **6609d7d458ccd37511163dc401cdcb6bf83708b0** is pushed and
remote-verified on `origin/research/native-feasibility`. The package identifies
that exact source, with no changed code and an empty source patch; its dirty flag
comes from four pre-existing Finder files. Commit/push both skip CI; zero hosted
jobs were requested. Closing documentation is published normally on the same
branch.

Current candidate: `/tmp/prepomaxx-task0088-delivery/PrePoMax-X Preview.app`.
Sibling `Native CAD Preview.command` enables
`/tmp/prepomaxx-task0063-recipe/runtime`. The task 0086 launcher forwards to it.
Evidence is `/tmp/prepomaxx-task0088-evidence` and numerical/original-Windows
reference evidence is `/tmp/prepomaxx-task0087-evidence`. Source/package/log and
manifest records are `/tmp/prepomaxx-task0088-package`; generated package payloads
are disposable after the verified copy. The superseded task 0086 app is removed;
all project/geometry/mesh/PMX inputs, frozen jobs, reference results, screenshots,
source/manifest/log evidence, installed app/state and shared caches remain.
Actual cleanup bytes and post-cleanup hash checks are in the receipt.

D058 prohibits hosted CI and D059 keeps Linux x64 pending for Windows/Podman.
Native Windows/net48, all remaining required functionality, D057 full original
PMX interoperability, installers/Homebrew, clean-system/signing/notarization and
release acceptance remain open. No final functionality requirement is waived.
