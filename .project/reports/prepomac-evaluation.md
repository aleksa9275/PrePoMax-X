# PrePoMac evaluation — conclusions

2 November 2026. [Detailed audit](prepomac-evaluation-detailed.md) and
[retained evidence](prepomac/source-review.json).

1. **Keep our main goal: installable native PrePoMax-X.** Original C# engineering
   behavior, shared services and native VTK remain a sound direction. PrePoMac is
   ahead in working desktop delivery; our frontend framework is still open and
   our planned UI has not yet demonstrated a better user experience.
2. **CalculiX remains primary.** Existing SPOOLES/PaStiX paths are the practical
   open-backend route. PARDISO need not hold up initial native delivery. Native
   build, correctness and useful capacity still need proving. PrePoMac's bundled
   ARM64 CalculiX 2.23 lacks PaStiX/PARDISO; that is a build choice, not a general
   SPOOLES-only restriction. Our 2.22 reference remains explicitly distinguished.
3. **Defer Code_Aster.** It is a credible optional engine, but its current adapter
   is a limited linear-static translator with model/element changes. It is not
   needed for our initial product. A Linux solver VM remains an option when
   measurements justify it; no speed advantage was established in this review.
4. **Reuse selectively.** Study PrePoMac's desktop project structure, Linux
   discovery/CMake, dependency bundling and regression fixtures. Its custom VTK,
   automatic backend rewriting, formatter restoration and substituted meshers
   require separate decisions.
5. **Build toward installation now.** Deliver a desktop preview, then a complete
   native static-analysis workflow. Move repeated historical/platform checks to
   milestones while retaining focused numerical checks and reproducible bugs.

The audit verified source/release fb5a89db (v3.0-mac.4), ZIP and solver metadata,
plus bounded Mac diagnostics. Whole-app/numerical/performance acceptance remains
open; both known correctness failures and the tetrahedron measurement gate stay.

Next: [accelerated delivery plan](../proposals/accelerated-native-delivery.md).
