# Task 0087 — Native C3D10 static calculations

Authorized 6 November 2026: the maintainer clarifies that IDENTICAL PrePoMax
3.0.0 functionality includes all mesh types and calculations, with unavailable
solvers the sole exception, and requests two more tasks. Preview-only features
are intermediate delivery steps, never accepted reductions of the final scope.

Separate the original PrePoMax measurement discrepancy from CalculiX's own
C3D10 formulation. Extend the shared original deck/result transport for C3D10,
then run native analytical straight and curved quadratic fixtures, including
free unknowns, stress, reactions and negative-Jacobian failure. Do not modify
original quadrature, expectations, tolerances or solver sources. Retain the
measurement failure and pyramid classifier failure explicitly.

Keep D057 original PMX compatibility, D058 hosted hold, D059 deferred x64 and
all unexecuted functionality/platform/release acceptance open. Publish normally
to origin/research/native-feasibility with CI skipped.

Implementation and source Mac/Linux ARM64 verification are complete within the
specified increment. Implementation `6609d7d4` is pushed/remote-verified with
CI skipped. The copied current app passes both quadratic viewports and affected
linear/PMX workflows. Actual numerical evidence, original Windows solver
comparison, desktop checks, remaining gates and publication/candidate closeout
are in [the report](../reports/quadratic-native-static.md) and its receipt.
