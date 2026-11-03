# Editable static-solid workflow — task 0044

3 November 2026. **Verified observation:** a packaged Mac desktop can edit the
existing bounded static-solid definition, validate it through the original C#
model/deck services, solve it natively and inspect its fields. No hand-edited
analysis JSON is required in this workflow. [3.0.0 parity scope](../PARITY.md)
and the full-product requirements remain distinct from this increment.

## Implemented user workflow

The model tree retains the source mesh, imported named node/element sets,
materials, solid sections, supports, nodal loads and step after FRD loading.
Configure (or double-click a definition in the tree) opens controls for:

- Explicit mesh units: mm/N/s/°C or m/N/s/°C. Selecting units interprets existing
  coordinates; it does not rescale them.
- Isotropic elastic material names, Young's modulus and Poisson ratio; solid
  section material/element-set references.
- Displacement supports on imported named node sets. Blank components remain
  free; zero fixes the corresponding original DOF.
- Force components **per node**, not a total force silently divided among nodes.
- Static incrementation/output frequency and original nodal/element history
  requests. Interactive history plots are not added here.

The user can add/remove supported records. Imported sets are listed and used as
regions; creating new sets from picked IDs is pending. The UI does not infer
supports, loads or physical properties from geometry. Fresh imports require
explicit units/properties/assignments; Solve example loads the known fixture.
Unsupported original analysis/model content is not reconstructed from INP.

Validate invokes `PrePoMaxX.Solve validate-static`: the original mesh reader,
`AnalysisFiles.Create/Build` and `StaticAnalysisDeckWriter` construct/check the
original types and deck. It needs no native solver registry and does not execute
a solver. The GUI does not evaluate engineering equations, convert physical
quantities or provide another mesh parser. Invalid definitions cannot apply;
editing clears a previously successful validation result.

Run analysis freezes the loaded mesh bytes and the current tool definition into
one fresh workspace's `inputs` directory; the original C# runner reserves/creates
its separate `solve` directory. Original solve/cancel/status/FRD behavior remains.
Job files opens that workspace. Model edits survive viewing completed results;
discard/close prompts protect unsaved session edits. The automated probe waits
for native cancellation/cleanup before exiting on an active-job failure.

**Persistence boundary:** these are retained job inputs using the existing
analysis tool schema. Project save/reopen, original PMX/PMH reconstruction and a
production/default format are not implemented or selected. The UI and bundled
guides state this explicitly. [Task 0045](../tasks/0045-supported-project-persistence.md)
prepares the next persistence decision/proof.

## Engineering ownership and scope

`X/Desktop/analysis_editor.py` owns presentation; `viewport.py` owns the model
tree/session and `jobs.py` owns snapshots/QProcess transport. `MeshScene/Program.cs`
adds only original set names/counts to its DTO. `X/Execution/Solve/Program.cs` adds
solver-free validation ahead of native-registry loading. No original Cae* source,
numerical algorithm, tolerance, assembly ownership or original reader/writer
semantics changes. Native CalculiX 2.22/SPOOLES and the existing one-thread profile
are unchanged. The bridge remains default; native Cocoa remains opt-in.

## Verification

The actual copied/ejected DMG app uses bundled Python/Qt/VTK, three self-contained
C# hosts and relocated solver runtimes, with `PATH=/usr/bin:/bin` and invalid
external DOTNET_ROOT. No developer SDK/Python on PATH is used by the copied app.

| Check | Actual bounded result |
|---|---|
| Current-source Analysis | 333 accepted checks; both known element failures/tetra gate retained |
| Current-source Execution | Existing 49 checks/13 CLI rejection controls and pipe controls pass; new desktop validation controls pass |
| New validation CLI | Original deck hash matches standalone original builder; edits change hash; units/material/node-set/free-only-support rejections; no solver registry/execution |
| Real Qt editor + original C# validation | Seven checks pass, including free-DOF preservation, missing references, changed equations and invalidation of stale validation |
| Real Qt process/original job host | Four checks pass: cancel/reaping, preflight diagnostics, tampered solver rejection and frozen edited inputs despite source/definition mutation |
| Build boundaries | Eight checks pass |
| Actual mounted/copied/ejected app | Signature/hash/link and original solve/render checks; retained report identifies file/link counts |
| Real packaged editor, native Cocoa | 18 controls/workflow checks and 15 independent deck/numerical/control checks pass |
| Real packaged editor, default bridge | Same 18 controls/workflow checks and 15 independent deck/numerical/control checks pass |

