# Task 0010 — PMX Linux verification

Date: 2026-10-15, Europe/Belgrade. **Verified execution:** 24 synthetic tests
pass on Linux ARM64. Both private reference copies yield exactly the same
framing, serialized types/member names/array shapes, selected reference edges,
source context and tool hashes as their Mac inventories. Original reference:
1,638 records/215 types; CrossOver-saved reference: 1,655 records/214 types.
Both input SHA-256 values are unchanged. No application assemblies loaded and
the unsafe formatter switch remains false. This is record inspection, not
engineering reconstruction, command replay or full PMX semantic compatibility.

## Reproduction and evidence

Use the existing Podman machine and cached ARM64 image, with no downloads:

```sh
podman machine start podman-machine-default
python3 .project/scripts/verify-pmx-linux.py \
  --image e2c86cca5b654054858118e3fe6e4cbdeb34c4f09ce762a36fd4f26a495f5567 \
  --legacy-input /path/to/private/reference.pmx \
  --saved-input /path/to/private/roundtrip-2.6.0.pmx \
  --output-dir /path/to/research-output
podman machine stop podman-machine-default
```

Run startup, checks and shutdown within the same terminal/tool session on this
host; use a shell EXIT trap for shutdown if a check fails. Original inputs are
not in Git. Actual execution used the persistent CrossOver reference copies
whose hashes were checked against the existing Mac records. The runner mounts
the checkout and each reference read-only, uses a read-only container root with
disposable `/tmp`, disables networking and executes the immutable cached image
with `--pull=never`. No writable checkout, credentials or engine socket is
passed into the container. The image label must match the recorded recipe hash.

Evidence:

- [Final verification/image/command provenance](pmx-linux-verification/verification.json)
- [24 synthetic tests and Linux/Python/SDK evidence](pmx-linux-verification/synthetic-tests.json)
- [Original reference inventory](pmx-linux-verification/legacy-2.5.1-linux-arm64.json)
- [CrossOver-saved inventory](pmx-linux-verification/crossover-saved-2.6.0-linux-arm64.json)

Podman client/server 6.1.4, native aarch64 Linux process, Python 3.12.3 and SDK
10.0.402/.NET 10.0.13. SDK decoder version/hash are retained per inventory.
Earlier Mac records used SDK/runtime patch 10.0.12. No engine/tool/runtime
substitution occurred during this test.

## Differences and failures retained

Verified observation: Linux loads one additional framework support assembly,
`System.Collections.Concurrent`. The initial strict check correctly stopped on
this [runtime-only difference](pmx-linux-verification/runtime-assembly-difference.json).
The final comparator excludes runtime/decoder identities from the portable
projection and guards loaded assembly names separately: only that precise
addition is permitted, no removals or unknown additions. It also checks for
application assembly loading. Serialized type/assembly identities and reference
edges are not normalized. Full observations remain in both inventory files.
This runtime allowance does not declare different payload types compatible.

The first VM attempt failed before tests: networking helper `gvproxy` could not
bind a stale API socket. [Startup failure](pmx-linux-verification/startup-failure.json)
is preserved. After stopping, the socket was already absent when guarded cleanup
was attempted; no file was removed. A same-session restart worked. No VM reset,
package installation, rootful switch or network change was needed. The final
session stopped the VM successfully.

## Remaining gates

Native Linux x64 and Windows execution of this new probe remain open. Earlier
core/data x64 CI passes do not cover it. Full application/semantic persistence,
history replay, new-format writer, numerical/meshing and interactive rendering
acceptance remain open. See the prioritized [preparation exit gates](preparation-exit-gates.md).
Original application sources/projects/algorithms are unchanged; task 0010 and
earlier research remain uncommitted. No push, integration or PR occurred.
