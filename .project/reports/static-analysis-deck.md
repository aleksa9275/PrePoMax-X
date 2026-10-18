# First complete portable static analysis deck

2026-10-18, Europe/Belgrade. [Task 0023](../tasks/0023-static-analysis-deck.md)
continues the accepted model/deck → native solve → original results sequence.
All task 0022/0023 changes remain **uncommitted** on research/native-feasibility,
parent ed2dcb4d. No new publication, x/main integration, frontend/default document
format or numerical/native-tool policy decision is made.

## Verified observation — usable analysis input

`CaeModel.StaticAnalysisDeckWriter.Write` accepts the existing original
InpMeshData plus original Material/SolidSection/StaticStep objects. The new
`PrePoMaxX.StaticDeck build-static` CLI constructs those objects from bounded tool
configuration and writes a complete deck through existing original mesh/material/
section/BC/load/static-step/output keyword writers. [Commands and scope](../../X/Analysis/README.md)
are documented; [generated cube](static-analysis-deck/cube-generated.inp) is a
retained synthetic review artifact. **No solver is executed in this increment.**

The first boundary supports full-integration C3D8 solids, temperature-independent
isotropic elastic material, 3D solid sections, global translational constraints
and concentrated forces per node on named sets. Every element must have exactly
one section; every supplied material must be used. Ordinary U/RF nodal, E/S
field and S element-history output are supported. Nonlinear/perturbation steps,
custom solver/controls, local/complex/amplitude loads, rotational constraints,
selection-dependent regions, unsupported output and existing model keywords in
the mesh input are rejected before a new file is opened. Unsupported definitions
cannot silently disappear. The typed boundary rejects derived step/material/
section/load/output objects whose additional behavior is outside this slice.

CLI configuration explicitly chooses `mm-N-s-C` or `m-N-s-C`; mesh coordinates
are assumed to use that declared length unit. Original quantity/equation
converters evaluate material, displacement and force strings. A null displacement
component is free; force is **per node**, not a total divided among nodes.
Unknown/missing/duplicate JSON properties, oversized inputs, invalid increments
and region/name errors are rejected. Existing files/input aliases are refused
and space/Unicode paths work. This tool JSON does not select PMX persistence.
Typed export evaluates in the caller's culture, snapshots numeric values, calls
original invariant-culture writers, then restores culture and source equations.

Independent test-only keyword comparison against
`X/Feasibility/Solver/uniaxial-cube.inp` verifies:

- Exact eight node IDs/coordinates and one C3D8 element ID/connectivity.
- E = 210000 MPa, nu = 0.3, original solid-section/material/set references.
- Twelve expanded node/DOF constraints, four 25 N axial forces, 100 N total.
- Required field/history outputs, one static step/end and explicit time values
  `(1, 1, 1e-5, 1)`. Original defaults additionally request E and NOE fields.

Four semantic negative controls deliberately change force-per-node, elastic
modulus, boundary DOF or section material and must fail the comparison. The
comparison helper is a restricted test fixture checker, not another production
INP reader. Deck SHA256 is
`e7323f8f1b037a39ce81af06913b9dff91bfd0e76f75b709719e656f115680a1`.

## Verified observation — original source ownership and boundaries

Expanded source closure is **146 files** for current/RC2, **147** post-RC2.
Original data/serialized fields, constructors, math and keyword formatting stay
in CaeGlobals/CaeMesh/CaeResults/CaeModel. New orchestration is CaeModel-owned.
`X/Analysis/static_layout.py` reconstructs expected partial extraction from
immutable baseline Git bytes, verifies all checked-in core/legacy parts and
requires the same extraction at both upstream pins. No code is generated during
build. New partial files are included exactly once in the original net48 projects.

Selection's unsafe-copy capability; Step/StaticStep support-mutator methods;
DisplacementRotation preview/distribution methods; Distribution's FeModel
abstract method; and mesh/model-dependent keyword constructors/coordinate
handling remain in legacy partials. Portable assemblies keep original reusable
data and direct keyword behavior. CalCLoad retains virtual dispatch in the
portable build and explicitly rejects missing local-coordinate context; full
legacy dispatch keeps its original mesh handling. Pure phase normalization and
three unchanged extension helpers move to reusable partials. Three further
unused unavailable imports are removed. Original Step ordered dictionaries are
qualified as CaeGlobals types to avoid the new BCL name collision.

