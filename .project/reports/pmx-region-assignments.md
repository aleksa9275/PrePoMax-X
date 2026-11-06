# Persistent original PMX named-region assignments

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
combined desktop workflow passes 27 checks with original contours/legend, frozen
PMX inputs and native solve. Mac source workflow passes its 25 initial checks;
the final copied-app probes also check editor capture and contour mapping.
The four current engineering suites pass, retaining both original element failures
and the quadratic-tetrahedron gate. Desktop regressions pass 38 tests, analysis
ownership/formatter guards 12 and build guards nine. Legacy CAD PMX checks pass 17.

[Verification](pmx-region-assignments-verification.json). Local detailed evidence:
`/tmp/prepomaxx-task0073-evidence`. One combined replacement Mac candidate and
its exact copied-app evidence are recorded in the final receipt at closeout.
Normal research-branch publication uses CI skip; no hosted job is started.

New native-session serialization, new/deleted regions, general PMX/results/history,
broader assignments/analyses, native Windows, both correctness failures, quadratic
tetrahedra, all parity/installer/signing/notarization/release gates remain open.
D058's hosted hold and D059's deferred Windows/Podman x64 verification stay in force.
