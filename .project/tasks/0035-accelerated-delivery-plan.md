# Task 0035 — Accelerated installable-product plan

2 November 2026. Maintainer confirms native installable software as the main goal,
treats Code_Aster as useful but unnecessary, and requests faster delivery with
less repetitive testing while retaining cross-platform checks and bug tracing.

Completed: shortened [conclusions](../reports/prepomac-evaluation.md), retained the
detailed audit, and prepared the [delivery plan](../proposals/accelerated-native-delivery.md).
The plan brings desktop/installer integration forward, prioritizes CalculiX,
and defines changed-area checks, platform milestones and reproducible bug records.
Current test guidance records this lighter cadence for continued local work.

No application, CI or runner changes are implemented in this planning task.
Existing heavy CI remains until the first implementation step. Frontend, default
format, native solver version/profile and numerical changes remain explicit
decisions. Preserve both correctness failures/tetra gate and final parity/release
requirements. No commit/push/contact/integration/publication; changes stay local.
