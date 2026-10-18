# Proposed next implementation — awaiting maintainer approval

2026-10-18, Europe/Belgrade. Requested after task 0021 publication. This is a
proposal, not authorization to begin. The maintainer explicitly requires reading
and approval before the next feature steps. Windows testing may be deferred
while portable implementation continues after that approval; its release gates
remain mandatory. Publication authorization does not extend to future features.

## 1. Complete a first analysis deck through original model behavior

Turn the current standalone mesh into a small, runnable 3D static linear-elastic
analysis definition. Expand original shared material/section/BC/load/step types,
equations/units and CalculiX keyword generation, keeping original assembly/type
ownership and a single engineering implementation. Begin with isotropic elastic
material, a solid section on an element set, prescribed nodal displacements and
concentrated forces on node sets, and a static step with useful outputs.

Use existing definitions.inp/native-Windows reference decks as regression inputs;
retain their IDs, material values, regions, units and load/BC meaning. Export
an actual analysis deck rather than dropping its model keywords as mesh-only
export intentionally does. Prove structural/numerical equivalence of keyword
content and named references, plus invalid-region/material/step failures, on
Mac/Linux ARM64 and hosted Linux x64. Keep unsupported features explicit.
This does not invent another FeModel, frontend or document format. Dependency
boundaries must be measured and adapted narrowly using existing pins.

Deliverable: the portable host can define the simple cube analysis and produce
a validated solver input deck with material/section/BC/load/step semantics.

## 2. Run the same solver version natively

Extend the existing executable/job-runner seam with portable process handling,
working directories, progress/error reporting, timeout/cancellation and output
collection. Establish and fingerprint native builds of the current solver
version for the available targets. Reuse the existing analytical uniaxial-cube
fixture and solver evidence; do not silently replace the solver, meshers or
runtime dependencies. Native binary/source/ABI availability is an explicit
prerequisite for execution, not a reason to claim an unexecuted solve passed.

Deliverable: the host launches a real solve natively on Mac/Linux where the
matching build is available, distinguishes success/failure/cancellation and
retains provenance and output files. Numerical outcomes must match independent
analytical expectations and the recorded reference within reviewed tolerances.

## 3. Read and inspect the resulting engineering fields

Expand the original FRD/DAT readers and necessary results/mesh/field graph into
their original shared assemblies. Use the existing buffered reader rather than
writing another format decoder. Retain node/element IDs, increments, units,
displacements, stress components and derived calculations. Compare retained
Windows result fixtures and actual new native outputs. Add a useful portable
result-inspection command with ordinary tool output, without selecting the
application's persistence format.

Deliverable: mesh → analysis definition → solver deck → native solve → readable
results, exercised end-to-end in CI and packaged as a development tool.

## Subsequent interface and persistence decisions

Once the workflow is usable, resolve the interactive VTK host experiment
(picking, clipping IDs, deformation, material axes, DPI/input and lifetime),
then select the frontend from evidence. Implement save/reopen/history/clone
semantics with old/new PMX compatibility, including upstream composite fields.
Matching patched CAD/mesher sources remain an early release dependency; a
mesh-based workflow can progress while CAD parity is unresolved.

Recommendation: approve steps 1–3 as the next implementation sequence, working
in tested increments. Windows is a later differential check rather than a
blocker to local Mac/Linux coding; full native Windows/net48/RC2, four-platform,
correctness, persistence/UI/CAD/source and packaging gates remain before release.
Both original correctness failures and the tetrahedron measurement gate remain
until separately reviewed. No next feature work has started under this proposal.
