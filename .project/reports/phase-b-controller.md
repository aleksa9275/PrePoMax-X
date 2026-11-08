# Phase B — original Controller and persistence

Implemented and verified as a headless integration milestone, 8 November 2026
(D062). This completes the Phase B code path; Phase C remains the application/UI
integration. The [verification receipt](phase-b-controller-verification.json)
records executed coverage and pending acceptance, rather than inferring full
product parity from compilation.

The complete original Controller, all 276 original Commands compile items,
annotations, collections, settings, mesher runners, Python engine/gateways/journal
and APIs build for .NET 10 with their original assembly identities. The generated
`IControllerHost` boundary is implemented by both the original Windows form and
the portable headless host. Original engineering algorithms and tolerances stay
in the original assemblies. Runtime path, executable, physical-memory, culture,
Python and presentation boundaries contain platform code. Original Windows-only
methods were moved to partials; all eleven original C# assemblies also compile
with C# 7.3/net48 reference metadata, including the full Windows Controller/form.
This is compile-only evidence; native Windows execution remains pending.

Original PMX envelopes, mesh/results streams, original history and clone entry
points use restricted NRBF graph persistence on .NET 10. The checked-in explicit
type catalog, reviewed BCL containers and metadata-only converter/interface types
preserve cycles, reference identity, serialization constructors, original aliases,
comparers, arrays and value types. Old persisted UI delegate metadata remains
inert and is accepted only from its known undo/redo event slot. No unrestricted
BinaryFormatter switch is enabled. The original net48 formatter implementation
is retained behind the small original-source interface.

Executed on **macOS ARM64 and native-architecture Linux ARM64/Podman**:

- All 12 focused build/workflow stages pass, with no missing native profiles.
  Twenty persistence graph/rejection checks pass on each host.
- Original material commands, undo/redo, INP import/export, PMX save/reopen and
  fresh-process reopen; embedded original Python.NET engine and recorded scripts.
- Native face/edge picking, closest-cell queries, volume-frustum selection and
  actual original `SelectionNodeMouse` resolution. Undo reopens a saved baseline
  and replays a picked face node-set; redo preserves it. Original triangulation
  and edge selection are shared unchanged; VTK supplies native locators/filters.
- Original Controller job preparation → pinned CalculiX 2.22 SPOOLES execution →
  FRD loading → results-bearing PMX save/reopen.
- Original Controller CAD import using native Netgen → pinned patched Gmsh 4.13.0
  through original GmshCaller → 786-element tetra mesh → PMX round-trip.
- Original 3MF command produces 12 cube surface triangles through matching lib3mf
  2.4.1. Texture pixels/checksums are decoded independently. Native crop/smooth
  filters preserve original filter parameters/output choices and write STL.
- Established engineering regressions: mapping 25, data 30, elements 95, mesh 69,
  analysis 58 plus deck 74, execution 49, results 90. Both known D029 correctness
  checks remain **failed** with their original values; none was weakened or fixed.

**Original Windows 3.0.0 reference through isolated CrossOver:** the new solid PMX
opens with eight nodes, one element, one material and one step. Its original-app
CalculiX export is identical to the native Controller export after CRLF/LF
normalization; raw file bytes differ only in line endings. The original
app resaves the project, which reopens in the new Controller. A separate
results-bearing PMX opens with one eight-node/one-element result; the original
app queries displacement `0.00047619000542908907`, saves, and the native Controller
reopens and queries the identical value. Retained original CAD (843 elements),
saved-results and older-input PMX reads also pass. These are representative
bidirectional interoperability proofs, not exhaustive PMX compatibility. The
source RC/version marker still differs from the stable reference binary; exact
source/binary correspondence remains unverified.

Two write-interoperability defects were repaired: Windows-compatible typed,
inline value-type records, and the development host's missing original invariant
culture startup (the latter changed a density's parsed value). The shared startup
now invokes original culture code; arithmetic and tolerances were not changed.
The net48 sweep also exposed earlier helper code using C# 9 pattern/conditional
syntax; equivalent C# 7.3 expressions preserve those helpers' behaviour.

Native versions remain explicit: existing Netgen and patched Gmsh pins are
unchanged; Gmsh 4.15.2 is not adopted. CPython 3.12.14 (Mac) / 3.12.3 (Linux) are
fingerprinted verification profiles with Python.NET 3.1.0, not a newly selected
shipped Python default. Native spatial glue uses the existing VTK 9.5.2 host.
lib3mf 2.4.1 matches the original binding interface, from its
[official release](https://github.com/3MFConsortium/lib3mf/releases/tag/v2.4.1);
Linux builds the fingerprinted source-with-submodules archive, Mac tests its
universal binary. These profiles are verification inputs, not installers.

Phase C owns windows/controls, camera interaction, screenshots, rendered animation
and property editors; contour 3MF export takes the renderer's explicit lookup
table. The headless development entry point does not replace the original full
CLI/RPC/MCP application servers. The inventory marks structural B reachability,
not execution of every command or V coverage for entire feature families. Full
PMX/feature matrices, all native mesher variants/backends, native Windows, deferred
Linux x64, UI parity, installers/signing and release acceptance remain open. The
dormant Q-Morph wrapper has no exposed original option established and still lacks
its exact sources/license. Original numerical bugs and ordinary warnings remain
deferred under D061. The retained Qt preview is unchanged; no partial build was
copied over an installed application. Podman was restored to stopped.

Local evidence: `/private/tmp/prepomaxx-phase-b` (temporary, not distributed).
Early failed readbacks and the missing Linux Python-library setup failure are
retained as failures; final independent runs passed. Automatic approval review
rejected a direct diagnostic call to the original generic deserializer because
it could bypass the PMX allowlist. It was not run; restricted-reader/source
inspection and the approved normal original-application workflow supplied evidence.
