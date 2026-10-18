# Repository organization and public release lane

Accepted maintainer requirement, 2026-10-18: the final repository must be clean,
understandable, carry all third-party software sources in appropriate folders,
and have a dedicated public release branch serving installers and package
managers. This is a delivery requirement; recording it does not publish a branch
or redistribute incomplete dependencies.

## Repository map

| Location | Purpose |
| --- | --- |
| Original CaeGlobals/CaeMesh/CaeModel/CaeResults/CaeJob and application folders | One engineering implementation, original paths/type/assembly ownership; portable build projects source-link these files |
| X/Core | Earlier offline partial-build tools and regression baseline |
| X/Analysis | Expanded model/deck build, strict input tools, fixtures and checks |
| X/Execution | Modern CaeJob platform boundary, native process tests, pinned solver preflight/run command |
| X/Feasibility | Historical bounded experiments and reference capture tools; not the end-user product |
| ThirdParty/Sources/<component>/<version> | Unchanged corresponding third-party source, own license, per-file/archive pins and provenance |
| ThirdParty/Patches and ThirdParty/Build | Final reviewed patches and reproducible RID-specific build recipes, separate from pristine source; added as recovered/verified |
| Existing ThirdParty SDK/native folders | Preserved upstream assets during migration; not evidence of matching implementation source |
| Licenses | Third-party attribution/notices and source links, reconciled against each actual shipped dependency |
| X/*/artifacts and ignored build/cache paths | Local packages, downloaded archives, object files and runtime outputs; excluded from source commits |
| .project/STATUS.md | Current state and next work; earlier entries are historical |
| .project/RELEASE.md | Installer/Homebrew/signing/clean-machine acceptance |
| .project/reports and tasks | Evidence and bounded task records, separate from application/dependency sources |

The final public source release must contain corresponding source for every
shipped third-party component, including transitive libraries and managed/native
runtime components as applicable, with exact version/revision, local patches,
licenses and reproducible build/asset relationship. An SDK header, package name,
download URL or unrelated stock source snapshot is not the corresponding source
for a modified binary. Preserve all upstream license boundaries. Complete the
inventory incrementally; do not move upstream project paths simply for cosmetics.

CalculiX 2.22 is the first recovered component under the new source layout.
Other documented custom-source gaps remain explicit release blockers. Keep
artifacts and caches out of pristine source directories. The public download
must expose the matching source archive and checksums alongside binaries.

## Branches and distribution

- `master`: exact upstream mirror, fast-forward only.
- `x/main`: reviewed PrePoMax-X integration, keeping upstream ancestry.
- `research/*`, `feature/*`, `integration/*`: scoped implementation/review lanes.
- `x/release`: planned dedicated public release lane. Promote reviewed commits
  from x/main after the required release gates; package builds must use an exact
  immutable version tag/commit, never a floating research branch. Maintain this
  branch with normal reviewed commits, no forced rewrites.

The branch role is accepted; `x/release` is the chosen project-prefix naming
convention to make it easy to follow. Create/protect/populate it when a concrete
release candidate is ready for reviewed publication, under normal maintainer
publication policy. No branch or protection setting is changed by this record.

Homebrew tap/cask/formula and other package-manager metadata must resolve to
versioned public release artifacts produced from that release commit. Publish
architecture-specific checksums, matching source archives, runtime dependency
manifests and notices. A package manager must not build from a moving branch or
consume an unreviewed development ZIP. RC and stable channels remain explicit;
installation, upgrade and uninstall are tested independently on required targets.

This organization is additive during research. Plan any eventual consolidation
of experimental build projects and historical evidence deliberately so the final
public entry point is short and usable, while preserving reproducibility/history.
