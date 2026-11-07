# Preparation exit gates — 2026-10-15

This is the next-work sequence following tasks 0002–0009, not a production
architecture decision or a release acceptance claim. See [test strategy](../TEST_STRATEGY.md)
for the full eventual platform/feature matrix. Complete bounded investigations
and review the remaining risks before beginning shared-core/frontend extraction.

Required targets, corrected by the maintainer on 2026-10-15: Windows x64,
Linux x64, Linux ARM64 and Apple M-series macOS ARM64. Intel Macs are excluded.
Resume using the [Windows-session handoff](../history/handoffs/windows-next-session.md).

Task 0012 [local follow-up](local-preparation-completion.md) adds shallow PMX
value comparisons with explicit job-settings drift, a successful synthetic
solver reference, VTK parent-ID/lifecycle checks and Linux compiler controls.
The ARM64 default -O2 failure is retained; diagnostic contraction-off passes.
These findings narrow the remaining gates without closing semantic/history,
native source/tool, genuine UI or production-policy requirements.
Native Linux x64 public research execution subsequently
[passed](research-linux-x64.md); private legacy-file execution there remains open.

| Priority | Verified observation now | Next bounded work and exit criterion |
|---|---|---|
| 1. Persistence meaning and history | One 2.5.1-dev project opens, saves and reopens in original Windows 2.6.0 through CrossOver. Selected custom model/result bytes are preserved; NRBF changes are recorded. | Compare engineering entities, units, materials, sections, sets, steps, BCs and loads using explicit semantic snapshots. Explain job/environment-field changes. Capture history regenerate/undo/redo and a results-free save, with original copies preserved. Accept only explained changes; a displayed model or type inventory cannot close this gate. |
| 2. Platform repetition | Earlier core/data probes passed Mac ARM64 and native Linux x64. PMX tests/private inventories pass Mac/Linux ARM64; new structured Linux checks expose contraction sensitivity. | Record native Linux x64 research CI, repeat PMX/kernel checks on Windows and resolve the Linux ARM64 numerical build-policy gate. Both Linux architectures are required. Keep exact source/input hashes and distinguish diagnostic compiler settings from production defaults. |
| 3. Matching native source | Native audit identifies patched Gmsh access failure, external NetGenMesher/nglib and QuadWild modifications, and absent QuadMesher implementation. | Recover exact source revisions, patches, build flags and license/source notices. Reproduce a small original Windows meshing case before cross-platform builds. Use the existing [source-recovery packet](native-feasibility.md); contacting upstream needs the maintainer's instruction. This work can proceed alongside persistence checks. |
| 4. Interactive rendering | Synthetic native Mac VTK renders and programmatic picks pass. Clipping drops FEM global-ID arrays. | Prove explicit ID provenance through clipping, point/rectangle selection and deformation on mixed element orders. Exercise actual pointer input, Retina scaling, resize and repeated create/destroy on candidate hosts. Record failures and license/build routes before selecting a frontend or binding. Later repeat on all required target platforms. |
| 5. Reproducible engineering workflow | No mesher/solver/history regeneration ran in the CrossOver experiment. Shell-junction inputs are hand-authored contracts only. | Establish a tiny analytical solve with pinned solver/version, input deck, expected displacement/reaction and FRD/DAT results. Compare original-reference and native execution. Add a real CAD shell T-junction meshing reference with exact shared node IDs, preserved part/section assignments and an intentional-gap control. This establishes a baseline for F001, not implementation of the feature. |

## Reference corpus to capture next

Start with small controlled, shareable models rather than requiring more private
production projects. Include a minimal solid; a shell model with separate part
thickness/material assignments; and a shell T-junction plus intentional-gap case.
Save each without results and with a completed analysis where applicable.
Capture a deliberately short command history and its regeneration outcome.
Record producer binary hashes, header/version, units, exact IDs/connectivity,
sets/assignments, load/BC/step values and solver/native-tool versions. Existing
private files remain local; only approved shareable fixtures belong in Git.

The supplied production model remains valuable as a larger regression reference,
but it cannot represent every PMX version or feature. CrossOver is available now
for supplementary original-application observations. Native Windows is still
needed to distinguish Wine behavior and to establish the Windows reference/build
route. The released 2.6.0 binary lacks the newer repository's script/RPC switches;
do not promise automated fixture capture through those switches.

## Decision after these investigations

Architectural inference: these checks should support a bounded first shared-core
change, not another round of general audits. Review whether legacy import can
preserve engineering meaning/history, required native sources are obtainable and
an open-source interactive VTK host is viable. Then choose and authorize the next
implementation slice with its Windows regression check. A portable schema remains
a [proposal](../proposals/portable-document-schema.md); no default file-format,
frontend or production dependency is selected here. Full feature parity, all
four required native targets and packaging remain later release gates.
