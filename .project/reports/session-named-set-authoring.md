# Session named set authoring

The desktop static analysis toolbar adds **Add set…** for node and element sets.
Enter original mesh IDs or use the currently picked element or nearest vertex
to seed the list. The new sets appear in the model tree and assignment choices.
The mesh host appends a set to a session copy, validates it through the original
INP reader, and returns the updated mesh snapshot. Set edits invalidate prior
analysis validation. The job host freezes the updated input on submission.

On macOS ARM64, the Qt tests check assignment choices, validation, invalid IDs
and duplicate names, and a nonsequential picked ID passed through the dialog.
A native CalculiX job used the authored node set for the applied force and the
authored element set for the solid section. All seven existing cube analytical
checks passed, including 100 MPa axial stress and force balance.
[Native solve receipt](session-named-set-solve.json).

This was a source desktop run with an explicit native solver registry. It
covers session creation and one picked ID as a seed. Multi-pick, set replacement,
deletion, project persistence and packaged acceptance are separate work.

All 14 current desktop tests passed on macOS. Offline Linux ARM64 built and
ran the mesh host, rejected a case-insensitive duplicate name, and emitted
byte-identical node and element set meshes for the nonsequential fixture.
[Linux mesh host receipt](session-named-set-linux-arm64.json).

## Packaged macOS verification, 4 November 2026

One task 0047 ad-hoc signed local DMG was built from 90939dc5 plus the
retained working-tree source snapshot. Image verification, read-only mount,
strict signature checks, copy, eject and copied bundle hashes passed.
The copied app passed 11 baseline GUI checks and seven analytical checks
with external build tools absent from PATH.

Both the default frame bridge and opt-in Cocoa viewport passed 24 GUI
checks and 21 deck, numerical and rejection checks each. The probe creates
both sets through the actual Add set dialog, selects them in the analysis
dialog, and verifies their membership in the frozen input and executed deck.
The edited solve uses 105 GPa and 50 N per node and reproduces the existing
200 MPa axial-stress and fourfold-displacement expectations.

The retained candidate is
`X/Build/artifacts/task0047-delivery/dist/PrePoMax-X-Preview-arm64.dmg`.
Seven duplicate generated directories were removed after verification.
Build and test receipts, source snapshots and job results are retained.
[Package and cleanup receipt](session-named-set-packaged-macos.json).
