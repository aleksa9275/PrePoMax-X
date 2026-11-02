# PrePoMac compared with PrePoMax-X — retained detailed audit

2 November 2026, Europe/Belgrade. [Task 0034](../tasks/0034-prepomac-evaluation.md).

**Assessment:** PrePoMac is substantially ahead of us in delivering a usable
desktop workflow. Its shared-source compilation, compatibility controls, native
helper and packaging are valuable work. Its Code_Aster integration offers a
useful additional analysis route, but does not yet replace CalculiX across our
required workflows. Its SPOOLES-only Mac binary is a build choice, not proof that
other CalculiX matrix solvers are impossible. I recommend retaining our shared
engineering boundary and native-VTK direction, evaluating selected PrePoMac work,
and treating Linux solver workers as a serious option. These are engineering
recommendations, not a frontend/solver/default adoption decision.

## Evidence, pin and limits

The separate source checkout is pinned to
**fb5a89dba6ac975956d9001edf6d6756f18fe0ca**, 28 October 2026. GitHub's live API
confirms that the annotated release tag **v3.0-mac.4** points to this same commit.
The live API matters: the web reader returned a cached release page stopping at
mac.2. [Public metadata snapshot](prepomac/primary-metadata.json) retains the
observed release, tag target, build/release runs, Linux discussion and package
platforms.

I downloaded the latest Mac ZIP into a temporary directory and verified its
120,389,305 bytes and SHA256
`1b3e00532056dae81c62eb3c5d5039349b4a6ffadf3821da959d05bc81131ed8`
against GitHub's asset digest. Only solver/runtime/bundle metadata was extracted
for inspection; the application was not installed or launched. The ZIP has
4,500 entries. [Release inspection](prepomac/release-inspection.json) records
binary identities, dependency names and runtime settings. This is actual archive
verification, distinct from the earlier task 0032 preview-only transport.

Forty reviewed files have retained byte fingerprints. The
[review script](prepomac/review-source.py) parses three Python files, checks
eight shell scripts, inspects project path spelling, runs the author's analytical
formula functions independently of the app and generates a package-free C#
diagnostic harness from selected **unchanged source methods**. The harness ran
on native Mac ARM64/.NET SDK 10.0.403. It tests method outputs using controlled
type/file fixtures; it does not instantiate the real FeModel, assemble a matrix
or solve a physical problem. [Source/formula observations](prepomac/source-review.json),
[Mac method outputs](prepomac/isolated-methods-macos-arm64.json).

**No whole-app, interactive GUI, numerical solver, load/capacity or performance
benchmark was run in this review.** OpenCASCADE/gmsh/lp_solve/CalculiX and Docker/
Colima are not installed here as a PrePoMac environment. The existing Podman VM
could initially list cached images, but forwarding subsequently failed; a bounded
restart failed with a gvproxy socket error. Cleanup stopped the VM successfully.
[Linux diagnostic status](prepomac/isolated-methods-linux-arm64.json) records
not-run, not pass. Linux conclusions below distinguish source observations from
the author/user's reported execution.

Our two existing correctness failures and tetrahedron measurement gate remain.
PrePoMac's FeElement.cs and ParabolicTetraElement.cs are byte-identical to our
retained f6273e39 upstream pin; this review finds no fix there. Its two reported
API failures are a different test set and must not be equated with our failures.

## 1. What the implementation actually is

PrePoMac's `macOS/` folder adds SDK-style net10 projects that compile the shared
PrePoMax source folders. Original forms, controller, commands, model and APIs
remain central. Rather than separating every form from application behavior, it
implements the APIs that those forms expect:

| Boundary | PrePoMac implementation | Consequence |
|---|---|---|
| Windows Forms | Own assembly named System.Windows.Forms, controls/windows/layout/events implemented on Avalonia 11.3.1 | Original forms and most controller/UI calls can compile together; fast access to broad functionality |
| System.Drawing | Own compatibility assembly using SkiaSharp | Retains drawing call sites, but takes responsibility for text metrics, painting and drawing semantics |
| ActiViz/VTK | C# Kitware.VTK-compatible classes and a custom OpenGL renderer | Avoids the managed native-VTK binding problem by implementing its required behavior itself |
| Win32 imports | Small C library under kernel32/user32-compatible filenames, with callbacks to controls and some stubbed operations | Preserves P/Invoke call sites; job-object/console/hook semantics are not Windows equivalents |
| CAD/meshing | New native OpenCASCADE/gmsh helper using the NetGenMesher filename/protocol | Existing runners can call it; it is not the original patched Netgen tool |
| CalculiX | Find installed/bundled ccx; adjust unsupported backend selections | Immediate native execution with a different binary/backend policy |
| Code_Aster | Original model → new study writer → Docker/run_aster → custom FRD postprocessor | A second FEM engine with an explicit translation layer |
| Persistence | Restored BinaryFormatter package plus compatibility surrogates/binder | Enables familiar files/cloning while retaining the legacy serialization mechanism |

