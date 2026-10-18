# Task 0025 — Research the exact PrePoMax solver and cross-platform identity

Later policy: task 0026/D042 narrow the complete-backend requirement below.
Panua machine-bound licensing is excluded; a new alternative is needed only
if omission of PARDISO cripples functionality. See the
[assessment](../reports/without-pardiso-assessment.md); this task's exact identity
findings remain valid, but its all-backend condition is historical.

2026-10-18. Maintainer explicitly requires the same complete solver software as
PrePoMax, adjusted only for cross-platform use, and requests research/report here.
Research only: identify actual PrePoMax distributed solver binaries (including
3.0 RC2 where available), publisher, source/patch/build/backend/runtime/ABI chain,
existing native build instructions, required four-platform constraints and exact
remaining gaps. Distinguish stock source, binary identity, source identity,
backend coverage and measured numerical equivalence; do not infer a different
solver merely from a different default Makefile. Preserve all current local work.

Use primary sources and retained binary fingerprints; recover/check authoritative
archives/source/build metadata if useful. Do not contact anyone, publish, change
a solver/backend/default/numerical policy or claim native acceptance from source
availability. Record a concise recommendation and actionable evidence-backed
recovery/build/parity route with uncertainties and targeted maintainer questions
if an actual source/build fact is unavailable. Leave changes uncommitted.

Status: research complete within scope. Downloaded official RC2 and CalculiX
Windows archives; exact executable and all five DLLs match the previously pinned
reference, and README files match. Identified original provider and canonical
source archive, PARDISO GUI default, additional backends and source/build gaps.
All six choices pass seven unchanged analytical checks and native-Windows data
comparisons on the synthetic cube through the existing CrossOver bottle. This
is a compatibility experiment, not native ARM or full solver acceptance.

Native ARM64 cannot currently reproduce the complete Intel MKL/PARDISO dependency
stack from identified supported distributions. Exact PaStiX/Scotch revision,
flags/ABI/transitive build recipes remain unproven; a historically pinned
cudaless fork is a lead, not accepted matching source. Same-binary compatibility/
worker routes and full native builds are distinguished without selecting an
architecture or substituting a backend. No contacts/publication/production
changes occur. [Research report](../reports/exact-solver-provenance.md) and
[retained evidence](../reports/exact-solver-provenance/verification.json).
All changes remain uncommitted; existing correctness/release gates remain.

2026-10-18 follow-up: checked implementation-source availability. Exact Intel
MKL PARDISO is not publicly available source to port; CalculiX pardiso.c is a
wrapper. Panua-Pardiso vendor advertises native ARM support but is a distinct
licensed implementation, not the original MKL engine. Added sourced distinction
and possible vendor/API/distribution investigation to the report. No production
or numerical policy change is implied.
