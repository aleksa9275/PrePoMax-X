# Original equation/material foundation and installable release objective

2026-10-18, Europe/Belgrade. [Task 0022](../tasks/0022-analysis-material-foundation.md).
The maintainer accepts the model/deck → native solve → original results sequence,
with Windows testing deferred during local coding, and explicitly requires an
installable desktop application. [Release delivery](../RELEASE.md) now records
Windows x64 EXE/MSI, Apple M-series macOS ARM64 DMG, Linux x64/ARM64 DEB/RPM or
reviewed equivalent, Homebrew, signing/notarization, clean-machine workflow,
upgrade/uninstall and source/license/dependency acceptance. Packaging was already
Phase 7 in ROADMAP; package formats and Homebrew are now explicit requirements.
Apple Developer ID can be provided. No account signup, signing credentials or
package publication is performed here.

## Verified observation — bounded implementation

`X/Analysis` is a source-linked superset of the existing four partial assemblies.
It reuses the original source in CaeGlobals/CaeMesh/CaeResults/CaeModel, not another
engineering implementation. Its build directories and dependency closure stay
separate from the earlier offline mesh/core build. No partial DLL may replace
an original installed application's assemblies. Source closure is **90 files**
for current/RC2 and **91** for the post-RC2 overlay.

Original `EquationContainer`, `EquationString`, `MyNCalc`, ordered dictionaries,
material properties and unit converters are callable. Original `CalMaterial` and
`CalElastic` produce the actual material keywords. New
`CaeModel.MaterialDeckWriter.WriteIsotropic` validates the bounded transport
scope, evaluates in the caller's culture, snapshots numeric values, then invokes
the original writers in invariant culture without changing source equations or
static converter units. `PrePoMaxX.MaterialDeck write-isotropic` writes a new
material fragment with an explicit pressure unit; an existing file is refused.
No mesh/load unit system is inferred. The boundary supports one active/valid,
temperature-independent isotropic elastic property with finite E > 0 and
-1 < nu < 0.5; unsupported properties/tables are rejected rather than omitted.

A material fragment is **not a complete analysis deck or installer**. Original
sections/BC/load/step graph and full consistent unit context are the next
component of accepted step 1; native solver execution, result readers and desktop/
persistence/CAD/installers follow under the accepted sequence.

Production source changes are narrow and mechanically checked:

- `ExtensionMethods.ToCalculiX16String` moves unchanged from Extensions.cs into
  Extensions.Calculix.cs; original namespace/class/assembly remain, class becomes
  partial and the original net48 project includes the new file exactly once.
- Remove four unused unavailable imports, proven by compilation: remoting
  contexts in EquationContainer/EquationString, WindowsRuntime in OrderedDictionary,
  and WinForms in StringNewtonGravityUndefinedConverter. No method body changes.
- The new material boundary remains CaeModel-owned and explicitly included in
  the original net48 project. Existing production package versions/references,
  serialized fields/interfaces and engineering algorithms are unchanged.
- The existing mesh regression is reused with `ANALYSIS_SLICE` permitting only
  the two explicitly pinned NCalc/UnitsNet dependencies in the expanded build.
  Default offline-core dependency expectations remain unchanged; the new material
  tests also reject desktop dependencies. The original test implementation is
  source-linked rather than copied.

## Verified observation — dependencies and upstream differences

Use exact existing upstream versions **NCalc 1.3.8** and **UnitsNet 4.89.1**.
PackageReference lock files and `X/Analysis/dependency-artifacts.json` pin the
NuGet content hashes, raw archive SHA256/SHA512 and selected runtime DLL hashes.
The modern build uses original NCalc `lib/NCalc.dll` and same-version UnitsNet
`lib/netstandard2.0/UnitsNet.dll`; net48 keeps its existing net40 reference.
The asset change is explicit and covered by quantity-conversion checks; full
native Windows comparison remains pending. NCalc's **NU1701** warning remains
visible because this old package does not declare modern framework support.
The bounded successful execution does not establish universal compatibility.
Package metadata/notices are retained in reports; NCalc's old CodePlex license
URL needs matching-source/license recovery before end-user redistribution.
No dependency binaries or packages are committed.

