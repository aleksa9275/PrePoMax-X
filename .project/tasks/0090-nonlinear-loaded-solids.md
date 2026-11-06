# Task 0090 — Nonlinear and distributed-load solid workflows

Authorized 6 November 2026 by the maintainer's request for more progress under
larger functional milestones and the unchanged full-functionality specification.

Connect original geometric nonlinear static controls, isotropic plasticity data,
density, pressure and gravity to the solid model/editor/job/results workflow.
Reuse original engineering objects, unit converters and keyword writers; pressure
uses original element-face identities and original pyramid conversion. Expose
increment selection and equivalent plastic strain through original FRD decoding.
Deliver representative runnable examples and one candidate integration check on
native Mac/Linux ARM64 with pinned original Windows solver comparisons.

Preserve original mathematical algorithms and existing numerical expectations,
D029's known failures, D057 full PMX, D058 hosted hold, D059 deferred x64 and all
other original functionality/four-target/distribution/release requirements.

Completed as one substantial functional milestone. Implementation `630b6ccd` is
published and remote-verified with CI skipped. Native Mac/Linux ARM64 and both
copied Mac viewports complete the combined workflow; the pinned original Windows
solver comparisons, affected engineering suites and representative PMX/solid
regressions pass. B006's inherited quadratic-pyramid wedge-pressure accuracy
check remains explicitly false; original algorithms/tolerances and prior D029
failures remain intact. Current candidate, actual checks/publication/cleanup and
all remaining full-functionality requirements are in
[the report](../reports/nonlinear-loaded-solids.md) and its receipt.
