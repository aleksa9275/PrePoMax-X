# Task 0059 — Responsive CAD import

Run the existing checked CAD conversion and VIS decoding off the GUI
thread. Keep the current document until success and let Cancel and
window closing stop an active import. Prevent concurrent document edits
or analysis starts while conversion is active. Exercise cancellation,
failure, successful import and the original reference bytes.

Retain the explicit CrossOver reference configuration, single emitted
part and size limits, native-source boundary and all existing gates.

[Verification](../reports/responsive-cad-import.md).
