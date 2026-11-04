# Task 0048 — Checked desktop Open and Save As for static PMX

Bring the task 0045 shape-checked PMX workflow into the macOS ARM64 preview.
The maintainer will test their own workflow once a fully operational 3.0.0
parity candidate is ready. Notify the maintainer when Developer ID and
notarization require their involvement.

- Open a supported PMX 3.0.0 project through the desktop, show its mesh
  summary, units, material and load, and allow two validated equation edits.
- Save to a new original PMX file. Preserve the source, original IDs and
  unaffected records. Reopen the new file through the same dialog.
- Publish the three record, mesh and deck helpers as self-contained hosts
  in the opt-in package. Verify the copied app without SDKs on PATH.
- Compare the desktop output to the previously verified original-application
  readback. Preserve all full parity, four-target and release gates.

The scope is the existing checked result-free C3D8 shape and two scalar edits.
PMX loading into the viewport and the native solver workflow remains a separate
increment. General model graphs, results, command histories and Linux desktop
packaging remain open.

Completed within this scope on 4 November 2026. The copied ARM64 app
passed the native solver/render checks and both viewport PMX probes.
[Implementation, verification and publication](../reports/desktop-static-pmx.md).
