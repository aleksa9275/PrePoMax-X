# Persistent original PMX named-region assignments

Task 0073's candidate is superseded and pruned after verified tasks 0074–0077.
[Current candidate and CAD editing evidence](desktop-cad-editing.md).

Task 0073 adds section, support and load region selectors to the checked original
CAD/C3D4 PMX editor. Choices come from compatible existing nonempty element/node
sets. Assignment edits preserve set names, labels, object names, original BREP,
mesh, meshing data and history; they change only audited `_regionName` member
slots. This does not create new regions or serialize a newly authored CAD session.

The pinned original 3.0.0 app adds duplicate named-region choices to the task 0069
fixture. The native edit moves the X support and load to opposite faces, reassigns
the other supports and selects the duplicate solid element region. Twenty-one
Mac assignment/interoperability checks pass, including an equivalent graph with
forward-referenced string members, repeated reassignment, wrong entity kinds and
missing/unknown assignments. Original-app resave retains equal CAD, mesh, material,
vector force and assignment semantics. Its exported deck and native reconstruction
produce exactly equal original decoded fields through the same native solver.

All three final persistence suites pass on Mac and Linux ARM64: material (including
wire-depth rejection), signed vector forces and region assignments. Linux's real
combined desktop workflow passes 28 checks with original contours/legend, frozen
PMX inputs and native solve. Each final copied Mac viewport passes the same 28
checks, including editor capture and actual colored mesh pixels on screen.
The four current engineering suites pass, retaining both original element failures
and the quadratic-tetrahedron gate. Desktop regressions pass 38 tests, analysis
ownership/formatter guards 12 and build guards nine. Legacy CAD PMX checks pass 17.

[Verification](pmx-region-assignments-verification.json). Local detailed evidence:
`/tmp/prepomaxx-task0073-evidence`. One combined replacement Mac candidate and
its copied-app evidence are recorded below and in the final receipt.
Normal research-branch publication uses CI skip; no hosted job is started.

New native-session serialization, new/deleted regions, general PMX/results/history,
broader assignments/analyses, native Windows, both correctness failures, quadratic
tetrahedra, all parity/installer/signing/notarization/release gates remain open.
D058's hosted hold and D059's deferred Windows/Podman x64 verification stay in force.

## Current candidate and publication

Retained app: `/tmp/prepomaxx-task0073-delivery/PrePoMax-X Preview.app`.
Its sibling `Native CAD Preview.command` enables the retained explicit native CAD
runtime. Earlier task 0067/0068/0070 launchers forward to this one. Open the local
generated fixture `X/Feasibility/Pmx/artifacts/task0073/region-reference.pmx` through
that launcher or **Open static PMX…**. This increment edits supported original
projects; native set creation and new native-session Save As remain separate.

All 2422 copied payload file hashes, symlink targets and the ad-hoc signature
verify. The source patch is empty; the dirty flag reflects only the four
pre-existing Finder files. The final app identifies published source `3de11f59`.
Its bridge and native Cocoa edited PMX files are byte-identical to each other,
the Linux output and the native file validated by the original app. Original
decoded Mac/Linux result fields also match exactly. The final copied C3D8 PMX
workflow passes 17 checks. The bundled official-decoder persistence contracts
pass 20 material, 15 vector and 21 assignment/readback checks.

Visual review caught a stale first Cocoa capture immediately after switching
fields. Probe-only follow-up `3de11f59` waits through presentation and checks
colored pixels within the displayed mesh. Both final Mac captures were visually
inspected. The initial capture and receipts remain; no renderer/product behavior
or tolerance was changed to obtain the corrected evidence.

Implementations `72f12c2a`, `919df90c`, `ec009d72` and capture correction
[`3de11f59`](https://gitlab.com/aleksa9275/pre-po-max-x/-/commit/3de11f59aaa67dded3eb79b4ee21d83b574e5031)
are pushed and remote-verified on `origin/research/native-feasibility`, with
`ci.skip` and no hosted runs requested. Closing evidence is a normal
documentation-only CI-skipped follow-up. Seventeen generated directories,
including superseded app/staging/cache copies and the isolated reference
extraction/bottle, were pruned (11.63 GiB logical bytes). All generated projects, jobs, receipts, original ZIP and shared
tool/native caches remain. The user's installed app, state and original bottle
were not changed.
