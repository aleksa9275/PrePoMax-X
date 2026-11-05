# Task 0061 — CAD part scene identity

Compose a rendering DTO from independently decoded original VIS parts.
Preserve each part's source node, triangle, face and edge IDs and CAD
measurements. Keep coincident nodes in separate parts distinct and
generate only renderer IDs for the combined VTK grid. Verify duplicate
source IDs across parts against the original reference outputs.

[Verification](../reports/multipart-cad-preview.md).
