# B010 — Concurrent CAD native stages are not tracked by the stop method

Discovered in the C3 source audit, 9 November 2026. Original-code finding;
runtime kill behavior of every concurrent stage remains unverified. Deferred
under D061 until the post-parity correctness increment.

`PrePoMax/Common/ExecutableJobRunner.cs` stores the job used by `Run` in
`_executableJob`. `RunConcurrently` creates local `ExecutableJob` instances in
its parallel loop without storing them there. `IsRunning` and `Kill` consult
only `_executableJob`. `Controller.StopExecutableJob` delegates to that `Kill`.

C3 exposes the same original stop path. It must not be described as proven
cancellation for concurrent CAD import/visualization stages. A later fix should
track the active jobs, stop all requested processes with bounded drains, retain
logs/statuses and cover partial import and cleanup behavior without changing
engineering algorithms. Existing process-boundary timeout/kill tests do not
establish this Controller-level coverage.
