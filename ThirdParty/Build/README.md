# Native CPU research build

Task 0041 adds a shared target entry (`X/Build/build.py`) and a Linux GNU/ELF
adapter alongside the extracted Mac adapter. The original command below still
auto-selects a matching native host; `--target` can make it explicit. The same
source/patch/recipe is used, with OpenBLAS int32 configuration checked at runtime.
`verify-workflow.py --hosts-dir <shared-build-output>` validates and runs the
staged self-contained hosts without an external dotnet command. See
[shared commands](../../X/Build/README.md) and actual task 0041 results. Historical
Mac-only wording below describes the initial task 0038 proof, not all new recipes.

First implemented target (task 0038; now i8 with PaStiX and multithreaded SPOOLES, D070): macOS ARM64, CalculiX **2.22**, serial SPOOLES 2.2,
static ARPACK-ng 3.9.1 int32 and OpenBLAS LP64. This explicit research profile
does not replace the default Windows reference registry or choose a production
solver default. Core source/version and precision stay unchanged.

On the recorded Mac, install GCC/gfortran and CMake (Homebrew), then:

    python3 ThirdParty/Build/calculix-cpu.py --output ThirdParty/Build/artifacts/my-build --jobs 6
    dotnet build X/Execution/Solve/Solve.csproj -c Release --source X/Analysis/artifacts/offline-feed
    dotnet build X/Results/Inspect/Inspect.csproj -c Release --source X/Analysis/artifacts/offline-feed
    python3 ThirdParty/Build/verify-workflow.py --build ThirdParty/Build/artifacts/my-build --output ThirdParty/Build/artifacts/my-workflow

Both output directories must be new. Compiler and BLAS paths are explicit CLI
options; sources are verified before copying. Patches are applied only to build
copies. Source lists/formatting remain original; duplicate mafillmm.o is removed
from the link list, and `-fcommon` retains the legacy tentative-global behavior.
`-DARCH=Linux` selects the original GNU Fortran symbol convention on this Mac;
it does not pretend the execution host is Linux. No fast-math flags are used.

Build JSON retains compiler versions, commands/logs, source/recipe/binary/runtime
hashes and resolved load paths. Non-system runtime load paths, including opt
symlinks, are fingerprinted; a Homebrew upgrade requires rebuilding/reviewing the
profile. Current binaries depend on installed Homebrew runtimes. Public source/
license closure for compiler/OpenBLAS/transitive runtimes and relocation into
an installer are still work. Research profile JSON belongs to its build output.

The workflow verifier uses the original C# deck/job/FRD/DAT/monitor hosts and
reuses the existing analytical checker/tolerances and altered-displacement
negative control. Its cube is not a modal/nonlinear/contact/capacity/scaling or
PaStiX acceptance corpus. Additional native targets need their own recipes and
common-fixture evidence. [Retained evidence](../../.project/reports/native-cpu-workflow.md).
