# Third-party source area

Newly recovered third-party sources live here by component and exact version.
Keep upstream files unchanged; record local changes separately as reviewed patch
files and pin the original archive/revision, every source file, license and build
provenance. Generated objects, native runtimes and downloaded archives belong in
ignored build/cache directories or versioned release artifacts, not source trees.

| Component | Recovered source | Correspondence / release status |
| --- | --- | --- |
| CalculiX CrunchiX 2.22 | [source and provenance](CalculiX/2.22/README.md) | Official source recovered; matching bundled Windows PaStiX/MKL patch/build chain and native builds remain unproven |

Run `python3 ThirdParty/Sources/verify-sources.py` from any directory to check the
pinned source-manifest bytes and every extracted file. Archive hashes identify
the downloaded official bytes; they are not an upstream signature claim.

This is an incremental source inventory. Existing upstream SDK/native folders
elsewhere in ThirdParty are preserved. Their presence is not evidence that all
corresponding implementation sources have been recovered. NetGenMesher, patched
Gmsh, QuadWild, Q-Morph, ActiViz and all transitive runtime/package sources still
need the exact-source/license/build review recorded in `.project/DEPENDENCIES.md`.
The final repository must carry corresponding source for every shipped component;
source gaps remain release blockers.
