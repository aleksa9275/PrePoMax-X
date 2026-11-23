# M3-0 — upstream 3.0.2, housekeeping and release basics (D068)

23 November 2026, macOS ARM64. Upstream `master` moved 51 commits past our pin `1e2f83f2` (15–22 November): version
3.0.2 at `6703b1cb`, not released yet. The maintainer chose to sync before M3 CI, with housekeeping and release basics,
and to have a macOS build on 3.0.2 before asking upstream about collaboration.

## What 3.0.2 brings

- **Storage without BinaryFormatter**: stored types carry `[PmxType]`/`[PmxKey]` (MessagePack, Zstandard), `.pmx` is a
  chunked container with a journal for the history, clones go through the same serializer, and files of older
  versions are read by a new assembly `PrePoMax.LegacyImport` (an NRBF reader on `System.Formats.Nrbf`). `PmxTool`
  (corpus, schema snapshot) is new.
- **HiGHS 1.16.0 instead of lp_solve** for the interval assignment (element counts, sweep choices).
- Meshing: submapped, lens, tube, ring, cap and pole faces (structured quads), all-quad free faces (Blossom), sweep
  sources from those, pyramids at right-angle corners; two Netgen updates; mesher time limit.
- Change Element Order (tool, command, form), body force and edge loads, 2D edge loads, Show Nodes, ambient
  occlusion fixes in vtkNative, a highlighted-surface crash fix, MIN_RESERVE_FACTOR, composite critical layer.
- `FeElement.IsParabolic` now includes the quadratic pyramid (our D029 finding, pyramid part).
- 21 more Python API test scripts (102, was 81).

## The merge (`d5f3b24c`)

