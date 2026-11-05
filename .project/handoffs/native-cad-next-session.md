# Native CAD continuation — 5 November 2026

Task 0068 adds visual CAD face/part regions, original-reader node/element set
unions, highlighting, CAD/mesh/result switching and frozen region provenance.
Read [the region report](../reports/cad-region-selection.md) and its receipt for
actual source/candidate/publication checks. Implementation `d6a52ea3` is remote-
verified with CI skipped. Current app: `/tmp/prepomaxx-task0068-delivery/PrePoMax-X Preview.app`;
its sibling launcher enables native CAD, and the old task 0067 launcher forwards.
Mac copied viewports and Linux ARM64 pass 46 region/assignment/solve checks;
existing PMX and C3D8 paths pass. Task 0067's app is pruned; evidence/jobs remain.
Next is [task 0069](../tasks/0069-cad-mesh-pmx-interoperability.md), the original-PMX-compatible
CAD/mesh persistence boundary under D057. Keep D058/D059 and all correctness,
quadratic-tetrahedron, full-parity and release gates. Earlier app paths below
are historical after task 0068 closeout.


Task 0067 completes the bounded native CAD → first-order C3D4 → static results
workflow, verified through the real desktop on Mac/Linux ARM64. Read
[the new report](../reports/native-cad-static-workflow.md) and its receipt first.
Linux x64 tests are explicitly deferred to Podman on Windows at finishing (D059).
No hosted CI runs/retries without explicit new instruction (D058).
The current candidate and remote publication identity are recorded in the new
receipt. Implementation `817d47fd` is remote-verified; no hosted jobs were run.
Retained Mac candidate: `/tmp/prepomaxx-task0067-delivery/PrePoMax-X Preview.app`.
The sibling `Native CAD Preview.command` enables the retained native runtime.
Its source patch is empty; dirty reflects only Finder files. Both copied-app
viewports pass 18 native workflow checks, and the existing C3D8 path passes ten.
Superseded task 0064/preliminary payloads below are pruned; jobs and evidence stay.
Next: geometry-backed mesh region selection and an explicit reviewed CAD/mesh
persistence boundary. General PMX, broader meshers/analyses, Windows/net48, both
known correctness failures, the quadratic tetrahedron gate and all parity/release
acceptance stay open.


Read current STATUS, D058 and [the native CAD report](../reports/native-cad-meshing.md).
The original custom sources are recovered; earlier "source unlocated" notes are
historical. Original source bytes and separate POSIX patches are under
`ThirdParty/Sources/NetgenMesher/c5ecb0ba`, with pinned OCCT 8.0.1 build tooling
under `X/Build/NativeCad`.

**No hosted CI runs or retries without explicit new maintainer instruction.**
The maintainer reports no CI for 25 days. Root workflow blocks automatic pushes;
all checks remain available to a deliberately requested web pipeline. The first
x64 CAD job timed out during OCCT compilation after 45 minutes; CAD execution
was not reached. Do not call x64 accepted or retry this cold build unchanged.
Research source checks passed; unrelated jobs were cancelled. See the exact
per-job publication receipt. D051 still authorizes normal research-branch
commits/pushes; use local checks and preserve pending platform/release gates.

Mac/Linux ARM64 native CAD import and first-order Netgen meshes pass two-repeat
geometry/quality comparisons. Original Windows L-bracket mesh connectivity is
identical; the strict native visualization replay remains failed for recorded
floating-point and planar-diagonal differences. Separate native criteria retain
exact source nodes, edges and IDs. Valid-box repair, translation, split and STEP
roundtrip pass on both native targets and the Windows reference. Three BREP
operation outputs are byte-identical across all three paths.

Prior task 0064 app (historical path; pruned):
`/tmp/prepomaxx-task0064-current/dist/PrePoMax-X-Viewport.app`.
Explicit native CAD runtime: `/tmp/prepomaxx-task0063-recipe/runtime`.
Run the app executable with `model.step --cad-native <runtime>` for the native
research profile. Both packaged viewports pass. Its CAD source hashes match
published `26189d8f`; Finder metadata alone sets the dirty flag. CAD is read-only;
general PMX, CAD editing/mesh authoring and full parity remain open.

Linux runtime and receipts: `/tmp/prepomaxx-task0063-linux`.
Reusable native Linux OCCT builder image:
`localhost/prepomaxx-native-cad-builder:occt8.0.1-arm64`, ID
`34610ff4c4a9d6a39bcf1c5576dd4cfe86b7a1347c885acd048bb9ab8ed64e25`.
It retains `/native/occt-install` and its source receipt. Run the current build
adapter in a fresh output with `--occt-prefix /native/occt-install` to avoid a
kernel rebuild. The duplicate stopped build container is removed. Mac OCCT
source/build/install caches and original archives remain; prototype packages
and duplicate generated allocations of about 3.38 GiB were pruned under D056.
Evidence/jobs are retained under `/tmp/prepomaxx-task0064-evidence` and tracked
receipts; do not rebuild historical packages merely to restore old paths.

[Task 0067](../tasks/0067-native-cad-static-workflow.md) prepares the next full
bounded native CAD → first-order mesh → static solve/results desktop path.
Retain owned BREP inputs for document lifetime, share the original VOL reader
and engineering permutations, then extend the existing bounded static/results
interfaces for C3D4. Keep original Windows type ownership, both correctness
failures and the quadratic-tetrahedron gate. General repair, full 3.0.0 parity,
all four targets, source/runtime/installer acceptance and notarization remain.
Notify the maintainer when Developer ID/notarization actually needs them.
