`cube.brep` is a synthetic 10 × 10 × 10 cube at the
origin, created for C3 verification with the retained patched Gmsh 4.13.0 runtime:
`gmshInitialize(0, null, 0, 0); gmshModelOccAddBox(0,0,0,10,10,10,-1);`
`gmshModelOccSynchronize(); gmshWrite("cube.brep"); gmshFinalize();`
No user model or proprietary CAD data is used.