Sources: [shared build settings][build-props], [WinForms project][winforms],
[VTK project][vtk-project], [native compatibility library][win32]. This is an
effective adaptation strategy; it is not a clean standalone engineering backend
or a new portable frontend over UI-independent services.

A byte comparison against our previous upstream checkpoint f6273e39 found
1,816 identical and 121 changed common-path C# files in the selected application
folders. Against upstream Composites f6080786 it found 1,805 identical and 129
changed common-path files. [Paths and comparison scope](prepomac/shared-source-comparison.json).
These counts exclude removed/renamed paths from the identical/changed tally and
include later upstream work as well as port changes: **they are not an attribution
of 121 files to macOS modifications**. They show that importing the whole fork
would require more review than adding its macOS project files.

## 2. SPOOLES: what is confirmed, and what is not

**Confirmed for the actual release:** its bundled `Solver/ccx` is a Mach-O ARM64
executable. Embedded version strings identify **CalculiX 2.23**. It contains the
original missing-library error messages for PASTIX and PARDISO. Combined with the
formula and source dispatch, this corroborates that those two backends are not
compiled into this binary. The dynamic dependencies include ARPACK, gfortran,
GNU OpenMP, quadmath and Apple Accelerate. No PaStiX/MKL library appears among its
dynamic dependencies or the reviewed Frameworks entries. Static dependencies
cannot be inferred from `otool` alone; the negative messages and build recipe
are the stronger backend evidence. No executable invocation is claimed.

The [Homebrew formula][brew-formula] explicitly compiles with `-DSPOOLES`,
`-DARPACK`, `-DUSE_MT=1`, and no PASTIX/PARDISO macro. It builds the SPOOLES MT
library. Thus “SPOOLES only” means **this supplied direct-solver build**; CalculiX's
built-in iterative choices are a separate matter. It also means **2.23**, whereas
our recovered original/RC2 reference is **2.22**. Importing this binary as our
matching solver would be an unreviewed version change.

PrePoMac does not assume every Unix ccx has the same backends. Its
`Tools.CalculixHasSolver` searches binary bytes for a missing-library message.
`SolverSettings.CalculixDefaultSolverType` returns SPOOLES if the selected
PARDISO/PaStiX backend is judged absent; Controller's
`ReplaceMissingCalculixSolvers` rewrites matching `SOLVER=` keywords in the
generated input and logs a fallback message. This runs for non-Windows platforms,
including Linux. [Detector][tools], [settings][solver-settings],
[deck rewriting][controller-fallback].

The exact-method diagnostics reproduce limitations of this detector: a missing
executable or arbitrary file without the negative marker is treated as supported;
replacing the binary at the same path leaves a cached negative result in the
running process. This is a useful heuristic, not a version/hash/capability proof.
Our executable registry should retain positive build profiles and reject unknown
or unsupported saved selections, or obtain an explicit user decision. The logged
fallback is observable, but it is still automatic input transformation that our
current policy does not permit adopting unchanged.

**No, this does not establish that we can use only SPOOLES.** Our unchanged 2.22
source contains SPOOLES and PaStiX direct routes, including modal/buckling paths
whose actual dispatch needs care. The [official CalculiX site][ccx-official]
documents the PaStiX build route. The [PaStiX handbook][pastix] documents CPU
threading and BLAS/runtime requirements. A packaged library is not a ready,
validated CalculiX adapter: we still need the matching modified PaStiX interface,
integer ABI, build and regression evidence. Native Mac ARM64 PaStiX feasibility
has not been settled by this review; Linux PaStiX remains a serious existing route.

PrePoMac also takes the SPOOLES thread concern seriously. Its
`AnalysisJob.SetNumberOfProcessors` sets OMP_NUM_THREADS, but on non-Windows
platforms additionally sets **CCX_NPROC_EQUATION_SOLVER=1**, allowing later explicit
environment overrides. Therefore its default avoids multithreaded SPOOLES
factorization while other phases may remain threaded. This is not an all-thread
high-performance SPOOLES solution. [Job settings][jobs]. Our earlier thread/
precision/modal caveats in [the PARDISO-free assessment](without-pardiso-assessment.md)
still apply; no new default is selected here.

## 3. Code_Aster: real integration, narrow adapter

There are two different uses of “solver”:

- CalculiX and Code_Aster are complete FEM engines: element formulations,
  constitutive laws, constraints, nonlinear/time algorithms and result semantics.
- SPOOLES, PaStiX, PARDISO and MUMPS are linear-system engines used inside an FEM
  engine. Adding Code_Aster does not add MUMPS to CalculiX.

Code_Aster's official [linear-solver documentation][aster-solvers] describes
MUMPS, PETSc and its other methods, including parallel options and MUMPS pivoting.
This makes it a credible additional route for robustness/capacity. Those engine
capabilities do not imply that PrePoMac exports the corresponding analyses.
Its writer emits `MECA_STATIQUE` without an explicit SOLVEUR configuration; it
does not expose or verify a chosen MUMPS/PETSc variant or a distributed strategy.

