# Task 0029 — Publish analysis, execution and solver research

2026-10-18. Latest maintainer instruction explicitly authorizes committing and
pushing all current work after one bounded task using about 15 percentage points
of remaining usage. Supersedes earlier leave-uncommitted restrictions for this
publication. Scope: review tasks 0022–0028, relevant checks, organized public
third-party source/license and synthetic evidence audit, normal origin research-
branch publication, independent remote verification and hosted CI follow-up.

No force push, upstream/x/main/public-release branch writes, private files or
binary/cache publication. Retain known correctness failures, no native solver
acceptance/profile substitution, Windows/net48/RC2/full-workflow/four-target/
installer gates. Record actual published SHA and CI state; never infer remote
success or green CI. Close with reset handoff and stop feature work until resumed.

## Completed

Implementation 993f9263 published normally and remote verified; master unchanged.
Exact-commit pipeline #2960594131 passes all four native Linux x64 jobs. Actual
three-pin analysis/execution artifact downloads verify published source/tool/
dependency fingerprints and retained Mac outcomes. Closing evidence is docs only.
[Publication record](../reports/analysis-execution-publication.md). Stop feature
work until the maintainer resumes. Every existing correctness/release gate remains.
