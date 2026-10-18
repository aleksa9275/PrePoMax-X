# Task 0023 — Complete a first portable static analysis deck

2026-10-18, Europe/Belgrade. Maintainer requests continuing the accepted native
model/deck → solve → results sequence. Preserve all task 0022 uncommitted work;
no new commit/push or frontend/default format/numerical/native-tool decision.

Build a bounded 3D linear-static deck through original section, displacement,
concentrated-load, static-step and output types/keyword writers. Mechanically
separate coupled preview/model capability members from reusable data/formatting
parts, retaining original net48 inclusion, namespaces, fields and assembly
ownership. Do not introduce substitute model types, selection stubs, evaluators
or formatting algorithms. Reuse the existing standalone mesh boundary and
analytical uniaxial cube/reference semantics. A tool configuration transport may
construct original engineering objects; it does not select PMX persistence.

Deliver a callable typed boundary and a no-overwrite CLI producing an actual
mesh/material/section/BC/load/static-step/output deck. Require explicit consistent
units and named regions; reject unsupported/omitted definitions, invalid sets,
coverage, unsupported flags and invalid numeric input. Keep both correctness
failures and the tetra measurement gate. Do not run or substitute a solver here.

Verify geometry/IDs/material/BC/load/step/output semantics against the retained
cube reference and independent keyword expectations, source extraction/type
ownership, negative controls, all previous checks and current/RC2/post-RC2 native
Mac/Linux ARM64. Prepare hosted x64 follow-up without claiming it ran; retain
Windows/full net48/RC2 and installable desktop/release gates. Record evidence,
limits and next work before ending the increment.

Status: complete within this bounded local deck-generation increment. All
implementation/evidence remain uncommitted; no native solve or new hosted/
Windows/full-net48 result is claimed.

Implemented original typed static-deck boundary, strict no-overwrite CLI with
explicit units and synthetic reference fixture; mechanically checked core/legacy
partial extraction and original net48 ownership. Current/RC2/post-RC2 pass native
Mac/Linux ARM64: 44 material + 69 static + 218 previous = 331 accepted checks per
build, eight material/21 static CLI controls and four semantic negative controls.
Nine analysis guards/ten original replay guards pass; offline core independently
passes. Six-run fingerprints/outcomes match. Both known correctness failures and
quadratic-tetra host gate remain. [Evidence and limitations](../reports/static-analysis-deck.md).
Continue matching native solver execution/results under the accepted sequence;
retain all installable desktop and Windows/net48/RC2/source/release gates.