The integrated flow is:

1. Deep-copy the original FeModel and remove inactive parts.
2. Write Gmsh 2.2 mesh, `.comm` commands, `.export` study and `_ppm.json` identity/
   result metadata.
3. Mount the host work directory into Docker at `/work`, invoke `run_aster`.
4. Run an embedded Python postprocessor, producing a CalculiX-shaped `.frd`.
5. Open that FRD through the existing results path.

This is a sensible process boundary that reuses existing model/job/results
infrastructure. The full writer is 728 lines plus a 204-line embedded Python
postprocessor; its bounded scope is visible in those implementations.
[Writer][aster-writer], [postprocessor][aster-post], [controller launch][controller-aster].

### Actual translation coverage

| Feature | Implemented behavior | Implication for our requirements |
|---|---|---|
| Analysis steps | Only exact StaticStep types; each becomes its own linear MECA_STATIQUE solve. Other active step types produce warnings and are omitted | No dynamic/modal/buckling/thermal/wear parity through this adapter; no path-dependent continuation between these static solves |
| Model space | Rejects 2D model spaces | No plane-stress/plane-strain/axisymmetric export here |
| Materials | Isotropic elastic, engineering constants or lamina; first property-table row; optional first density row | No exported plasticity, temperature-dependent evolution or other material laws, even if present beside an elastic property |
| Shells | DKT with shell thickness/reference vector; DEFI_COMPOSITE for layered materials | Valuable true layered-shell route, but different formulations from CalculiX shell-to-solid expansion |
| Shell order | S6/S8-like quadratic geometry is reduced to three/four corner nodes | Different approximation space and junction/load behavior; not the same discretized equations |
| Solids | Linear tetra/hexa/wedge; ten-node tetra retained with Gmsh node-order conversion | Quadratic hexa/wedge are reduced to eight/six corners and warn; pyramids and 1D elements are rejected |
| BCs | Fixed and displacement/rotation on supported node/surface/part regions | Non-global BC systems warn and are applied globally; shell midside nodes are filtered from the solved mesh |
| Loads | Nodal force, moment, gravity | Unsupported load types warn/skip; pressure/distributed/surface traction semantics are not generally translated |
| Constraints/contact | No writer traversal implementing the model's constraints/contact pairs | Ties, rigid couplings/joints/contact are not available merely because Code_Aster can model them |
| Offsets/missing sections | Shell offsets warn/are ignored; elements without sections warn/are omitted | A successful remaining solve can describe a reduced/changed model |
| Results | Displacements, solid nodal stress, plain-shell top/bottom von Mises; composite Tsai-Wu index/reserve/critical ply | No equivalent full DAT histories, reactions, contact outputs, full tensor/ply history and energy/time coverage |

Source details: writer lines 64–90, 98–120, 147–203, 324–420, 432–475,
481–651 and postprocessor lines 153–200. The exact-method Mac harness confirms
6→3 and 8→4 shell node mappings, 20→8 hexa and 15→6 wedge mappings, while the
ten-node tetra remains ten-node with the last two Gmsh edge positions exchanged.
This confirms mapping code, not physical element equivalence.

### Changes needed before adopting that adapter

The most material issue is **model eligibility**, not installing Code_Aster.
The writer can proceed after omitting unsupported content. It does not perform
a complete reject-before-export capability audit. For example:

- A static model with elastic-plus-plastic material is written from its elastic
  property only; the exporter does not inspect the plastic law.
- Static-step geometric nonlinearity and model constraints/contact are not mapped
  into its MECA_STATIQUE calls.
- `WriteLoad`'s gravity branch writes PESANTEUR with no GROUP_MA or region
  restriction, so gravity scoped to a part becomes global in the exported model.
- The nodal force/moment branch takes component values directly and does not
  transform a user coordinate system. Non-global displacement BCs at least warn,
  but become global.

These are source observations about the adapter, not accusations that the
underlying Code_Aster engine lacks those capabilities. They require rejection
or explicitly reviewed conversion, followed by tests. An automatic choice of
Code_Aster based only on “large model” or “SPOOLES singularity” would be unsound.

The FRD postprocessor also has a separate validation surface. It reduces selected
shell results to nodal envelopes, emits ordinal step numbers as result times,
and does not preserve all integration-point/ply provenance. Controlled helper
diagnostics show missing per-node components can be initialized to zero and both
signs of infinity are formatted as positive 1e30. These cases do not prove a
normal run produces corrupt fields; they identify coverage/error cases that need
explicit treatment. Our parser accepting that FRD would not validate its FEM
meaning or lost histories.

**Verdict:** Code_Aster can address part of our open-backend/capacity problem,
especially as an independently validated optional engine. PrePoMac supplies a
concrete starting adapter and useful shell examples. It does not yet solve our
complete solver parity problem, and a singular physical model is not made valid
merely by switching linear solvers or element formulations.

