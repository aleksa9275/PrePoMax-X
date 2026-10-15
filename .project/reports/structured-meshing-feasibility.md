# Structured meshing kernel execution

Task 0005, 2026-10-14 (Europe/Belgrade). Baseline
`de8f73032a72746e3d6d9afd53d9fbd289eb310a`, branch
`research/native-feasibility`. **Verified observation: unchanged native C++
mapping executes on Mac ARM64; unchanged C# count/grid types compile and execute.**

## Evidence

```sh
python3 X/Feasibility/Meshing/run-meshing.py --output .project/reports/structured-meshing/macos-arm64.json
```

[Execution JSON](structured-meshing/macos-arm64.json) retains eight pinned source,
header and fixture hashes, six experiment-tool hashes, actual build/process
commands, diagnostics and runtime details. Apple Clang 21 targets
arm64-apple-darwin; .NET SDK 10.0.401/.NET runtime 10.0.12 reports native Arm64
OS and process. Managed build has zero errors/warnings; the known Mac
CSSM_ModuleLoad diagnostic is retained without a workaround. No package
dependencies or original project/source edits were introduced.

The existing `CaeMesh/Meshing/Transfinite/Cpp/three_block_mapping_check.cpp`
compiled unchanged and passed **all 13** cases in `three_block_vectors.txt`:
right_45_45, equilateral, diagonal_34, sharp_10, sharp_5, quarter_disk,
deltoid_10, deltoid_30, deltoid_all, graded_34, chained_34, cylinder and sphere.
The original checker compares exact quad connectivity/fold counts and interior
parameters within 1e-9 times its reference scale. These vectors originate from
upstream C#; they establish agreement with recorded upstream observations, not
an independently derived FEM oracle or current Windows execution.

**Independent native checks: 17 pass.** A separately specified equilateral
triangle has six boundary nodes, one symmetric interior node, three quads,
total area sqrt(3), six boundary edges/three shared interior edges and disk Euler
characteristic 1. Uniform scale/translation preserve the expected centroid and
topology. Evaluator placement/incorrect lengths and mismatched UV/XYZ side sizes
are checked. Positive side-count triples 1–12 are checked against brute-force
enumeration of positive inner-line lengths, rather than reusing the algorithm's
count formula.

**Managed checks: seven pass**, through source links to the complete unchanged
`TransfiniteSideTriple.cs` and `ThreeBlockGrid.cs`: exhaustive count oracle,
invalid counts, boundary count, cyclic corner IDs, boundary-ID round trip,
inner-node classification and stored grid values. Two CLI contracts pass.
**All 1,728 C#/C++ count results match exactly.** The original comparator rejects
a 0.01 change in one reference parameter (exit 1), and reports a missing vector
file with exit 2. Those regression checks verify that a pass cannot result from
an empty fixture or a comparator that accepts a material difference.

## Measured managed boundary

The full unchanged C# Mapping/Grid/count slice with original
`CaeGlobals/ExceptionTools.cs` fails **CS0103: MessageBoxes** at its UI reporting
call. `CaeException` resides in that same file; source inspection of
`CaeGlobals/MessageBoxes.cs` confirms WinForms and additional helper dependencies.
The measured attempt stops at that exact boundary. No exception extraction,
namespace shim, assembly relocation or UI refactoring was used to make it pass.
The managed probe therefore does not execute ThreeBlockMapping.Map, and a new
live C#-versus-C++ mapping comparison is not claimed.

**Architectural inference:** the original kernel arithmetic/topology is a useful
shared cross-platform candidate. Reuse its existing vector checks in future
matching native builds. The exception/reporting dependency needs a reviewed
boundary change before the whole C# mapping can join a portable production core.

## Limits and completion

Task 0005's bounded execution/count/grid/compile-boundary evidence is complete.
No native CAD geometry engine, shell T-junction connectivity implementation,
interactive/rendering test, solver, Windows oracle, PMX/history or whole-core
portability is established. Linux/Windows execution of this new probe remains
pending; existing task 0002/0003 platform results do not imply those passes.
No GitLab CI configuration changed and nothing was committed or pushed.
