# Original CAD PMX reference and safe projection

Task 0069 establishes the original PrePoMax 3.0.0 CAD/mesh persistence boundary.
The pinned official Windows executable runs under an isolated CrossOver bottle;
its executable SHA-256 remains `3f73da2f17941f857c51045f3650992af5eb639031052b338f88dc83b843278c`.
The tracked two-box BREP supplies one retained box. The capture explicitly uses
bundled first-order Gmsh tetrahedral meshing, named node/element regions, isotropic
elasticity/density and an automatic static step with the default solver selection.
This is reference-fixture generation; no native Gmsh/backend default is selected.

The resulting PMX contains one CAD/mesh part, **276 nodes and 843 C3D4 elements**.
Its CAD volume is 2000 model units cubed and it has six source faces. The first
capture used the original app's automatic hexahedral strategy; that diagnostic
capture is retained locally, and the tetrahedral fixture is explicit.

[Capture script](cad-pmx-reference/capture.py) ·
[Original-app readback script](cad-pmx-reference/readback.py) ·
[Verification receipt](cad-pmx-reference/verification.json).
The small generated PMX/INP remain local/ignored under
`X/Feasibility/Pmx/artifacts/task0069`; no private user model is added to Git.
The original archive and executable identities retain the earlier source/release
correspondence gate; an official binary is not a newly verified stable source pin.

## Projection and supported boundary

The original PMX has separate bounded NRBF graph and custom geometry/mesh frames.
A new C# binary-frame path constructs original FeNode, LinearBeamElement,
LinearTriangleElement and LinearTetraElement types in their original CaeMesh
assembly. It checks IDs, connectivity, positive original tetra volumes, complete
part visualization framing and absence of trailing bytes. It admits one matching
CAD/analysis part with first-order tetrahedra; quadratic tetrahedra stay blocked.
The old C3D8 reader remains separate and retains its previous acceptance rules.

The public pinned System.Formats.Nrbf 10.0.14 decoder projects records without
payload type activation or BinaryFormatter. CAD BREP decompression is bounded by
its original length-prefix/GZip framing and strict UTF-8. Graph and binary CAD
membership IDs must agree, as must analysis part/region membership. Transforms,
exploded offsets, saved results and unsupported history/engineering shapes are
refused. The accepted initial import history is preserved, never executed by
the native reader. Original meshing and visualization records remain untouched.

Seventeen Mac contract/interoperability checks pass, including original-app
resave, exact model-frame preservation, three-string edit ownership and six
malformed/unsupported input controls. Linux ARM64 passes sixteen checks (the
original-app resave comparison is performed on Mac). Existing checked C3D8 shape
write/reconstruction/refusal checks pass. The native reader is a bounded project
projection, not full FeModel/Controller or general PMX compatibility.

Task 0070 connects these readers to desktop edit/save/reopen/native solve.
Both original correctness failures, the quadratic-tetrahedron gate, Windows/net48
native execution, general PMX, four-target parity and release acceptance stay open.
