# B016 — upstream's 3.0.2 suite: 77 of 108 on macOS ARM64 (open, triage)

23 November 2026, the macOS package from `d5f3b24c` under `sandbox-exec` (repository denied, fresh data folder),
`Run_Tests.py --exe <PrePoMax.com>` with the scripts copied out of the repository. 3.0.1: 61 of 81 on the same
layout. 31 runs fail; none is the legacy-file reading fixed after this package (no suite script opens an older file).

Expected on this layout (as in M3-1):
- Windows-only test content: `TEMP`/`LOCALAPPDATA` (Journal_Mesh_Setup, Mcp_Http, Mcp_Workflow, Api_View_Results),
  PowerShell (Job_Correctness), named pipes and the automation server (Rpc_Live_Session, Rpc_Server, Batch_Run [4]).
- Scripts that read the repository's sources (Audit_API_Coverage, Audit_API_Documentation, Api_Enum_Vocabulary,
  Meshing_Three_Block_Mapping); the layout keeps the repository out of reach.
- `test_runner_offline`: upstream's own runner self-test expects two scripts for the filter "loads" and 3.0.2 adds two
  more (`Loads_Body_Force`, `Loads_Edge`) — an upstream inconsistency, to report.

To triage (new in 3.0.2 or changed; compare with Windows first, D061):
- Geometry and meshing results that differ from the Windows baselines (fingerprints, element counts; cf. B014):
  Meshing_Ring, Meshing_Submap (98/126 for 92/131), Meshing_Quad_Dominant (172/40 for 165/54), Side_Spacing,
  Submap_Round, Submap_Sweep, Sweep_Compound, Wrapped_Range, Transfinite_Frame, Revolve ("a vertex … lies on no
  circle"), Split_Cells_Fuse, Split_Periodic_Faces (0 new faces), Delete_Cad_Faces, Geometry_Transform (B014).
- Possibly port defects, to check first: Offset_Face (sub-part offset keeps area 36 for 64), Meshing_Shell_Types
  (the generated mesh file holds no nodes), Loads_Body_Force (element 1 loaded with BX 1.414 for 2x/r),
  Loads_Edge (nodal forces equal to 9 digits, the test wants 1e-9 relative — number formatting?).

Passed among the new 3.0.2 tests: Element_Order (3 runs), Meshing_Cap, Lens, Lens_Planar, Lens_Sweep, Pole_Faces,
Tube, Quad_Cleanup, Quad_Dominant_Leftovers/Seam, Ring_Mapping, Submap_Fillets/Holes/Loop_Start/Mapping,
Loads_Two_D_Edges, Transfinite_Prism, Split_Cells_Compound/Group.
