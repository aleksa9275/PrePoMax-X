# Native desktop CAD editing

Tasks 0074–0077 bring the task 0066 original command implementations into the
native desktop. Task 0074 adds selected-part translation with explicit model-unit
X/Y/Z values. It retains unselected BREP/VIS bytes and all original source data.
The analytical box moved by (7,-3,5) matches the original Windows output BREP
exactly and has the expected volume/center. Twelve initial native checks pass.

An owned transaction copies inputs, runs the pinned native command, splits and
decodes every resulting part, checks source/runtime identity, then publishes the
new document on the GUI thread. Failure/cancellation retains the previous CAD,
mesh, regions, analysis and unsaved state. Successful edits discard dependent
mesh/analysis only after confirmation and publication. Geometry edits retain
their recipes, exact command inputs/outputs, part-origin mapping and tool identity
in subsequent frozen jobs. An opened PMX cannot have its geometry mutated by
this path; the original PMX rewriting boundary remains explicit.

The lifecycle checks cover errors, cooperative/late cancellation, deferred
closing, successful invalidation and PMX mutation refusal. A first harness run
waited on an unintended discard prompt; the harness now supplies its response.
Native Linux ARM64, the next three operations and combined copied-app evidence
follow at task 0077 closeout. Detailed local evidence starts at
`/tmp/prepomaxx-task0074-evidence`.

New native-session PMX persistence, broad defective-geometry repair, additional
CAD operations, both correctness failures, quadratic tetrahedra and all parity/
four-target/installer/signing/notarization/release gates remain. Preserve D058's
hosted CI hold and D059's deferred Windows/Podman Linux x64 verification.
