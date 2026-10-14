# Task 0002 — Complementary GitLab verification preparation

Date: 2026-10-14, Europe/Belgrade. **Verified observation: both pinned revisions
pass CI orchestration locally on macOS ARM64 and match the saved observations.
Native Linux x64 and hosted CI execution remain pending.**

## Authorization and changes

The maintainer approved retaining Podman, preparing complementary native Linux
x64 GitLab verification and investigating the previous pipeline if access is
available. This supersedes the earlier local-only instruction. Commits, pushes,
x/main integration and follow-on implementation remain separately controlled.

Root `.gitlab-ci.yml` is restored. The included job in
`X/Feasibility/Core/gitlab-ci.yml` selects `saas-linux-small-amd64`, uses the .NET
10 SDK image, installs Python/Git in its ephemeral container, and fetches the
official v2.6.0 branch to obtain the divergent pinned commit. Rules enable
relevant pushes and manual web runs only on `feature/core-feasibility`.
Other branches, tags, schedules and MR pipelines are outside this task's scope.

The job runs six regression tests and `run-ci.py`. The wrapper calls existing
`run-probe.py` with Linux/X64 assertions for baseline
`de8f73032a72746e3d6d9afd53d9fbd289eb310a` and replay
`9e91252563739ee5304cea16c34863dfb17a74d5`.
The existing Podman comparison is now shared through `probe_evidence.py`:
source/fixture hashes, individual checks, parser observations, CLI contracts
and cube geometry. Actual runtime/build details remain in the full records.

Reports retain selected non-secret CI runner/job/pipeline identifiers, image
reference, actual SDK/runtime and tooling/reference hashes. They never dump the
environment or job tokens. Probe failures retain diagnostics; comparison
failures retain the complete measured report. Both outputs are initialized as
pending before execution, so a baseline failure cannot leave a stale successful
replay artifact. Failure stops before replay. JSON artifacts upload on success
or failure and expire after 30 days. Failures in image acquisition, checkout or
`before_script` require GitLab logs; no probe output exists at those stages.

Original application sources/projects, algorithms, manifest and fixtures remain
unchanged. Podman's image recipe/container restrictions are retained. All
changes remain uncommitted on `feature/core-feasibility` for maintainer review.

## Commands and verified outcomes

```sh
python3 X/Feasibility/Core/test_probe_evidence.py
ruby -ryaml -e 'ARGV.each { |p| y=YAML.load_file(p); abort("invalid mapping: #{p}") unless y.is_a?(Hash); puts "Parsed #{p}" }' .gitlab-ci.yml X/Feasibility/Core/gitlab-ci.yml
python3 X/Feasibility/Core/run-ci.py --expect-os macOS --expect-architecture Arm64 --output-dir .project/reports/core-feasibility/ci-rehearsal/macos-arm64
python3 X/Feasibility/Core/run-ci.py --output-dir X/Feasibility/Core/artifacts/ci-wrong-platform
git diff --check
```

- Six regression tests pass. They check both retained Linux ARM64/Mac records,
  accepted runtime/path variation, rejection of each changed/missing measured
  contract, child-failure diagnostics/stale replay replacement/secret omission,
  and retention of changed geometry with replay stopped.
- Both YAML files parse using Ruby's standard YAML library. GitLab semantic
  lint and actual pipeline rule execution remain unverified.
- Mac rehearsal passes **23 checks, zero failures and two CLI contracts each**
  for both revisions, matching saved Mac observations. SDK 10.0.401, .NET
  10.0.12, Arm64. Reports explicitly say `local rehearsal`:
  [baseline](core-feasibility/ci-rehearsal/macos-arm64/baseline.json),
  [replay](core-feasibility/ci-rehearsal/macos-arm64/v2.6.0.json).
- Strict CI defaults correctly return exit 1 on this Mac with `Expected OS
  Linux, got macOS`. Retained [failure](core-feasibility/ci-rehearsal/wrong-platform/baseline.json)
  and [replay not run](core-feasibility/ci-rehearsal/wrong-platform/v2.6.0.json)
  are expected rejection evidence, not Linux test results.