## 4. Linux VM on Mac: worthwhile option, different architectures

The maintainer explicitly permits evaluating a Linux VM for better solver
performance. That is now a valid research direction. Native desktop targets
remain; optional virtualized compute need not force the UI into the VM.

PrePoMac's Code_Aster Dockerfile starts from **linux/amd64** Miniforge, installs
`code-aster=18.1` from conda-forge, and tags the result `prepomax/code_aster:18.1`.
Both its build command and Controller run command force linux/amd64. Its README
starts Colima with Apple Virtualization and Rosetta. On Apple Silicon the intended
stack is a Linux VM with **translated x86-64 userspace** for this container, not
native ARM64 Code_Aster. [Container recipe][aster-container],
[launch construction][controller-aster].

That choice has a concrete packaging reason: live conda-forge metadata contains
592 Code_Aster files, with platforms **linux-64 and win-64 only**, including the
18.1 series. No linux-aarch64/osx-arm64 package is present in that package record.
The current [feedstock recipe][aster-recipe] skips macOS and provides separate
sequential/MPI dependency variants. This does not prove the source cannot be
built for ARM64, or that no other distributor has an ARM build. It means this
specific prebuilt route does not supply one. The Dockerfile does not lock an
exact package build/dependency solution, image digest or MPI variant.

### Current resource and lifecycle limitations

`WriteExport` requests half of the **exporting process's** Environment.ProcessorCount,
one MPI rank, 4096 MB memory_limit and an 86400-second time_limit. It does not
receive the job's configured NumCPUs, the VM allocation or the 75% application
budget. The exact method on this Mac requests **9 CPUs** from a process seeing
18; our existing Linux VM has **4 CPUs and 4 GiB**. That mismatch is evidence
of why budgeting must occur on the execution worker. It is not a benchmark.

`OMP_NUM_THREADS` set on the host's Docker CLI is not automatically forwarded
into the container: the generated run command supplies no `-e` option. The
study's own ncpus request therefore matters independently. One MPI rank can still
use threaded libraries if that build supports them, but it is not a configured
distributed-MUMPS run. Code_Aster's general MPI capacity is not fully exercised
by this launch recipe.

The command uses a composed argument string. The mount path is quoted, while
the export basename is appended without equivalent token handling. The diagnostic
study writer also emits paths containing spaces without escaping. I did not run
Code_Aster path parsing; these are concrete input/argument cases to test, not
claimed reproductions of every parser's behavior.

Cancellation follows host processes through `pgrep -P`. A Docker CLI's children
are not the container's solver processes in the daemon/VM. The command uses
`--rm` but has no retained container ID/name and no explicit docker stop/kill
path. Therefore full container cancellation after client termination is **not
established** by this implementation. We should keep a worker job handle, stop
the actual container, drain logs and verify no solver remains. This is a source-
based lifecycle gap; no orphan-container experiment was performed.

### Options worth comparing

| Execution route | What it changes | Assessment |
|---|---|---|
| Native macOS ARM64 CalculiX/SPOOLES | Native CPU; no VM/translation; current Homebrew build only one supplied direct backend | Useful first reference and delivery route; solve-stage scaling/capacity remains a concern |
| Native Linux ARM64 VM + CalculiX/PaStiX | Same FEM engine; different OS/build, optional virtualization; no ISA translation if all components are ARM64 | High-value build/recovery candidate; PaStiX/BLAS correctness still needs validation |
| PrePoMac's Linux amd64 Code_Aster under Rosetta | Different FEM engine/formulations plus ISA translation and VM memory limits | Convenient access to a substantial packaged engine; no demonstrated speed advantage in this review |
| Linux ARM64 Code_Aster built from source | Same additional engine without x86 translation | Worth feasibility work if Code_Aster is selected; current conda recipe is not a ready ARM package |
| Actual Linux x64 worker/server | Native x86 engines, larger-memory hardware if available, optional MPI | Strong candidate for demanding jobs; remote submission/data/lifecycle is another explicit adapter |
| Linux x64 CalculiX with PaStiX/PARDISO | Keeps CalculiX model/deck semantics; platform/backend-specific build/licensing | Compare against open-backend routes under existing Panua exclusion; a VM alone does not grant backend rights or ARM support |

An ARM Linux VM is not inherently faster than macOS on the same chip. A better
algorithm/library/build can overcome virtualization overhead; translation and
insufficient VM RAM can also erase it. We need full-job elapsed time, peak RAM,
paging, equilibrium/residuals and repeated correctness before recommending a
worker. CPU/GPU rendering in the UI is independent of solver acceleration. No
GPU benefit or automatic Apple GPU use follows from Docker/Code_Aster here.

## 5. UI strategy: what we should learn without assuming ours wins

