# Task 0043 — Bounded native viewport boundary (proposed next)

3 November 2026. Maintainer reports the task 0042 local DMG test went well and as
expected. This is a user-reported pass of the current preview on the existing Mac;
no separate uninstall, clean OS or wider engineering test details were supplied.

Next engineering increment under the accepted delivery plan: resolve one bounded
native VTK widget/host attempt, including the practical C# binding route, before
expanding production dialogs. Do not begin another broad framework survey or
silently select the frame-copy bridge as the production viewport.

Deliverable: a packaged prototype that visibly renders the common fixture,
preserves original FEM IDs/scalars, handles pointer selection/rotation/resize and
closes cleanly. Measure a representative larger mesh (load time, interaction and
memory) against the existing bridge. Record actual host/dependency/source identity.
If the attempt is blocked, record its exact prerequisite and concrete tradeoff
for the maintainer; the existing tested DMG remains available as the harness.
No successful binding/performance outcome or production frontend choice is claimed.

Subsequent product increments, in order:
1. First editable solid analysis: model tree, material, supports and loads through
   original C# services; configure → solve/cancel → inspect results in the app,
   without requiring hand-edited analysis JSON for this supported slice.
2. Save/reopen the supported slice, with an explicit persistence decision and
   preservation of original model identities/units. Do not silently introduce a
   replacement PMX format or unsafe serialization to make the preview appear full.
3. Add the thin-shell workflow and expose supported DAT histories. Publish the
   next local DMG with updated install/reset notes and concrete bug/run evidence.
4. At that integration checkpoint, repeat available four-RID builds and exercise
   native Linux ARM64/Windows workers and Debian/Fedora/Arch packaging as available;
   keep Linux x64 compute feedback continuous. Record missing environments honestly.

Use affected current-source checks and the relevant packaged smoke during routine
work. Historical/full distro/desktop matrices remain milestone checks. Signing/
notarization can follow when available; they do not block internal local previews.
Both known correctness failures/tetra gate, B002 and full release requirements stay.
This record is a proposed next increment, not an implemented feature or new policy.
