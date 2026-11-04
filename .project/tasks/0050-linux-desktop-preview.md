# Task 0050 — Native Linux desktop preview archive

Add a shared Linux desktop package adapter for ARM64 and x64. Use the
existing Qt/VTK frame bridge, self-contained C# hosts and a verified native
CalculiX 2.22/SPOOLES build. Keep PMX opt-in and reuse the checked task 0049
workflow. Build on Ubuntu 24.04 with pinned architecture-specific wheels.

Verify the extracted archive from a path with spaces, outside the build
environment where available. Exercise the existing native INP solve and
render/ID checks; on the retained static PMX fixture also compare the edit,
deck and original-reader results with the task 0049 reference.

This is an internal archive. Debian/Fedora/Arch packages and distro floors,
general PMX, full 3.0.0 parity, both correctness failures and the tetrahedron
gate, platform release tests and signing all remain open.
