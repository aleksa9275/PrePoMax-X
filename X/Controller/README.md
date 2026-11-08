# Original Controller host (Phase B)

Build `dotnet build X/Controller/PrePoMaxX.Controller.slnx`. The .NET 10 assembly
keeps the original `PrePoMax` identity and compiles the whole Controller, every
original Commands compile item, mesher runners, settings, annotations, Python
engine/gateways/journal, and APIs. Source inclusion is checked against the original
projects, rather than copying feature implementations into a second model.

`PrePoMax.IControllerHost` is generated from original main-form signatures.
The Windows form implements it; the headless host supplies model-related callbacks,
result selection, actor data and observable presentation events. The original
Controller owns all engineering operations and command/history state. Native VTK
9.5.2 supplies locator/frustum and surface-filter operations without a render
window; original cell triangulation and edge-selection code are shared unchanged.
Window controls, screenshots, camera interaction, live animation and property
editors belong to Phase C. Required queries are explicit; missing services throw.
For contour 3MF output, supply the renderer's `ExportLookupTable`; optional
`ExportUpDirection` controls the original writer's orientation argument.

The development command-line host executes original recorded Python commands:

```sh
dotnet X/Controller/Headless/bin/Debug/net10.0/PrePoMaxX.Headless.dll \
  run script.py /absolute/work /absolute/python-profile.json /absolute/project.pmx
```

It does not replace the original application's CLI/RPC/MCP servers or GUI.
Original script-recording guards still apply (including new/open inside a recorded
script). Use `HeadlessSession.Open`, `Controller.New` and other original methods
for embedding. Configure one runtime profile per process before starting work;
original Controller/settings/Python state is process-wide and not a concurrent
multi-document service. Session settings never overwrite the installed user's file.

CPython profiles require `schemaVersion: 1`, exact `version` (3.12.x), absolute
`home` and `library`, `librarySha256`, and optional absolute `moduleDirectories`.
VTK-dependent operations require VTK 9.5.2 in those module directories. Profiles
are explicit verification/runtime inputs, not a new shipped Python default.
`NativeTools.Configure` accepts `schemaVersion: 1` and a `tools` object mapping
original tool identities to `{ "path": "/absolute/file", "sha256": "..." }`.
The optional `lib3mf.dll` identity resolves the original binding to native lib3mf
2.4.1 after verifying fingerprint and runtime version. No PATH fallback or implicit
native version upgrade is used. Solver selection separately requires the existing
build registry, selected build ID and verified binary directory.

Run `python3 X/Controller/verify-controller.py --output /absolute/result.json` for
focused build, persistence and original INP/PMX workflows. Optional
`--python-profile`, `--three-mf-library`, `--solver-registry/--solver-id/--solver-directory`,
`--netgen/--gmsh-library/--cad-fixture` enable native workflows; missing inputs
are reported as pending. `X/Checks/check.py --area controller` runs the basic check.
`verify-net48.py --reference-directory /original/app/lib --output /absolute/check`
compiles all eleven original C# assemblies with C# 7.3/.NET Framework metadata.
It never executes reference DLLs and supplements actual Windows acceptance.

See the [milestone report](../../.project/reports/phase-b-controller.md) for actual
coverage, native pins and remaining product/platform acceptance.
