# B012 — Analysis cancellation can arrive before the child process starts

9 November 2026; original lifecycle finding, deferred under D061. No original
job lifecycle or solver behavior changed in C4.

C4's first cancellation check observed `JobStatus.Running`, immediately called
`Controller.KillJob`, then failed its five-second task-completion check. In the
original `CaeJob/AnalysisJob.cs`, `Submit` publishes Running before entering the
worker; `Kill` can set Killed while `_exe` is null. Starting the child afterward
can therefore miss the stop request. The active-child check now waits for the
controlled helper's ready marker, then verifies actual termination and Killed;
that distinct coverage passes on Mac/Linux ARM64. It is not evidence that the
pre-start window is repaired. The earlier failure/log is retained.

Post-parity: latch cancellation through process initialization and all run
stages; test cancellation before initialization, after spawn, between increments
and during output drains, retaining original run files and final status.
This is separate from B010's concurrent CAD stop tracking.
