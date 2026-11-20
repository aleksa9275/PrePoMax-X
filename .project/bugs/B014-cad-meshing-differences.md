# B014 — CAD/meshing results differ from the Windows original in 9 upstream scripts

19 November 2026; found by upstream's `Run_Tests.py` through `X/App` on macOS ARM64 (M2 closeout). Meshers are the
pinned 3.0.1 sources (NetgenMesher `c5ecb0ba` = `f0ba926`, Gmsh fork `4156db5d`, OCCT 8.0.1 / 7.7.0).

| Script | Failure |
|---|---|
| Test_Model_Delete_Cad_Faces | the bottom box is not a plain solid part with its id |
| Test_Model_Meshing_Revolve | Compound mesh generation failed |
| Test_Model_Meshing_Shell_Types | Gmsh shell mesh file without nodes |
| Test_Model_Meshing_Sweep_Compound | first-order sweep of the overhanging plate does not fill its cell |
| Test_Model_Meshing_Transfinite_Frame | missing inner node of three blocks |
| Test_Model_Offset_Face | offset surface area 36 against 64 |
| Test_Model_Split_Cells_Compound | box outside the copy 48000 instead of 36000 (passes alone) |
| Test_Model_Split_Cells_Fuse | fused box 6 faces, 7 expected |
| Test_Model_Split_Periodic_Faces | periodic faces gain no face |

Geometry_Transform and Split_Cells_Compound pass alone but have failed in the full run: some results depend on
earlier scripts in the shared work directory. 20 November: in the next full run (64/81) Offset_Face passed and
Geometry_Transform failed; alone, both then failed (Geometry_Transform: a compound's sub-part did not move with it,
`[30, 20, 17]` instead of `[124.24, 24.24, 22.0]`; Offset_Face: area 36 against 64). The results are not
reproducible from run to run, not only order-dependent. Next: run each with the original 3.0.1 (CrossOver, then Windows) on
the same inputs, compare the intermediate BREP/.vol/.msh files, and separate native-build differences from port
defects. Never relax the scripts' tolerances (D061).