PrePoMac has a working desktop implementation and release; we currently have
bounded portable libraries and CLIs. It is ahead in usable application breadth.
Our *planned* UI cannot fairly be declared better in appearance, responsiveness
or feature completeness without an interactive implementation and comparison.

Its strongest UI decision is preserving the original forms. That retains a
large volume of dialogs, prompts, commands, tree/editor behavior and upstream
workflow knowledge. The compatibility assembly is a practical way around
Controller's direct FrmMain coupling. It can bring upstream form changes across
with fewer manual presentation rewrites.

The cost is owning WinForms compatibility. The reviewed source has **19,423
physical lines in 31 WinFormsCompat C# files**, plus **2,214 lines of DrawingCompat**.
These are size indicators including comments/blanks, not quality scores.
They implement meaningful property grids, grids, trees, binding, menu strips,
dialogs, controls, input and painting. A minor difference in layout, focus,
event order or font metrics can affect many dialogs at once. Its Avalonia render
timer workaround uses reflection into internal implementation details; that is
another version-sensitive boundary. This is real engineering maintenance work,
even when the shared forms compile unchanged.

Our [proposed transition architecture](../MIGRATION_STRATEGIES.md) aims to keep
Windows as the oracle and share original model/commands/application behavior
through narrow services, with a portable frontend. It can yield a cleaner
cross-platform UI and headless API in the long term, but requires implementing
the presentation surface that PrePoMac already has. The biggest danger on our
side is translating every dialog and accidentally duplicating Controller logic.
The shared API gateways and existing commands should remain the behavior layer.

**Recommendation:** keep our separation objective, but include PrePoMac's form
compatibility route in the actual frontend experiment. A hybrid—temporary form
compatibility with independently preserved native VTK and narrow process/
document services—could accelerate a preview. It is an untested option, not an
approved integration plan. We should compare representative dialogs and workflows
before deciding whether compatibility debt is cheaper than a new presentation.

## 6. Rendering: API compatibility is not native VTK equivalence

The macOS vtkControl project compiles original view code against its own
Kitware.VTK implementation. It does **not** bind that code to modern native VTK.
There are **12,504 C# lines in 18 files** under macOS/vtkControl, including
substantial data structures, filter algorithms, locators, picking, camera,
widgets, exporters and custom OpenGL shaders. It is much more than a triangle
renderer, and deserves evaluation on its merits.

However, it becomes responsible for results interpolation, geometric clipping,
cell identity, picking and surface behavior that our strategy intends to retain
from VTK. Those operations can affect scientific interpretation, not only visual
appearance. The implementation includes concrete non-equivalent edges:

- vtkHardwareSelector returns an empty selection; the port instead uses area
  picking in its current view path. This is not evidence that all selection is
  broken; it is a narrower compatibility contract.
- Decimation/smoothing/subdivision classes near the end of Filters.cs pass input
  through. The source labels these development-use functions. Their callers and
  future upstream use must be reviewed before promising full VTK behavior.
- vtkProbeFilter implements its own spatial lookup/interpolation and validity
  mask. Clipping and picking are also real rewritten algorithms that need exact
  FEM-ID and scalar-value tests.
- The view hosts OpenGL through Avalonia OpenGlControlBase and handles render
  scaling. OffscreenRenderer is separate and still hardcodes Apple's OpenGL
  framework/CGL functions. Linux has no matching framework path, so this exact
  offscreen route is not portable. Linux screen rendering and headless compute
  success do not establish screenshot/video support.

Sources: [filter implementations][filters], [picking/widgets][interaction],
[interactive surface][render-surface], [offscreen CGL][offscreen]. Rendering/input
equivalence and performance were not run. We should test exact IDs on deformed/
clipped quadratic meshes, rectangle occlusion semantics, probes, scalar ranges,
DPI/focus and repeated host disposal, rather than rely on screenshots/API pass
counts. Large mesh upload/frame time and memory also need measurement.

**I favor our native-VTK preservation direction for long-term scientific and
maintenance reasons**, subject to proving its bindings/host on required targets.
That does not select Avalonia versus PyQt6/Python VTK. Both remain candidates.
PrePoMac's working input/navigation/layout and adapter code are useful references;
adopting its renderer wholesale would take on a second visualization algorithm
implementation that our plan deliberately avoids.

## 7. What Linux support actually consists of

Linux uses the **same macOS net10 project graph**, compiled and run natively on
Linux, not Wine and not a Mac VM. The source implements:

- `.so` versus `.dylib` output/copy rules in shared build settings.
- `cc -shared -fPIC` Win32 compatibility library and Linux gettid syscall.
- Case-correct project paths. Our literal project-reference audit found zero
  case mismatches in its scoped scan; no whole Linux build is implied.
- OpenCASCADE headers from `/usr/include/opencascade`, gmsh from `/usr` or GMSH_DIR,
  with Linux CMake link/rpath rules.
- gmsh/lp_solve/Python library discovery under Linux names and native ccx on PATH.
- Avalonia platform detection and interactive OpenGL; a Mesa shader extension
  fallback for arrays-of-arrays accepted by the Mac compiler.
