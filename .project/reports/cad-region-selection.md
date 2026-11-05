# Visual CAD region selection

Task 0068 connects retained source CAD to analysis assignments. After native
meshing, choose **CAD geometry** in the view selector. **Pick faces** or **Pick
parts** controls viewport picks. Click replaces a selection; Ctrl/Command-click
adds or removes a region. The source CAD tree also supports multiple selections.
Selected surfaces highlight orange. **Clear CAD selection** clears the selection.

Choose **Set from CAD…** to name the region. Faces create node sets for supports
and nodal forces. Parts create node sets or element sets for solid sections.
The existing **Configure…** dialog offers these sets and validates assignments
through the original C# engineering types. Mesh, source CAD and matching loaded
results can be displayed without reimporting or discarding model edits. Analysis
controls remain available while viewing CAD associated with a generated mesh.

## Engineering boundary

Selection stores source part/face IDs. It resolves only the recorded original
VOL face/domain sets, preserving per-part scope. No geometric membership is
inferred from display triangles. The new C# `add-region-set` command unions those
sets using the original INP reader, deduplicates shared IDs, revalidates the
appended deck and publishes a new file. Existing manual ID entry keeps its 1000
ID limit; CAD regions allow up to 100000 mesh IDs and 256 source sets within the
existing 16 MiB mesh limit. Wrong-kind, missing, duplicate or oversized source
selections, invalid names and an existing output file are refused.

The job freezes each authored set's CAD references, source sets and before/after
mesh hashes alongside task 0067's CAD/mesh/native recipe inputs. Failed edits
leave the active mesh and provenance unchanged. Remeshing/replacement clears old
selections and remembered results. Switching display views preserves edits and
selection, and an overlay cannot intercept the original geometry picker.
A solver-start timing check exposed a brief UI enablement gap before QProcess
became active; the desktop now treats Starting/Running/Cancelling as busy.

## Verification

The two-part reference workflow exercises actual VTK face and part picks,
source-tree multi-selection, highlighting, real invalid/valid set dialogs,
original-reader unions, assignments, native CalculiX and original FRD results.
Its eight authored CAD sets include combined part, bottom-face and separate
upper-face regions. The analytical 211-node/563-C3D4 solve still gives unit axial
stress and U3=0.001*z with maximum displacement error about 1e-8 at FRD precision.
Frozen job receipts retain the eight CAD associations.

Mac and native Linux ARM64 source desktop runs pass 46 checks. Thirty-seven Mac
desktop tests pass, including four original-reader union tests covering overlap,
typed source regions, refusal controls and a 2008-node region; those four tests
also pass in Linux ARM64. Nine packaging guards pass. These are affected-area
checks; the unchanged broad engineering and historical replay matrices were not
rerun. Existing numerical algorithms, tolerances, both correctness failures and
the quadratic-tetrahedron gate remain unchanged.

The existing Podman VM initially failed to start because its networking socket
was occupied. Verification proceeded after checking the VM was stopped and
checking stale sockets for active listeners; no VM disk/image was recreated.
Linux uses the retained SDK/Qt runtime image, native CAD and verified relocated
solver, with container networking disabled. No hosted CI or Linux x64 run occurs.

[Verification and candidate receipt](cad-region-selection-verification.json).
Local detailed evidence: `/tmp/prepomaxx-task0068-evidence`.
The final app, copied-payload checks and normal CI-skipped research publication
are recorded in the closing receipt.

## Remaining work

General CAD/mesh project save/reopen is next. Preserve original PMX compatibility
under D057; do not introduce a silent replacement format. This task does not
provide mesh-face surface loads, pressure distribution, edge selection, arbitrary
mesh multi-pick, region replacement/deletion, geometric edits or broader analysis
acceptance. Windows/net48 execution, deferred Linux x64/Windows-Podman testing,
exact native visualization differences, both original correctness failures and
all full 3.0.0/four-target/installer/signing/notarization/release gates stay open.
