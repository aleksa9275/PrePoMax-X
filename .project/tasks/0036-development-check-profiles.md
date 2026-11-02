# Task 0036 — Start accelerated delivery with check profiles

2 November 2026. Maintainer accepts the accelerated plan and requests starting.
Implement its first bounded increment: current-source/affected-area checks,
explicit compatibility replay, compact diagnostic manifest and CI separation.
Reuse existing engineering tests and package caches. Do not change algorithms,
tolerances, native solver profiles or frontend/format policy; preserve all prior
uncommitted work and both correctness failures/tetra gate. No commit/push.

Initial Mac ARM64 current-results baseline passes in 6.70 seconds. Prioritize
avoiding unnecessary suite/pin repetition rather than introducing a speculative
compiled-output cache. Existing verifiers keep fresh isolated builds and execute
their tests each run. Full historical checks remain available explicitly.

## Outcome

Changed: [X/Checks](../../X/Checks/README.md) supplies fast/current and explicit
compatibility profiles using unchanged existing verifiers; logs/leaf results and
compact manifests retain source/tool/host identity and dirty-code reproductions.
CI prepares four current-source checks instead of twelve historical/current runs,
keeps compatibility as an optional manual milestone job, and caches pinned
package archives. Source/config pushes conservatively run current CI; local area
selection is explicit. Documentation pushes skip these jobs.

Checked: seven focused orchestration regressions; native Mac ARM64 fast all four
suites (43.356 s); results guards plus all three source pins (39.448 s); final
manifest-field change rerun with results (6.491 s including runner). Local YAML/
template/profile checks and whitespace checks pass. Existing engineering tests,
numerical tolerances and both failures/tetra gate are unchanged.
[Compact verification record](../reports/development-check-profiles.json).

Open: no new Linux/Windows or hosted CI acceptance. Build outputs remain fresh
per verifier; measured checks already fit the target, so additional compiled-output
caching is deferred. Optional CI compatibility status is not a release pass;
require an actual successful run for any compatibility claim. Full diagnostics
remain in ignored local X/Checks/artifacts directories; compact evidence is tracked.

Next: bounded native-VTK host/package proof and original native CPU CalculiX
build, converging on one real user workflow. No commit/push/integration performed.
