# Responsive CAD import

Task 0059 moves CAD conversion and VIS decoding into a Qt worker thread.
The file dialog and positional STEP/BREP entry points start this worker
and leave the current document visible. Successful decoding publishes
the new scene on the GUI thread. Failure and cancellation preserve the
previous model, mesh bytes and edit state.

The existing Cancel action stops the active import or analysis.
Document replacement, model editing and new analysis starts are disabled
during import. Closing the window requests cancellation and waits for
worker completion before releasing the viewport. A cancellation arriving
after decoding but before scene publication still keeps the old document.
The synchronous programmatic reader entry remains available to its
existing callers.

CAD commands and reader subprocesses run in owned process groups on
macOS and Linux. Cancellation and timeouts kill that group and collect
the subprocess before the workspace is removed. The checked Windows
runtime and original conversion options remain the reference profile.

The macOS desktop suite passed 24 tests. It exercises responsive
timer delivery, cancellation, close during import, failed and successful
replacement, and cancellation after worker completion. The six portable
boundary tests passed on macOS and Linux ARM64. A spawned child heartbeat
stopped after both cancellation and timeout. A real CrossOver console
process was absent from the bottle process list after cancellation.

A real BREP import was cancelled from the Mac window while its event
timer continued to run. The previous scene was preserved, and the
original NetGenMesher process was absent afterward. Two normal replay
runs still produced the exact original L-bracket BREP and VIS bytes.

The ad-hoc-signed Mac package also completed background STEP and BREP
imports through its two viewport transports with a system-only PATH.
It retained the original VIS hash and six visible source face picks.
The packaged native INP solve and its result display passed.
[Verification receipt](responsive-cad-import-verification.json).

The task keeps the existing single-part and input-size limits.
CrossOver reference execution, matching native C++ source recovery,
native CAD execution, both correctness failures, the tetrahedron gate
and all parity and release requirements retain their documented scope.
