# Task 0069 — CAD/mesh PMX interoperability boundary

Prepared after task 0068; not started. D057 requires original PMX compatibility.
The next persistence increment must retain editable CAD/mesh/region semantics,
not merely the frozen job folder or a replacement project format.

1. Capture a small original PrePoMax 3.0.0 CAD + first-order tetrahedral mesh
   project with named regions and a static definition, using the retained local
   reference. Record source/version identity and original save/reopen behavior.
2. Inventory its original NRBF/object and mesh records with the existing safe
   readers. Compare with the checked C3D8 PMX subset, identifying CAD payload,
   source topology IDs, mesh association and editable assignment ownership.
3. Define an explicit supported subset and preserve/refuse unsupported members.
   Reuse original C# owners and reviewed PMX records; no BinaryFormatter/type
   activation, silent member loss or new default format.
4. Implement the smallest interoperable native open/save slice justified by that
   inventory. Verify original-app readback and native close/reopen/edit/solve,
   preserving geometry/mesh IDs, CAD region provenance and engineering values.
   If new graph extraction is needed, split it into tested bounded records.

Use Mac/Linux ARM64 locally. D058 blocks hosted CI; D059 defers Linux x64 to
Windows/Podman near finishing. General PMX/results/history breadth, both known
correctness failures, quadratic tetrahedra and every parity/release gate remain.