- 52 conflicts. Most were our own vestigial splits: ~25 original classes had been split into `*.Legacy.cs`,
  `*.Transformations.cs`, `Tools.*.cs` partials in the Phase A era, all still compiled by the original projects (pure
  moves). They are upstream's single files again. Kept: the WinForms/Windows partials the portable build excludes
  (`*.WinForms.cs`, `*.Windows.cs`, `ExecutableJob.Legacy.cs`), the X deck-writer constructors of the `Cal*` keywords,
  the FRD/DAT snapshot hooks and the `CaeGlobals.OrderedDictionary` qualifications (.NET 9+ has its own
  `OrderedDictionary<,>`; now re-applied by a build-driven pass to 3.0.2's code).
- Original-area divergence from upstream: **175 files (50 added, 125 changed), was 192**.
- Portable GmshCommon: 3.0.2's `GetVisibility`, `ReparametrizeOnSurface`, `GetCurveNodes` on the Gmsh C API.
- `X/Domain/PrePoMax.LegacyImport` builds upstream's legacy reader for .NET 10; the domain subset lists 3.0.2's
  `PmxDocument`, `ILoadNamesCommand`, `CChangeElementOrder` and the new load views; `FrmChangeElementOrder` is compiled
  whole with the other forms (74).

## Files of older versions: upstream's reader under our allowlist

Upstream's legacy reader resolves any type a file names (`Type.GetType`), creates it uninitialized and runs its
serialization constructor and callbacks — what our rules call unrestricted deserialization. Our own
`RestrictedNrbfSerializer` needed `[Serializable]`, which 3.0.2 removed. So the X build now uses upstream's reader with
a small opt-in hook (`LegacyReader.RestrictingBinder`; with it, the reader resolves no type itself, every name goes
through the binder): 23 added/5 changed lines in three upstream files, compiled by net48 too (`net48_check.py`).
`X/Persistence/AllowlistBinder` binds through the reviewed `allowed-types.txt`: unknown assemblies and types outside
the list are refused, a name of an application assembly that no longer has the type is a removed type (null,
reported, as upstream does), renames follow upstream's table. The X build fails closed: until a host installs the
binder, the legacy reader refuses every type. Our `RestrictedNrbfSerializer` and the `BinarySerialization` seam are
retired.

Real files found three gaps the record-level checks had not: old files hold the `PrePoMax.Controller` object (wrongly
removed from the list with the static classes), net48's `System.OrdinalComparer`, and net48's default comparer types
(`GenericEqualityComparer<string>`), which .NET names differently, so upstream's storage did not take them as the
default when the history was written. Fixed in the policy (`c3a0cb88`); `Runner --open-legacy` and
`verify-app.py --legacy-pmx` now open real files. The release's example models (Profile, Bearing_bracket, 3.0.1) and
the maintainer's 2.5.1 bridge model open with their parts, materials, steps and units.

Persistence checks (28): the storage round trip (cycles, shared objects, ordered dictionary with comparer, IEEE values,
more than 2 M objects and 32 M array elements, B013's FileInfo), the legacy reader's refusals (unknown framework type,
unknown assembly, spoofed comparer assembly, application type outside the list, no reader fallback to
`Type.GetType`), a net48 FileInfo and OrdinalComparer read, removed types, both renames, the binary formatter disabled.

## Native components

- **HiGHS** (`X/Build/Highs`, new): 1.16.0 at `f3f113d`, the release upstream vendors for Windows, as
  `highs.dll.dylib`/`.so` beside the assemblies and GmshCaller; every entry point the wrapper imports is exported; no
  build path or build-tree rpath left (the recipe fails on one).
- **NetgenMesher** re-pinned to the published `01e30ce0` (one file, `occgeom.cpp`); rebuilt with OCCT 8.0.1. 3.0.2's
  `nglib.dll` (upstream `42974ee7`, pyramids at right-angle inside corners) carries a change not yet in the published
  repository — a question for upstream.
- **vtkNative** rebuilt on our pinned VTK 9.7.1 (211 exports, with 3.0.2's `vtkn_view_set_nodes_visibility`). Upstream's
  new prebuilt VTK SDK download (`vtk-sdk-9.7.1-pmx1`, Windows) is not used: same VTK version and patch, our recipe.
- Gmsh 4.13.0, Mmg, QuadWild, CalculiX unchanged (P1 / M3-1 builds).

## Housekeeping

- Retired: `X/Desktop` (the Qt desktop preview), its host publication and DMG/tar.gz/deb packaging (`build.py` keeps
  `plan` and the solver build for `build_ui.py`), `linux_deb.py`, four `verify-*.py`, the lp_solve recipe; HiGHS replaces
  lp_solve in `build_ui.py`, `package_ui.py`, both X/App packagers and the notices.
- `REMAINING_WORK.md` rewritten without the Qt-era items; AGENTS/UPSTREAM_SYNC pin `6703b1cb`; D068.
- Superseded payloads pruned (the 3.0.1 vtkNative runtime, Netgen/OCCT/vtkNative build trees; the OCCT install and
  source archive kept for reuse).
- Check expectations moved to the 3.0.2 contract, not loosened: stored types carry `[PmxType]` and none
  `[Serializable]`; GeometryMetadata keeps its legacy constructor; the quadratic pyramid is now classified parabolic
  (one open correctness item left: the quadratic tetrahedron quadrature); the CaeGlobals reference allowlist names
  MessagePack and ZstdSharp. The Windows data reference was observed on 3.0.1 and needs re-observing on Windows (M3/M4).

## Release basics

- `build_ui.py` maps the repository and the workspace out of every native binary (`-ffile-prefix-map` for C, C++,
  Fortran), so a CI build from source leaves no build-host path.
- Both packagers record `bundle.json` `buildPaths`. The macOS bundle built here lists 61 files (VTK libraries, OCCT
  in Netgen, QuadWild, ccx): source paths compiled in by `__FILE__`, from components built before the prefix maps. A
  release requires none; M3 CI rebuilds them.
- `bundle.json` names the NetgenMesher revision and HiGHS; the notice lists HiGHS (MIT) and its license.
- Not possible here: notarization and Windows signing (credentials), a complete third-party notice file (release step).

## Evidence (macOS ARM64)

- `check.py`: domain, controller, core, analysis, execution, results pass; `net48_check.py`: CaeGlobals,
  PrePoMax.LegacyImport, CaeJob compile as C# 7.3 for net48.
- The macOS package (`c3a0cb88`, 220 MiB zip) under `sandbox-exec` with the repository, the GitLab checkout,
  Homebrew and .NET denied, fresh data folder: app probe 16/16, probe areas 124 + 4 + 9 + 5 (as on 3.0.1), the four
  upstream scripts of `verify-app.py --scripts` pass, and `--legacy-pmx` opens the three older files (Profile 1 part,
  1 material, 1 step; Bearing_bracket 1 part; the 2.5.1 bridge model 1 part, 1 material, 1 step; MM_TON_S_C).
- Upstream's full suite (102 scripts) on the package from `d5f3b24c` (before the legacy fixes; no suite script opens a
  file of an older version): **77 of 108** (3.0.1: 61 of 81). The 31 failures are sorted in
  [B016](../bugs/B016-302-suite-failures.md): Windows-only test content and repository-reading scripts as before, an
  upstream runner self-test, and new 3.0.2 meshing/load tests whose results differ from the Windows baselines — four
  of them (offset face, shell types, body force, edge load) to check first as possible port defects.

## Publication (23 November, maintainer's approval)

- `origin/master` fast-forwarded to upstream `6703b1cb`; source tag `preview-3.0.2-1` (`a0eebd50`).
- macOS preview 4 on `release/macos-arm64-preview` (`6c645979`, bundle from `c3a0cb88`, zip `e514ccad…`).
- **Linux build kit** (`X/Build/Linux/build-package.sh`, `Containerfile.package`, `build-inside.sh`): one command
  builds the whole Linux package from source in Podman or Docker for the machine's architecture (x86-64 or ARM64):
  every native component through `build_ui.py` (prefix maps), the PrePoMax 3.0.1 release data from
  prepomax.fs.um.si (pinned SHA-256, byte-identical to the reference copy), `package_linux.py`. Its first run from
  scratch found five gaps, fixed on the way (lib3mf's flat archive, `--vtk-native` to the wrong packager, Python's
  terminfo on case-insensitive volumes, the `dist/` path, the lock files the publish rewrites). Run on ARM64 in the
  local Podman machine (about 3 hours): package from `a0eebd50` (not dirty), `buildPaths` only the VTK receipt, two pip
  script shebangs and ARPACK's Fortran source paths in `ccx` (container paths); in the Ubuntu 24.04 session without
  the repository: app probe 16/16, probe areas 124 + 4 + 9 + 5, the four upstream scripts and the three older files.
  **x86-64 has not been built or run.**
- `release/linux-preview` (`b5b382b0`): the build instructions and the ARM64 package (tar.gz `b186def8…`);
  `release/linux-arm64-preview` (3.0.1) deleted at the maintainer's request.
- `PREPOMAX-X-TESTING.md` for testers. Issues are disabled on the fork (GitHub's default): the maintainer enables
  them before the forum post.

## Next

- The first x86-64 build of the Linux kit (testers, or Podman on Windows per D059).
- Ask upstream (the maintainer's step): collaboration, the NetgenMesher revision behind 3.0.2's `nglib.dll`, the
  legacy-reader hook and the GmshCommon additions as possible upstream changes.
- M3: GitHub Actions for the four targets, Windows first.
