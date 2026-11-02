# Task 0042 — Local macOS solver preview DMG

3 November 2026. Maintainer requests a local-installable Mac DMG while Developer
ID signing/notarization are unavailable, and explicitly chooses desktop solver
controls before the first DMG. This moves the bounded solver UI/package increment
ahead of the remaining native viewport binding attempt; it does not select the
frame-copy bridge as the production renderer.

Plan and scope:
1. Add shared desktop job start/cancel/status/output controls using the existing
   C# run-static host and original deck/job/readers. Support the current bounded
   static analysis JSON plus INP mesh, include a working synthetic cube example,
   and open successful FRD results. Preserve diagnostics and fresh job folders.
2. Bundle the verified Mac CPU solver and its non-system runtime closure, rewrite
   load paths within the package, retain original/relocated hashes and explicit
   research profile identity. No Homebrew/SDK dependency at execution time.
3. Add a shared package --format dmg path. Build an ad-hoc-signed internal preview
   with app, examples, installation/scope notes and Applications shortcut. No
   Developer-ID/notarization claim, security setting change or quarantine removal.
4. Verify meaningful cancellation/failure boundaries, real packaged cube, visible
   contours/IDs, signature, DMG integrity and copied-app execution from a path with
   spaces without external Python/dotnet on PATH. Record exact artifact hash.
5. Commit/push source and progress normally to origin research. Deliver the local
   DMG path; do not commit binaries or claim a public signed release.

Apple container runs Linux VMs/containers, not a macOS desktop guest. It may be a
later Linux compute check, not a DMG/GUI/signing test environment. Native Mac
verification comes first; a clean macOS account/VM/second Mac remains a separate
acceptance checkpoint. No new container installation is needed for this increment.

Scope remains an internal static-solid workflow preview; original full model/
PMX/CAD/meshing/history/other-backend parity is pending. Preserve both known
correctness failures/tetra gate, shared source/four targets and release gates.
