# 384edea2 pipeline diagnosis and repair — task 0040

2 November 2026. The maintainer signed into GitLab and identified the commit.
Read-only browser inspection confirms [pipeline **3019186769**](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3019186769)
failed at clean **384edea2f24bf51b57cac60d02f87e1b37dd77de**. Its only failed job
is [shared-core-linux-x64 **17675531644**](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17675531644).
Analysis, execution, results and research passed; compatibility was manual.
The preceding 66e3ca0f pipeline 3019099554 is visibly passed. Documentation
pipelines d7498f8e/84445a42 are skipped, not fresh engineering acceptance.

The failing job ran on native Intel Xeon Platinum 8581C, Ubuntu 24.04.5 LTS,
.NET SDK 10.0.403. Seven check-runner and ten replay guards passed. Core mapping
25/data 30/element 95 checks and 68 mesh unit checks passed before the **actual
CLI export/reopen metadata comparison failed**. Packaging never ran; missing ZIP
artifact warnings are a consequence. This is not a runner/setup failure.

The [downloaded verifier](core-pipeline-regression/failed-core-current.json)
records both actual CLI JSON outputs: element block **CUBE → null**, with other
mesh metadata equal. [Failure summary/archive SHA](core-pipeline-regression/failure-summary.json),
original leaf log and orchestrator manifest are retained. Raw job-upload tokens
and authentication/session data are not retained.

Root cause and fix: [B003](../bugs/B003-element-block-name-roundtrip.md). Preserve
inline block names while filtering already-emitted memberships from explicit
ELSET definitions. This keeps B001's duplicate-history fix and original block
identity. The existing full CLI roundtrip assertion is unchanged. Shared math,
original parser/keyword implementation, precision and tolerances remain unchanged.

Local native Mac current-source Core and Analysis pass in approximately **24 s**:
mesh checks now 69, analysis total 333 accepted checks; both existing correctness
failures/tetra gate remain. The original native CalculiX workflow passes all
twelve checks plus altered-displacement rejection, including exactly eight
integration-point stresses and original DAT history import. Development publish/
smoke, 125-entry package verification and ten replay/nine analysis source guards
also pass. Actual publication/hosted status is recorded below.

## Publication and hosted verification

The bounded repair is prepared for normal publication to origin research under
the existing maintainer authorization. Exact repair SHA, pipeline and job outcomes
will be recorded after the push and actual hosted run. A local pass is not a
native Linux acceptance claim. No native Windows/Linux desktop/distro installer
or production frontend/backend/format acceptance follows from this CI repair.
