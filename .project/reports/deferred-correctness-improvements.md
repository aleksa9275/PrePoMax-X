# Deferred correctness fixes and improvements

Maintainer direction, 6 November 2026, D061: record the findings/proposals and
continue the existing implementation toward full PrePoMax 3.0.0 parity first.
Implement fixes and improvements after that milestone. These proposals are a
post-parity backlog, not the next engineering increment. The earlier suggestion
of a combined correctness increment is superseded by this sequencing decision.

The target remains IDENTICAL original functionality on all four targets, with
the unavailable Intel/PARDISO solver as the sole exception (D060). Preserve
original algorithms, conversions and existing tolerances during the parity
phase. Continue necessary port/integration repairs to reproduce original
behavior; this deferral does not defer missing original functionality. Keep
known failures explicit, existing measurement safeguards and reference evidence
intact. Deferral does not mark an analytical failure passed or close a numerical,
exact-parity, platform or release gate. Do not let these inherited findings halt
unrelated functional implementation.

## Recorded findings and proposed post-parity work

| Finding | Evidence/status | Deferred proposal |
|---|---|---|
| D029 quadratic tetrahedron measurement integration | Straight tetrahedron, volume 4, affine field 2+x+2y+3z: integral 26.794910717854155 versus exact 28 (4.30% low). Original quadrature weights sum to 1/6, but each first moment is 0.03915606399552952 versus exact 1/24. Source-level discrepancy; original code unchanged. | Correct the point/weight table against independently verified moments; check straight and curved elements before enabling the affected measurement path. Native CalculiX C3D10 solving uses its separate formulation and remains operational. |
| D029 quadratic pyramid classification | Both original FeElement.IsParabolic overloads omit ParabolicPyramidElement. Explicit current dispatch avoids the helper; no resulting numerical field corruption has been demonstrated in the current workflow. | Include the quadratic pyramid in both overloads and check affected callers. |
| B006 quadratic pyramid → collapsed wedge under pressure | Maximum displacement error 3.7943e-5 mm and stress error 0.047 MPa against the 1 MPa analytical case. Reproduced on native Mac/Linux ARM64 and by the pinned original Windows solver through CrossOver. Hexahedron conversion passes that case; both routes remain selectable. Underlying cause unresolved. | Isolate equivalent pressure forces, degenerate-element stiffness and stress extrapolation using integration-point/nodal output, then correct the responsible conversion or solver routine. The hexahedron route is the current example's explicit workaround, not a proven general numerical correction. |
| Small identical-deck solver field differences | Latest native/original Windows comparisons: displacement values identical, maximum stress differences approximately 1e-12 to 1.41e-6 MPa. Earlier curved case has displacement differences about 2e-16. No engineering error established from these differences alone; precise cause unproved. | Investigate build/compiler/backend/arithmetic-order effects. Make a numerical change only if the cause and need are demonstrated; retain exact comparisons and existing accuracy bounds. |
| Cross-platform CAD meshing differences | One six-body fixture: Mac 402 nodes/898 C3D4 elements, Linux ARM64 402/900. Both meet its analytical checks. Other curved CAD meshes also differ. Exact native mesh/deck/field parity remains open; positional result arrays from different meshes are not comparable. | Audit native dependencies, build options, ordering and supported reproducibility controls. Compare geometry and fields at common locations while diagnosing exact-mesh differences; no claim that these measures guarantee identical topology. |

Additional finding, 7 November 2026: [B007](../bugs/B007-buckling-search-shift.md)
records original buckling mode selection near its unit search shift. A tenfold
reference-load increase omits the lower factor expected near 0.25661845; both
native and original Windows solvers report 1.0216758 first. Post-parity proposal:
review shift management and mode-selection/refinement with reference-load
scaling and competing modes. No solver change or automatic load rescaling is
made; D061's sequencing applies.

Sources: [original element findings](shared-element-kernel.md),
[B006](../bugs/B006-quadratic-pyramid-wedge-pressure.md),
[latest native/original comparisons](nonlinear-loaded-solids.md),
[curved quadratic comparison](quadratic-native-static.md) and
[Mac/Linux mesh differences](cad-mirror-scale-copies.md).

Already repaired port/integration defects remain repaired: duplicate element-set
emission/stress rows (B001), exported block identity loss (B003), field-only job
output classification (B004), solver node-format overflow (B005), and original
FRD/VTK display-order integration. This decision does not revert those repairs.
No numerical/application/build/test change is made by this record.

7 November 2026 thermal-control diagnostic, tasks 0098–0100: for k(T)=1+.01T
on a unit rod with 0/100 °C ends, original one-increment nonlinear heat-transfer
controls produce a maximum stored nodal temperature error .07975413 °C against
T=100(sqrt(1+3z)-1), failing the .002 °C analytical check. Explicit original
increments .05/.025 reduce it to .00264386/.00134386 °C; the example selects
forty increments explicitly. The pinned original Windows solver reproduces the
coarse result. Keep that accuracy diagnostic false; no default, tolerance or
solver change is made. Post-parity investigation: isolate nonlinear convergence
and spatial/time-control effects before proposing any change. This observation
does not establish a general solver defect or defer thermal functionality.
[Native/original evidence](radiation-amplitudes-thermal-stress.md).

