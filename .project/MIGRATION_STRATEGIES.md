# Migration strategies: proposal, not commitment

Judgment is based on the existing dependencies in [ARCHITECTURE](ARCHITECTURE.md), not an assumption that the core/controller is already independent. Complexity estimates are relative; no schedule or person-month estimate is defensible until the feasibility gates run.

| Criterion | A — minimal-difference adaptation | B — modern .NET + new cross-platform GUI | C — shared core with separate frontends |
|---|---|---|---|
| Definition | Keep upstream layout/algorithms/controller; add platform services and substitute unavoidable GUI/control hosting incrementally | Modernize projects and build a new GUI, preserving engineering and command behavior | Keep upstream Windows WinForms frontend as reference; introduce a native cross-platform frontend over shared source/behavior and services |
| Feasibility | Feasible as incremental boundary work; unchanged WinForms cannot satisfy all native targets | Feasible after serialization/native/render gates; large interface surface | Feasible transition if shared-source compilation and API seams prevent a second independent controller |
| Scope | Small boundary edits accumulate; GUI replacement still unavoidable | New dialogs/tree/property editors/plots/layout + controller adapters + core/interop modernization | Add shared build targets and adapters, cross-platform frontend in parallel; avoid physically moving all source first |
| Windows | Existing UI can remain first; validate new services against old behavior | UI/graphics migration risk across all Windows features | Existing UI retained as oracle; new frontend may eventually serve Windows too |
| macOS ARM64 / x64 | Host, UI, native binaries and ABI work; no benefit from WinForms-only compatibility | Framework candidate must support both architectures plus VTK surface integration | New frontend/native services required; reference Windows frontend is not delivered on Mac |
| Linux x64 / ARM64 | Same barriers, X11/Wayland/input/native build differences | GUI framework coverage + GPU/backend behavior need real tests | New frontend and native builds; ARM64 remains a later capability gate |
| Rendering | Preserve VTK via binding/host adapters; least pipeline change | Same VTK retention possible; adopting Avalonia does not itself solve bindings | Separate legacy Windows view host and portable VTK host sharing scene semantics/mappings |
| Upstream merges | Lowest source movement; conditional logic can become hard to maintain | Highest conflicts if Controller/forms/models are broadly reorganized | Low-to-medium if upstream files stay in place and adapter changes stay narrow; high if a second business-logic layer emerges |
| Long-term maintenance | Minimal patches desirable, but scattered conditionals can create debt | One UI eventually helps, yet manual translation of every upstream GUI feature is costly | Two hosts initially; require one command/model behavior layer and retire duplication only after parity |
| Testing | Adapter contracts + Windows differential + all required targets | All engineering and UI flows revalidated; widest early regression surface | Shared core contracts + frontend equivalence + Windows oracle; behavior drift explicitly monitored |
| Licensing | Existing GPL with native closure; binding choice unresolved | Framework license/renderer/native distribution review; Avalonia core is a candidate, not a purchase decision | Same GPL/shared-source obligations; proprietary wrapper coupling can still defeat open-source distribution |
| Main risk | “Minimal changes” cannot mean unchanged UI/binaries; platform conditionals sprawl | Maintenance fork becomes a separate product; rewrite loses numerical/command semantics | Permanent duplication of controllers, GUI-only upstream changes needing new presentation work |
| Relative complexity | Medium-high overall; low-risk increments | Highest initial breadth | Medium initial infrastructure, high GUI work later; most controllable transition |

## Recommendation

Use **C as the transition architecture, implemented with A's minimal-difference discipline**. Keep original Windows build/frontend as a regression oracle. Add portable services/shared builds around existing source files and reuse current IPython gateways, commands, mesher runners and engineering behavior. Keep one source of truth for numerical/application operations. A second independent FEM/controller implementation is out of scope. Reassess a unified frontend only after native feasibility and feature parity are demonstrated.

This is an architectural inference: it offers the best chance of limiting permanent divergence while avoiding a simultaneous Windows/frontend/core replacement. Its cost is maintaining two presentation adapters during transition. Track GUI feature parity explicitly and prohibit copying Controller into a separate evolving implementation.

## GUI candidates, not a selection

- Avalonia: .NET desktop candidate to investigate; native Mac views can be embedded through [NativeControlHost](https://docs.avaloniaui.net/docs/platform-specific-guides/macos). Must prove layout/input/focus/DPI and VTK integration on both Mac architectures and Linux; a platform handle is not an embedded-rendering guarantee.
- PyQt6 + Python VTK + shared C# backend: full production candidate, not only a diagnostic prototype. VTK provides a [Qt/Python interactor widget](https://docs.vtk.org/en/latest/api/python/vtkmodules/vtkmodules.qt.QVTKRenderWindowInteractor.html); PyQt's GPL option suits a GPL-compatible open-source project according to [Riverbank](https://riverbankcomputing.com/commercial/pyqt). Preserve engineering/application behavior in C#; compare pythonnet versus process interfaces for bulk data, lifetime, threading, cancellation and packaging. Existing WinForms/C++/CLI/serialization barriers still need solving in the shared backend. Port custom scene/selection logic without duplicating FEM logic. This option may reduce managed-VTK-binding work, but no native interoperability or parity experiment has run.
- Qt native frontend: credible VTK host ecosystem but introduces a larger C++/managed bridge, tooling and license review. Compare only if .NET-host route fails or native maintainability is better.
- .NET MAUI: examine required Linux coverage and custom native hosting before treating it as viable for all specified targets; no automatic choice.
- Mono WinForms/X11: existing code is a useful diagnostic route, not an accepted final architecture for native Apple Silicon/UI behavior.

## Rendering options

| Option | Reuse and cost | Decision gate |
|---|---|---|
| Modern supported ActiViz | Closest managed API family; vendor supplies cross-platform builds and GUI hosting | [Kitware user guide](https://www.kitware.eu/wp-content/uploads/2025/10/ActiViz.NET_9.5_Users_Guide.pdf) describes proprietary licensing and legacy 5.8 as the last open-source release. Confirm GPL/open-source development/redistribution rights and exact target tiers before adoption |
| Rebuild/modernize legacy open-source bindings | Potentially small C# call-site diff, substantial obsolete wrapper/runtime/native build work | Recover licenses/source and establish maintainable target builds; do not assume VTK 5.8 is sustainable on modern Mac toolchains |
| Focused C ABI + .NET facade over modern native VTK | Open-source controllable bridge; preserves native VTK filters/mappings, changes managed API boundary | Compare required VTK call surface, callbacks, lifetimes, thread ownership and performance; keep bridge narrow instead of wrapping all VTK |
| Qt/Python VTK frontend with shared C# backend | Established Python VTK wrappers and Qt widget; retain C# engineering code across an explicit data/command boundary | Full production candidate; prove native picking/scene behavior, efficient mesh/results exchange, shared-core integration and runtime packaging alongside the C# host candidate |
| Alternative renderer (OpenGL/Metal/other scene engine) | Reimplements picking, clipping, contours, widgets, exports and IDs | Last resort if VTK gates fail; requires a documented failure and larger equivalence budget |

Preserving VTK is recommended; **which binding/host** remains unresolved. No proprietary product, framework, dependency or renderer replacement is approved by Phase 0.
