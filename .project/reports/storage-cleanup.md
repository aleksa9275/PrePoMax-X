# Generated preview storage cleanup — task 0046

3 November 2026. Maintainer reports the editable-solid preview seems to work and
requests reclaiming unnecessary .app/.dmg storage before task 0045. This is a
user-reported local preview pass, not additional clean-OS/full-parity acceptance.
The new retention direction supersedes older instructions to preserve tested DMGs.

## Inventory and selected scope

The generated X/Build and X/Desktop artifact roots occupy about **46.46 GiB**.
Each recent package attempt retains roughly 3.6 GiB: an app and standalone
payload in dist, compressed image, another DMG staging copy, private PyInstaller
cache, published host copies and build intermediates. The DMG alone understates
the storage cost substantially.

The reviewed [plan](storage-cleanup/plan.json) selects **74 directories**, estimated
**46.315 GiB**, exclusively inside ignored task 0041–0044 target-build outputs
and the two earlier desktop-preview package outputs:

| Generated data | Directories | Estimated allocated GiB |
|---|---:|---:|
| dist: app/standalone payloads and DMGs | 15 | 22.146 |
| Per-build PyInstaller caches | 10 | 8.200 |
| DMG staging payloads | 9 | 6.764 |
| Test-installed app copies | 6 | 4.509 |
| Repeated self-contained host publications | 19 | 4.423 |
| PyInstaller build intermediates | 15 | 0.272 |

No running preview in these output paths or mounted disk image was found. The
script rechecks these conditions before deletion, refuses tracked files, symlinked
roots and changed payload trees, and never follows payload symlinks outside them.
The exact inventory and timestamp/inode tree stamps are recorded. APFS shared
extents/snapshots can make apparent allocated bytes differ from actual reclaimed
space; the execution receipt records observed filesystem availability separately.

## What remains

- All tracked source, native sources/build recipes, pinned requirements, targets,
  Git history and .project verification records. Seven retained evidence indexes
  comprising **292 entries** hash-verify before cleanup.
- Small sibling package/build manifests, commands/logs, locks, reproduction source
  snapshots, example definitions and checksum files. Their old success/identity
  fields remain historical evidence, not proof deleted payloads still exist.
- All generated job inputs/results and diagnostic screenshots outside the removed
  app/build subdirectories. No private model or per-user preview state is removed.
- Installed/user app copies outside these generated artifact roots; no application
  uninstall, Library cleanup, Gatekeeper/quarantine change or system-cache sweep.
- Verified native Mac solver at
  `X/Build/artifacts/task0041-final-mac-solver/solver` (about 56 MiB).
- Pinned packaging environment `/private/tmp/prepomaxx-desktop-runtime` (about
  752 MiB), exact NuGet cache `X/Analysis/artifacts/packages` (about 578 MiB), the
  offline feed and current source bin/obj outputs. These avoid expensive repeated
  downloads/rebuilds; they are not duplicated once per package.

## Availability and validation

After execution, previous app/DMG/host payload paths in tasks/reports/handoffs
become historical. This includes task 0042/0043 images and task 0044's current
image, whose hashes and successful verification remain recorded. Rebuild to a
**new output directory** before using them again. A source rebuild is not a
promise to reproduce the old timestamped/signed DMG bytes or its original SHA.

The [bounded audit script](storage-cleanup/cleanup.py) and plan make the removal
reviewable. Apply requires an unchanged inventory and writes an execution receipt;
afterward, both commands refuse replay/overwriting the completed record. It is intentionally scoped to
these historical task numbers, not an automatic/general-purpose cleaner.

```sh
python3 .project/reports/storage-cleanup/cleanup.py plan
python3 .project/reports/storage-cleanup/cleanup.py apply
```

**Completed:** the [execution receipt](storage-cleanup/execution.json) records
all **74 directories removed** successfully. Observed filesystem availability
increased by **45,075,312,640 bytes (41.98 GiB)**, from 188.2 to 230.2 GiB.
`df -h .` reports 230 GiB available, 75% used. Remaining generated roots occupy
142,020 KiB (Build) and 10,244 KiB (Desktop), about **149 MiB combined**.
The 46.315 GiB inventory estimate is not the physical space gain.

The first apply refused an allocation-count difference before deleting anything.
An [allocation-only refresh](storage-cleanup/plan-refresh.json) confirmed the same
74 paths, tree stamps and file metadata; the original plan is retained separately.
No deletion guard was disabled.

[Post-checks](storage-cleanup/post-checks.json) verify all selected directories
are absent and their parent records remain. Seven prior evidence indexes / 292
files verify identically [before](storage-cleanup/evidence-before.json) and
[after](storage-cleanup/evidence-after.json). All nine pinned solver/runtime file
hashes still match; the retained Python environment imports Qt 6.10.2 and VTK
9.5.2. The source Solve apphost, NuGet cache and offline feed remain present.
The [native source verifier](storage-cleanup/sources-after.json) and
[Mac recipe dry plan](storage-cleanup/build-plan-after.json) pass. No app rebuild,
numerical rerun or new hosted engineering acceptance was needed for storage cleanup.

## Retention for subsequent work

1. Build one current candidate at a time. Before deleting failed/superseded outputs,
   keep their small source/command/diagnostic evidence needed to reproduce defects.
2. After packaged verification, discard standalone duplicates, copied test apps,
   staging trees, private packaging caches, host copies and object files. Preserve
   active/mounted payloads until no longer used. Keep at most the current DMG
   temporarily while the maintainer needs it for a test/install.
3. After the maintainer confirms the test, the generated DMG/app can be deleted.
   Keep the user's installed app and jobs unless removal is separately requested.
4. Keep one useful native solver and shared tool/dependency caches. Do not rebuild
   old previews just to satisfy superseded keep-binary handoff text.
5. Never treat a preserved manifest's `success=true` as current payload presence;
   a new build and appropriate smoke must validate the next actual payload.

Rebuild entry (same tracked process; fresh output name):

```sh
/private/tmp/prepomaxx-desktop-runtime/bin/python X/Build/build.py package --target osx-arm64 --format dmg --solver-build X/Build/artifacts/task0041-final-mac-solver/solver --output X/Build/artifacts/next-preview
python3 X/Build/verify-macos-dmg.py --package X/Build/artifacts/next-preview --output X/Build/artifacts/next-preview-copy-check
```

The existing job-process test can use a current source build instead of the old
pruned task 0042 host path:

```sh
dotnet build X/Execution/Solve/Solve.csproj -c Release --source X/Analysis/artifacts/offline-feed
DESKTOP_TEST_SOLVE_HOST="$PWD/X/Execution/Solve/bin/Release/net10.0/PrePoMaxX.Solve" /private/tmp/prepomaxx-desktop-runtime/bin/python -m unittest discover -s X/Desktop -p test_jobs.py
```

Task 0045 remains unstarted. Last application repair is 921b24a6, exact-commit
Linux pipeline 3022312183 passing six automatic jobs. Cleanup is maintenance,
not new engineering/platform acceptance; all existing correctness/release gates stay.
