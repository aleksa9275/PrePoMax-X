# Multi-part CAD conversion and preview

Tasks 0060–0062 extend the existing reference conversion to all BREP
parts emitted by a split. The new multi-part boundary allows 1–32
parts, up to 32 MiB of combined BREP output and 16 MiB of combined VIS.
The existing per-file limits and original `0.01 1 0.26` visualization
arguments apply. Every part must convert and decode before the GUI
replaces the current document. The original single-part API retains its
one-output requirement.

The rendering DTO assigns unique renderer node and cell IDs and retains
the source part, node and triangle IDs alongside them. It copies
per-part CAD metadata and edge identities. Coincident nodes in different
parts stay distinct. The combined scene hash identifies the ordered
part IDs and VIS hashes. A single-part scene retains its previous
contract and hash.

The native preview displays all parts together and lists their original
measurements under separate tree entries. Face picks return the source
part and face IDs and open the corresponding tree row. The imported
document remains read-only. Cancellation and failure of a later part
preserve the previous document.

The tracked `sweep_two_apart.brep` fixture produces two solids, each
with eight nodes, twelve triangles and twelve CAD edges. The source
node and face IDs repeat across those parts. Two fresh command replays
produced byte-identical BREP and VIS outputs. Two imports in the pinned
Windows 3.0.0 application through CrossOver produced byte-identical
geometry captures. The original application reports volumes of
1999.9999999999995 and 768 model units cubed.
[Original reference and hashes](multipart-cad-reference.json) ·
[Original application capture](multipart-cad-reference/geometry.json).

The portable check makes 359 exact comparisons against the original
application and verifies every combined source-node, triangle, face
and edge relationship. macOS ARM64 and Linux ARM64 pass with the same
combined-scene hash. The original app's global vertex IDs are related
to each VIS part by exact coordinates during this comparison.
Windows geometry selection numbering remains a separate boundary.

The source desktop suite passes 30 tests, including coincident nodes
with repeated IDs, a failed second part, conversion size limits,
multi-part viewport picks and the existing cancellation controls.
Nine build boundary tests pass. Both packaged Mac viewports display
and pick three visible faces in each part. The single-part L-bracket
and bundled native INP solve also pass.

The conversion uses the explicitly configured original Windows runtime
through CrossOver. Matching native C++ source recovery, native CAD
execution, CAD repair and meshing, both correctness failures, the
tetrahedron gate and broader parity and release acceptance remain open.
