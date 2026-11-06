# Native desktop CAD PMX save and reopen

Task 0070's candidate is superseded and pruned after verified tasks 0071–0073.
See [the current candidate and broader editor](pmx-region-assignments.md).

Task 0070 opens the checked single-part original CAD/C3D4 PMX, edits Young's
modulus and positive axial nodal force, saves a new original PMX, reopens it and
runs the native solver. Existing CAD/mesh/result views preserve the model.
With the explicit `--cad-native <runtime>` profile, the saved BREP also supplies
a native geometry preview. Without that profile, the analysis mesh and checked
PMX editing still work and the CAD payload remains preserved in the file.

Use **Open static PMX…**, **Edit PMX…**, save to a new filename, reopen the saved
copy and choose **Run analysis**. Existing destinations and unsupported inputs
are refused. This editor changes only its audited material/force equations;
remeshing and CAD region authoring are disabled for this PMX subset. Creating
and saving arbitrary new native CAD/mesh sessions is still pending.

## Original compatibility and immutable jobs

Save As replaces three independently owned NRBF string records for modulus,
force and force magnitude. It preserves all other graph bytes, including CAD,
meshing settings, named regions and original import history, and preserves the
entire original custom geometry/mesh frame and result-free tail byte for byte.
Both source and edited engineering decks and fresh semantic readback must pass
before a new file is published. The native reader never replays saved commands.

The original Windows app reopened the native-edited CAD PMX, exported its deck
and resaved the project. Portable inspection of that original resave gives equal
CAD BREP/topology, mesh, material, named regions, supports and load semantics.
The original fixture stays unchanged. Every submitted PMX job now freezes the
complete validated source PMX bytes in `inputs/source.pmx` alongside its existing
mesh/definition and identity, so CAD survives after the document is closed.

## Exporter formatting discrepancy and repair

A strict comparison initially found small result differences between the original
exported deck and the reconstructed CAD PMX deck. Original CalNode exports E8
coordinates; the standalone portable mesh writer preserves G17 coordinates.
These differ for this mesh's fractional coordinates. No tolerance was relaxed.

The original CalNode 3D statement is now shared by a mechanically checked helper
in CaeModel, also included once in the original Windows project. The checked CAD
PMX adapter explicitly uses that original node export, while standalone INP/mesh
exports and the existing C3D8 path retain their behavior. This restores the
original CAD PMX export semantics without a new general precision policy.
The native solver then gives **exactly equal decoded nodes, elements, value order
and every result field** for the original-app export and native reconstruction.
Mac and Linux ARM64 also produce identical deck hashes and decoded fields.
The initial mismatch receipt is retained with the final passing comparison.

## Verification and candidate

Mac source desktop, Linux ARM64 and both final copied Mac viewports each pass
18 CAD PMX workflow checks. Both copied-app edited PMX outputs are byte-identical
to the file reopened/resaved by original PrePoMax. The packaged old PMX workflow
passes 17 checks, CAD/region/meshing passes 46, and C3D8 solve/render/picking passes
ten. The native Cocoa CAD screen capture was visually inspected.
[Verification receipt](desktop-cad-pmx-verification.json).

Retained candidate: `/tmp/prepomaxx-task0070-delivery/PrePoMax-X Preview.app`.
Its sibling `Native CAD Preview.command` enables the retained native CAD runtime;
older task 0067/0068 launchers forward to it. All 2421 copied payload file hashes
and ad-hoc signature verify. Source identity names implementation `4d0ee6b3`, with
an empty source patch; Finder files alone set its dirty flag. Seven duplicate
payload directories (4.69 GiB logical bytes), the extracted reference application
and its isolated bottle were pruned. All generated/reference projects, jobs,
evidence, original ZIP and useful native/tool/image caches remain. The user’s
original bottle and installed app/state were unchanged; the test VM is stopped.

Implementation [`4d0ee6b3`](https://gitlab.com/aleksa9275/pre-po-max-x/-/commit/4d0ee6b3a38097e4f34e899f61c4a2aa8c09cca7)
is pushed and remote-verified on the research branch. Closing evidence is a
normal documentation-only follow-up, also pushed with CI skipped.
All four current Mac source suites pass after the formatter extraction; both
known element failures and the tetrahedron gate remain explicit. Thirty-eight
existing desktop tests, twelve analysis ownership/formatter guards and nine build
guards pass. Linux builds/tests use cached images and the hash-verified NRBF
package offline; no hosted CI or Linux x64 run occurs.
Local detailed evidence is `/tmp/prepomaxx-task0070-evidence`; original reference
and diagnosis data are under `/tmp/prepomaxx-task0069-reference` while retained.

Native documents retain explicit part scope even with a single CAD body, so
source identity remains available to picking/region presentation. The legacy
single-part VIS/reference scene contract is unchanged.

The native CAD preview regenerates a display from the saved BREP; it does not
claim exact original VIS tessellation parity. General PMX, new native-session
serialization, multipart/transformed models, arbitrary assignment editing,
embedded results, full command replay, broader analyses, both correctness
failures, quadratic tetrahedra and all four-target/installer/signing/notarization/
release acceptance remain open. D057 original compatibility stays in force;
D058 holds hosted CI and D059 defers Linux x64 to Podman on Windows near finishing.
