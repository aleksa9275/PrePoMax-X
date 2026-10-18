# Task 0026 — Functionality and performance without PARDISO

2026-10-18. Maintainer rejects Panua's machine-fingerprint licensing and requests
web research, including their PrePoMax forum discussion, before our own later
comparisons. A new alternative is needed only if omitting PARDISO cripples useful
functionality. This narrows task 0025/D041's requirement to reproduce every backend:
preserve CalculiX engineering capabilities and investigate its existing open
backends before treating proprietary Intel MKL parity as a release prerequisite.

Scope: primary forum observations, official CalculiX 2.22 manual, read-only
inspection of recovered unchanged source; distinguish speed, memory, correctness,
analysis coverage and actual backend dispatch. No solver build, benchmark,
default/environment change, third-party replacement, external contact or publication.
Preserve all existing uncommitted implementation and correctness/release gates.

## Completion

Completed sourced [assessment](../reports/without-pardiso-assessment.md).
Located the relevant September 2024 topic under forum username `aleksa`; the
requested `aleksa9275` public user-actions endpoint returned HTTP 404. Do not
represent that endpoint as verified account alias metadata. Topic metadata and
post dates corroborate the public discussion; no private models downloaded.

Recommendation: do not start a PARDISO port or new-backend integration now. Assess
existing SPOOLES and PaStiX against representative correctness/capacity cases later.
There is no identified PARDISO-exclusive analysis category in the reviewed paths;
native reliability, capacity and acceptable performance remain unproven. PaStiX
precision and modal/buckling dispatch are explicit follow-up issues. No numerical
acceptance follows from forum evidence, source inspection or the earlier cube.

Verification: cited public pages/manual read, relevant source branches inspected,
documentation links checked and git diff whitespace check performed. No numerical
tests run in this research-only increment; all changes remain uncommitted.
