# Phase C1 — original-code UI foundation

8 November 2026. C1's representative workflow is implemented: open an original
PMX, render/pick its mesh, edit an existing material using original property
classes, undo/redo, save and reopen. This is the UI foundation milestone, not
full Phase C, full material-form parity or a new installer candidate.

## Framework and reuse

The working implementation uses the existing pinned **Qt 6/PyQt6 + native VTK**
with **.NET owning the application and original Controller**. Python.NET exposes
those same objects to the widget layer in process. This is the C1 technical
framework choice based on demonstrated reuse (D062); no duplicate Python model,
engineering algorithms, deck writer, PMX format or interprocess model copy was
introduced. The earlier Qt/Python preview is retained unchanged until this host
supersedes its workflows.

All eleven original material view classes compile from their original paths.
Their property descriptors, units/equation converters, enum choices, descriptions,
read-only state, dynamic visibility, setters and original data points drive the
portable editor. The original `FrmMaterial.ShowMaterial` view construction and
`Add` material construction/validation were moved into a small shared
`MaterialEditor`; the Windows form calls the same methods. The original
case-insensitive name check likewise has one shared implementation. Original
sources remain C# 7.3/net48 compatible. No validation/tolerance was relaxed.

The editor clones a draft through the restricted Phase B persistence boundary.
Cancel and invalid acceptance preserve the live model. Acceptance invokes the
original `ReplaceMaterialCommand`; unchanged acceptance records no command.
Undo/redo availability comes from the original history callback. PMX saving is
the original Controller path with the unchanged explicit type allowlist.

The viewport consumes original Controller actor coordinates, IDs and original
surface topology. Mac reuses the existing VTK-owned Cocoa child NSView adapter;
Linux/Windows use a small Qt native VTK interactor adapter. C1 uses no copied
framebuffer transport. Native VTK provides the hit coordinate; original selection
code resolves the IDs with world precision derived from display pixels. Selection
is highlighted. Original Controller camera get/set/rotate callbacks reach VTK.

## Verification

Final receipts and images are under `/private/tmp/prepomaxx-c1`; the small checked
in [receipt](phase-c1-ui-verification.json) records hashes and outstanding gates.

| Check | Actual outcome |
|---|---|
| Mac ARM64 original-property workflow | 20 checks passed |
| Mac native Cocoa display workflow | 18 checks passed; Retina scale 2 |
| Linux ARM64 original-property workflow | 20 checks passed |
| Linux native X11 VTK/Qt workflow under Xvfb | 18 checks passed; scale 1; supplemental virtual-display evidence |
| Original Windows 3.0.0 via isolated CrossOver bottle | final GUI-edited PMX opened, saved and exported; deck content identical apart from CRLF/LF |
| Native readback of original Windows resave | eight nodes, one element and edited modulus retained |
| All eleven original C# assemblies, C# 7.3/net48 compile only | passed |
| Focused Controller/persistence regression | nine stages passed, including 20 persistence checks and native picked-selection replay |
| `python3 X/Checks/check.py --area ui` | passed source/syntax/build checks; its no-profile runtime checks remain explicitly pending |

GUI checks dispatch synthetic native Cocoa NSWindow events on Mac and Qt events
on Linux. They cover element and face-node ID picks, selection highlight, camera
drag and original Controller camera callbacks, actual screen pixels, original
invalid-value rejection/cancel/unit conversion, undo/redo, PMX save/reopen and
resize/DPI. These are not human input or all-target GUI acceptance. Property
checks additionally cover equations, temperature table cells, dynamic visibility,
case-insensitive name collisions, draft isolation and unchanged acceptance.

Initial Mac sandbox launch could not access a display; normal local-display
verification succeeded outside that sandbox. Initial Linux GUI attempts exposed
a Qt method-name collision and missing X11 dependencies/default offscreen
platform. The C1 adapter/test-image extension resolves them; final Linux checks
run with `QT_QPA_PLATFORM=xcb`. A trackball-style VTK event consumer also exposed
why clicks belong at the widget boundary; both final adapters distinguish clicks
from drags there. No failed assertion was weakened. VTK 9.5.2, PyQt6 6.10.0,
Qt 6.10.2 and Python.NET 3.1.0 remain pinned.

## Boundaries and next milestone

C1 edits existing material properties and existing temperature/plastic table
cells, preserving other project state. Creation/removal/reordering of material
properties, table-row changes, temperature switching and the complete original
material/library forms remain C2 work. The original form family is therefore not
marked C; only Open, Save and ReplaceMaterial commands gain C in the inventory.

C2 connects the full model tree, remaining original form/property behaviour,
selection/set authoring, materials/sections/interactions and analysis definitions.
C3 connects geometry/meshing. C4 connects jobs/results and completes viewport
symbols/annotations, contours/legends, animation and screenshots. C5 completes
remaining application/automation integration and audits parity. C1 opens the
model/geometry view of a PMX containing results; its result data remains preserved.

Native Windows x64, deferred Linux x64, physical Linux desktop/GPU and Wayland,
human input/focus/DPI matrices, full PMX/feature/mesher/solver coverage, production
CLI/Python/RPC/MCP integration, installers/signing and release acceptance remain
open. CrossOver is original-app reference evidence, not native Windows acceptance.
No native mesher/solver version changed. Established Phase A/B engineering
results remain; C1 changes no engineering algorithm and did not rerun all backend
matrices. The two original D029 failures and the D061 correctness backlog remain
open unchanged. Hosted CI was not used.

[Usage and reproduction](../../X/UI/README.md).