Current source is the baseline slice at de8f7303 with local mechanical changes;
RC2 replay is 912fb3d08014f246d48bef14d62a2cba0fdf5bb0. Post-RC2 replay is
f6273e39983e06042ae8b06e9a3dd0f729ea4b91. Unlike the earlier mesh closure, the
expanded material closure has real post-RC2 changes:

- ElasticLamina adds `GetPoissonsRatio23` and validates the completed 3D normal
  compliance block, tightening stability for some G23 values.
- Material.ContainsEquation recognizes the new original CompositeStrength type
  and its seven strength/interaction equation containers.

The exact three upstream file hashes are reviewed in analysis-sources.json.
Post-RC2 compiles those Git bytes in an isolated overlay, including the extra
original CompositeStrength type; its original net48 ownership is checked.
Baseline production material/lamina files are not replaced. Tests distinguish
old versus tightened lamina acceptance and absent versus present composite
capability, including strength equation detection and invalid interaction value.
No common algorithm/tolerance change hides the difference.

## Verified observation — execution and evidence

Each current/RC2/post-RC2 snapshot passes on **native Mac ARM64 and native Linux
ARM64**: 44 material/equation/unit/type/formatting checks plus all 218 existing
mapping/data/element/mesh checks, for **262 accepted checks per build**. Eight
material CLI/error controls pass per build. The expanded libraries retain the
same two original element correctness failures and tetrahedron measurement gate.
The old offline core also independently passes its 218 checks/39 CLI/four data
controls on Mac. Seven analysis source guards and ten existing replay guards
pass on Mac. Source, dependency and tool hashes, portable test/CLI outcomes and
all regression observations match between Mac and Linux for each source mode.
[Six-run verification and hashes](analysis-material-foundation/verification.json).

Representative commands (full arguments/stdout/stderr retained in each JSON):

```text
python3 -m unittest discover -s X/Analysis -p test_analysis_layout.py
python3 -m unittest discover -s X/Core -p test_upstream_replay.py
python3 X/Analysis/verify-analysis.py --expect-os Darwin --expect-architecture Arm64 --output <current report>
python3 X/Analysis/verify-analysis.py --upstream-revision 3.0.0-rc2 --expect-os Darwin --expect-architecture Arm64 --output <RC2 report>
python3 X/Analysis/verify-analysis.py --upstream-revision post-rc2-2026-10-17 --expect-os Darwin --expect-architecture Arm64 --output <post-RC2 report>
python3 X/Analysis/run-podman.py --output-dir <Linux reports>
python3 X/Core/verify.py --expect-os Darwin --expect-architecture Arm64 --output <offline core report>
```

Linux uses cached immutable image
`27c38b4417f399491c60ba15f35bf450ffcea6d57c78ccbc5ce3c9fb05cfcc88`, ARM64
server/image, networking disabled, repository mounted read-only and temporary
writable build/package storage. Exact downloaded packages are reused as a local
feed. It is a native architecture container in the Mac's Linux VM, not Linux x64
acceptance. The user-started Podman VM remains running.

Initial diagnostics are retained separately: a verifier incorrectly compared
signed-package NuGet contentHash to the raw ZIP SHA512; these are distinct and
now both recorded/checked correctly. A reused mesh assembly-reference check
initially rejected the two new upstream dependencies; its expanded-only allowlist
was made explicit while preserving the offline check. Neither is an engineering
algorithm/tolerance fix. Original constructor validation is deferred until
CheckEquations for some types; regression tests call that original API explicitly.

Native x64 CI is prepared additively in X/Analysis/gitlab-ci.yml, including both
pins, source guards and retained artifacts. **No new hosted pass is claimed**:
this increment is uncommitted and unpublished. Native Windows/.NET10, the full
original net48 build/RC2 oracle, full equation/parameter/model coverage and all
correctness/UI/persistence/CAD/native-source/four-platform/release gates remain.

## Architectural inference and next component

The tested foundation supports sharing original material semantics without
introducing a replacement evaluator or material model. It does not prove the
full Step/FeModel dependency closure is portable. Continue accepted step 1 with
original sections, constraints, loads, static steps and keyword generation,
measuring selection/preview/FeModel dependencies and preserving their ownership.
Then exercise the analytical cube as a complete analysis deck before adding
matching native solver execution and original result fields. Installer layout/
provenance work proceeds as hosts become usable; full release acceptance remains
separate from these source-linked increments.
