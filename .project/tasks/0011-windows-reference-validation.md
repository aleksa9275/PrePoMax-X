# Task 0011 — Native Windows reference validation

Status: prepared; Windows execution pending. Handoff written 2026-10-15 after
the maintainer said Windows will be available next session. This record does
not claim a Windows test/capture pass or schedule unattended work.

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