- Avalonia Headless for `-g No` unless PPM_NATIVE_BATCH=1, avoiding a window server
  for many scripted tasks. This still uses the compatibility UI/controller graph;
  it is not an independent headless core.

[Build settings][build-props], [native build/CMake][linux-build],
[application initialization][compat-app], [Linux discussion][linux-issue].

The author reports a Debian 13 ARM64 container build, STEP/BREP import, both
Netgen-labelled/gmsh mesh routes and Python scripts without a window. The original
reporter shows the UI on Arch Linux/X11. These claims are concrete and credible,
but not our executed results. The author also documents font/label truncation and
window-title issues. The native helper links **gmsh, not a separate Netgen
library**: a Netgen-labelled item uses Gmsh's Frontal/Netgen algorithm, not the
original patched nglib implementation.

There is no Linux job in the two reviewed GitHub workflows. There is no verified
Linux x64/ARM64 full numerical/interactive acceptance matrix, Wayland result or
Linux installer in those workflows. The Mac-only CGL capture path, forced amd64
Code_Aster command, default `colima-aster` context and host resource assumptions
are important portability gaps. A native Linux x64 Docker installation would
usually need its context configured; Linux ARM64 still faces the explicit amd64
container target even though the desktop itself can be ARM64.

Our four-target acceptance remains broader than this delivery matrix. Its Linux
changes are worth reusing selectively, especially discovery/CMake/case checks,
but they do not close our Linux rendering/solver/package requirements.

## 8. CAD/meshing differences matter for the solver comparison

PrePoMac's native helper is **3,608 physical C++ lines across eight files**, plus
headers/build configuration. It handles real CAD operations and writes protocols
the original controller can consume. It uses OpenCASCADE and gmsh, including
structured faces and mesh-size controls; it is not merely an executable shim.
The reviewed Mesh.cpp sets gmsh Algorithm3D=4 and uses gmsh's optimization and
quad recombination. It maps entities by geometry measures/centers, so topology/
identity must be checked on ambiguous and compound cases. [Native mesh code][mesh].

Q-Morph explicitly reports unavailable and leaves surfaces to gmsh recombination.
QuadWild remains unavailable in the README. Mmg is built from v5.7.0. These choices
enable an app but differ from our unchanged-tool/source-parity goal. They should
be described as capabilities or explicit substitutions, not presumed equivalent
because the command or file names match. [Q-Morph adapter][qmorph].

For shells, a gmsh recombination setting avoids nearly flat quads at tube
junctions because CalculiX's through-thickness expansion can produce a negative
Jacobian. That is directly relevant to our F001 interest. It is not proof that
our shell junction problem is resolved: the README still reports approximately
50% stiffness disagreement on the bike frame between CalculiX and Code_Aster,
with junction/support causes unresolved. Changing mesh generation and changing
shell formulation at the same time prevents attributing the difference solely
to a sparse linear solver.

## 9. Validation: useful fixtures, weaker acceptance than we require

The repository reports **77 of 79 API scripts passing**. This review did not
rerun that suite and found no retained complete run JSON/log corpus among the
reviewed source artifacts. Our 78 results checks and their 79 API scripts are
not comparable counts: they test different scopes.

The live GitHub API confirms successful **Build and Release workflows for the
exact reviewed fb5a89db commit**. Their YAML builds the Mac app/native parts and
packages it; it does not run the 79 API scripts, the composite validation, a
solver regression or a Linux matrix. Build/packaging success is real evidence
of deliverability, but not numerical acceptance. [Exact build run][build-run],
[exact release run][release-run], [workflow source][ci].

The composite validation is a valuable contribution: original model/API scripts
compare a Navier cross-ply plate, a tension strip and a cantilever against
classical laminate theory, using layered CalculiX, smeared CalculiX and Code_Aster.
The current README reports excellent plate agreement and also reports material
differences that matter: layered CalculiX reserve error around -7.5% in tension,
smeared cantilever deflection around -54% and reserve around +28%, and the
unresolved bike-frame discrepancy. Blanket descriptions such as “all within 1%”
would be inaccurate for its current table. [README validation][readme],
[validation script][plates].

I executed only its analytical formula definitions, obtaining finite values and
the intended reserve factor 2 for all three cases, and checked matrix symmetry.
That verifies that the formula code executes coherently, **not the author's
published FE results**. The validation main prints relative errors without
asserting numerical acceptance thresholds. Its shell runner also does not enforce
an aggregate numerical gate. We should retain these fixtures with pinned meshes,
material/BC definitions, expected limits, results/reactions and actual run records.

The reported two failing API cases—mirrored revolve end cap and approximately
1% second-order swept-mesh volume error—remain useful regression fixtures.
Passing many headless API scripts does not validate dialogs, pick IDs, contour
accuracy, cancellation, all nonlinear cases or PMX round-trips across versions.

