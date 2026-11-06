# Native CAD mirror, scaling and transform copies

Tasks 0081–0083 complete three bounded native CAD authoring increments: plane
mirror, explicit-center scaling and translated/rotated copies through the original
recovered `BREP_TRANSFORM` protocol. [Verification receipt](cad-mirror-scale-copies-verification.json).
New native-session PMX persistence remains open under D057.

## Behavior and scope

**Mirror part…** uses an explicit plane point and nonzero normal. The original
kernel owns reflection and shape orientation. An off-origin oblique plane passes
positive volume, centroid/bounds, retained face/edge/vertex IDs and untouched
part-byte checks. No new geometric kernel implementation is added.

**Scale part…** takes an explicit center and three positive factors between
0.000001 and 1000, excluding an identity-only scale. Uniform and non-uniform
scaling pass separate analytical volume, centroid, bounds and source-ID checks.
The recovered source uses an exact uniform transform and a general spline
transformation for non-uniform factors; those original paths remain unchanged.
Negative/singular factors are outside this preview's supported boundary.

**Copy part by translation… / Copy part by rotation…** retain every original
part's BREP/VIS bytes and append the original command's numbered outputs. Copy k
applies k translations or rotation angles. Each transaction allows 1–16 copies
within 32 total parts and requires one supported solid per selected/copied part.
It checks the exact output inventory, per-file bounds and the existing complete
256 MiB edit-input limit. Missing, extra or cancelled outputs are cleaned up
before publication. Originals are never replaced by the command's first copy.
The new receipt retains each raw output filename/hash, source-part origins and
copy numbers; submitted jobs freeze every output and parameter file. Copies are
independent bodies; no imprinting, joining, collision handling or general
assembly authoring is claimed. Coincident bodies can be refused by STEP export's
existing unambiguous-origin checks.

All four new dialogs use background cancellation, atomic document publication,
owned undo/redo and dependent-mesh/analysis invalidation after confirmation.
Unsupported inputs and failed/cancelled operations preserve the active model.
Opened PMX geometry remains immutable through these tools. Geometry edits remain
session state; STEP exchange does not substitute for native-session PMX saving.

## Actual verification

- Native Mac ARM64 and Linux ARM64 each pass **99 CAD transaction checks**.
  They cover mirror, uniform/non-uniform scale, both ordered copy patterns,
  original-part bytes, copy geometry/IDs/origins/output hashes, STEP readback,
  invalid inputs and the earlier native edit/export/history contracts.
- Source desktops on both hosts and both final copied Mac viewports pass **91
  workflow checks**: all dialogs, undo/redo, eight active edit recipes, six-solid
  remeshing, affine displacement/unit axial stress, frozen files/receipts, visible
  contours and selected/whole-model STEP export/reopen. The selected scaled solid
  retains volume 750 and centroid [-2, 2, 10]; total STEP volume is 4768.
- **50 desktop regression tests** pass on each native host. A new transaction
  test injects partial, extra and cancelled copy outputs and verifies cleanup
  before decoding, unchanged originals and no document replacement. Existing
  worker/history/closing/PMX protections remain. **Nine Mac build guards** pass.
- Existing CAD PMX and C3D8 PMX workflows pass **28 / 17 checks** in the final
  copied Mac app and against the current Linux ARM64 source.

The final Mac mesh has **402 nodes / 898 C3D4 elements**; Linux ARM64 has **402 /
900**. Both pass the original positive-tetrahedral mesh boundary and independent
analytical result checks. Maximum affine-displacement error on each host is
~3.47e-18; the existing unit-stress tolerance is unchanged. Strict nodes,
connectivity, deck bytes and decoded field arrays differ, while result value-order
IDs match. The complete strict receipt/deck diff is retained. No pointwise field
error is claimed across these different meshes. This does not close exact native
mesh/deck/field parity; earlier strict CAD and edited-three-body differences also
remain open. No coordinate formatter, numerical tolerance or solver precision
was changed to force agreement.

The earlier translation/split/repair BREP hashes still match the retained original
Windows task 0066 reference on both native hosts. No new Windows mirror, scaling,
copy or original GUI execution occurred. Original C#/numerical owners and native
runtimes are unchanged; checks target affected Python/CAD paths. The full
numerical/platform/release matrix was not rerun.

## Publication and current candidate

All three normal research checkpoints are pushed and remote-verified:

- 0081: `ba5a3900e0b115faf1b466c39ab30fbd97f84d4e`
- 0082: `fb9da6c4b7fdd29ca539f785d11bf96bde54e224`
- 0083 / packaged source: `b938adac7742d2318d0eee54607e1963d3769862`

Commits contain `[skip ci]`; pushes use `-o ci.skip`. No hosted jobs were requested.
D058's hold and D059's Windows/Podman Linux x64 deferral stay in force.

Current app: `/tmp/prepomaxx-task0083-delivery/PrePoMax-X Preview.app`.
Its sibling `/tmp/prepomaxx-task0083-delivery/Native CAD Preview.command` enables
`/tmp/prepomaxx-task0063-recipe/runtime`. Older task 0067/0068/0070/0073/0077/0080
launchers forward to it. The package source patch is empty, with no changed code;
four pre-existing Finder files account for the dirty flag. All **2,422 copied
payload hashes**, symlink targets and the ad-hoc signature pass after cleanup.
Both final result screenshots were visually inspected and show the six-solid
workflow's mesh contours and configured model tree.

Evidence: `/tmp/prepomaxx-task0083-evidence`; manifest/build logs/source snapshot:
`/tmp/prepomaxx-task0083-final`. The tracked receipt pins the retained data.
Seven generated directories, including the superseded task 0080 app and the new
build's duplicate payloads/caches, were pruned: **5,035,202,697 logical bytes**,
with **4,436,180,992 bytes (~4.13 GiB)** of measured free-space gain. All generated
CAD/STEP/PMX/mesh projects, jobs, screenshots, receipts, source snapshots and shared
native/Python/.NET/package/Podman/source caches remain. Installed user app/state
was untouched. Earlier candidate payload paths are historical after replacement.

## Remaining acceptance

Native-session original-compatible PMX serialization and broader project graphs,
exact native parity, arbitrary CAD/assembly and analysis/mesher breadth, both known
element correctness failures, quadratic tetrahedra, Windows/net48 and all
four-target/installer/Homebrew/signing/notarization/release gates remain open.
No production frontend, default format, backend or precision decision is made.
This remains an internal ad-hoc-signed, unnotarized preview. Notify the maintainer
when Developer ID or notarization actually requires their involvement.
