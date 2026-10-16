# Verified core development build delivery

Task 0018, 2026-10-16 Europe/Belgrade. Maintainer explicitly requested publishing
task 0017 and selecting a small task within 20% of the five-hour allowance.
The selected increment makes the existing framework-dependent development ZIP
downloadable from native Linux x64 CI, with verification of the actual archive.
No numerical algorithms or the two open correctness failures were changed.

Implementation commit **b83fa49f96559c1aeb583d7c527647aab0342354** was pushed
normally to origin/research/native-feasibility; ls-remote confirms that exact
SHA. The existing source-linked element kernel, measurement host, diagnostics
and local bundle evidence are included. No binary/private model was added to
Git; the ZIP is generated and uploaded as a job artifact.

## Implemented checks

The existing shared-core-linux-x64 job runs the engineering verifier, existing
package.py and new check-package.py, then retains the ZIP and JSON reports for
30 days under the existing artifact policy. No new dependency/image or native
tool version was introduced. The checker:

- Checks bounded archive paths, unique members, complete manifest coverage,
  every file checksum and required binaries/source/examples/license.
- Rebuilds the extracted source in an independent temporary directory with
  its included offline NuGet configuration.
- Runs both published CLI examples against independent geometry expectations,
  and confirms the published quadratic-tetrahedron gate rejects that case.
- Rejects three altered archives: changed binary, extra unmanifested file,
  and parent-traversal member. Rejections occur before extraction/execution.

Local Mac ARM64 and native Linux ARM64 both pass these checks over all 88
manifest entries and reproduce the prior 25 mapping/30 data/95 accepted element
checks, 28 CLI controls, four data-verifier controls and two explicitly open
correctness failures. Current source/tool fingerprints match across ARM64.
The offline read-only Podman run reuses cached ARM64 image
27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88;
the existing VM was stopped after testing.

```sh
python3 X/Core/package.py
python3 X/Core/check-package.py \
  --archive X/Core/artifacts/development-build/PrePoMaxX-Core-development.zip \
  --report X/Core/artifacts/development-build/verification.json
```

Local evidence is under [build-delivery](shared-core/build-delivery/).
## Hosted outcome and actual download verification

[Pipeline #2956835416](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2956835416)
passed both research job #17245732138 and
[shared-core job #17245732139](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17245732139)
at exact commit b83fa49f. The sanitized trace identifies native Intel Xeon
Platinum 8581C and SDK image ID
`sha256:9cd0d6fa04def99891bf4d5a29eb9a3878b6041f9cc25cb389ea0df2177d23fd`
(registry digest `sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa`).
SDK 10.0.402/.NET 10.0.13. Engineering checks, ZIP generation, extracted-source
rebuild, published CLI samples/gate and archive rejection controls all pass;
both known correctness failures remain explicitly false.

[Download the pinned job's build and reports](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17245732139/artifacts/browse/X/Core/artifacts/development-build/).
Downloaded ZIP: **389052 bytes**, SHA-256
`bd409d1a9d54694bcccbfe0d7c3b3659ba077452c2d638497ac919823a42ee51`.
The downloaded package/checker reports agree on that hash and a clean b83fa49f
checkout. Independent inspection verifies all 88 manifest entries, every
packaged source byte against published Git objects, and core tool/source
fingerprints plus accepted element results/both open failures against ARM64.
The actual x64-produced framework-dependent ZIP was then verified on native
Mac ARM64: extracted source builds, both published examples execute, and the
tetrahedron gate/three tamper controls pass.
[Downloaded evidence and independent verification](shared-core/build-delivery/linux-x64/independent-verification.json)
include the sanitized trace and Mac execution report. ZIP remains outside Git.

Usage read at start: 72%; read after hosted/download verification: 87%, a
15-percentage-point increase before closing records. No reset was used. Stop
at task 0018; further feature work is outside this budgeted continuation.

Native Windows new-slice execution and full application/GUI/CAD/VTK/
persistence/history/native-source/compiler-policy gates remain open. The ZIP
requires an installed native .NET 10 runtime and is a core development build.
