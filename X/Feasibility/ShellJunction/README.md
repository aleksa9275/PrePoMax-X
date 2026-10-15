# F001 shell T-junction fixtures

Four hand-authored **mesh-only** inputs and an independently specified geometry/
topology manifest. These are preparation for Windows reference inspection and
the automatic-connectivity proposal, not CAD geometry or mesher output.

Plate midsurface: x=-100..100 mm, y=0..200 mm, z=0. Web midsurface: x=0,
y=0..200 mm, z=0..100 mm. The intended attachment line is (0,0,0)–(0,200,0).
Import using MM_TON_S_C; INP does not encode a unit system. Material, thickness,
section, weld/contact, BCs, loads and analysis steps are deliberately unspecified.

| Input | Exact expected behavior |
|---|---|
| connected.inp | Plate elements 11/12 and web element 21 share the complete edge [2,5]. Reference connectivity, not automatically generated |
| coincident-disconnected.inp | Web nodes 9/10 coincide with plate nodes 2/5, but their IDs differ; no shared plate/web edge |
| unsplit-plate.inp | One plate quad spans the attachment line; web nodes 2/5 are not plate connectivity nodes. Coincident-node merging cannot supply the missing plate edge |
| intentional-gap.inp | Web bottom is 0.1 mm above the plate; this case is intended to stay separate |

All plate areas are 40,000 mm² and web areas 20,000 mm². The connected shell
T-junction has three elements incident on one edge; this is an assembled shell
junction, not a manifold surface suitable for every surface-remeshing algorithm.

Run the fixture-only checker (Python standard library, no upstream algorithm copies):

```sh
python3 X/Feasibility/ShellJunction/check-fixtures.py --output .project/reports/shell-junction/fixture-contracts.json
```

It verifies hashes, element/node identities, shared edges, distinct-ID coordinate
coincidence, areas and gap, and rejects two deliberately broken contracts. Its
tiny supported grammar is only *NODE and S4 *ELEMENT/ELSET records; it is not a
general INP parser. Hashes/expected values in manifest.json are hand-specified;
the checker does not generate its own expected topology.

Windows follow-up: import each input in a fresh original PrePoMax session,
record application identity and actual counts/connectivity, save/reopen PMX,
preserve PMH/input dependencies and export the deck. Input-only compatibility
and ELSET-to-part behavior are still unverified in the real application. Recreate
the stated midsurfaces as CAD surfaces for separate-part/compound meshing
comparisons; imported orphan shell meshes alone cannot prove automatic CAD meshing.

F001 remains Proposed; an automatic connection policy and production behavior
are not chosen. See [fixture report](../../../.project/reports/shell-junction-fixtures.md).
