# Shell T-junction fixture preparation

Task 0007, 2026-10-14 (Europe/Belgrade), research/native-feasibility.
F001 remains a proposal. **Verified observation:** four hand-authored S4 mesh
fixtures satisfy their independent ID/topology/area/gap contracts, and two
deliberately altered contracts are rejected by the fixture checker.

```sh
python3 X/Feasibility/ShellJunction/check-fixtures.py --output .project/reports/shell-junction/fixture-contracts.json
```

[Manifest](../../X/Feasibility/ShellJunction/manifest.json) records exact input
hashes, geometry, units-on-import, intended connection and expected observations.
[Checker result](shell-junction/fixture-contracts.json) retains all four cases,
two regressions and checker/manifest hashes. No third-party packages were needed.

The [fixture README](../../X/Feasibility/ShellJunction/README.md) explains:
connected reference sharing edge [2,5]; coincident duplicate nodes without
connectivity; web joining the interior of an unsplit plate quad; and an intentional
0.1 mm gap. Plate/web areas are 40,000/20,000 mm² in all cases. The reference
preserves separate PLATE and WEB element sets. Import using MM_TON_S_C; the deck
itself does not declare units or physical material/section/weld properties.

**Verified source observation:** at baseline
de8f73032a72746e3d6d9afd53d9fbd289eb310a,
`CaeModel/FileInOut/Input/InpModel/InpFileReader.cs:43` maps S4 to its original
linear quadrilateral constructor. This is not a live import or full reader test.
The fixture checker supports only this tiny fixture grammar, not the original
PrePoMax reader or arbitrary INP files.

**Architectural inference:** the unsplit-plate case demonstrates why merely
welding duplicate nodes cannot supply an attachment edge missing from plate
connectivity. The connected reference has three incident shell elements on the
joint, so native CAD/surface-mesher handling of nonmanifold shell junctions is
an explicit experimental question. Shared connectivity alone does not choose
shell offsets or weld/contact idealization.

Task 0007 fixture preparation is complete. Windows import/PMX/history readback,
CAD surface creation, separate/compound meshing and numerical load transfer
remain pending. No automatic meshing implementation, solver execution or
production source change occurred.
