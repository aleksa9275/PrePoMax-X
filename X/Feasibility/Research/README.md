# Public synthetic research suite

Task 0012. `run-research.py` checks the actual native Linux process/compiler and
managed runtime architectures, runs 24 PMX synthetic tests, three scalar-binding
controls, four shell fixture contracts/two negative controls, the original
structured kernel (13 vectors, 17 native and seven managed checks, 1,728 count
comparisons), and the unchanged data probe (30 checks/two CLI contracts).
Structured observations are compared with the Mac reference; tiny native area
rounding is allowed within 1e-12, while IDs/count signatures/check outcomes/source
identities remain exact. No private models, GUI, mesher or solver execution.

```sh
python3 X/Feasibility/Research/run-research.py --expect-architecture X64 --output-dir /tmp/research-output
```

Requires Linux, Python 3, Git, g++ and .NET 10 SDK, including trusted NRBF decoder.
The additive GitLab job runs only for push/manual pipelines on
research/native-feasibility. It does not run private model comparisons or graphics.
Job artifacts include failures; configuration is not a hosted pass.

Local ARM64 route: build the compiler-only layer using `Containerfile` with
BASE_IMAGE set to the already recorded/cached core SDK image ID. The recipe's
package download is explicit setup; tests run with `--network=none`, checkout
read-only, writable disposable `/tmp` and a dedicated public report directory.
Record actual image ID/digest, compiler target/version and SDK/runtime evidence.
Changing architectures does not turn translated execution into native proof.

The ARM64 default GCC -O2 vector failure is retained. Use
`diagnose-contraction.py --output /path/to/diagnostic.json` to measure four modes
against unchanged vectors. The suite's `--fp-contract-off` option selects an
explicit research control only; it is not the default or a production policy.
