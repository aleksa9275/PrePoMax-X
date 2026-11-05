# VIS kernel IDs for partly triangulated faces

The official 3.0.0 Windows archive's `nglib.dll` matched one of 53 distinct
`nglib.dll` blobs checked in reachable history. Its SHA-256 is
`dee9ffc5363626f2fe4df89fd8f9364c99390509722dc5fd3ec17f3ee84f16f2`.
Upstream commit `a55b39c63b7ae1c10741a4d8103210ac5a7a8a12` introduces that
blob. Hashing all 38 tracked Netgen executable/DLL files at that revision
matched the official archive's complete Netgen runtime inventory.
[Upstream commit](https://gitlab.com/MatejB/PrePoMax/-/commit/a55b39c63b7ae1c10741a4d8103210ac5a7a8a12) ·
[Release inventory](l-bracket-cad-reference/verification.json).

The shared VIS reader now applies the corresponding upstream managed fix.
A free triangle side that skips a node on a CAD polyline can no longer
become a segment of that edge. Consecutive free sides and consecutive
internal sides still follow the upstream rule. The segment merge retains
every source ID when two CAD edges genuinely share a segment.

The legacy `FeMesh` face and edge renumbering now keeps unmatched entries
at their original position before sorting. An unmatched entry gets kernel
ID zero, and later matches retain the correct original index. The edits
match upstream exactly. Native Windows execution of this legacy path is
pending.

The added regression failed on the former reader because it assigned the
skipped side to an unrelated source edge. After the fix, the adjacent
side kept its two valid source IDs and the skipped side retained only
its original edge ID. The original L-bracket's decoded geometry and
desktop scene hashes were unchanged. macOS ARM64 and Linux ARM64 each
passed all 348 checks. The macOS fast Core profile also passed.

The native library at this revision re-triangulates some partially
meshed faces at finer edge divisions. The upstream repository carries the
runtime and describes the behavior, while the source for the custom
wrapper and matching modified library remains unlocated. The pinned
native source/build request can now name the exact binary drop. The
managed application release's source correspondence is tracked separately.
[Upstream maintainer's STEP import description](https://prepomax.discourse.group/t/step-import-source-code-questions/3312/3).

Native STEP/BREP import, CAD repair and volume meshing remain open, along
with both correctness failures, the tetrahedron gate, broader 3.0.0 parity
and release acceptance.
