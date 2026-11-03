# PrePoMax-X local preview — Apple Silicon

This internal preview is ad-hoc signed, without Developer ID or notarization.
It includes native Python/Qt/VTK, self-contained .NET readers/job host and the
CalculiX 2.22/SPOOLES research CPU build with its runtime libraries. It requires
an Apple Silicon Mac. The current tested OS is macOS 26.7.1; older versions have
not been verified. No external Python, .NET SDK or Homebrew installation is needed
to run the bundled workflow. Build tools are only needed to rebuild it.

## Install and try

1. Open the DMG and drag PrePoMax-X-Viewport.app to Applications (or a writable
   folder of your choice). Eject the DMG and open the copied app.
2. If macOS blocks this unnotarized app, review its origin and checksum. Apple's
   documented per-app route is System Settings → Privacy & Security → Open Anyway
   after the attempted launch. This must be your own decision. Do not disable
   Gatekeeper or remove quarantine attributes globally.
3. Click **Solve example**. The original C# services generate a deck, run native
   CalculiX, and load the completed FRD. Choose a contour component, Fit, click
   for original FEM IDs/values, or drag to rotate.
4. Click **Configure…** (or double-click a model-tree item) to edit units,
   isotropic elastic materials, solid sections, displacement supports, forces
   per node, static increments and requested histories. **Validate** checks the
   definition without running a solver; **Apply**, then **Run analysis** submits it.
   For example, change Young's modulus to 105 GPa and the axial force to 50 N per
   node. The cube then carries 200 N and has four times the original displacement.
5. To configure your own supported mesh, use **Open INP / FRD** and select an INP.
   Choose its units explicitly and assign materials/supports/loads to its imported
   named sets. Blank displacement components are free; zero fixes a component.
   Forces are applied to each node in the chosen set. This preview imports mesh
   data, not existing INP analysis definitions or arbitrary CalculiX analyses.
6. **Cancel** requests cancellation through the job host. **Job files** opens the
   workspace with frozen submitted inputs and a solve folder containing the
   generated deck, solver output, errors and outcome. Closing
   during a job requests cancellation and waits for cleanup before exiting.

Jobs are stored in a new unique folder under Qt's per-user AppLocalDataLocation
for PrePoMax-X Preview; **Job files** reveals the exact location. No input file is
overwritten. The initial CPU profile uses one thread, matching the verified run;
this preview does not introduce a production thread/backend default.

## Scope and removal

This is a bounded static-solid editor and experimental viewport. The frame-copy
viewer remains default; the native Cocoa transport is opt-in. Model edits live
in this session: **project save/reopen is not available**, and discarding edits or
quitting loses the editable session. Submitted job inputs/results remain on disk.
Full PMX editing/save/history, new or picked-set creation, CAD, meshing, other analyses/backends and final
viewport performance are not delivered. It is not the complete PrePoMax product.

Follow **UNINSTALL-AND-RESET.md** beside this file for full removal: app copies,
job data, preferences/cache, mounted images, DMG files and generated test folders.
Deleting the DMG alone does not uninstall the copied app. No privileged installer
or background service is installed. A second Mac/clean macOS test and downloaded
Gatekeeper flow remain separate from the local copied-app test.

Source, build records and pending source/license redistribution closure:
https://gitlab.com/aleksa9275/pre-po-max-x/-/tree/research/native-feasibility
This package is for internal local testing; public release packaging is pending.

Apple app-opening instructions: https://support.apple.com/en-gb/102445
Apple container runs Linux containers, not macOS desktop apps:
https://github.com/apple/container
