# Task 0013 — First callable shared engineering slice

2026-10-16 Mac closeout: exact ac51fc77 first slice also passes native Mac ARM64
and Podman Linux ARM64, 25 mapping checks/nine CLI controls each. Hosted Linux
x64 job #17244123735 in pipeline #2956616374 passes the same checks. Portable
results/source/tool hashes independently match the retained Windows report and
published commit. First-slice required-platform execution is complete within
scope; [evidence](../reports/shared-core/platforms/verification.json). Task 0015
tracks the next bounded data increment; older pending statements below are history.

Status: first Windows implementation checkpoint complete, 2026-10-16. Maintainer
explicitly supplied the private PMX and requested completing testing and moving
to building. Continue on research/native-feasibility, preserve existing work,
the later task 0014 now authorizes committing/pushing the reviewed changes and
MacBook handoff. No x/main integration is authorized.

The native private-model read/save/reopen and results-enabled/disabled cases
are in task 0011's Windows report. Exact custom model/results payload evidence
agrees with the CrossOver pass. This supports a bounded implementation without
waiting for every full-application release gate.

Implementation: move the existing CaeException class unchanged to its own
source file and add it to the original net48 CaeGlobals project. Add separate
partial .NET 10 CaeGlobals/CaeMesh library projects with explicit source links,
original namespaces/assembly names/versions and zero package dependencies.
Expose the full unchanged ThreeBlockMapping through a small JSON CLI host.
Preserve the existing Windows ExceptionTools/MessageBoxes implementation.

Acceptance: unchanged source hashes and mechanical extraction verified; 13
original vectors plus independent geometry/topology/evaluator/domain-error/type
identity checks (25 total); valid CLI example and nine failure/usage controls;
legacy CLR source-slice compilation and geometry/error/type identity smoke;
readable build/run instructions and native Linux x64 CI job prepared. Evidence
is in [the report](../reports/shared-core-first-slice.md). Portable library and
host build with zero warnings/errors on native Windows x64. The entire Windows
solution was not rebuilt, and this is not a complete core/PMX/GUI implementation.

Next: execute this exact library verifier natively on Mac ARM64 and Linux ARM64,
then the prepared Linux x64 job when publication is authorized. Expand the next
model/deck boundary incrementally, preserving existing engineering behavior.
Do not choose a frontend or serializer merely because this slice passes.
Custom mesher-source recovery, interactive VTK, full history/clone compatibility
and the remaining native tool/platform gates remain release requirements.
