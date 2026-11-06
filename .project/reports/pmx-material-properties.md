# Persistent original PMX material properties

Task 0071 extends the checked single-part CAD/C3D4 PMX desktop editor with
Poisson's ratio and density (tonne/mm³). Modulus, material tables, named regions,
original CAD, mesh and command history retain their original owners. The C3D8
editor and standalone mesh exporter keep their existing contracts.

The public NRBF decoder validates the graph and identifies editable owners.
A bounded MS-NRBF wire index locates their exact member slots. An edited member
gets a fresh string ID; any original inline string definition is retained before
MessageEnd so existing references keep their original value. No payload types
are activated. Unsupported wire shapes fail closed. Original model-frame bytes
and all graph bytes outside edited slots/string-definition relocation remain.

Nineteen Mac contract checks pass, including repeated editing, a shared string,
invalid physical values and malformed input. Twenty real desktop checks pass:
edit, Save As, reopen, native CAD display, frozen original PMX and native solve.
The pinned original Windows 3.0.0 executable under an isolated CrossOver bottle
reopens the edited file, exports a deck and resaves equal projected semantics.
Its exported deck and the native reconstruction produce exactly equal original
decoded nodes, elements, value order and all result fields using the same native
solver. No numerical tolerance changes.

[Verification](pmx-material-properties-verification.json). Detailed local evidence:
`/tmp/prepomaxx-task0071-evidence`. The sandbox display-less test attempt is
retained; actual display-enabled desktop tests are recorded separately. Linux
ARM64 changed-area checks and one combined package follow at task 0073 closeout.
The current task 0070 candidate stays available until its replacement is verified.

New native-session serialization/general PMX, broader materials/analyses,
Windows native execution, both correctness failures, quadratic tetrahedra and
all parity/release gates remain open. D058 forbids hosted CI and D059 defers x64.
