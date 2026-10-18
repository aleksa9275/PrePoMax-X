# Upstream 3.0.0 RC2 sync and implementation impact

2026-10-18, Europe/Belgrade. [Task 0019](../tasks/0019-upstream-3.0.0-rc2-sync.md).
Machine-readable ranges, filenames, immutable commits and native hashes are in
[comparison.json](upstream-rc2/comparison.json). Test outcomes and limits are in
[verification.json](upstream-rc2/verification.json).

## Verified source/release and fork state

The [official downloads page](https://prepomax.fs.um.si/downloads/) lists
3.0.0 RC2 dated **17 October 2026**. The upstream source commit explicitly named
RC2 is [912fb3d0](https://gitlab.com/MatejB/PrePoMax/-/commit/912fb3d08014f246d48bef14d62a2cba0fdf5bb0),
dated 16 October. Its change sets `Globals.ReleaseCandidate` to RC2.
Upstream master is already ten commits beyond that marker, at
[f6273e39](https://gitlab.com/MatejB/PrePoMax/-/commit/f6273e39983e06042ae8b06e9a3dd0f729ea4b91).
`Globals.ReleaseCandidate` remains RC2 there. No Git tags were advertised in
the fetched tag inventory. The downloaded Windows RC2 archive has **not** been
matched to an exact source commit; neither the label nor release date proves
binary/source correspondence.

| Range | Commits | Changed files | Text additions/deletions |
|---|---:|---:|---:|
| Previous de8f7303 → RC2 source marker | 12 | 12 | +608 / -180 |
| RC2 source marker → current upstream master | 10 | 159 | +7579 / -124 |
| Previous de8f7303 → current upstream master | 22 | 168 | +8187 / -304 |

Git rename detection is enabled; range file counts overlap. Binary changes are
listed separately rather than counted as text additions/deletions.

`upstream-sync.py --dry-run` fetched the actual default `master`; normal mode
fast-forwarded the unchecked-out local mirror. The maintainer's sync request
then authorized `git push origin refs/heads/master:refs/heads/master` for exactly
de8f7303 → f6273e39. `git ls-remote origin` independently confirmed master at
f6273e39983e06042ae8b06e9a3dd0f729ea4b91 and research/native-feasibility still at
2f2eca945c8acad0c3b902537f95055e67be6a42. Local mirror comparison with
upstream/master is `0 0`. No upstream write or forced update occurred.

`git merge-tree --write-tree --name-only HEAD f6273e39...` returned exit 0 and
tree bad83a90cd88fcf41617969bf00c1d821e43697c with no conflicts. This is a
Git-object rehearsal only: no merge commit, branch integration or checkout
change. It includes the existing CaeException separation and original Windows
project inclusion. A clean merge establishes textual compatibility only.
The working branch and portable baseline remain unchanged; new replay tooling
and these records are local, uncommitted implementation/evidence changes.

## Required adjustments by owning layer

| Area | Verified upstream change | Consequence for PrePoMax-X |
|---|---|---|
| Current shared slice | All 37 selected sources have identical engineering bytes at both new pins; same mapping vectors | No new engineering patch or baseline/tolerance change is needed for this slice. Existing two boundary adapters suffice. |
| RC2 sweep meshing | `FeModel.ValidateSweepBlockGeometry`, `GetSweepTurnAxis`, `SampleSweepLengths`, `GetLinearFitDeviation` distinguish affine tapers, curved sweeps and poor/last-resort candidates. `SweepBlockValidation` gains unlike-end/quality state; manually selected sources have distinct policy. | Retain the upstream implementation when full model/meshing is ported. Add curved/taper/loft/chamfer/poor-block fixtures against a matching Windows oracle. Existing ThreeBlockMapping tests do not exercise this search. |
| RC2 geometry identity | `VisFileReader.GroupVisualizationFacesByGeometryFace` regroups individual cells and reconstructs boundaries; polyline handling avoids false long chords. `FeMesh` preserves positions of missing face/edge kernel IDs. | Import/selection/CAD adapters must retain stable geometry IDs and unknown slots. Test partially triangulated thin faces, shared chords and missing kernel IDs. |
| RC2 mesher setup/errors | `Controller.GetPartNodesBoundingBox` derives default sizes from nodes with exploded offsets removed. New `NetgenKernelIds.Get` is shared by transfinite setup and diagnostic face naming. | Carry source behavior unchanged into services; don't reconstruct CAD IDs or use oversized CAD control-net bounds in the new UI. Compound/single-part error messages need oracle checks. |
| Patched native binary | Only `ThirdParty/netgen/nglib.dll` changes among tracked runtime binary/package files in this range; README describes retriangulating partially meshed faces with finer edge divisions. | Refresh the corresponding-source/patch requirement for this exact build. Native CAD/mesher parity remains blocked; stock Netgen cannot stand in as equivalent. |
| Post-RC2 sweep | `FeModel.GetRingWallSplitError` rejects ring walls that the mesher cannot split into four-sided walls | Include ring/tube-wall rejection and manual-source cases when adapting full sweep workflows. |
| Post-RC2 model/decks | `MaterialOrientation`, `CompositeStrength`, `CompositeLayer`, `CompositeShellSection`; `CalOrientation`, `CalCompositeShellSection`, `ShellOrientationGroup`. `ElasticLamina` checks the completed compliance matrix and derives v23 from E2/G23. | New model/API/deck behavior must be included if stable 3.0 contains it. Composite shells require the upstream S8R/S6 restriction, layer order, symmetry, angle, density/thickness and unit behavior. Don't duplicate these calculations in presentation. |
| Post-RC2 persistence/results | `FeModel` serializes `_materialOrientations` with an old-file default. `FeResults` adds `_shellResultData`; new shell/ply data and result-output types support material axes, plane stress and four composite failure criteria. | Extend type/member inventories and old/new PMX/results/history/clone fixtures before claiming 3.0 compatibility. Earlier 2.6 Windows/CrossOver saves do not cover these fields. |
| Post-RC2 API/journal/UI/VTK | Material orientation collection/gateway/journal support, composite sections/results APIs, new dialogs, tree nodes and material-axis symbols. Existing section/command folders move. | Reuse the upstream gateway/journal and new tests; maintain a portable workflow/feature matrix. Resolve moved paths, preserve serialized type identities and colored material-axis highlighting. |

Native SHA-256 change: baseline nglib.dll (2,325,504 bytes)
`d65e08883a3c57dfd54898d3a7a5cbe6d5a3d699ffc3927a23328ac45812039d`;
RC2/current master (2,345,472 bytes)
`dee9ffc5363626f2fe4df89fd8f9364c99390509722dc5fd3ec17f3ee84f16f2`.
`ThirdParty/netgen/README.md` still says the custom source tree is outside the
repository and asks that the executable/DLL be deployed as a matched pair.
No solver/Gmsh/ActiViz/CPython version change is inferred from this range.

## Executable replay and evidence

`X/Core/verify.py --upstream-revision` now accepts only reviewed names/full SHAs
in `X/Core/upstream-replays.json`. It checks ancestry, extracts selected Git
bytes into a temporary source tree, applies the two existing verified boundary
adapters, and checks compiled hashes against the current guarded slice. Changed
engineering files or vectors fail pending explicit adaptation. Builds pass
`RepositoryRoot` to all shared projects; the vector fixture now follows that
same property, so the actual fixture is taken from the replay snapshot too.
The default working-tree build remains available and retains its original pin.
No fetch or branch change is performed by the verifier.

Commands, from repository root:

```sh
python3 -m unittest discover -s X/Core -p test_upstream_replay.py
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 --output X/Core/artifacts/rc2/current-macos-arm64.json
python3 X/Core/verify.py --upstream-revision 3.0.0-rc2 --expect-os Darwin --expect-architecture Arm64 --output X/Core/artifacts/rc2/macos-arm64.json
python3 X/Core/verify.py --upstream-revision post-rc2-2026-10-17 --expect-os Darwin --expect-architecture Arm64 --output X/Core/artifacts/rc2/post-rc2-macos-arm64.json
```

Native **Mac ARM64/.NET SDK 10.0.402**: all three builds pass 25 mapping,
30 data and 95 accepted element/host checks, 28 CLI controls and four data
rejection controls. Mapping/data/element/CLI outcomes and tooling fingerprints
match across all three builds. Seven replay tests pass, including rejection
of a moving branch, an unreviewed SHA, changed upstream engineering code,
changed exception extraction, changed import adapter and changed vectors.
Full retained JSON reports and hash comparisons are beside comparison.json.

The two original correctness failures are unchanged in both upstream revisions:
quadratic-tetrahedron affine integration is 26.794910717854155 against expected
28, and quadratic-pyramid classification is false against expected true.
`fullyAccepted` remains false; the quadratic-tetrahedron host gate remains.
No numerical algorithm, expected value or tolerance was changed.

The existing native x64 CI job is extended with exact-object fetches from the
fork, replay guard tests and both new source builds. This configuration is local
and uncommitted; **hosted x64 and native Windows replay have not run**. Previous
hosted acceptance still applies only to its published commits, not this tooling.

Initial native Linux ARM64 replay attempts could not connect to the existing
Podman VM and then failed starting it with a gvproxy socket error. Cleanup
stopped that VM successfully. The maintainer subsequently started Podman and
requested a retry; the retry reuses the cached image
27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88,
with Linux/ARM64 image architecture verified, no network, read-only repository
and root, and a disposable /tmp. Final retry results are recorded in
verification.json; no initial infrastructure failure is counted as a test pass.
The maintainer-started VM is left running.

**Retry verified:** all three builds also pass on native **Linux ARM64/.NET
SDK 10.0.402**, with the same 25/30/95 accepted checks, 28 CLI controls, four
data rejection controls and both unchanged correctness failures. All seven
replay guard tests pass in the container. Engineering/CLI outcomes (excluding
runtime descriptions) and tooling fingerprints match the Mac reports exactly.
The six full Mac/Linux reports and comparison hashes are retained alongside
verification.json. The initial VM problem is resolved for this run; native
Windows x64 and hosted Linux x64 replay are the remaining platform follow-ups.

## Faster route to 3.0.0 — architectural inference and priorities

Our source-linked approach has kept divergence small: only four original
production paths differ from de8f7303, and the new upstream changes merge
textually without conflicts. That supports continuing shared implementation.
It does not establish a near-finished native application: there is still no
native portable frontend, complete model/results workflow, compatible document
store or matching-source native CAD/mesher build. A same-day/nearby stable
release cannot yet be promised from kernel-test counts.

The next implementation milestone should be a usable vertical workflow:
**load a mesh/deck → inspect/select → assign a simple material and boundary/load
definitions → export → run the pinned solver → read/display results → save and
reopen**. Use the existing gateways, runners and journals. Expand the original
FeMesh/model/reader/writer closure toward that workflow instead of accumulating
independent micro-probes. Keep new upstream composite behavior in the parity
backlog and source implementation; don't make a parallel engineering model.

The sequence is: (1) advance that shared mesh/deck/results workflow and obtain
an RC2 Windows oracle; (2) make the interactive VTK/host experiment decisive,
including picks, clip IDs, material axes, input/DPI and disposal on required
targets, then choose a frontend from evidence; (3) implement the document/clone
boundary with measured old/new PMX semantics, including new composite fields;
(4) reproduce the patched native tools and complete four-platform workflow and
packaging acceptance. Steps involving native source access are schedule risks
that need resolving early. A mesh-only development preview could precede CAD
parity if explicitly scoped; it must not be labelled full 3.0.0 parity.

This is the recommended implementation direction under the maintainer's request
to increase coding pace. It does not select a production frontend/serializer,
change F001 or silently close correctness/native-source/release gates. Stable
release alignment still requires its exact source/artifact pin and rerunning
the affected upstream/native workflows before packaging.