## 10. Persistence and distribution

PrePoMac restores `System.Runtime.Serialization.Formatters` 10.0.0 and enables
unsafe BinaryFormatter serialization. The actual release runtimeconfig confirms
that setting. Its surrogates handle .NET Framework type holders, filesystem
objects and delegates, with assembly resolution that ignores versions. This is
substantial legacy-compatibility work worth understanding. It is not our proposed
bounded NRBF/document reconstruction boundary and does not settle graph alias,
clone, event, history or bidirectional Windows compatibility. [Surrogates][surrogates],
[build settings][build-props]. We have neither enabled nor adopted this mechanism.

It ships a self-contained Apple Silicon `.app` ZIP with .NET runtime, native
libraries, CalculiX and embedded Python/NumPy. The bundler recursively copies
Homebrew dylibs, rewrites load paths, copies licenses/formula versions and checks
for remaining Homebrew references. Those are immediately useful packaging ideas.
The verified release contains no Code_Aster/run_aster payload: the optional engine
requires a separately built image and Docker/VM setup. [App builder][app-builder],
[bundler][bundler], [release metadata](prepomac/release-inspection.json).

The source uses ad-hoc signing and tolerates bundle-sign failure; it does not
implement Developer ID notarization, DMG, Windows MSI/EXE, Linux DEB/RPM or a
Homebrew application formula. Native libraries come from the then-installed
Homebrew versions; NumPy installation is unpinned, and the Code_Aster environment
is not fully locked. The source has license tracking and corresponding-source
guidance, but does not itself provide our complete immutable source/build closure.
These are delivery/reproducibility differences, not a claim about the legal status
of its releases.

## 11. Side-by-side judgment

| Dimension | PrePoMac today | PrePoMax-X today / intended direction | Judgment |
|---|---|---|---|
| Usable application | Mac release with broad model→mesh→solve→results workflow; Linux reports | Tested bounded original libraries/CLI; no portable desktop yet | PrePoMac is ahead in delivery |
| Engineering ownership | Shared original folders, plus changes and new Code_Aster translation | Original assemblies/source, guarded extractions and exact replay pins | Keep our source/semantic discipline; reuse reviewed changes |
| UI approach | Original forms over a custom Avalonia WinForms layer | Narrow behavior/services and portable frontend, framework undecided | Ours may reduce compatibility debt; theirs avoids large immediate dialog rewrite |
| Rendering | Own VTK-compatible algorithms/OpenGL | Retain native VTK, binding/host undecided | Prefer native VTK long term, prove it; study their working host/input |
| Solver delivery | Native 2.23 SPOOLES; optional translated amd64 Code_Aster subset | Native 2.22/open-backend recovery not accepted yet | Borrow recipes; do not confuse available binary with matching numerical acceptance |
| Linux | Shared Mac graph builds experimentally; native helpers; capture/container gaps | Linux ARM64 bounded checks and hosted native x64; desktop work pending | Selective reusable platform code; neither completes four-target desktop parity |
| Persistence | Legacy formatter restored with surrogates | Bounded inspection/compatibility evidence; production format undecided | Study fixtures; no automatic formatter adoption |
| Native mesh/CAD | New gmsh/OpenCASCADE implementation; unavailable families | Recover exact original patched tool behavior/sources | Different feature-equivalence contracts |
| Validation | Broad author API claims, analytical fixtures; CI build/release | Narrower but retained cross-host/source/negative-control evidence, explicit failures | Combine useful corpus with our acceptance discipline |
| Packaging | Verified Mac ZIP, dependency bundler | Required four-target installers/Homebrew not yet delivered | Reuse bundling ideas; finish signing, locks and target matrix |

## 12. Recommended next work

1. **Preserve our core and add a compute-worker boundary to the design.** A worker
   can be local Mac, native Linux, Linux VM/container or later a remote machine.
   Resolve actual architecture/build/capabilities, CPUs/RAM and lifecycle there.
   Keep local native solving available for suitable workloads. The maintainer's
   VM tolerance removes the need to reject a useful worker merely for being a VM;
   it does not prove any route faster or require a VM for all users.
2. **Complete one real CalculiX workflow before a broad solver switch.** Build a
   pinned native CPU reference with understood SPOOLES threads, then recover/
   compare PaStiX on Linux. Keep 2.22/2.23 explicit. Use cube equilibrium and
   shell/solid fixtures, followed by modal/buckling/contact cases and memory/
   thread scaling. Preserve the original algorithms/tolerances and unknowns.
3. **Evaluate Code_Aster as an explicit additional engine.** Start with a strict
   eligible linear-static subset, reject unmapped model content before writing,
   choose/document formulations, retain result provenance/reactions, and use
   worker resources/container handles. Reuse PrePoMac's translator and analytical
   fixtures only after a focused code review and attribution. Compare its exact
   amd64 VM route against native routes rather than assuming it is faster.
