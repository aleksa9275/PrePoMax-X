# Task 0063 — Native original CAD and meshing build

The maintainer requests accelerating native CAD and meshing. Recover the newly
published PrePoMax NetgenMesher source, pin its original bytes and licenses,
and add a reproducible native build using its OCCT 8.0.1 dependency. Keep local
portability changes as reviewed patches outside the original source tree.

Build and execute on macOS ARM64 first, then Linux ARM64. Compare original
STEP/BREP import and visualization fixtures, exercise original Netgen volume
meshing, and connect a passing native import candidate to the desktop. Record
actual differences and source correspondence rather than infer binary identity
from matching source labels. Patched Gmsh and QuadWild recovery can be pinned
without silently selecting them as a replacement mesher.

Preserve original engineering algorithms, both correctness failures, the tetra
host gate and all broader 3.0.0/four-target/release requirements. Publish useful
reviewed checkpoints under D051 with actual remote and relevant CI verification.

Outcome: original source and reproducible build are implemented; Mac/Linux
ARM64 pass native CAD/linear-meshing experiments and relocation checks. The
first hosted x64 attempt timed out after 45 minutes building OCCT, before CAD
execution. Native x64 acceptance remains pending. D058 prohibits retries or
other hosted runs without explicit new instruction. [Evidence](../reports/native-cad-meshing.md).
