# Task 0014 — Windows closeout, publication and MacBook handoff

Completed publication closeout on Mac, 2026-10-16: bundle SHA-256
4e6ea00ce6a6a961f35bb7afc7e24da39fe9d99186be4cea7c0f6c5b727c070d verified,
clean f1e757f1 checkout fast-forwarded to ac51fc77449da26d9c25ddedd924feda2a55e7db.
Normal push and subsequent ls-remote confirm that exact origin research SHA.
Push pipeline #2956616374 passes research job #17244123734 and new shared-core
job #17244123735 on native Linux x64; [report](../reports/shared-core-data-slice.md).
Publication exception is complete. New task 0015 implementation is uncommitted.
Historical Windows credential limitations and transfer instructions follow.

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
