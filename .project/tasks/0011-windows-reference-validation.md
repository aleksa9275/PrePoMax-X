# Task 0011 — Native Windows reference validation

Windows closeout: pinned portable LLVM-MinGW 20261006/Clang 23.1.3 now runs
the native structured-kernel suite successfully with compiler defaults and
explicit contraction off: 13 vectors, 17 native checks, seven managed checks,
and 1,728 C#/C++ count comparisons per mode. See compiler-provenance.json and
meshing-native-*.json under reports/windows-reference. The earlier missing-tool
reports are historical diagnostics. The hardlink sandbox error remains open;
deeper history/CAD/interactive rendering remain broader release requirements.

2026-10-16 follow-up: supplied original private PMX hash matches CrossOver's
input. Native 2.6.0 read/save/reopen displays the model and four embedded result
fields. Custom model bytes remain identical; all inflated result frames match
CrossOver exactly, including its documented datatype insertion. The same 27/29
shallow type matches and job/keyword-member changes recur. The only difference
between native/CrossOver type-inventory rows is 18 string records. A separate
results-disabled save reopens with no result fields and unchanged model bytes.
Original/private copies stay outside Git. See the report's follow-up section.
Maintainer requested moving into implementation; task 0013 now starts a bounded
shared-library slice. Overall release acceptance remains open for the existing
hardlink/compiler, deeper histories, CAD and interactive-rendering gates.

Status: controlled native Windows cube/import-history checkpoint completed
2026-10-16; broader Windows gates remain open. The maintainer authorized
continuation on the planned research branch with desktop versions 2.5.1 dev
through 3.0.0 RC1 available. See the
[Windows report](../reports/windows-reference-validation.md) and
[manifest](../reports/windows-reference/manifest.json).

Official-reference 2.6.0 application/VTK hashes match the earlier CrossOver copy.
Mesh and explicit material/set/section/static-step/BC/load exports pass 30
expected/observed checks; save/reopen, atomic-import undo/redo and native history
regeneration were exercised. The regenerated export matches all nonvolatile
original deck lines. The old executable's success-text/0xFFFFFFFF exit mismatch
is retained. Its importer names XSTATIC as Step-1; individual entity-edit
histories remain outside this fixture.

Both core pins pass 23 checks + 2 CLI contracts, data passes 30 + 2 with exact Mac
comparisons, six evidence regressions and three PMX scalar controls pass, and
the exact bundled CalculiX 2.22 passes seven native analytical checks plus its
negative control. PMX inventories pass; the 24-test synthetic suite remains
23 passes + one sandbox hardlink-creation error. Structured-kernel execution is
unrun without a native C++17 compiler. Results-in-PMX variants, private legacy
model/job policy, CAD meshing and interactive rendering remain open.

Research changes/evidence are uncommitted. Production source/projects are
unchanged. No push, merge, frontend/schema choice or F001 implementation.

Read [the next-session handoff](../handoffs/windows-next-session.md) first.
Establish checkout identity (research branch containing task 0012's publication), exact application
identity and native Windows x64 environment. Start with disposable cube PMX/
deck capture and explicitly specified engineering definitions, then save/reopen,
undo/redo/history regeneration. Preserve inputs; use existing capture manifest
and gateways only when the actual release supports them. Private models stay
outside Git. Repeat existing portable PMX/core/data probes as tools allow.

Acceptance for the first checkpoint: producer/input/output hashes, expected vs
observed mesh/units/definition values, Windows readback and history outcomes,
commands/route and failures retained in reports and STATUS. Unsupported or
unrun cases stay open. Solver/results and CAD meshing are separate follow-ups
requiring actual pinned tool identity; no silent replacement or parity claim.

Targets: Windows x64, Linux x64, Linux ARM64 and Apple M-series macOS ARM64;
Intel Macs and 32-bit x86 excluded. No production refactoring, new default
schema/frontend, F001 implementation, integration, commit/push or upstream
communication follows from preparing this handoff.
