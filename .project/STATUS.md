# Project status

_Replace this file's content as work progresses; history is in git and in
`.project/history/`._

## Where we are (8 November 2026)

- **Strategy reset (D062):** whole-code reuse in three phases. Progress is
  measured in [PARITY_INVENTORY.md](PARITY_INVENTORY.md) (generated from the
  original sources: 127 model/mesh features, 237 commands, 72 forms).
- **Working preview:** the Python/Qt desktop on Mac/Linux ARM64 (last candidate
  code `1580fa9c`) covers imported-mesh workflows for all element families,
  native CAD import/tetrahedral meshing, representative static/nonlinear,
  frequency/buckling, thermal and transient jobs, results and a limited PMX
  round-trip. It reimplements the application layer, so it is not counted in
  the inventory; see [full-completion-status](reports/full-completion-status.md).
- **Open findings** (fix after parity, D061): D029, B006–B009, thermal/
  axisymmetric diagnostics — [backlog](reports/deferred-correctness-improvements.md).

## Phases

| Phase | Content | State |
|---|---|---|
| A | Whole CaeGlobals/CaeMesh/CaeModel/CaeResults/CaeJob for .NET 10, net48 kept | in progress |
| B | Original Controller + Commands headless; original PMX open/save (allowlisted) | next |
| C | Cross-platform UI reusing original forms/property classes + native VTK viewport | later |
| Fixes | All recorded bugs and compiler warnings | after parity |
| Release | Four targets, installers, Homebrew, signing/notarization, sources/notices | after fixes |

## Next step

Finish Phase A (see the Phase A report once written), then start Phase B by
putting the Controller's main-form dependency behind an interface.

## Environment notes

- .NET 10 SDK at `/usr/local/share/dotnet` (10.0.403). Local caches and the
  last preview candidate live under `/tmp` and may disappear; see
  `.project/history/handoffs/current-next-session.md` for their paths.
- Hosted CI is on hold (D058); push with `[skip ci]` / `-o ci.skip`.
