# MacBook continuation — start here

Mac continuation completed, 2026-10-16 Europe/Belgrade: reviewed ac51fc77 is
published and pipeline #2956616374 passed both native x64 jobs. Exact original
mapping slice passed Mac/Linux ARM64 as requested. [Task 0015](../tasks/0015-shared-core-data-slice.md)
and [current report](../reports/shared-core-data-slice.md) now define the next
handoff: expanded shared data libraries pass locally and remain uncommitted.
The current verifier includes 30 data checks as well as the original 25 mapping
checks/nine CLI controls. Preserve this working tree; do not re-import/fetch over
it or re-publish the old range. New native Windows/new-commit x64 follow-up is
pending. The original transfer checklist below is retained as provenance.

Prepared on native Windows x64, 2026-10-16. The maintainer requests continuing
on one MacBook, after committing/pushing the Windows work. The next useful
engineering step needs the Mac/Linux environments. Do not repeat the completed
Windows read/save/reference pass or restart the initial repository audit.

## Retrieve the actual work

Repository: https://gitlab.com/aleksa9275/pre-po-max-x.git
Branch: **research/native-feasibility**, not master or x/main.
Previous published parent: **f1e757f15b80bb3f615c887b420180ae1a918ed5**.
New publication commit is the commit containing this handoff; identify it with
`git log -1 --format='%H %s' -- .project/handoffs/macbook-next-session.md`.
The Windows chat's final message also supplies the exact commit ID. A local
commit is not proof of a successful remote push: Windows Credential Manager
returns Access denied in the sandbox, and this may need the normal terminal
or the already-authenticated Mac to complete publication.

In the existing Mac checkout, inspect status/branch first and preserve all
local changes. If clean, fetch origin, switch to the planned branch if needed,
then fast-forward only:

```sh
git status --short --branch
git fetch origin
git switch research/native-feasibility
git merge --ff-only origin/research/native-feasibility
git log -3 --oneline
```

Stop and inspect divergence or unrelated dirty work; do not reset, stash away
or overwrite it. Verify the new X/Core projects, three X/Core/Tests files and
task 0014 are present. Read AGENTS.md, PROJECT/STATUS/DECISIONS and tasks
0013/0014. This handoff is the current entry point; older Windows-pending and
research-only paragraphs elsewhere are historical.

If the remote is still at f1e757f1, the Windows output includes a **Git bundle**
named `PrePoMax-X-Windows-handoff.bundle`, containing the new commit range with
f1e757f1 as prerequisite. Transfer that bundle to the Mac outside the checkout.
Run `git bundle verify /path/to/PrePoMax-X-Windows-handoff.bundle`, then fetch
its planned branch into an auxiliary ref and fast-forward the working branch:

```sh
git fetch /path/to/PrePoMax-X-Windows-handoff.bundle \
  research/native-feasibility:refs/remotes/windows-handoff/research-native-feasibility
git merge --ff-only refs/remotes/windows-handoff/research-native-feasibility
git push origin HEAD:refs/heads/research/native-feasibility
```

The maintainer explicitly authorizes publishing this reviewed Windows handoff
range to origin for this transfer. No force push, upstream write or x/main
integration. This publication exception does not authorize future feature pushes.
Confirm the remote commit and actual pipeline outcome after publication.

## What is already complete

- Same original Windows 2.6.0 app/VTK and CalculiX 2.22 identities as CrossOver.
  Controlled cube/definitions save/reopen, import undo/redo/history regeneration
  and 30 explicit deck checks; analytical solve passes seven checks plus control.
- Supplied private 2.5.1-dev PMX hash is
  `80e3c303a0719317af9d23016a4f70fe5f5acb91d731e704ec45dcbbfe2e0379`.
  Native save/reopen displays model and results; custom model bytes are unchanged.
  Inflated result mesh and all four field payloads match the CrossOver save.
  A results-disabled save reopens with the same model and no result fields.
  Job/settings/member drift is the same 27/29 shallow-type result in both hosts.
- First reusable **partial** CaeGlobals/CaeMesh .NET 10 libraries and MapFace
  CLI are implemented. Only the original CaeException class was separated from
  Windows presentation; existing engineering algorithms are source-linked.
  25 mapping checks (13 original vectors, zero Windows coordinate deviation)
  and nine CLI controls pass; source slice also compiles/runs on the legacy CLR.
  Do not copy partial DLLs into an original Windows installation.
- Native Windows C++ is now tested with pinned portable LLVM-MinGW 20261006,
  Clang 23.1.3: defaults and explicit contraction off both pass 13 vectors,
  17 independent native checks, seven managed checks and 1,728 count comparisons.
- The new tests were initially hidden by upstream's generic `Tests/` ignore
  rule. X/Core/.gitignore now explicitly includes them. Check they arrived.

Evidence: reports/windows-reference-validation.md, windows-reference/,
shared-core-first-slice.md and shared-core/. These are scoped passes, not whole
application or persistence equivalence. Older missing-compiler diagnostics are
retained as history. Compiler production policy was not changed.

