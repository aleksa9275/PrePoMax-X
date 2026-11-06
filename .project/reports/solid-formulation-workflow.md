# Connected solid formulation workflow

Task 0089 connects the original mechanical 3D solid families through INP import,
formulation selection, configuration, native static solving, original results and
mesh export/reopen. This is one functional milestone under the reaffirmed D050
cadence. The final specification remains all original PrePoMax functionality on
all required platforms, with only the unavailable Intel/PARDISO solver excepted.

## Usable behavior

**Solid formulations…** selects topology-compatible original formulations per
imported element block, preserving coordinates, IDs, connectivity and named
regions. A change invalidates previous analysis/results. Choices are checked
in C# and read back through the original INP reader before publishing session
bytes. Existing destinations and incompatible topology changes are refused.
The original imported file is preserved.

The connected mechanical solid choices are **C3D4, C3D10, C3D10T, C3D6, C3D15,
C3D8, C3D8R, C3D8I, C3D20 and C3D20R**. Formulation names remain explicit in the
model tree, exported input and frozen solver deck; reduced/incompatible variants
are not flattened to the full-integration default. Mixed meshes retain separate
original element blocks and section memberships.

**C3D5/C3D13 pyramids** use the original `CalElement` and element conversion
methods. Configure → Model / units requires an explicit **collapsed wedges** or
**collapsed hexahedrons** choice. The submitted definition records the choice;
no default conversion is inferred. Original result restoration reconstructs
linear/quadratic pyramids from those collapsed elements for display, while a
separate `solverElements` inventory retains original decoded solver connectivity.

Mesh and result transport now carry `GetVtkNodeIds()` separately from engineering
`NodeIds`. The viewport uses the original per-family VTK permutation, including
wedge ordering, without changing solver connectivity. This also preserves the
original quadratic FRD wedge/hexahedron permutations. Original element,
quadrature, classifier and solver algorithms remain unchanged.

**Solve example…** now offers the original cube, a mixed solid model covering
all ten formulations, and pyramids using either original conversion. Examples
are bundled with Mac/Linux packages and available as readable INP/analysis inputs:

- [Mixed solid mesh](../../X/Analysis/StaticDeck/mixed-solids.inp) and
  [definition](../../X/Analysis/StaticDeck/mixed-solids.json).
- [Linear/quadratic pyramids](../../X/Analysis/StaticDeck/mixed-pyramids.inp) and
  [definition](../../X/Analysis/StaticDeck/mixed-pyramids.json).

## Integration evidence

[Receipt](solid-formulation-workflow-verification.json) records actual source,
native workflows, original-Windows comparison, candidate and publication.

Native Mac and Linux ARM64 desktops complete formulation editing, original
configuration, native solving, nodal history decoding, result rendering,
mesh-only export and fresh reopen for the mixed solid model and both pyramid
conversion routes. The mixed model has **249 nodes and 54 elements**; the two
pyramid parts have **38 nodes and 12 elements**. Both include free axial unknowns
between prescribed top/bottom displacements, with E=1000 MPa and nu=0. The
analytical solution is U3=0.001z, other displacements zero and axial stress 1 MPa.

All three models reproduce analytical displacement, stress and force equilibrium.
The mixed model's maximum printed stress residual is 5e-5 MPa (original solver
extrapolation/FRD precision); the new fixture bounds are 1e-9 displacement,
1e-10 lateral displacement, 1e-4 axial stress, 1e-5 other stress and force balance.
Existing numerical expectations/tolerances are unchanged. Both original element
failures and the independent quadratic-tetrahedron measurement gate remain.

The same three native solver decks execute with the fingerprint-checked original
Windows CalculiX 2.22 binary/runtime in the existing CrossOver bottle. Mesh
identities and decoded displacement fields match exactly; maximum stress-field
difference is about **3e-13 MPa**. Force/strain comparisons also pass the recorded
bounds. This is original Windows binary reference execution, not native Windows
platform acceptance or bitwise equality of all fields.

Affected current analysis/results suites and existing Mac desktop regressions
pass. The old rejection case for C3D8R is updated to a thermal DC3D8 case because
C3D8R is now deliberately supported; the original mathematical checks are intact.
A native Linux PMX regression passes with a rebuilt affected deck consumer. The copied Mac candidate completes the same mixed-solid and both pyramid
workflows in both viewport modes, plus representative PMX and curved-CAD C3D10
regressions. Its payload, source identity and ad-hoc signature verify.

## Remaining scope and delivery

This milestone extends imported solid mesh calculations. It does not yet supply
CAD-driven hexahedral/wedge/structured mesh authoring, shell/beam/2D/axisymmetric
analysis, all materials/loads/contact, nonlinear/dynamic/thermal steps or the full
native-session PMX/model/results graph. All remain required implementation work.
General curved quality, both known original failures, exact cross-platform
parity, native Windows/net48/Linux x64, installers/Homebrew/signing/notarization
and full release acceptance remain open. D057/D058/D059 remain in force.

Implementation **73a4b9d399de5b29d5c645af764522e84a15926c** is pushed and
remote-verified on `origin/research/native-feasibility`, with CI explicitly
skipped and no hosted jobs requested. The package identifies this exact source,
no changed code and an empty source patch. The dirty flag comes from four
pre-existing Finder files. Closing documentation follows on the same branch.

Current app: `/tmp/prepomaxx-task0089-delivery/PrePoMax-X Preview.app`.
Sibling `Native CAD Preview.command` enables the retained native CAD runtime.
Use **Solve example… → Mixed solids — all mechanical formulations**, or select
one of the pyramid examples. Qt's toolbar overflow menu exposes controls when
the window is narrow.

All **2,426 copied file hashes**, symlink targets and the ad-hoc signature verify.
The superseded task 0088 app and duplicate package build/payload/cache directories
are pruned; its launcher forwards to the new candidate. Approximately 4.13 GiB
of free space is reclaimed. Models, exports, frozen jobs, screenshots, source and
reference/manifest/log evidence, installed user app/state and shared tool caches
are preserved. Actual removed paths/bytes and post-cleanup checks are in the
receipt. Evidence is `/tmp/prepomaxx-task0089-evidence`; retained package/source/
manifest/log metadata is `/tmp/prepomaxx-task0089-package`. Hosted CI remains
held under D058 and native x64 remains deferred under D059.
