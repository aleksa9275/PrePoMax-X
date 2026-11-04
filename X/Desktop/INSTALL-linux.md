# PrePoMax-X Linux desktop preview

This internal preview opens a bounded set of INP meshes and completed static
C3D8 FRD results. It includes a static cube example and the native
CalculiX 2.22/SPOOLES solver. When bundled with the optional PMX tools,
**Open static PMX…** supports the checked result-free 3.0.0 solid subset.
Edit the two supported values, save a new copy, reopen it and run the analysis.

Extract the archive for your architecture into a folder you can write to,
then launch the executable inside it. Keep the entire extracted folder
together, including `_internal`.

    tar -xzf PrePoMax-X-Preview-linux-arm64.tar.gz
    ./PrePoMax-X-Preview/PrePoMax-X-Preview

Use a Linux desktop with X11 or XWayland and working OpenGL/Mesa. The build
environment is Ubuntu 24.04; other distributions and older releases have not
been qualified. The bundled app includes Python, Qt, VTK, the .NET hosts and
the solver. The system still supplies glibc, graphics/display and supporting
libraries. See the repository's `X/Build/README.md` for the Ubuntu dependency
setup. You do not need to install Python, .NET or CalculiX to launch the app.

To uninstall, close the preview and remove its extracted folder. The app's
jobs are stored in the Qt app data directory, usually
`${XDG_DATA_HOME:-$HOME/.local/share}/PrePoMax-X/PrePoMax-X Preview/jobs`.
The app folder may contain job inputs and results: move or back them up first
if you want to remove that data too. Uninstalling does not remove saved PMX
files or input models from other folders.
