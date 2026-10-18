# Original FRD static field inspection

2026-10-18. [Task 0030](../tasks/0030-portable-frd-fields.md), local/uncommitted.
Maintainer resumed after reset. Published 6c51ced6 matches origin and closing
pipeline #2960615926 is passed in authenticated GitLab UI. This new increment
is not in that pipeline and has not been published.

## Implemented boundary

`CaeResults.FrdFileReader.ReadStaticSnapshot` and X/Results `inspect-frd` now
read mesh nodes, element connectivity, static step/increment/time and nodal
fields through the original buffered FRD ASCII/float/double binary decoder.
Original Field/FieldData/FieldComponent and CaeMesh node/element identities are
preserved; magnitude, Mises/Tresca and principal components use original Field
methods. NodeIdsInValueOrder explicitly maps component-array indices to IDs.
Source SHA256/raw unit header are retained. No units are inferred/converted and
no global unit-converter setup runs. The snapshot is an inspection boundary,
not a replacement FeResults or persistence-format choice.

```sh
dotnet build X/Results/PrePoMaxX.Results.slnx -c Release --disable-build-servers -m:1 --source X/Analysis/artifacts/offline-feed
dotnet X/Results/Inspect/bin/Release/net10.0/PrePoMaxX.InspectResults.dll inspect-frd .project/reports/windows-reference/solver/uniaxial.frd
```

The retained Windows cube yields 8 nodes, one LinearHexaElement and
DISP/STRESS/FORC/ERROR fields. Checks compare independent 100/210000 displacement,
Poisson contraction, force balance/25-per-loaded-node force, magnitude and a
pure-shear tensor's Mises/principal values. Stored FRD axial stress is **99.996**,
while its analytical/DAT reference is 100. Inspection preserves the FRD value;
it does not round it, change tolerances or establish fresh numerical acceptance.
This increment does not diagnose the cause of that FRD-vs-DAT difference.

## Mechanical ownership and explicit limits

Original full Read/FeResults/FeMesh orchestration, axisymmetric scaling and
UnitSystem construction move unchanged to FrdFileReader.Legacy.cs, included
exactly once by the original net48 project. Original IO/random-heading/cubic/
principal helpers move unchanged to CaeGlobals/Tools.Results.cs. Existing
analysis still compiles its previous source set. Two unused imports are removed;
Field's generic OrderedDictionary is fully qualified to the original CaeGlobals
type rather than the newer framework type. Modern snapshot/CLI code stays out
of net48; no stubs or second decoder replace original orchestration.

Four private partial validation hooks are erased in net48. Modern hooks bound
headers/components/binary allocation and reject incomplete tails. Original
decoding/math bodies remain intact. The full-field decoder assumes node order
when counts match; ambiguous reordered field records are explicitly gated.
An unclosed final field which the original collector can skip is rejected.

Initial limits: completed C3D8 3D static results; complete single-record-per-node
displacement/force/stress/total-strain/error fields; 64 MiB, 100000 nodes/elements,
64 fields and 16 components. Unsupported analyses/axisymmetric scaling, partial/
continuation records, unknown components, nonfinite values, incomplete counts
and invalid references are rejected. Calls serialize original static reader
state, restore caller culture and reject input bytes changed during inspection.
Original mutable node/field types are retained in independent snapshots.
Full FeResults preprocessing/part/material graph, other elements, DAT history,
modal/complex/axisymmetric and large-model capacity remain future work.

## Verification

Current/RC2/post-RC2 each pass on Mac ARM64 and native Podman Linux ARM64:
**39 results checks and five CLI rejection controls**, plus a rerun of **331
accepted analysis checks**. The two original correctness failures/tetra host
gate remain. Results tests include the actual Windows fixture, independently
written binary float/double counterparts, raw/derived components, culture/path,
malformed/truncated/reordered input, assembly ownership and concurrent snapshots.
Six results/mechanical negative guards, nine analysis/four job/ten core replay
guards pass. Source snapshots have 155 current/RC2 or 156 post-RC2 rows including
prior analysis contracts and a separately checked compiled subset.

[Twelve retained reports/comparison manifest](portable-frd-fields/verification.json)
show exactly matching sources/tools/packages/fixture/field/CLI outcomes across
hosts per pin after runtime metadata removal. Linux is offline/read-only with
disposable build/package storage. Exact NCalc/UnitsNet pins and NCalc NU1701
remain explicit. No solver or solver-performance benchmark runs.

Prepared native x64 CI adds a fifth results job; it has not run for this local
increment. Native Windows/full net48/RC2, actual native solver/source admission,
full results/persistence/UI/CAD, corresponding third-party source, four targets
and installers/Homebrew remain required. No commit/push is authorized here.
Next accepted work: original DAT history/results integration and reproducible
native CPU solver recovery. No gfortran is in PATH; no compiler is installed or
backend substituted here. Solver advice/active 75% scheduling/GPU remain separate.