7 November 2026 structural increment: [B008](../bugs/B008-original-structural-diagnostics.md)
records original quadratic-membrane, T3D3, CIRC-beam and stored shell/beam force
observations, plus the explicit original T2D3 refusal. Independent failures remain
false and original-Windows comparison evidence is retained. Root causes/modeling/
result-semantics interpretations remain open; no algorithms/tolerances/forces are
changed. D061 sequencing and every functionality/correctness/release gate remain.

7 November 2026, tasks 0107–0110: [B009](../bugs/B009-modal-beam-and-invariant-diagnostics.md)
retains the original/native modal-beam crash after explicit zero-load basis DOF
initialization and the strict signed-principal-stress tie discrepancy in implicit
beam transient output. Original Windows reference evidence is through CrossOver;
root causes remain unresolved. No numerical change, sign normalization or existing
tolerance change. The separate zero-exit solver-error completion check is an
integration repair and retains the failed calculation as failure. D061 and every
original functionality/platform/release obligation remain.

8 November 2026, Phase A ([report](phase-a-domain-libraries.md)): building the
whole original libraries for .NET 10 recorded: original `CalCLoad` writes global
directions when its local coordinate system cannot be resolved; `BinaryFormatter`
clone paths (`DeepClone`, `Selection` copy constructor) need Phase B allowlisted
serialization; Windows-only APIs reachable on all platforms (registry/WMI in
`Tools.cs`, `AnalysisJob.IsAdministrator`, bitmap export, `GmshAPI`
`Thread.Abort`); missing Q-Morph `QuadMesher` source; GmshCommon quirks
(`OCC.Remove` with (0,0) pairs, `GetMaxNodeTag` int truncation); 83 compiler/
analyzer warnings including `CS1717` in `Tools.cs`. Platform API repairs are
port work for Phase B; the rest waits for the post-parity fixes.

C2 warning follow-up, 8 November 2026: generated nonvisual form adapters retain
original selection-sentinel branches and some presentation-related fields. The
portable draft keeps its selection graph directly, so CS0649/CS0169 report
inactive fields in these generated classes. Review/remove those adapter fields
in the post-parity warning pass; do not edit the generated file independently
of its original-source generator. The C2 legacy encoding-provider startup gap
and stale computed-property writeback were port/integration defects and are
repaired now; no original numerical algorithm/tolerance changed.

C3 follow-up, 9 November 2026: generated nonvisual geometry/mesh adapters retain
some original presentation fields and the inactive modal-regeneration branch.
CS0169/CS0414 and CS0162/CS0642 are recorded for the post-parity generator cleanup,
alongside the existing original warnings. Keep the generator and generated rules
in sync. Reused Controller history needed separate per-invocation portable native
logs; that integration defect and dynamic draft-field flushing were repaired now.
No original numerical algorithm, tolerance or mesher version changed.

C3 cancellation audit: original `ExecutableJobRunner.RunConcurrently` creates
local job objects, whereas `Kill` only stops `_executableJob` assigned by `Run`.
Cancellation of concurrent CAD visualization/import stages is therefore not
accepted; see [B010](../bugs/B010-concurrent-cad-cancellation.md). Preserve the
original behavior under D061 and address this in the post-parity correctness
pass; do not claim the new Cancel control covers every native stage.

9 November 2026 C4 closeout: [B011](../bugs/B011-c4-linear-cube-stress-diagnostic.md)
retains the failed 200 doubled-stress expectation (actual 199.99200439453125,
absolute tolerance .001); original Windows PMX readback gives identical stored
values, without establishing the cause. [B012](../bugs/B012-analysis-cancellation-before-start.md)
records cancellation before process initialization; active-child cancellation
passes separately. Neither finding is marked fixed. Original/generated unused
field/unreachable/modal-path warnings remain deferred; C4 does not suppress them.

## C5 application/UI audit (9 November 2026)

C5 reuses original application/property/automation/query/plotting rules. No
engineering tolerance/algorithm change was made. B011 remains failed and B010/B012
remain open; script Stop is not a native-job pre-start/concurrency fix. See the
[C5 report](phase-c5-application-tools.md) and [72-form source audit](phase-c5-ui-audit.json)
for unaccepted control/input/viewport matrices; these are parity work, before the
post-parity correctness sweep. New original-source build warnings include existing
reflection/nullability/unused members and platform annotations in original plot/
settings/RPC code. Do not suppress them or alter algorithms to make checks pass.
The Linux video-decode dependency failure (`libpulse.so.0`) was a test-image
integration issue, resolved with `libpulse0`; hardware decode remains unavailable
and verified AVI frames use CPU decoding. No backend/solver/library version changed.
