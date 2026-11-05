# Task 0060 — Multi-part CAD conversion

Extend the checked original CAD command boundary to convert each BREP
emitted by one STEP/BREP split. Keep the single-part API for existing
callers. Bound part count and combined VIS size. Verify repeatable
two-part output with the original 3.0.0 tool and reject partial failure.

[Verification](../reports/multipart-cad-preview.md).
