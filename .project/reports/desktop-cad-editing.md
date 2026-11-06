# Native desktop CAD editing

Tasks 0074–0077 add **CAD tools…** beside Open in the explicit native CAD preview.
The original Netgen/OCCT commands now run from real desktop controls:

| Task | Control | Verified bounded behavior |
| --- | --- | --- |
| 0074 | Translate part | Explicit X/Y/Z model-unit offset; untouched parts retain BREP/VIS bytes |
| 0075 | Split part by plane | Explicit origin/normal; original solid separation and source-origin mapping |
| 0076 | Repair part | Original ShapeFix option 1; positive tolerance up to one model unit |
| 0077 | Export part as STEP | Native reimport before atomic publication to a new file |

Each geometry edit owns independent copies of the original input, current parts,
command inputs/outputs, parameter files, logs and receipts. The worker validates
all resulting parts before the GUI replaces the document. Failure, cancellation
and late cancellation retain the old CAD, mesh, assignments, analysis and unsaved
state. Closing waits for the worker before releasing inputs. Successful geometry
edits invalidate dependent meshes/analysis and clear stale region selections.
Recipes, part origins and exact inputs survive in subsequent frozen jobs.

STEP export preserves the active geometry/mesh/analysis and unsaved state. It
stages checked bytes on the destination filesystem and refuses existing paths.
An opened PMX can supply geometry for export; mutation of its CAD remains refused.
STEP exchange does not serialize a newly authored native CAD session as PMX.

## Verification and current candidate

Mac and offline Linux ARM64 each pass 33 native transaction checks. Translation,
plane split and valid-box repair BREP hashes match the retained original Windows
reference from task 0066. STEP reimport retains analytical volume and center. No
new original Windows GUI run is claimed. Broad repair of defective CAD is open.

Both final copied Mac viewports and Linux ARM64 pass 43 desktop checks: all four
real CAD dialogs, stale mesh cleanup, three-body remeshing, checked STEP export,
analytical native solve, visible contour pixels, frozen edit provenance and STEP
reopen. The original decoded mesh has **208 nodes and 533 C3D4 elements**. Existing
checks verify affine displacement at every node and unit axial stress; maximum
displacement error is about 3.47e-18. No tolerance or engineering owner changed.
Desktop regressions pass 44 tests on both hosts; build guards pass nine. The final
copied CAD PMX and C3D8 PMX workflows pass 28 and 17 checks respectively.

Strict cross-platform comparison retains a difference: topology, decoded node
coordinates and value order match, but G17 deck coordinates differ in their last
digits and some decoded fields differ, with maximum absolute component difference
1.318205e-13. Both independent analytical checks pass. Exact deck/field byte parity
remains open; no rounding, standalone mesh precision or acceptance tolerance was
changed to force equality. This is separate from the two existing element
correctness failures and quadratic-tetrahedron gate, which also remain open.

[Verification receipt](desktop-cad-editing-verification.json). Detailed local data:
`/tmp/prepomaxx-task0077-evidence`, with initial task 0074–0076 receipts retained.
The initial split grouping, cross-filesystem export and repository-only packaged
probe path failures are retained alongside their passing corrections. Final
Cocoa/bridge result captures were visually inspected. Generated project, STEP,
mesh and job bytes remain local/ignored.

Retained candidate: `/tmp/prepomaxx-task0077-delivery/PrePoMax-X Preview.app`.
Its sibling `Native CAD Preview.command` enables the retained native CAD runtime;
older task 0067/0068/0070/0073 launchers forward to it. Source identity is published
[`b7daf541`](https://gitlab.com/aleksa9275/pre-po-max-x/-/commit/b7daf541ea2b62bf8eed5815bbfce75730fc337a),
with an empty source patch; only four pre-existing Finder files set the dirty
flag. All 2422 copied payload hashes, symlink targets and ad-hoc signature verify.
Superseded app/staging/cache copies are pruned; the final receipt records paths
and logical bytes. Source, evidence, generated projects/jobs and shared native/
Python/.NET/package/image caches remain. User installed app/state were unchanged.

All reviewed task checkpoints and probe fixes are pushed/remote-verified on
`origin/research/native-feasibility`, with CI skipped. Closing evidence is a
normal documentation-only CI-skipped follow-up; no hosted verification is claimed.
D058's hosted hold and D059's deferred Windows/Podman Linux x64 verification remain.
New native-session PMX persistence, broad CAD/repair/analysis coverage, Windows
native execution, all correctness/parity/four-target/installer/signing/notarization/
release gates stay open. No production frontend or precision policy is selected.
