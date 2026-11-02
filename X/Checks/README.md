# Development check profiles

Use the existing engineering checks with one entry point:

```sh
# Changed results reader/inspection code: current source only.
python3 X/Checks/check.py --area results

# Shared change: all four current-source suites.
python3 X/Checks/check.py

# Upstream/compatibility milestone: guards + current/RC2/post-RC2.
python3 X/Checks/check.py --profile compatibility

# Inspect the selected commands without executing/writing anything.
python3 X/Checks/check.py --profile compatibility --area results --dry-run
```

Areas: `core`, `analysis`, `execution`, `results`. Repeat `--area` to select
several. Selection is explicit; this first increment does not infer dependencies
from a Git diff. For shared math/units/model or broad project changes, run all.
For documentation-only changes, check the content/links instead. Compatibility
does not fetch or change branches: the reviewed Git objects must already exist.

Every invocation executes fresh checks using the existing verifiers and their
isolated builds. Existing pinned NuGet archives in `X/Analysis/artifacts/packages`
are reused and verified; no successful test result or compiled DLL is substituted
from a previous run. Populate those packages with the existing documented restore
when needed. A Mac current-results baseline took 6.70 s; all four fast suites
took 43.36 s locally. These are single observations, not a platform speed promise.
An additional compiled-output cache is deferred until timings justify it.

Results go to a new `X/Checks/artifacts/<run-id>/` by default. `--output <new-dir>`
chooses a new destination; an existing directory is refused. The compact
`manifest.json` points to each verifier report/log, records elapsed time, host,
SDK and source pins, and preserves known correctness failures. A nonzero exit,
missing/malformed report or `success: false` fails the profile. Remaining steps
are pending, never passed. A passing profile is not full numerical/platform/
desktop/release acceptance.

For dirty work, the run retains a patch and copies changed build/test/shared
source under `source/`, including untracked code. Generated output, ignored files,
arbitrary untracked JSON and user models are excluded. Retain new fixtures
separately when needed for a bug reproduction. These diagnostics are local unless
explicitly packaged/published. Avoid editing tested code during a run; individual
verifier source hashes identify the compiled/inspected inputs.

GitLab changes prepare four current-source jobs and the existing native research
job for source/config changes. Ordinary documentation pushes skip them; a web
pipeline explicitly runs them. Exact area selection is local/manual for now;
source changes conservatively run the current-source CI matrix. Package archives
use a cache keyed by their pin manifest. Historical checks move to the optional
manual `portable-compatibility-linux-x64` job. Its optional status cannot satisfy
a release gate: require an actual passing run when compatibility is claimed.

On Linux, execution checks need an init reaper (`tini -s` in CI, Podman `--init`).
Use a native target process, with the .NET 10 SDK and Python installed. Host
expectations are passed to each verifier. This increment was tested on native
Mac ARM64; the changed CI configuration has not yet run on GitLab.
