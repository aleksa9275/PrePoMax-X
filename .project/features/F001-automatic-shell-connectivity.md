# F001 — Automatic shell-junction connectivity

Status: **Proposed**. Recorded 2026-10-14 (Europe/Belgrade).
Source: maintainer suggestion in conversation; initial geometry confirmed as
**shell surfaces**. Priority and scheduling: unset. Implementation is not
authorized by this record; no application code has changed for this proposal.

## Maintainer input and problem

The maintainer reports that a compound part is currently needed to obtain a
connected mesh at joints such as a T-profile on a plate. The desired improvement
is to ease modeling work and make the mesh "unified always or as far as
practically aplicable." This describes the requested outcome, not a verified
claim that every existing mesher requires compounds in every case.

Initial example: a shell web meets the interior of a shell plate along an
attachment line. Elements on both surfaces should share mesh nodes along that
line when the modeled connection is intended to be continuous.

## Desired behavior and boundaries

- Generate compatible mesh topology along intended connected shell junctions
  without requiring the user to create a compound part manually.
- Use shared node IDs/connectivity at the joint, rather than only coincident
  node coordinates. Preserve separate part identities, shell thicknesses,
  section/material assignments and meaningful named selections.
- Preserve explicitly disconnected interfaces, contact and intentional gaps.
  The connection policy and user override need review; global node welding is
  not an agreed policy.
- Preserve the meaning of loads, boundary conditions, surface orientation and
  shell offsets through meshing, remeshing and command replay.
- Explain unsupported or ambiguous joints and leave the model recoverable.
  Do not silently bridge gaps, move surfaces or change physical connections.

Initial scope is shell junctions. Solids, mixed shell/solid connections, beams,
imported orphan meshes and nonmatching-mesh coupling are separate scope questions.
This is a behavior improvement beyond upstream parity, not a prerequisite for
declaring the current portability probes complete.

## Evidence and candidate approach

**Verified source observations** at upstream baseline
`de8f73032a72746e3d6d9afd53d9fbd289eb310a` (source inspection, not live meshing):

- [Controller](../../PrePoMax/Controller.cs):
  `CreateAndImportCompoundPart` and `CreateBrepCompoundPart` provide existing
  compound creation paths; CAD creation invokes the native `BREP_COMPOUND` route.
  `MergeCoincidentNodesCommand` executes through the existing command history.
- [FeMesh](../../CaeMesh/FeMesh.cs): `MergeCoincidentNodes` maps node references
  and removes merged nodes. This operates on existing mesh nodes.
- [NodesAPI](../../APIs/Python/Model/Mesh/NodesAPI.cs): `merge_coincident` exposes
  that operation through the existing Python mesh gateway and command history.
- [GmshAPI](../../CaeMesh/Meshing/Gmsh/GmshAPI.cs):
  `FragmentVolumesWithCurves` invokes `OCC.Fragment` and maintains geometry-ID
  mappings. It handles volumes and carried curves/points; it does not establish
  automatic connectivity for arbitrary shell assemblies.

**Architectural inference:** when plate elements cross the web attachment
line, merging existing coincident nodes alone cannot supply the missing mesh
edges. Preparing shared topology along that line and meshing the participating
surfaces consistently is a candidate approach. An internal meshing group could
remove manual compound creation while preserving user-visible parts.

**Experimental questions:** can the existing compound/native mesher paths
produce the required shell topology and preserve entity mappings? Where are
imprinting or embedding needed? Investigate these paths and their matching
native sources before selecting an algorithm, replacement gateway or tool
version. No new mesher, production dependency or serializer is selected here.

## Candidate acceptance cases

1. A shell T-junction, including an attachment line inside a plate face:
   both sides use the same node IDs along the full intended joint, with no
   unintended disconnected segments or degenerate elements.
2. Different requested mesh sizes on the web and plate: the joint remains
   conformal, and element quality is measured against reviewed criteria.
3. Distinct materials/thicknesses and named loads/selections: assignments
   survive meshing and remeshing; exported solver connectivity reflects the joint.
4. A deliberate gap or contact interface: surfaces remain disconnected under
   the chosen policy. Include a near-coincident case to test tolerance handling.
5. Undo/redo, history regeneration and PMX save/reopen: preserve the connection
   intent and mappings. Compare semantics, not arbitrary generated node numbering.
6. A simple independently specified shell load-transfer problem: compare
   reactions/displacements with a manually prepared connected reference using
   pinned solver identity and reviewed tolerances. Visual coincidence is not
   numerical evidence.

These are proposed acceptance criteria, not completed tests. No Windows model,
live mesh, rendered inspection or solver result has been captured for F001.

Fixture preparation completed 2026-10-14 under task 0007:
[four hand-authored shell mesh cases](../../X/Feasibility/ShellJunction/README.md)
and a geometry/topology manifest now specify connected, coincident-disconnected,
unsplit-plate and intentional-gap behavior. Four contracts and two checker
regressions pass; see [evidence](../reports/shell-junction-fixtures.md). These
are mesh definitions, not CAD/mesher-generated or Windows-observed references.
The proposal status and implementation gate remain unchanged.

## Open questions and next review

- Should connectivity be a model default, an explicit meshing option or a
  per-interface instruction? How does the user preserve intentional separation?
- How should tolerances depend on units and geometric scale? Are any geometric
  repairs allowed, and how should they be reported?
- How should shell offsets, nonintersecting midsurfaces and finite weld geometry
  affect the idealized connection? Shared nodes alone do not resolve those choices.
- Which current mesher and supported element orders can satisfy the first case?

Next review: capture a small shell T-junction and its manual compound reference
on the Windows machine when available, retaining geometry, PMX/history, exported
deck, mesher/solver versions and observed connectivity. Windows work is deferred
until the maintainer returns to that machine. Keep this proposal separate from
the pending [PMX/history reference gate](../reports/windows-fixture-capture.md).
Approve a bounded investigation task before beginning meshing implementation.
