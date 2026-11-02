# Task 0034 — Detailed PrePoMac evaluation

2026-11-02, Europe/Belgrade. Maintainer requests a detailed evaluation of
PrePoMac against PrePoMax-X's solver, UI/rendering, Linux and delivery ideas,
including Code_Aster and whether CalculiX is restricted to SPOOLES. A Linux VM
on Mac is acceptable to consider if it improves solver performance. This expands
the execution architectures to evaluate; it does not select a production worker,
backend, default, renderer, frontend or serializer.

Inspect a pinned separate source checkout and primary dependency sources. Record
concrete code paths, capability/translation limits, validation quality, platform
and packaging support, maintainability and reusable work. Perform bounded
isolated diagnostics where useful; distinguish them from whole-app, GUI and
numerical tests. Preserve all existing changes and both correctness failures/
tetra gate. No third-party installation into the project, public contact, commit,
push, integration or release is requested.

Deliverable: [detailed report](../reports/prepomac-evaluation.md) with retained
source fingerprints and reproducible review diagnostics. Keep the existing
four-target desktop objective and normal maintainer publication policy.

Completed within review scope: exact source/release pin fb5a89db (v3.0-mac.4),
actual ZIP checksum and bundled ARM64 CalculiX 2.23 inspection, 40 source hashes,
Mac exact-method diagnostics, analytical-formula/syntax/path checks and live
release/CI/package metadata. The report distinguishes source findings from
author claims and proposed changes. Local Linux execution was unavailable after
Podman forwarding/restart failure; cleanup stopped the VM. No full application,
GUI, numerical solve or performance acceptance is claimed. Code_Aster's limited
translation is not complete CalculiX parity, and SPOOLES-only packaging does not
prove other CalculiX backends impossible. No implementation is adopted; changes
remain uncommitted.
