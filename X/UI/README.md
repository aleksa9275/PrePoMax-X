# Original-Controller desktop foundation (Phase C1)

This host embeds the existing pinned CPython/PyQt6/VTK runtime in the .NET 10
application, on the main thread. Qt builds widgets and native VTK draws the scene.
Python.NET exposes the **same live original Controller and model objects** to the
widgets. There is no model/deck/PMX translation, IPC model replica or second
engineering implementation. The retained `X/Desktop` preview is unchanged.

The C1 implementation choice is Qt 6 / PyQt6 plus native VTK, supported by the
working reuse demonstration. Material view classes and data points compile from
the original PrePoMax project. `MaterialEditor` contains the original form's
view construction and validation, called by both forms. `PropertySheet` reads
original .NET descriptors, converters, choices, read-only flags and dynamic
visibility. Drafts are isolated with the restricted Phase B serializer; acceptance
calls the original `ReplaceMaterialCommand` and history.

## Run

Use the explicit CPython 3.12 profile described in
[the Controller README](../Controller/README.md). Its module directories must
contain the existing target-specific `X/Desktop/requirements-*.txt` pins:
VTK 9.5.2, PyQt6 6.10.0 and Qt 6.10.2. No runtime version is selected from PATH.
Python.NET 3.1.0 is supplied by the managed project. No additional Python wheel
is required to import the already embedded CLR.

```sh
python3 X/UI/run.py --python-profile /absolute/python.json \
  --work-directory /absolute/session-directory /absolute/project.pmx
```

`--feed /absolute/offline-feed` selects an offline NuGet source. `--no-build`
uses the existing Release output. Start without a project to use Open. Use a
separate session directory; this development host does not load/save installed
application preferences. It is one document per process.

Open original PMX; switch Model/Geometry; fit, rotate, pan and zoom; pick an
element, face nodes or a node; double-click an existing material to edit its
name, description, scalar properties or existing temperature/plastic table
cells. Enter units/equations using the original converters. Cancel discards the
draft. Save/Save As and Undo/Redo use original commands and PMX persistence.
The original command callback controls undo/redo availability. Close/Open
prompts before discarding edits.

C1 does not yet provide material/property creation/removal, table row topology
changes, temperature-dependence switching, the remaining model editors, full
original viewport symbols/annotations/results/animation or production
CLI/RPC/MCP integration. All remain required by D060. Original form families
are not marked complete from this demonstration.

## Viewport

The Mac adapter reuses `X/Desktop/native_cocoa.py`: VTK owns a child NSView and
receives forwarded Qt events at device-pixel resolution. Windows/Linux use the
native QVTK interactor adapter in `qt_viewport.py`. Clicks are distinguished from
drags at the widget boundary; VTK's camera style cannot consume selection events.
No framebuffer-copy bridge is used by C1. Points/connectivity/IDs and surface
triangulation come from original Controller actor data and original topology
code. The VTK picker supplies world coordinates; original selection code
resolves IDs and retains its original precision rules. Selected IDs are shown
and highlighted. Original Controller view get/set/rotate methods reach the real
VTK camera.

C1 displays model/geometry when opening a PMX containing results; original result
state is preserved in the project. Results presentation is the C4 milestone.
Only the C1 geometry presentation is implemented; this is not full `vtkControl`
parity or a replacement installer candidate.

## Verify

```sh
python3 X/UI/verify-ui.py --output /absolute/check.json \
  --python-profile /absolute/python.json --gui --feed /absolute/offline-feed
```

`python3 X/Checks/check.py --area ui` runs source/syntax/build checks; runtime
checks are explicitly pending without a supplied Python profile. `--gui`
requires a display. The local Linux test image extension is
`Containerfile.checks`; run under `xvfb-run` with `QT_QPA_PLATFORM=xcb` for
supplemental X11/software-renderer evidence. This is not physical desktop,
Wayland/GPU or native Windows acceptance.

[Milestone report](../../.project/reports/phase-c1-ui-foundation.md) records actual
checks, original-app comparison and remaining work.
