# Task 0022 — Original equation/material foundation for analysis decks

2026-10-18, Europe/Belgrade. Maintainer accepts the complete sequence in
proposals/next-native-workflow.md and explicitly defines the end goal as an
installable PrePoMax-X desktop application: Windows EXE/MSI, macOS DMG,
Linux DEB/RPM or equivalent and Homebrew. Apple Developer ID enrollment is
available when required. This supersedes task 0021's approval stop for local
implementation. Publication is not newly authorized; leave work uncommitted.

First bounded component of approved step 1: compile original equation evaluation,
unit converters and material types/CalculiX material writers in their original
CaeGlobals/CaeModel assemblies, with guarded source ownership and exact existing
NCalc/UnitsNet versions. Preserve upstream semantics; no replacement evaluator,
material model, default format or frontend. Mechanical separation of original
formatting and removal of proven unused unavailable imports are permitted.
Keep the existing offline mesh/core build intact while measuring the expanded
assembly/dependency closure in X/Analysis; this is a source-linked superset,
not another engineering implementation. Do not copy these partial assemblies
over an original installation.

Verify typed material/equation/unit/writer behavior and invalid input on native
Mac/Linux ARM64, replay both reviewed upstream pins, preserve all earlier checks
and both correctness failures/host gate. Retain commands, package/source hashes,
licenses and limits. This component does not complete the full analysis deck:
sections/BCs/loads/steps, native solver and result graph follow under the accepted
sequence. Native Windows/full net48/RC2 and release requirements remain open.

Status: bounded component complete locally. Current/RC2/post-RC2 each pass native
Mac/Linux ARM64 with 44 material plus 218 existing accepted checks (262 total),
eight material CLI controls and both known element failures/gate retained.
Seven source guards and ten existing replay guards pass on Mac; portable source/
dependency/tool/outcome comparisons match across hosts. Original post-RC2 lamina/
composite changes are explicitly replayed rather than flattened. The existing
offline core independently passes its checks. [Evidence](../reports/analysis-material-foundation.md).
Native Windows/new hosted x64/full net48 and release gates remain. All changes
are uncommitted. Continue the accepted sequence with original section/BC/load/
step and complete deck generation; no fresh approval stop is imposed here.
