# Native CAD continuation — 5 November 2026

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

Current local Mac app:
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