No Linux container rerun is claimed for this preparation: the shared comparison
was checked against retained Podman results. No PMX, whole-core, mesher, solver
or rendering tests ran. Diff whitespace and changed-document links pass;
production paths have no diff from HEAD, and `master...upstream/master` remains
0/0 without a new fetch.

## Access and remaining native x64 gate

Initial unauthenticated inspection returned 404/sign-in. After the maintainer
signed in on 2026-10-14, read-only authenticated inspection established:

- [Pipeline #2944154347](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/2944154347),
  commit `92a491cd30a0198cb41ce837ee4a564519a08e58`, branch
  `feature/core-feasibility`, created/finished 2026-10-13 22:16:16 Europe/Belgrade,
  has **zero jobs**. Its `yaml invalid` badge help states
  "Identity verification is required in order to run CI jobs"; the error badge
  states the pipeline failed because the user was not verified. No checkout,
  build or probe ran, so there are no job logs/artifacts to inspect. The badge
  name alone is not evidence of a configuration syntax defect.
- [Project runner settings](https://gitlab.com/aleksa9275/pre-po-max-x/-/settings/ci_cd#js-runners-settings)
  show instance runners enabled. Runner `#54907241`,
  `k8s.saas-linux-small-amd64.runners-manager.gitlab.com/default`, includes tag
  `saas-linux-small-amd64` and is Online/Active. No project runner is assigned;
  the enabled instance runner is the intended route.
- [Personal namespace quota](https://gitlab.com/-/profile/usage_quotas#pipelines-quota-tab)
  shows 0/400 compute minutes used since October 1, 2026. Quota exhaustion is not
  indicated at this inspection.
- The new-pipeline form was inspected with the feature branch selected, but not
  submitted. Account settings/form inspection did not establish whether the
  earlier identity restriction is now cleared. The documented signed-in
  identity-verification path returned 404; this does not prove eligibility or
  a persistent block. A new run is needed to establish current CI eligibility.

Selected non-secret observations and URLs are retained in
[diagnostic evidence](core-feasibility/gitlab/pipeline-2944154347-diagnostic.json).
The maintainer entered the login credentials; the agent entered none and did
not change settings, retry the historical pipeline, publish files or submit a
new pipeline. GitLab's [documented identity-verification error](https://docs.gitlab.com/ci/debugging/#error-identity-verification-is-required-in-order-to-run-ci-jobs)
confirms this is a hosted CI eligibility requirement, distinct from signing in.
If it recurs, the maintainer completes the verification GitLab requests; no
payment method or phone/identity data was requested or handled by the agent.

Architectural inference: the documented native x86-64 hosted runner can supply
the missing environment. Actual job/runner/runtime evidence must confirm this
before acceptance. The SDK tag follows patch releases; retain the resolved
image digest from the job log alongside downloaded reports. Python/.NET
architecture assertions alone cannot rule out translation; inspect actual
hosted runner identity and job log too.

Next steps:

1. Maintainer reviews, commits the complete Podman/CI tooling, evidence and
   records, and pushes `feature/core-feasibility`. Relevant changes trigger CI;
   a manual web run on this branch is also supported after publication.
2. Runner enablement/availability and quota have now been checked; the previous
   failure was an identity-verification block before jobs existed. A new run
   confirms whether current account eligibility is sufficient. If GitLab repeats
   that requirement, the maintainer completes its requested verification.
3. Download `artifacts/ci/baseline.json` and `v2.6.0.json` before expiry. Retain
   job log, actual runner identity and resolved image digest; verify Linux/X64,
   both successful comparisons and both source pins.
4. Record actual native x64 evidence in reports/STATUS/task 0002 before closing
   acceptance 4 and the native x64 portion of 5. Native Linux x64 Podman remains
   an alternative route. Feature integration/follow-on work need separate
   authorization.

Primary sources: [GitLab hosted Linux runner architectures](https://docs.gitlab.com/ci/runners/hosted_runners/linux/),
[CI YAML syntax and validation](https://docs.gitlab.com/ci/yaml/).
