# Shell, membrane, beam and truss workflows

Tasks 0105/0106 connect steps 3/4 of the requested element-family plan at the
imported-mesh static-workflow boundary. They follow the published plane/
axisymmetric increment, a3a18ae8. The maintainer requested proceeding directly
from the first two milestones to these two; a combined candidate follows.

## Delivered original functions

Element formulations… preserves source identities while selecting compatible
original types. Six shell formulations S3/S6/S4/S4R/S8/S8R and six membrane
formulations M3D3/M3D6/M3D4/M3D4R/M3D8/M3D8R are connected. Native line examples
cover B31/B31R/B21/B32/B32R and T3D2/T2D2/T3D3. The original T2D3 alias is retained
for mesh transport but explicitly fails in both native and pinned original
Windows CalculiX 2.22; no silent replacement or new solver exception is made.
Other import aliases are not claimed as exhaustively solver-verified here.

Configure → Sections selects solid, shell, membrane, beam, truss or composite.
Original ShellSection/CalShellSection and MembraneSection/CalMembraneSection
supply thickness/offset. Original displacement/rotation and moment owners add
rotational supports and global nodal moments, with region/DOF compatibility.
Original CalDLoad supplies explicit normal shell-side pressure (S1/S2). Surface
normals follow input connectivity. The ordinary field-output dimension control
selects original default/2D/expanded-3D output for structural models.

The source pin has no dedicated beam-section or composite-layer domain object.
A bounded configuration descriptor uses original section objects for region/
material ownership and the unchanged CalculixUserKeyword for the solver section
card, matching the original manual-keyword route. RECT/CIRC beam dimensions and
nonparallel direction 1, truss area and positive ordered isotropic composite
layers are explicit. S8R/S6 composite topology is checked against the unchanged
solver source. This is tool/job configuration, not new PMX serialization.
Anisotropic materials/orientation breadth and general user-keyword editing remain
required follow-up model functionality; they are not claimed implemented.

Original INP line factories decode the original MeshPart aliases at the portable
boundary and restore exact formulation names without changing node ordering or
broadening prefix fallbacks. Original FRD readers/field math decode expanded
shell/beam meshes and unexpanded membrane/line output. Layer-expanded FRD can
contain more element records than its original-element header declares. Frozen
decks carry an explicit original/expanded count pair; the reader checks both,
retains actual layer elements and reports OriginalElementCount separately.
Unmarked mismatches, incomplete blocks and wrong declared expansion are refused.

Ten bundled examples cover shell/membrane tension, a quadratic-membrane
reference diagnostic, shell pure bending, symmetric three-layer extension,
mixed line tension, rectangular/circular beam bending, quadratic centerline output and shell normal pressure.
Configuration, immutable native jobs, original fields/histories/CSV, deformation/
outline and original-source mesh export/reopen are connected. Broader analysis
combinations remain step 6, mesh authoring step 7 and full PMX step 8.

## Actual verification and explicit diagnostics

[Receipt](structural-elements-verification.json) records source/native/reference
checks and publication/candidate state. Mac and native Linux ARM64 complete the
nine workflows (143 functional checks each). Decks, decoded meshes and fields
match exactly across these hosts. Identical decks run with the fingerprint-
checked original Windows CalculiX 2.22 under CrossOver: all recorded field/history
comparisons pass existing 1e-6 absolute/relative bounds; largest field difference
is about 1e-8. This is not native Windows application or Linux x64 acceptance.

Independent checks reproduce linear membrane/shell tension, shell tip bending
-.075, rectangular-beam tip bending -.25 and shell-pressure tip bending -.018755
versus continuum -.01875. The symmetric layered shell has mid-span strain .001
and separate layer stresses near 1 and 2, with 40 original/120 expanded elements.
Seven line formulations reproduce the axial solution to about 5e-18 displacement.

[B008](../bugs/B008-original-structural-diagnostics.md) retains the failing
quadratic-membrane displacement/stress checks, quadratic-truss stiffness and
circular-beam continuum comparisons, and stored shell/beam force-resultant
observations. The original Windows solver reproduces the recorded stable cases.
The free quadratic-membrane exploratory case has very large responses; its raw
outputs remain retained separately. Root causes and appropriate modelling/
postprocessing interpretations remain unresolved. No numerical fixes, force
renormalization, expectation replacement or relaxed existing tolerance is made.
Full numerical acceptance remains false, including these observations and all
prior D029/B006/B007/thermal/axisymmetric findings. T2D3 refusal stays open too.

Current Core/Analysis/Execution/Results suites pass, with 219 source identities,
74 static-deck checks, 84 results/history checks and all existing numerical gates.
All 88 desktop tests pass, including eight new structural behaviors. A new
French-culture regression exposed lazy moment/section quantity evaluation across
formatting cultures. The boundary now evaluates original quantities in caller
culture and freezes numeric keyword snapshots in invariant culture; the old
French-material regression still passes. Original converters/math are unchanged.
Initial build/closure/helper/culture failures and their raw logs remain in evidence.
The disposable Linux Xvfb-as-PID1 launch stall is retained; the established shell
wrapper completes the checks. The first copied candidate passes both viewports and existing plane/dynamics/
thermal/thermomechanical/eigenmode/nonlinear/PMX regressions. An additional 2D
quadratic-line check exposed missing FRD descriptor 12 in the original reader.
Portable erased hooks now map its ASCII/binary end/end/midpoint records to the
unchanged original ParabolicBeamElement, following unchanged CalculiX frd.c.
Original net48 behavior/math remain unchanged. The dedicated ASCII/float/double
regression passes, and the centerline example returns tip -.25. A refreshed
candidate follows this transport repair.

All original material/orientation, interaction/contact, mixed-family calculation,
mesher/editing/results/PMX and four-target/distribution/release requirements stay
open. D057/D058/D059/D060/D061 remain; hosted CI is skipped and native x64 stays
deferred. Unavailable Intel/PARDISO remains the sole solver exception.