## First Mac actions — exact shared-library build

Use the installed native ARM64 .NET 10 SDK and Python 3. No package feeds,
Windows app, private model, new SDK installation or frontend choice is needed.
Run from the repository root:

```sh
uname -m                         # arm64; do not use a Rosetta terminal
dotnet --info
task_out="$PWD/X/Core/artifacts/macbook"
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 \
  --output "$task_out/macos-arm64.json"
```

Expected: success, **25 mapping checks and nine CLI controls**. Preserve a
failure report before repair. The verifier checks original source bytes,
exception extraction/type ownership, native process architecture, vector
tolerances, geometry, connectivity, callbacks and CLI failures. Compare names,
counts and scoped outcomes with reports/shared-core/windows-x64.json; do not
compare host descriptions/timestamps as portable semantics. Do not silently
loosen tolerances or replace upstream vectors if an ARM64 difference appears.

Then use the existing **native Linux ARM64 Podman VM**. It was stopped after
the previous checks. Inspect before starting; don't initialize another VM or
use the translated amd64 image. Cached compiler-equipped research image:
`27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88`.
Earlier SDK/Python/Git-only ARM64 image:
`e2c86cca5b654054858118e3fe6e4cbdeb34c4f09ce762a36fd4f26a495f5567`.
Either can run the shared-library verifier; inspect image/VM architecture first.

Example after confirming the named VM/image still exist:

```sh
podman machine start podman-machine-default
task_out="$PWD/X/Core/artifacts/macbook"
mkdir -p "$task_out"
task_image=27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88
podman image inspect "$task_image"
podman run --rm --pull=never --platform linux/arm64 --network=none \
  --read-only --tmpfs /tmp:rw,size=1g \
  --mount "type=bind,source=$PWD,destination=/workspace,ro=true" \
  --entrypoint python3 "$task_image" -c '
import pathlib, subprocess, sys
result = subprocess.run(["python3", "X/Core/verify.py", "--expect-os", "Linux",
    "--expect-architecture", "Arm64", "--output", "/tmp/shared-core.json"], stdout=sys.stderr)
sys.stdout.write(pathlib.Path("/tmp/shared-core.json").read_text())
sys.exit(result.returncode)
' > "$task_out/linux-arm64.json"
podman machine stop podman-machine-default
```

Use cleanup/trap or a finally block so a failed check does not leave the VM
running. These exact new-library Mac/Podman commands are prepared, not executed
from Windows. Record actual image/runtime/compiler/source identities and copy
sanitized reports into reports/shared-core after inspection.

The new `shared-core-linux-x64` GitLab job and the existing research suite run
on pushes/web pipelines for this branch. Their new-commit results are not
claimed here. Check the exact source SHA, logs and downloadable artifacts;
pipeline configuration or Git push success alone is not acceptance. Retain the
Linux ARM64 GCC default -O2 failure from earlier research: the explicit
contraction-off control passes, but no production policy decision was made.

## Keep building after those runs

The next bounded candidate is to promote the already-proven geometry metadata,
IntegrationScale and FRD stream reader into the shared assemblies, and execute
the existing 30 engineering-data checks through project references. This
expands callable reuse without choosing a GUI or reconstructing PMX objects.
Create a scoped task record, retain original source/type/assembly ownership and
Windows behavior, and reuse the existing DataProbe expectations. Avoid broad
Controller/serializer refactoring or another general repository audit.

Interactive native VTK picking/clipping/deformation/DPI, corresponding custom
mesher-source recovery, real CAD fixtures and full persistence/history/clone
semantics remain subsequent work/release requirements. The frontend, default
serializer, F001 and x/main integration are still undecided/out of scope.

## Private files and Windows return conditions

No private files are needed for the first shared-library runs. The Mac already
has the original/CrossOver reference under bottle PrePoMax-X-reference-2.6:
`C:\PrePoMax-X-reference\Work\reference.pmx` and `roundtrip-2.6.0.pmx`.
CrossOver-saved hash:
`79f8f17be53fcbdde22e2f40ea7ca1ce129e574599abd58e1b793d7256727341`.

Optional separate transfer: Windows output `Windows-reference-private.zip`
contains the original, native results-enabled/disabled saves and controlled
PMX/PMH/decks with an internal hash manifest. SHA-256:
`735b1025c3d3cef468302f18d441c8003231e66eccfeccd399890b4018844943`.
Keep it outside Git. PMX/PMH contain local-path history; do not automatically
regenerate them against Mac/live user folders. No app settings/authentication,
SDK or compiler bundle needs transfer.

Windows-only pending infrastructure: one hardlink creation test is denied by
the sandbox (23/24 tests pass; no skipped pass). A normal-terminal rerun script
is retained with Windows outputs. Full original solution build was not done;
only the legacy source slice was compiled/executed. Return to native Windows
when new source changes require its differential oracle, or for planned CAD/UI
acceptance. Neither blocks moving this shared-core work to the Mac now.
