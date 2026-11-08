# Development checks

One entry point runs the existing verifiers for the selected areas:

```sh
# Changed results reader/inspection code.
python3 X/Checks/check.py --area results

# Shared change: domain build + all suites (about one minute on a Mac).
python3 X/Checks/check.py

# Show the selected commands without executing anything.
python3 X/Checks/check.py --area domain --area core --dry-run
```

Areas: `domain`, `core`, `analysis`, `execution`, `results`. `domain`
(`X/Domain/verify-domain.py`) checks that the generated source lists match the
original csproj files, builds the whole original assemblies for .NET 10 and
compiles the original net48 CaeGlobals/CaeJob projects (C# 7.3) from reference
assemblies. The other areas build their test hosts against the same
`X/Domain` libraries (D062); the historical slice guards and upstream replays
were retired with the slices.

Results go to a new `X/Checks/artifacts/<run-id>/` (or `--output <new-dir>`).
`manifest.json` points to each verifier report/log and records elapsed time,
host and SDK. A nonzero exit, missing/malformed report or `success: false`
fails the run; known correctness failures stay recorded as failures. A passing
run is not numerical, platform, desktop or release acceptance.

On Linux, execution checks need an init reaper (`tini -s` in CI, Podman
`--init`). Hosted CI is on hold (D058).
