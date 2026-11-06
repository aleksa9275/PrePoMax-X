# Quadratic CAD mesh preview and mesh-only export

Historical tasks 0084–0086 report. Tasks 0087/0088 supersede the blanket solver
refusal below with [native quadratic calculations](quadratic-native-static.md).
The original PrePoMax measurement gate and both original failures remain.

Tasks 0084–0086 add native **C3D10 quadratic tetrahedron meshing, preview, CAD
regions and mesh-only INP export**. Quadratic numerical measurement and analysis
remain blocked. [Verification receipt](quadratic-cad-preview-verification.json).

## What is supported

**Mesh CAD…** defaults to Linear C3D4 and offers **Quadratic C3D10 — preview/export
only**. The new profile uses the original MeshingParameters writer with original
Netgen/OCCT second-order generation, retaining ten-node tetrahedra and six-node
CAD surface triangles. Original node, element, domain, face and edge identities
are carried into part-scoped mesh data. Surface and edge node sets include
midsides. The same VTK grid receives cell type 24 and all ten points; the preview
does not flatten those cells into four-node tetrahedra.

A separate `ReadQuadraticPreviewData` path reuses the unchanged original VOL
permutations. It checks finite/used nodes, distinct ten-node connectivity,
positive corner orientation, one consistent midside node per shared edge,
triangle-to-tetrahedron midside correspondence and complete six-node boundary
incidence. Existing size/part/count limits remain. It does not call quadratic
GetCG/GetVolume/Integrate to authorize numerical use. Positive corner orientation
is not curved Jacobian/quality acceptance. The linear reader's admission rules
remain separate and still reject quadratic VOL input.

**Export mesh…** publishes a new mesh-only `.inp` after the original reader
confirms exact node/element identities and connectivity. Validated bytes, authored
sets and all ten nodes are preserved; existing destinations, changed bytes and
changed readback are refused. Publication stages on the destination filesystem
and links atomically. Analysis, geometry settings and project state are omitted;
this does not create a native-session PMX format or save a full project.

The quadratic preview supports CAD/mesh switching, region authoring, rendering
and fresh INP reopen. Configure/Run controls are disabled, direct desktop job
calls refuse it, and the original static-deck validator independently refuses
C3D10. Frozen preview receipts record `elementOrder: 2` and
`analysisEligible: false`. Cancellation, failed/late-cancelled mesh publication
and deferred close preserve the previous document for either mesh order.

## Why numerical acceptance stays blocked

The current original-source quadratic tetrahedron test still returns
**26.794910717854155** for an affine-field integral with exact answer **28**.
The original table's first moments are incorrect; retained independent evidence
is in [the element-kernel report](shared-element-kernel.md). The measurement host
continues to refuse quadratic tetrahedra, and `elementTests.fullyAccepted` remains
false. The separate quadratic-pyramid classification failure also remains false.
No original quadrature table, algorithm, analytical expectation, tolerance or
coordinate precision was changed. This gate concerns the shared PrePoMax element
kernel; native CalculiX C3D10 workflow acceptance has not been established here.
No quadratic solver job was executed by these preview checks.

## Actual checks

- Mac ARM64 and native Linux ARM64 each pass **11 native checks per fixture** for
  the two-body BREP and curved L-bracket STEP. Two bodies retain 130 tetrahedra:
  70 linear nodes become 330 quadratic nodes. The curved fixture has **2,548 nodes /
  1,154 C3D10 elements** on each host. Original INP readback retains exact local
  connectivity, source bytes remain unchanged, midside CAD sets and every frozen
  file hash verify.
- Source Mac/Linux desktops and both final copied Mac viewports each pass **27
  quadratic workflow checks**: real order dialog/default, background meshing,
  true ten-point VTK cells, UI/direct/backend analysis refusal, regions/midsides,
  CAD/mesh switching, frozen profile, new-file export, readback and gated reopen.
  Final screenshots show the curved mesh, enabled export and disabled analysis.
