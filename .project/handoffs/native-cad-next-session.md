# Native CAD continuation — 6 November 2026

Tasks 0074–0077 are complete within their native CAD editing boundary. Read
[the desktop CAD editing report](../reports/desktop-cad-editing.md) and its final
receipt. **CAD tools…** provides selected-part translation, plane split, original
ShapeFix option 1 repair and checked STEP export. Mutation of PMX geometry remains
refused; export can read its owned CAD. A failed/cancelled edit preserves the old
model; successful edits clear dependent mesh/regions/analysis. Jobs freeze exact
operation inputs, parameters, command outputs, receipts and part-origin mapping.

Retained candidate: `/tmp/prepomaxx-task0077-delivery/PrePoMax-X Preview.app`,
source `b7daf541`, published/remote-verified with CI skipped and empty source patch.
Its sibling native CAD launcher enables `/tmp/prepomaxx-task0063-recipe/runtime`;
older task 0067/0068/0070/0073 launchers forward to it. Both copied Mac viewports
and Linux ARM64 pass 43 checks: all four dialogs, edited three-part mesh (208
nodes/533 C3D4), native affine-displacement/unit-stress solve, frozen provenance,
visible contours and STEP reopen. Native transaction suites pass 33 on each host;
desktop regressions 44 and build guards nine. Copied CAD PMX/C3D8 paths pass 28/17.

Three bounded BREP outputs match the retained task 0066 original Windows hashes;
no new original Windows GUI run occurred. Strict final Mac/Linux comparison
matches topology, decoded coordinates and value order, but differs in G17 deck
coordinates and tiny field components (maximum absolute difference ~1.318205e-13).
The strict difference is retained; analytical checks pass independently and no
tolerance/coordinate precision changed. Both earlier correctness failures,
quadratic tetrahedra, exact native parity and all release gates remain open.

Superseded app/staging/per-build cache copies are pruned. All generated CAD/STEP/
PMX/mesh projects, jobs, receipts/screenshots and native/Python/.NET/package/image
source/tool caches remain. Earlier app paths below are historical. New native CAD
session PMX persistence is still next under D057; STEP exchange is not a PMX
substitute. Preserve D058 hosted hold and D059 Windows/Podman x64 deferral, along
with Windows/four-target/installer/signing/notarization/full parity requirements.


Tasks 0071–0073 are complete within the checked original CAD/C3D4 PMX boundary:
material Poisson's ratio/density, signed vector forces and existing named-region
assignment edits persist through Save As/reopen/native solve. Read
[the combined report](../reports/pmx-region-assignments.md) and its final receipt.
Source `3de11f59` is pushed/remote-verified with CI skipped. Retained candidate:
`/tmp/prepomaxx-task0073-delivery/PrePoMax-X Preview.app`; sibling launcher enables
the retained native CAD runtime and older launchers forward to it. Both copied
Mac viewports and Linux ARM64 pass 28 checks, including displayed color pixels.
The final C3D8 PMX path passes 17. Bundled contracts pass 20/15/21 checks; the
four current engineering suites and 38 desktop/12 analysis/9 build guards pass,
retaining both correctness failures and the quadratic-tetrahedron gate.

Mac/Linux edited PMX bytes/deck hashes and original decoded fields match exactly.
Each feature has original-app reopen/export/resave evidence. Original/reference
projects, frozen jobs, screenshots, pinned ZIP and shared native/Python/.NET/tool
caches remain. Superseded app/staging/per-build caches and the isolated temporary
reference extraction/bottle are pruned; older candidate paths below are historical.
New native-session serialization and the full original project corpus remain
next under D057. Preserve D058/D059, both correctness failures, quadratic tetrahedra
and all Windows/four-target/installer/signing/notarization/parity/release gates.


Tasks 0069/0070 add a checked original CAD/C3D4 PMX boundary: safe projection,
controlled modulus/force Save As, reopen, original-app readback and native solve.
Read [reference](../reports/cad-pmx-reference.md) and
[desktop evidence](../reports/desktop-cad-pmx.md) with their receipts for actual
publication and candidate identity. Implementation `4d0ee6b3` is remote-verified;
no hosted jobs were started. Retained app:
`/tmp/prepomaxx-task0070-delivery/PrePoMax-X Preview.app`; sibling launcher enables
native CAD, old launchers forward. Both copied viewports pass 18 CAD PMX checks,
old PMX/regions/C3D8 paths pass, and final saved PMX bytes match original-app
readback. Superseded payloads and temporary reference bottle/extraction are pruned;
projects/jobs/evidence/ZIP/tool caches remain. Original CalNode E8 is shared only for the
CAD PMX export path; original-export/native and Mac/Linux decoded fields match
exactly. Jobs freeze complete source PMX. General new native-session serialization
is still next under D057, alongside broader original PMX graphs. Keep D058/D059
and all correctness/tetrahedron/parity/release gates. Prior app paths are historical
after closeout; keep the one candidate named in the current receipt.


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
