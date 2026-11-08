# Original-code desktop host — C1/C2

The .NET 10 application owns the original Controller/model. Embedded
Python.NET exposes those same live C# objects to a thin Qt/PyQt6 widget layer;
native VTK renders original Controller actor data. There is no second model,
engineering implementation, deck writer or PMX format. The retained `X/Desktop`
preview remains unchanged.

## Run

Supply the explicit CPython 3.12 profile described in
[the Controller README](../Controller/README.md), with the existing target-specific
`X/Desktop/requirements-*.txt` wheels. Pins remain VTK 9.5.2, PyQt6 6.10.0,
Qt 6.10.2 and Python.NET 3.1.0. No Python wheel is needed to load a second CLR;
.NET already hosts it.

```sh
python3 X/UI/run.py --python-profile /absolute/python.json \
  --work-directory /absolute/session-directory /absolute/project.pmx
```

`--feed /absolute/offline-feed` selects an offline NuGet source. `--no-build`
uses existing Release output. Omit the project for an empty window. This is a
single-document development host with isolated session settings, not an installed
application/package candidate.

## Authoring

- **New** chooses original model space/units; **Import mesh** invokes the original
  importer. Open/Save/Save As preserve original PMX through the Phase B allowlist.
- Double-click a collection to create, or an item to edit. Right-click for
  duplicate/remove, activation, ordering, folders, grouping and ungrouping where
  the original collection supports them. Steps have their original move command.
- The tree exposes model properties, parameters, mesh sets/surfaces, reference
  points, coordinate systems, materials, sections, constraints, interactions,
  contacts, distributions, amplitudes, initial conditions, steps and step items.
- The original factories determine available types and regions for each step and
  model space. The original view descriptors control fields, choices, visibility,
  units/equations and validation. The form's original apply code dispatches the
  original commands. Undo/redo and saved-state replay remain original.
- Model editors stay open while picking in the viewport. Other document edits
  are disabled until the draft is accepted/cancelled. Pick nodes, face nodes,
  elements, surfaces or parts, then **Use picked selection**. Shift adds, Ctrl/
  Command subtracts, and Shift+Ctrl/Command intersects using original operations.
  Sets also accept explicit IDs. Point editors use an original mesh node's
  coordinates. Coordinate systems expose their individual selection regions.
- Materials support original property add/remove/order, temperature switching,
  existing/new data rows, clipboard TSV and original equation/unit conversion.
  The same table adapter serves amplitude/contact data and direct modal damping.
- Parameters use the original table evaluator/name rules and one atomic original
  SetParameters command. Solution controls preserve the original confirmation.
  File, color, flag and damping editor metadata dispatch to Qt widgets.

Cancel discards the isolated draft. Only values changed in a widget are written,
so a stale computed magnitude cannot overwrite an edited component. Original
warnings/decisions use the original MessageBoxes policy and a Qt presenter; the
original unattended-thread refusal remains in effect.

## Shared source

Original property/data classes compile under their original assembly names and
paths. `MaterialEditor` and `SurfaceInteractionEditor` hold original form
construction/validation shared with the Windows forms. The unused Windows parent
argument of `ViewNodeSet` stays available in its original project's small Windows
partial. Original C# remains net48/C# 7.3 compatible.

`FormSourceGen` uses the SDK's Roslyn assemblies to extract complete reviewed
original members. `generate-forms.py` produces `OriginalFormRules.g.cs`: original
view setters, factories, applicability rules, validations, parameter evaluation,
control confirmation and command dispatch. Rewrites substitute UI-neutral
choice/property data and remove only presentation lifetime/layout operations.
The live model is never temporarily hidden/internalized; drafts retain original
selection graphs instead of the Windows numeric-selector sentinel. Source
fingerprints and `--check` detect upstream changes; this is generated reuse, not
an independently maintained implementation of the rules.

```sh
dotnet build X/UI/FormSourceGen/FormSourceGen.csproj -c Release
python3 X/UI/generate-forms.py --check
```

Use the generator without `--check` after reviewing an upstream change.

## Viewport and verification

Mac reuses the VTK-owned native Cocoa child view. Windows/Linux use QVTK's native
interactor with widget-level click/drag separation. C1 uses no framebuffer-copy
bridge. Native VTK supplies hit coordinates; original selection resolves IDs.
Original Controller highlight actors, topology and camera callbacks drive the
scene. PMX results remain preserved; results presentation belongs to C4.

```sh
python3 X/UI/verify-ui.py --output /absolute/check.json \
  --python-profile /absolute/python.json --gui --feed /absolute/offline-feed
```

This checks generated-source consistency, C1 regressions, C2 authoring and, with
`--gui`, actual display/widget workflows. `python3 X/Checks/check.py --area ui`
runs source/syntax/build checks; runtime checks remain explicitly pending without
an explicit profile. Linux under `xvfb-run`/`QT_QPA_PLATFORM=xcb` is supplemental
virtual-display evidence. Physical Linux/GPU/Wayland, human input and native
Windows execution remain pending.

C3 connects geometry/meshing tools; C4 connects jobs/results and full viewport
symbols/annotations/contours/animation; C5 finishes remaining application,
automation and UI parity. Original form conveniences such as curve plotting,
material libraries, complete selection-tool/keyboard/focus parity and application
preferences are not inferred complete from these core authoring adapters.
The full D060 scope and all four-target/installer/signing gates remain required.

[C1 report](../../.project/reports/phase-c1-ui-foundation.md) ·
[C2 report](../../.project/reports/phase-c2-model-authoring.md).
