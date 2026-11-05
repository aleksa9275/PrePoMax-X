# Task 0064 — Native desktop CAD import

Connect the recovered and natively built original Netgen/OCCT runtime to the
existing background CAD importer with an explicit `--cad-native` option.
Verify the local build receipt and runtime hashes before and after conversion.
Preserve cancellation, all-parts publication and source part/face IDs. Exercise
native STEP and multi-part BREP imports in the actual Mac viewport.

The original exact Windows replay remains a separate unchanged check. Record
native triangulation/rounding differences and the new fixture coverage bounds;
do not claim exact visualization parity or broader CAD/release acceptance.
