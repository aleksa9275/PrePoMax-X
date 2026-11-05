# Task 0065 — Conserve hosted runner quota

The maintainer warns that less than 25% of GitLab compute remains. The signed-in
UI shows 75/400 minutes before the current pipeline's job accounting and 64/400
after its early jobs. Under D050, reserve hosted native builds for milestones.

Cancel the unchanged desktop/solver rebuild and unneeded numerical jobs in the
current CAD checkpoint pipeline; retain the affected research/CAD checks. Some
short jobs may complete before cancellation. Record each actual outcome.

Make the expensive native CAD source build and desktop-package push checks
manual milestone jobs. Preserve every command, tolerance, automatic ordinary
source check, explicit web-triggered package workflow and numerical integration
trigger. A missing manual milestone stays pending for platform/release acceptance.
Publish this cadence/closing-evidence change without starting another full build.

Follow-up: the maintainer reports that the long first x64 build will exhaust
the allowance and leave no CI for 25 days. D058 now supersedes the earlier
partial cadence change: allow only explicitly requested manual web pipelines,
so ordinary pushes create no hosted pipeline. Let the existing x64 job finish;
no retry or other hosted job without explicit instruction. All original checks
remain defined and all missing platform/release checks remain pending.