- **52 desktop tests** pass on each native host. New checks cover control/direct
  job admission, return to the supported linear workflow, changed mesh bytes,
  changed readback and existing-file preservation. Mesher cancellation/failure/
  late cancellation runs at both orders. **12 ownership guards and nine build
  guards** pass on Mac.
- All **four current Mac engineering suites** pass; the affected current analysis
  suite also passes on native Linux ARM64. Its exact-count contract includes 58
  analysis tests, including four new quadratic topology/refusal checks. Both
  original correctness failures remain explicitly failed in those reports.
- Both final copied viewports and Linux pass the **91-check linear edited-six-body
  analytical workflow**. CAD PMX/C3D8 PMX regressions pass **28 / 17** respectively
  in the final copied app and on Linux. Linear analysis remains operational.

Strict Mac/Linux quadratic coordinates, connectivity and mesh bytes differ even
though the curved fixture's node/element counts and reported set names/counts
match. The complete comparison is retained; exact native parity stays open.
No field comparison or curved-quality pass is inferred. Previous native CAD and
linear edited-mesh parity differences remain open as well. New original Windows
quadratic interoperability/execution was not performed.

## Publication, candidate and retention

Normal research checkpoints are pushed and remote-verified:

- 0084 transport: `0e28e432f26824eac80978d633aabbdca69ffe9e`
- 0085 native profile: `d365fbbada2a96bdddc5430ce5600d50d9b35593`
- 0086 desktop: `76fbb7d7790fb71a99347f8445d6a0dc343cfca9`
- Visual QA label correction: `d4e98084` (full identity in the receipt).
- Final packaged source: `ec57aa53a3cca4354885b21da14d2c55883b0bd5`.

All commits contain `[skip ci]`; pushes use `-o ci.skip`; no hosted jobs were
requested. D058's hold and D059's Windows/Podman Linux x64 deferral remain.

Current candidate: `/tmp/prepomaxx-task0086-delivery/PrePoMax-X Preview.app`.
Sibling `/tmp/prepomaxx-task0086-delivery/Native CAD Preview.command` enables
`/tmp/prepomaxx-task0063-recipe/runtime`; older native CAD launchers forward to it.
The final package has no changed code and an empty source patch; four pre-existing
Finder files set the dirty flag. All **2,422 copied file hashes**, symlink targets
and the ad-hoc signature verify after cleanup. Visual QA corrected the preview's
inactive unit-configuration prompt to show model units. This remains an internal,
unnotarized preview, not full quadratic or release acceptance.

Evidence is `/tmp/prepomaxx-task0086-evidence`; final manifest/source/build logs
are `/tmp/prepomaxx-task0086-verified`. Preliminary manifests/diagnostics remain
under `/tmp/prepomaxx-task0086-final`. Fourteen duplicate payload/cache/app
directories, including the superseded task 0083 app, were pruned:
10,070,670,743 logical bytes, with 8,876,314,624 bytes (~8.27 GiB) measured free-space
gain. All CAD/STEP/INP/PMX/mesh projects, frozen previews/jobs, screenshots,
diagnostics, source snapshots and shared native/Python/.NET/package/Podman/source
caches remain. Installed user app/state was untouched; earlier app paths are
historical after replacement.

Initial missing build assets, the test-count guard, a stopped shared-build-server
stall, an action-initialization error and the GUI image's missing Git diagnostic
are retained. Corrected builds, tests and fresh cached-research-image analysis
checks pass. No missing check was represented as passed.

Next acceptance boundaries include separately reviewed quadratic kernel/solver
correctness, curved Jacobians/quality, broader quadratic formulations, exact native
parity, original-compatible new native-session PMX and general project graphs,
Windows/net48/four-target coverage and all installers/Homebrew/signing/notarization/
release requirements. Preserve D029/D057/D058/D059 and both original failures.
