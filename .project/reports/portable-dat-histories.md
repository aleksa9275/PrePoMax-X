# Original DAT static history inspection

2026-10-18. [Task 0031](../tasks/0031-portable-dat-histories.md); maintainer asks
to complete the next bounded task and publish all current work. Publication is
tracked separately in [task 0032](../tasks/0032-results-publication.md).

## Implemented behavior

`DatFileReader.ReadStaticSnapshot` / X/Results `inspect-dat` inspect stored
canonical displacement, force, stress and strain blocks through the original
DAT splitter, component repair, GetDatDataSet and ParseStringToDouble. DatDataSet
and HistoryResultEntries retain original CaeResults ownership; original Add
stores time/value/count samples. The boundary groups samples by step, set,
field/component and node or element/integration-point identity, retaining each
increment ID and local-coordinate flag. Time is exactly as printed, separated
by step; no resampling, unit inference, averaging or invariant computation.

The public Windows cube has three datasets and 96 component histories. Checks
use independent 100/210000 displacement, Poisson contraction, 25-per-loaded-node
forces/global balance and eight integration-point S11 values of 100. Existing
FRD values remain 99.996; no rounding/reconciliation, tolerance or solver change.
Independent multiple-increment/step, non-contiguous identity, strain ordering,
missing-E exponent repair, local coordinates, original internal-name repair,
UTF8 BOM/CRLF, culture/path and concurrent independent-entry cases pass.

Malformed/incomplete numeric rows, nonfinite values, duplicate rows/datasets,
missing or non-increasing metadata/time, mixed coordinate systems, unsupported
records, reference-point remapping and oversized input are rejected. Limits:
8 MiB, 4096-character lines, 256 datasets, 100000 rows/dataset, 100000 histories,
250000 scalar samples. Canonical headers/plain ASCII set names and original
splitter separators are required. Full modal/complex/axisymmetric/contact/
thermal processing, long-name expansion, full HistoryResults/FeResults graphs,
legacy persistence and general analysis acceptance remain outside the boundary.

**DAT has no reliable completion trailer.** Complete stored rows do not prove
job completion or that all model-requested records exist. A truncated file ending
at a complete row may be inspectable. JSON explicitly reports
completionEstablished=false. Actual job status/expected coverage must establish
completion in the later solver workflow. These DAT blocks alone do not identify
the analysis type; this is a static-shaped subset, not analysis classification.
Source bytes are SHA256-pinned/rechecked and caller culture restored after
success/failure. Each call creates independent mutable original history entries.

## Original source and ownership

- Full original DAT Read/HistoryResults, axisymmetric/modal/contact processing
  remain unchanged in DatFileReader.Legacy.cs, included once by original net48.
- Required original parsing/repair helpers move unchanged to the shared partial;
  unused Octree/configuration imports are omitted there. No second DAT decoder.
- HistoryResultEntries stream/binary persistence moves unchanged to its legacy
  partial, included once by net48. The unused Geometry2 import is omitted from
  the shared partial; no serialization format or unsafe switch is introduced.
- CaeMesh Globals/CalculixNameShortener are source-linked unchanged in CaeMesh.
  Existing Extensions.Calculix extraction adds the unchanged HashSet
  GetNextNumberedKey method, with its original owner; analysis source hash is
  mechanically updated and regressions rerun. No naming/numerical formula edits.
- Results layout guards reconstruct both partial pairs from each pinned upstream
  source, assert exact bodies/type ownership and reject simulated parser/history
  edits. The added API/CLI alone is modern-only.

## Verification and publication

Combined suite: **78 checks (39 FRD + 39 DAT)** and **nine CLI rejection controls**
per pin, current/RC2/post-RC2 on native Mac ARM64 and offline/read-only Podman
Linux ARM64. Nine results/nine analysis/four execution/ten core replay guards
are the required source review. Existing analysis suite retains 331 accepted
checks and both known correctness failures/tetra gate. Actual retained runs,
hashes and comparisons are recorded in [verification manifest](portable-dat-histories/verification.json).
Hosted x64 is separately verified during publication; local runs are not hosted
acceptance. No native solver or benchmark executes.

Full native Windows/net48/RC2, actual native solver/source recovery, full result/
model/history/persistence/UI/CAD parity, corresponding third-party source,
four-target acceptance and installers/Homebrew remain. Next engineering priority
is a reproducible native CPU solver/toolchain and a real deck → solve → FRD/DAT
comparison, while full results graph and interactive host integration remain.
