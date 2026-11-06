# Native desktop CAD editing

Tasks 0074–0077 bring the task 0066 original command implementations into the
native desktop. Task 0074 adds selected-part translation with explicit model-unit
X/Y/Z values. It retains unselected BREP/VIS bytes and all original source data.
The analytical box moved by (7,-3,5) matches the original Windows output BREP
exactly and has the expected volume/center. Twelve initial native checks pass.

Task 0075 adds selected-part plane splitting. Original BREP_SPLIT output and its
source-solid origins are retained, then the original explicit solid-separation
command creates individually owned result parts. The ordinary CAD import's
compound grouping remains unchanged. The checked mid-height split yields two
1,000-volume solids with the original Windows BREP hash, while the untouched
second body remains byte-identical. The initial compound-import attempt is
retained; the final native translation/split checks pass. Zero and nonintersecting
plane definitions are refused without publishing a replacement document.

Task 0076 adds original ShapeFix option 1 repair with an explicit finite positive
tolerance, bounded to at most one model unit in this preview. The valid-box BREP
matches the retained original Windows repair exactly; both bodies' measurements
and unselected bytes remain. Invalid tolerances and changed in-memory edit history
are refused. Repairing defective geometry broadly is still unverified.

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

Task 0077 adds selected-part STEP export. Native conversion and reimport run in
the worker; the GUI publishes checked bytes atomically to a new file. A sibling
staging directory keeps that final link on the destination filesystem, fixing
the first Linux bind-mount EXDEV failure without allowing overwrite. Export
preserves the active geometry, mesh, analysis and unsaved state, including when
reading geometry from a checked PMX preview. It is geometry exchange, not PMX
session persistence.

The Mac and offline Linux ARM64 transaction suites each pass 33 checks against
analytical measurements and the retained original Windows command hashes. No
new Windows GUI run is claimed. Desktop regressions pass 44 tests and build
guards pass nine. The source desktop completes all four real dialogs, remeshes
three edited bodies (208 nodes/885 C3D4 elements), freezes all edit inputs/recipes,
solves with native CalculiX and reopens the selected-part STEP. Every node passes
the existing affine-displacement/unit-stress checks, with no tolerance changes.
Final copied-app/visible-contour verification follows in the closing receipt.

New native-session PMX persistence, broad defective-geometry repair, additional
CAD operations, both correctness failures, quadratic tetrahedra and all parity/
four-target/installer/signing/notarization/release gates remain. Preserve D058's
hosted CI hold and D059's deferred Windows/Podman Linux x64 verification.
