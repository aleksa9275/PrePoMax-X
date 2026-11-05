# Task 0068 — CAD region selection and analysis assignments

Completed 5 November 2026 under the maintainer's project continuation.
[Report and actual publication](../reports/cad-region-selection.md).
Build on task 0067's retained CAD and original face/domain mesh associations.

- Switch between retained source CAD, generated mesh and loaded results without
  discarding model edits or rerunning import/meshing.
- Pick faces or parts, accumulate/clear a visible selection and select matching
  source entities in the model tree. Highlight selected CAD regions.
- Create named node sets from selected faces/parts and element sets from parts.
  Resolve source sets and union mesh IDs inside the C# host through the original
  INP reader; do not infer geometric membership or parse engineering data in Python.
- Make these sets available in the existing original-validated analysis editor;
  freeze their CAD provenance with submitted jobs. Reject stale/unmapped regions
  and preserve the active model after failed edits.
- Verify actual picking, multi-part isolation, selection unions, editor assignment,
  native solve and frozen inputs on Mac/Linux ARM64. Preserve existing CAD,
  INP, PMX, cancellation and result workflows.

No new project format or general CAD/mesh persistence is selected. Both original
correctness failures, quadratic tetrahedra and full parity/release gates remain.
Use local native checks; no hosted CI under D058. Linux x64 remains deferred to
Podman on Windows near finishing under D059. Publish normal research checkpoints
with CI skipped under D051, preserving one current candidate and useful caches.
