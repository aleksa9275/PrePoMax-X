# Native solve from a reopened static PMX

Task 0049 connects the checked result-free C3D8 PMX 3.0.0 subset to the macOS
model tree, viewport and native CalculiX job. Use **Open static PMX…**, then
**Edit PMX…** to edit Young's modulus and axial force and save a new copy.
Open the saved copy and choose **Run analysis**. The viewport loads the completed
FRD while the tree keeps the source model. Results stay in the job folder.

The job freezes the reconstructed mesh and controlled definition and records
the source PMX hash. The C# runner and the PMX Save As verifier use the same
deck builder, including the original density keyword and captured step
frequency and field outputs. The ordinary INP command continues to accept its
existing analysis definition, including optional histories. PMX editing is
limited to the two scalar equations and the existing shape checks.

## Verification

The ad-hoc-signed ARM64 DMG was mounted read-only, copied to a path with
spaces and ejected. The copied app passed the existing INP solve and render
checks. The default frame bridge and opt-in Cocoa view each passed 17 PMX
checks. The probe opens the original, edits and saves 84,500.5 MPa and
42.25 N per node, reopens the copy, runs the native job and loads the FRD.
The probes exercise the actual desktop actions and dialog with supplied paths.
An unsupported header preserves the active model. The jobs keep their
validated input snapshots and both project files keep their original bytes.

Both executed decks matched the C# validation hash and the previous PMX
reconstruction hash. The checked deck semantics matched the official
PrePoMax 3.0.0 export. A separate run of that export with the pinned native
Mac solver reproduced every decoded DISP, STRESS and FORC value in both
packaged runs. The saved PMX matched the file previously reopened by the
official Windows executable through CrossOver.
[Prior original-app readback](pmx-3.0.0-reference/shape-workflow-original-readback.json).

Fourteen desktop regression tests, four execution source guards, the current
execution profile and the standalone shape workflow passed on macOS ARM64.
The shape workflow also verified repeated Save As and six refusal controls.
[Package and comparison receipt](static-pmx-native-solve-verification.json).

The retained internal DMG is
`X/Build/artifacts/task0049-delivery/dist/PrePoMax-X-Preview-arm64.dmg`
with SHA-256 `faf470719ca820f702862f232b3799e2d22066f254ad8f88017836f259add2a5`.
The manifest names implementation commit `023383ce` and contains no changed
source patch. Its dirty flag reflects the untracked Finder metadata.
Eight generated payloads were removed, including the superseded task 0048
DMG, leaving 5.23 GiB more free space. The job folders and comparison receipts
were retained.

## Publication and remaining scope

Implementation `023383ce` was pushed and verified on
`origin/research/native-feasibility`. Exact-commit pipeline
[#3027275531](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3027275531)
passed all six automatic native Linux x64 jobs, including the solver workflow.
Compatibility stayed manual. Hosted archives were not downloaded.
The Linux jobs check the shared engineering workflows. The copied desktop PMX
run is macOS ARM64 evidence. Linux desktop packaging, general PMX graphs,
embedded results, command histories, both correctness failures, the
quadratic-tetrahedron gate and release requirements remain open.