Original Color data uses managed **System.Drawing.Primitives** without a desktop
host. An initial reused reference guard rejected all Drawing names; its expanded-
only allowance now admits Primitives while continuing to reject Common/GDI,
WinForms and VTK. The default offline guard is unchanged. The initial diagnostic
is retained; no engineering failure is hidden by that reference-policy update.
Mechanical source checks are not a substitute for a full original net48 build.
That Windows check remains open.

Task 0022 exact NCalc 1.3.8 and UnitsNet 4.89.1 package/archive/runtime-asset pins
remain. NCalc's NU1701 warning remains visible. Modern UnitsNet uses its explicit
same-version netstandard2.0 asset; original net48 keeps its net40 reference.
Post-RC2's exact Material/ElasticLamina/CompositeStrength changes remain isolated
and behaviorally distinguished; baseline source is not silently updated.

## Verified observation — six native source/host runs

| Source mode | macOS ARM64 | Linux ARM64 | Accepted checks per build |
| --- | --- | --- | --- |
| Current baseline with mechanical changes | Pass | Pass | 331 |
| RC2, 912fb3d0 | Pass | Pass | 331 |
| Post-RC2, f6273e39 | Pass | Pass | 331 |

Each build runs 44 equation/material checks, 69 static-deck checks and all 218
previous mapping/data/element/mesh checks. It also runs eight material CLI
controls, 21 static CLI controls and four semantic rejection controls. Nine
analysis source guards and ten existing replay guards pass on Mac. The old
offline core independently passes its 218 checks/39 CLI/four data controls.
[Verification manifest](static-analysis-deck/verification.json) retains report
hashes, reference results and comparisons. Per-run JSON retains actual arguments,
stdout/stderr, sources, packages, tools and runtime identity. Portable outcomes,
dependency assets, sources and all tool hashes match between hosts per source
mode; tools match across all six runs. Only runtime objects are removed from
test-result comparisons. The two known correctness checks remain explicitly
failed: tetra affine integral `26.794910717854155` versus `28`, and quadratic
pyramid IsParabolic false. Quadratic-tetra measurement remains blocked. No
algorithm/tolerance fix or whole-element acceptance is claimed.

Representative commands (exact commands/logs in JSON):

```text
python3 -m unittest discover -s X/Analysis -p test_analysis_layout.py
python3 -m unittest discover -s X/Core -p test_upstream_replay.py
python3 X/Analysis/verify-analysis.py --expect-os Darwin --expect-architecture Arm64 --output <current Mac report>
python3 X/Analysis/verify-analysis.py --upstream-revision 3.0.0-rc2 --expect-os Darwin --expect-architecture Arm64 --output <RC2 Mac report>
python3 X/Analysis/verify-analysis.py --upstream-revision post-rc2-2026-10-17 --expect-os Darwin --expect-architecture Arm64 --output <post-RC2 Mac report>
python3 X/Analysis/run-podman.py --output-dir X/Analysis/artifacts/static-linux-arm64
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 --output <offline core report>
```

Linux executes native ARM64 in the user's running Podman Linux VM, using cached
image `27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88`.
Network is disabled, repository mounted read-only and builds/restores use writable
temporary storage with cached exact packages. This is not x64 acceptance. The
user-started VM remains running. `analysis-workflow-linux-x64` CI is prepared for
all three source modes; **no new hosted or Windows pass is claimed**.

## Architectural inference, limits and next increment

The bounded deck component of accepted step 1 is implemented and tested locally.
This establishes keyword/reference semantics, not actual solver acceptance,
absence of rigid-body modes or general mesh-quality/solution correctness. C3D8
volume checks reuse the original exact zero/nonfinite guard without a new
Jacobian/quality policy. Full FeModel, arbitrary analyses, parameter graphs,
persistence/UI/CAD and installable desktop acceptance remain open.

Next: fingerprint/recover matching CalculiX 2.22 native sources, patches and
runtime dependencies; use the existing job-runner seam for real native process
execution, working directories, timeout/cancellation/error/output capture; solve
this generated cube against independent analytical/reference expectations. Then
expand the original FRD/DAT readers and result field graph to inspect actual
output. Do not silently substitute solver versions/builds. Windows/net48/RC2,
new hosted x64, both correctness failures and all four-target/source/UI/persistence/
CAD/signing/installer/Homebrew gates in [release requirements](../RELEASE.md)
remain. Continue accepted local work without another feature approval stop;
normal maintainer commit/push policy remains.
