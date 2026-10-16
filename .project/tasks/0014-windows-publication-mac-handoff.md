# Task 0014 — Windows closeout, publication and MacBook handoff

2026-10-16: maintainer explicitly requests committing/pushing the reviewed work,
finishing useful remaining Windows checks and providing immediate MacBook
continuation. Destination is origin/research/native-feasibility only; no force,
upstream write, x/main integration, frontend/serializer or F001 decision.

Windows engineering closeout is complete within this increment: the new native
C++17 compiler pass succeeds in default and contraction-off modes (13 vectors,
17 native/seven managed checks, 1,728 count comparisons); the shared library
verifier again passes 25 mapping checks and nine CLI controls. The generic
upstream Tests ignore rule was corrected locally so all new regression sources
will be published. Artifacts are excluded from verifier tool fingerprints.
Portable LLVM-MinGW stays in the disposable workspace, not the repository.

Next entry point: [MacBook handoff](../handoffs/macbook-next-session.md).
It contains retrieval/fallback-bundle commands, native ARM64 SDK verification,
cached Podman image/VM identities and exact offline Linux ARM64 commands,
expected counts/evidence paths, private-transfer manifest identity and a bounded
next implementation candidate. No private fixture is needed to start those runs.

Publication caveat: at preparation time, ordinary Git push cannot obtain
credentials because its MSYS helper and direct Windows Credential Manager call
are denied by the execution sandbox. User sign-in was not automated and no
credentials were extracted/stored. Create the reviewed local commit, attempt
the authorized normal push and verify the remote before claiming publication.
If denied, provide a normal-terminal push route and a Git bundle so the
already-authenticated Mac can publish the exact commit. The commit containing
this task is the transfer range after f1e757f1. Only that reviewed range and
closing evidence are covered by this publication authorization.

Remaining native Windows hardlink test needs an ordinary process outside the
sandbox. Full original solution, CAD/UI and broader histories remain separate
acceptance work. Windows-only work needed for this shared-library increment is
finished; switch to MacBook for the next platform runs and bounded build work.
