# Portable CAD scene and desktop VIS inspection

The original VIS reader now carries CAD source edge IDs through the node
and segment merge. Shared segments retain every contributing edge ID. The
existing inspect output has the same decoded hash as task 0053. The
self-contained `PrePoMaxX.InspectVis scene` command projects that data
into a desktop scene with the original triangles, source faces, CAD edge
segments and canonical measurements.

The native preview opens VIS version 2 exports up to 1 MiB through
**Open INP / FRD / VIS**. It draws CAD edges over shaded geometry and maps
triangle picks to source face rows in the model tree. CAD measurements come
from the VIS metadata in the file's declared units. The preview displays
rounded values and keeps the stored values in tooltips. VIS inspection is
read-only. The desktop checks that a refused import preserves an edited INP,
and that switching to FRD or INP restores the corresponding view and controls.
[Original fixture and reference](l-bracket-cad-reference.md).

The L-bracket scene contains 38 nodes, 72 triangles and 45 unique
segments for the original 21 CAD edges. The portable checks compare all
scene nodes, triangles, source face IDs, source edge coverage and measurements.
An alias control assigns one segment to two edge IDs and verifies both
survive. Unsupported-version and missing-tessellation files fail in both
reader modes. macOS ARM64, Linux ARM64 and GitLab Linux x64 each passed all
346 checks with identical inspector and scene hashes. [Linux x64 reader job](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17755041225).

The source desktop regression suite passed 15 tests, and nine build boundary
tests passed. The ad-hoc-signed Mac app launched with a system-only PATH and
used its bundled reader. Both viewports passed all 15 CAD checks and picked
six visible faces, including the concave cylinder. The existing INP example
also passed all 10 solve and result display checks using the bundled native
CalculiX. Its results passed seven analytical checks and an
altered-displacement refusal. The Mac app was built from the pre-commit working tree. The changed
application and build inputs were compared against the published commit.
One temporary Mac test app and both screenshots were retained. Removing
duplicate staging and cache directories reduced its build folder by 2.00 GiB.
[Verification receipt](desktop-vis-geometry-verification.json).

The exact implementation also built and ran as an extracted Linux ARM64
archive in the disposable Ubuntu builder under Xvfb and Mesa. All 14 CAD
checks passed with the same six visible source face picks. The packaged
INP solve, render and analytical checks passed in the same run.

Implementation `0d232799` was pushed and verified on
`origin/research/native-feasibility`. Its x64 reader job passed, but the
combined native x64 job hit its ten-minute limit while downloading
hash-pinned PyQt6 wheels. The archive and installed checks were not reached.
The follow-up CI change extends the job budget to 25 minutes and keeps the
same package, installation and test requirements.
[Initial pipeline #3029587252](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3029587252) ·
[Runner timeout](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17755041224#L995).

Windows part construction and local selection numbering remain in the
Windows reader. The next CAD increment requires a corresponding native
source/build for STEP/BREP import. Native CAD repair and volume meshing,
full 3.0.0 parity, both known correctness failures, the tetrahedron gate
and release acceptance remain open.
