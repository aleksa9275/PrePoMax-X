# Task 0005 — Structured meshing kernel feasibility

Status: bounded experiment complete on 2026-10-14. Authorized by the 2026-10-14 instruction to complete as
many bounded pre-Windows steps as usage permits, after task 0004. Branch remains
`research/native-feasibility`; preceding uncommitted documentation is preserved.

## Scope

Use the existing shared three-block mapping and its upstream C++ regression
checker/vectors. Run unchanged native C++ on Mac ARM64, add independently
specified geometric/topological and error-contract checks, and source-link the
unchanged C# count/grid types into a zero-package net10.0 probe. Measure the full
C# mapping compile boundary without namespace stubs or source edits; its
CaeException definition shares ExceptionTools.cs with UI logging.

Pin source/header/checker/vector identities. Distinguish original cross-language
vectors from independent expected values. Preserve all outcomes, warnings and
unresolved compilation boundaries. Full native CAD meshing, shell T-junction
behavior, rendering, numerical FEM and PMX/history compatibility remain excluded.
No new mesher or production dependencies; no algorithm rewrites, new process
gateway, frontend selection, commits, pushes or x/main integration.

## Acceptance

Reproducible runner/probes and native runtime evidence; original vectors pass
or retained failure diagnostics; independent topology/area/count and failure
checks; exact source hash verification and C#/C++ count-contract comparisons.
Record the measured C# mapping boundary rather than bypassing it. Complete this
task's bounded evidence before considering another workstream.

## Outcome

[Execution report](../reports/structured-meshing-feasibility.md): all 13 original
native C++ reference cases, 17 independent native checks and seven managed checks
pass on Mac ARM64. All 1,728 C#/C++ count contracts match. Two CLI contracts and
two original-comparator process regressions pass. Full unchanged C# mapping
compile attempt reaches CS0103 MessageBoxes in original ExceptionTools.cs;
source/reporting boundaries are retained, not bypassed. Full mapping execution,
Linux/Windows comparison and native CAD/meshing parity remain open.