These are automated real-widget/native-process tests, not a claim of human
input, clean OS, Windows/Linux GUI or full original-model acceptance. Actual
dialog/result screenshots were inspected. A final visual pass corrected tree
column truncation and stale validation feedback. Two sandbox SDK builds initially
stalled, were stopped by their exact owned PIDs and rerun with normal SDK access;
those stalled attempts are not passing results. Local SDK is 10.0.403; packaged
runtime remains explicitly pinned by the existing target catalog.

## Edited numerical proof

The packaged probe opens the real Configure dialog, attempts a missing material
reference (Apply rejects it without starting a solver), repairs it, edits
**210 GPa → 105 GPa** and **25 N/node → 50 N/node**, then applies/runs. It checks
the submitted snapshot equals the applied controls and the executed deck's SHA
equals the original validation hash. Node IDs/connectivity, supports, sections,
step/output structure and original fixture remain unchanged.

The four loaded nodes now carry **200 N** on the unit-area cube. Independent
checks require **200 MPa axial stress**, transverse/shear zero, **−200 N** support
reaction, zero global force sum and the uniform-strain displacement field for
E=105000 MPa, ν=0.3. Axial displacement on x=1 is **0.0019047619 mm**, four times
the baseline. Absolute tolerances remain displacement 1e−9, axial stress 1e−4,
transverse/shear 1e−5 and force 1e−5. Altered deck force and displacement controls
are rejected. The original baseline's seven analytical checks also pass.

Retained evidence includes submitted inputs, generated INP, actual DAT/FRD/STA,
run/desktop outcomes, current checks, package/reproduction manifests and screenshots.
See [evidence index](editable-solid-workflow/evidence-index.json),
[native verification](editable-solid-workflow/native-editor/verification.json)
and [default verification](editable-solid-workflow/bridge-editor/verification.json).
No private user model is used or included.

## Local artifact and reproduction

The fully captured/tested DMG is
`X/Build/artifacts/task0044-final-delivery/dist/PrePoMax-X-Preview-arm64.dmg`:
260,510,141 bytes, SHA256
`9a6e586c0c8b8065a1185e219a23ea8e159495d42daa67b111628723f4de316a`.
Its copied/ejected app passes the signature/1,610-file/1,470-link checks and all
native/default editor/numerical checks above. The included install/reset guides
match the new workflow. Earlier task 0042/0043 tested DMGs remain unchanged.

A later candidate adds only automated-probe timeout cleanup (wait for runner
cancellation before exit); all normal product-path sources are unchanged. Its
path is `X/Build/artifacts/task0044-reviewed-delivery/dist/PrePoMax-X-Preview-arm64.dmg`,
260,546,540 bytes, SHA256
`5d08e69e55e96beb61342587b53162cd7b783d8a1da5df7ba6c8f791ae6c2f27`.
Both actual native jobs, original validation/deck hash and 17 editor checks pass,
but the final actual screen capture fails. A separate minimal Qt application
also returns null for screen-region, own-window and full-screen grabs, with a Qt
ICC-profile warning. The cause is not established; display-session availability
was requested from the maintainer. This failed capture is **not** a passing GUI
check. Independent actual DAT checks still pass with unchanged bounds. Retain
the passing artifact above while this latest capture remains pending.

The package source identity records base **c0f60987 plus a retained dirty source
snapshot**; do not call it a clean-commit build. Compare the six desktop source
hashes and changed C# files with the publication commit; the passing artifact's
probe predates that final test-only cleanup change. Binary remains local and
ignored. Ad-hoc signing is internal-preview evidence; Developer ID/notarization,
downloaded Gatekeeper and clean-Mac acceptance remain pending.

```sh
/private/tmp/prepomaxx-desktop-runtime/bin/python X/Build/build.py package --target osx-arm64 --format dmg --solver-build X/Build/artifacts/task0041-final-mac-solver/solver --output <new-package>
python3 X/Build/verify-macos-dmg.py --package <new-package> --output <new-copy-check> --viewport native-cocoa
python3 X/Build/verify-editable-solid.py --app '<copied-app>' --output <new-editor-check> --viewport native-cocoa
python3 X/Build/verify-editable-solid.py --app '<copied-app>' --output <new-default-check> --viewport frame-bridge
```

Publication/CI is recorded after actual remote/hosted verification. All original
correctness/persistence/history/CAD/native-source/four-target/install/release gates
remain. No upstream/master/x/main/release write or public binary distribution.
