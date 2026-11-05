# Native CAD command roundtrips

[Task 0066](../tasks/0066-native-cad-command-roundtrips.md) runs four original
commands locally on native Mac ARM64, native Linux ARM64 and the pinned
official Windows 3.0.0 runtime through CrossOver. All three pass the independent
analytical box expectations.

| Operation on the checked 10 × 10 × 20 box | Checked result |
| --- | --- |
| Repair with ShapeFix option 1, tolerance 1e-6 | Valid box retains its six faces, volume 2,000 and center (5,5,10) |
| Translate by (7,-3,5) | Six faces and volume 2,000; center becomes (12,2,15) |
| Split with plane z=10 | Two solids of volume 1,000, centers (5,5,5)/(5,5,15), both mapped to source solid 1 |
| Export BREP as STEP and import it again | One six-face solid of volume 2,000 and center (5,5,10) |

The repair, translation and split BREP outputs are byte-identical on all three
paths. Their SHA-256 values are respectively `53d6637b…980a81`,
`16bf8fe1…c9b61` and `c2f47f77…7a1916`; the complete hashes and measurements
are retained in the receipts. STEP bytes differ, while the reopened solid
passes the same analytical checks. Input fixture and part bytes remain unchanged.
[Mac](native-cad-operations/mac-arm64.json) ·
[Linux](native-cad-operations/linux-arm64.json) ·
[Original Windows](native-cad-operations/windows-reference.json).

Reproduce with `.project/scripts/probe-native-cad-operations.py`, supplying
`--native-runtime`, `--inspector` and a new `--output` directory. For the original
Windows path use `--reference-runtime` and `--bottle` instead. Every command log,
definition, intermediate geometry and decoded measurement belongs to the fresh
workspace. The initial Mac attempt exposed a probe log-name collision, repaired
before the successful three-platform run; its failed receipt is retained in
`/tmp/prepomaxx-task0066-mac/verification.json`.

This checks the recovered command implementation on one analytical solid.
Repairing an already valid box does not validate repair of defective geometry.
Broad CAD operation coverage, desktop authoring/undo/persistence, native Windows
execution, meshing integration and all correctness/parity/release gates remain.