4. **Run the frontend/renderer experiment on evidence.** Compare a native-VTK
   C# host and the Qt/Python-VTK candidate over shared C# behavior; include a
   bounded PrePoMac compatibility/hybrid option for preview speed. Test actual
   forms, tree/property/plot behavior, exact picks, clipping/probing, DPI/input,
   large results and lifecycle on required targets. Do not rewrite Controller's
   engineering logic in presentation.
5. **Reuse specific assets, not the entire fork by default.** Highest-value
   candidates: native project/source lists, Linux discovery/CMake fixes,
   dependency-bundling logic, navigation patterns, form-compatibility lessons,
   composite/revolve/sweep fixtures and the optional Code_Aster prototype. Hold
   automatic backend rewriting, custom VTK, formatter restoration, gmsh-for-Netgen
   substitution and fixed-resource amd64 container launching behind explicit
   capability/policy review.

This investigation changes our information and the range of execution options
worth testing. It does not close the native solver, correctness, tetrahedron,
Windows/net48/RC2, persistence/CAD, interactive rendering, four-target installer,
corresponding-source or Homebrew requirements. All work remains local and
uncommitted; no publication, contact or production policy selection occurred.

## Reproduce the bounded diagnostics

Use the exact PrePoMac pin in a separate checkout; do not run its app installer.

```sh
python3 .project/reports/prepomac/review-source.py /path/to/pinned/prepomac \
  --output /private/tmp/prepomac-source-review.json \
  --harness-dir /private/tmp/prepomac-review-harness
dotnet build /private/tmp/prepomac-review-harness/Review.csproj -c Release \
  --configfile /private/tmp/prepomac-review-harness/NuGet.Config
review_fixture=$(mktemp -d /private/tmp/prepomac-fixture.XXXXXX)
dotnet /private/tmp/prepomac-review-harness/bin/Release/net10.0/Review.dll "$review_fixture"
```

Use a fresh fixture directory for capability/cache observations. A file remaining
from a previous run changes the missing-executable setup. No package feeds or
unsafe serializer setting is needed for this harness. Its output deliberately
contains no claim of solver/numerical/application acceptance.

[readme]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/README.md
[build-props]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/Directory.Build.props
[winforms]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/WinFormsCompat/WinFormsCompat.csproj
[vtk-project]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/vtkControl/vtkControl.csproj
[win32]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/Native/Win32Compat.c
[brew-formula]: https://github.com/costerwi/homebrew-calculix/blob/b128bf20a3d4db864832e54624d591473cde8e01/calculix-ccx.rb
[tools]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/CaeGlobals/Tools.cs#L241
[solver-settings]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/PrePoMax/Settings/SolverSettings.cs#L83
[controller-fallback]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/PrePoMax/Controller.cs#L22140
[controller-aster]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/PrePoMax/Controller.cs#L3515
[ccx-official]: https://www.dhondt.de/
[pastix]: https://solverstack.gitlabpages.inria.fr/pastix/index.html
[jobs]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/CaeJob/AnalysisJob.cs#L1008
[aster-solvers]: https://code-aster.org/doc/v17/manuals/man_u/u2/u2.08.03/Les_diff_rents_solveurs_lin_aires_disponibles.html
[aster-writer]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/CaeModel/FileInOut/Output/CodeAster/CodeAsterFileWriter.cs
[aster-post]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/CaeModel/FileInOut/Output/CodeAster/CodeAsterPostScript.cs
[aster-container]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/Native/CodeAster/Dockerfile
[aster-recipe]: https://github.com/conda-forge/code-aster-feedstock/blob/fc82bf852bb4fa490146bf524c0bb99092eb904a/recipe/recipe.yaml
[filters]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/vtkControl/Mac/Vtk/Filters.cs#L2849
[interaction]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/vtkControl/Mac/Vtk/Interaction.cs#L852
[render-surface]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/vtkControl/Mac/Gl/RenderSurface.cs
[offscreen]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/vtkControl/Mac/Gl/OffscreenRenderer.cs#L12
[linux-build]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/Native/NetGenMesher/CMakeLists.txt
[compat-app]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/WinFormsCompat/Forms/CompatApplication.cs
[linux-issue]: https://github.com/moritzschuettler/prepomac/issues/2#issuecomment-6399647971
[mesh]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/Native/NetGenMesher/Mesh.cpp#L870
[qmorph]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/GmshCommon/QMorph.cs
[build-run]: https://github.com/moritzschuettler/prepomac/actions/runs/40651486364
[release-run]: https://github.com/moritzschuettler/prepomac/actions/runs/40651491166
[ci]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/.github/workflows/build.yml
[plates]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/assets_composites/plate-validation/plate_validation.py
[surrogates]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/CaeGlobals/TypeSerializationSurrogate.cs
[app-builder]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/make-app.sh
[bundler]: https://github.com/moritzschuettler/prepomac/blob/fb5a89dba6ac975956d9001edf6d6756f18fe0ca/macOS/bundle-deps.py
