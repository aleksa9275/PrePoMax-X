# Native CAD to first-order static results

Task 0067 completes a bounded desktop path from native STEP/BREP import through
linear tetrahedral meshing, editable static analysis, native CalculiX and original
FRD decoding. It retains the original Netgen VOL parsing/permutations, meshing
parameter writer, engineering objects and CalculiX keyword writers in their
original C# assemblies. Python owns document lifetime, workers and presentation.

Enable the explicit research profile with `--cad-native <native-cad/runtime>`.
Open CAD, choose **Mesh CAD…**, enter the maximum size in model units, then use
**Configure…** and **Run analysis**. Units, material, sections and boundary
conditions require explicit input. This path selects first-order tetrahedra and
one meshing thread; it does not change the original Windows defaults or select
a production mesher/backend. The native tool remains an external verified runtime.

## Ownership and frozen inputs

A successful native import owns staged source CAD, BREP parts and VIS files
until document replacement/close. A separate cancellable worker meshes every
retained part. The GUI publishes the combined mesh only after every part and the
original parser/INP writer checks pass. Failed, cancelled and late-cancelled
replacement preserves the old document. Closing waits for owned process cleanup.

The original VOL parser supplies node ordering, volume domain IDs, surface BC
IDs and edge IDs. Combined IDs use recorded per-part offsets without merging
coincident parts. `PART_n_SOLID_d` element sets and `PART_n_FACE_f`/
`PART_n_EDGE_e` node sets make the source regions available to the analysis
editor. Source VOL hashes, offsets and domain maps remain in `cadMesh`.

The portable transport requires a bounded, conforming first-order tetrahedral
volume with finite coordinates, valid references and positive original signed
volumes. It checks volume/surface incidence and rejects quadratic tetrahedra,
truncation, duplicate sections and unsupported records. The original Windows
`FeMesh` orchestration remains separate. A mechanical guard compares the VOL
helper extraction and Windows selection-copy method to immutable `a293e892`;
only five explicit invariant-culture floating parses differ in the shared VOL
helpers. The original Windows projects include their extracted partials once.
Portable parameter copies explicitly reject unsupported selection graphs.

Static decks and FRD snapshots now admit C3D4 alongside C3D8. Quadratic tetrahedra
remain blocked. Engineering formulas, integration algorithms and numerical
acceptance tolerances are unchanged. Result scenes carry original VTK cell types.

Before a solver starts, its fresh job folder freezes source CAD, BREP/VIS parts,
VOL files, original parameters, base mesh, native tool build receipt, analysis
JSON and submitted INP. Hash verification rejects changed retained files.
The job distinguishes the base native mesh hash from the submitted mesh hash,
which may include user-authored sets. Closing the document removes temporary
inputs and leaves those immutable job copies intact. This is job provenance;
general CAD/mesh project save/reopen remains open.

## Verification on 5 November 2026

The tracked `sweep_two_apart.brep` fixture yields **211 nodes and 563 C3D4**
elements across two independent parts. An explicit analytical fixture prescribes
axial strain 0.001, E=1000 MPa and Poisson ratio zero. Native Mac and Linux ARM64
CalculiX 2.22/SPOOLES solves complete. Original FRD decoding gives S33=1 MPa at
every node and U3=0.001*z, with maximum displacement error about 1e-8 mm at FRD
output precision. Transverse displacements are zero. Raw Mac/Linux mesh hashes
differ because of last-bit coordinate differences; byte identity is not claimed.

- Mac: source GUI and both packaged viewports pass 18 workflow checks each,
  including real invalid/valid editor controls, meshing controls, frozen inputs,
  tamper rejection, cleanup and result display. The Cocoa screen capture was
  visually inspected. The checked PMX edit/save/reopen/native-solve path still
  passes all 17 checks in the packaged app.
- Linux ARM64: offline builds and all 54 analysis/parser tests pass. The CLI
  workflow passes seven checks. The Qt frame bridge under Xvfb/Mesa also passes
  all 18 desktop workflow checks. The SDK/Python and runtime images were combined
  locally without network downloads or rebuilding OCCT. The initial build image
  lacked GUI libraries; the first runtime attempt refused its mismatched external
  BLAS hash before solver execution. The existing verified Linux packager then
  relocated the pinned solver libraries, and the full retry passed. Both failure
  logs remain with the local evidence.
- Mac current source: core checks, 54 analysis plus 70 static-deck checks and
  existing mapping/data/element/mesh regressions, 49 execution checks and 78
  FRD/DAT checks pass. Thirty-three desktop tests, eleven analysis ownership
  guards, nine results guards and nine build guards pass. Earlier new-fixture
  BC-ID and harness-count/closure failures are retained and corrected; no
  engineering tolerance or existing correctness gate was relaxed.

[Machine-readable receipt](native-cad-static-workflow-verification.json).
Local detailed evidence/jobs: `/tmp/prepomaxx-task0067-evidence`.
The current local app and its publication identity are recorded in the receipt.
Only one current generated candidate is retained after verification; reusable
native tools, caches and previous job/evidence folders remain available.

## Publication and remaining work

D051 authorizes normal publication to `origin/research/native-feasibility`.
Push with `-o ci.skip`; D058 continues to block automatic pipelines. No hosted
check or retry is authorized by this task. Exact publication is recorded in the
receipt and handoff after remote verification. D059 defers Linux x64 execution
to Podman on a Windows machine during the finishing phase; it is still pending.

The next bounded increment is geometry-backed mesh region selection and a
reviewed CAD/mesh persistence boundary, building on these retained source IDs.
General CAD editing, broader meshing controls/meshers, general PMX, full analyses,
Windows/net48 execution, stable 3.0.0 source correspondence, both known original
correctness failures, the quadratic-tetrahedron gate and all four-target parity/
installer/signing/notarization/release acceptance remain open. Notify the
maintainer when Developer ID/notarization requires their involvement.
