# Original PrePoMax NetgenMesher source

Recovered 5 November 2026 from the newly public
[PrePoMax/NetgenMesher](https://github.com/PrePoMax/NetgenMesher) repository,
revision `c5ecb0ba3782b91649e06823e858480f6fe33aeb`; re-pinned 23 November 2026 for PrePoMax
3.0.2 to `01e30ce04f846bd10b0e9a04fcb97a2fa52404bf` (one file: `libsrc/occ/occgeom.cpp`, the extend-face
split surface rebuilt at zero offset). All 517 upstream files are retained unchanged under `src/`, including the original
Windows project files and license. `source-manifest.json` pins every byte;
the parent source verifier checks the manifest and complete inventory.

This includes the custom NetGenMesher command wrapper and modified Netgen
5.3.1 port to OCCT 8.0.1. It resolves the earlier inability to locate this
implementation. The released Windows executable/library correspondence still
needs a matching Windows rebuild; the revision label alone does not prove it.
The upstream Netgen root license is LGPL 2.1. The existing distribution's
license inventory identifies its command wrapper as GPL 3; preserve both scopes.

Local portability changes live in `patches/` and apply only to a disposable
build copy. They conditionalize the Windows startup headers and supply the
original exporter's MSVC path-helper interface on POSIX. The small C++17
adapter uses native filesystem paths, bounds its copies and preserves output
stem/suffix naming. No CAD or meshing algorithm is replaced.

[Build adapter](../../../../X/Build/NativeCad/README.md) ·
[Verification](../../../../.project/reports/native-cad-meshing.md).
