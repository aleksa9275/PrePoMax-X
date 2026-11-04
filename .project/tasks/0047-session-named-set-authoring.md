# Task 0047 — Session named set authoring

The maintainer asked to clean up the task 0045 research outputs and proceed.
Task 0045's broader compatibility and desktop persistence gates remain tracked.
This increment builds on the desktop INP static-solid workflow from task 0044.

- Add node and element sets by original mesh IDs. A current mesh pick can seed
  the ID field. The original C# reader validates the combined mesh.
- Keep the authored mesh in the editor session. Expose the sets for section,
  support, load and history assignments and freeze them with submitted jobs.
- Reject invalid IDs and duplicate names, and invalidate old analysis validation
  after a successful edit. A failed edit preserves the current session.
- Verify real Qt controls, original reader validation, and an actual native
  static solve using the new sets. Verify the copied app from a local DMG.

Completed within this scope on 4 November 2026. The ad-hoc local DMG passed
mounted and copied-app verification. Both viewports passed the actual packaged
set, edit and solve workflow. Public release gates are tracked separately.

[Implementation and verification](../reports/session-named-set-authoring.md).
