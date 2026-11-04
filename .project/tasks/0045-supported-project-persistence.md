# Task 0045 — Original PMX project compatibility

The maintainer selected full original .pmx compatibility and project reuse.
PrePoMax 3.0.0 is the target. Projects must transfer both ways between the
original Windows application and PrePoMax-X on macOS and Linux. Earlier
projects accepted by the target Windows application belong in the compatibility
corpus. Forward compatibility with future upstream releases is tracked per release.

1. Pin the exact original 3.0.0 source and executable. Capture controlled
   Windows files and semantic baselines for a mesh-only model, an editable
   static-solid model, and the same model with results and command history.
   Use the retained 2.6.0 cube, definitions, regeneration and private-project
   evidence as backward-compatibility references.
2. Build a safe read path for the first fixture. Decode records without
   activating payload types and map known records to the original domain
   objects with their IDs and shared references. Reuse original model,
   mesh and results codecs where their version gates and input bounds can
   be verified. Keep Controller/UI and execution side effects outside decoding.
3. Prove a writer against original Windows readback before exposing Save.
   Start with the supported static-solid slice. Verify Windows → X → Windows
   and X → Windows → X, including an actual material/load edit, deck
   comparison and native numerical rerun. Refuse a save if it would drop
   unsupported project state. Test failed writes, incompatible versions and
   preservation of the original file.
4. Broaden the bidirectional corpus to the full model and result surface,
   including geometry, mesh setup, material orientations, shell data, sets,
   outputs, jobs, annotations, and embedded command history. Test history
   replay and clone identity separately. Require native Mac and Linux desktop
   verification and the original Windows interoperability check before
   claiming completion.

The portable research workflow now proves edit → save → reopen → deck
reconstruction on macOS and Linux ARM64 for a checked result-free C3D8
project. The original Windows executable under CrossOver opens and resaves
the output. Native Mac solver fields match the independent official edit.
The task remains open for the broader graph and history corpus, native
Windows verification, and packaged desktop acceptance.

The [decision report](../reports/supported-project-persistence.md) records
the source boundaries, acceptance criteria and the earlier exchange proof.
Original engineering types, numerical tolerances and existing platform and
release gates govern each increment.
