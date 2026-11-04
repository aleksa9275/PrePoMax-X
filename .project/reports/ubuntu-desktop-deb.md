# Ubuntu desktop installer preview

Task 0051 wraps the existing native Linux preview archive as
`prepomaxx-preview` for Ubuntu 24.04 ARM64 and x64. It verifies the archive
digest and every payload file and link before assembly. APT manages the
runtime dependencies and the files under `/usr`. The desktop entry calls
`/usr/bin/prepomaxx-preview` and passes a selected file to the original app.
The package includes no maintainer scripts. Its internal version comes from
the archive build timestamp and source commit. [Build, install and remove](../../X/Build/README.md#ubuntu-2404-installer-preview).

## ARM64 verification

The retained installer is
`X/Build/artifacts/task0051-arm64-deb/prepomaxx-preview_0.0.0~preview+20261104162309.gitb55882eca795_arm64.deb`.
It is 415,485,218 bytes and has SHA-256
`03861c3db16530ff355da09268e9fcb4c6ba1c5164d3967aef84842dc78eb52b`.
It wraps the exact task 0050 ARM64 archive from `b55882ec`.

In a fresh native-architecture Ubuntu 24.04.5 ARM64 container, APT installed
the local package with its declared dependencies. The verification tools
were Python, Xvfb and desktop-file-utils. The environment had no external
.NET SDK, CalculiX or GCC on PATH. The menu entry passed
`desktop-file-validate`. The ordinary user ran the installed command from a
home path containing spaces under Xvfb and Mesa. All 2,149 payload file
hashes and 244 symlink targets matched the task 0050 manifest.

- The installed INP workflow passed 11 desktop and seven analytical checks.
  The solver wrote its results to the user's Qt XDG data directory.
- The installed PMX workflow passed all 17 checks. Saved PMX and deck bytes
  matched task 0049, and all decoded results matched its official-export solve.
- APT removal deleted the package files and preserved all 76 checked files
  in the test user's home, including a project and completed job results.
  Reinstall restored the package with the same user files. Purging that
  installation removed its files and package state and preserved the same
  user files byte for byte.
- Altered archive and installer bytes were rejected before assembly or
  APT installation. Nine shared build boundary checks passed.

The initial lifecycle attempt tried to purge an already removed local-only
package. APT had discarded its state because it had no configuration files.
The verifier now reinstalls between the independent remove and purge checks.
The failed attempt, final logs, screenshot and job outputs are retained.
The test containers were disposable. The current Mac DMG, ARM64 archive and
one ARM64 installer remain available.
[Verification receipt](ubuntu-desktop-deb-verification.json).

## Publication and remaining scope

Implementation `559cb506` was pushed and verified on
`origin/research/native-feasibility`. All six automatic jobs passed in
[Pipeline #3028114125](https://gitlab.com/aleksa9275/pre-po-max-x/-/pipelines/3028114125)
and historical compatibility stayed manual. The
[native x64 job](https://gitlab.com/aleksa9275/pre-po-max-x/-/jobs/17743502888)
passed the archive probe, built the .deb, and verified APT install,
ordinary-user INP solve/render, remove, reinstall and purge. The installer
hash matched its build report. The installed PMX fixture was exercised on
ARM64. CI uploaded the logs and receipts. The binary installer is retained
locally for ARM64.

Task 0052 subsequently removed the local installer. Its checksum,
verification and rebuild archive remain available.
[Cleanup receipt](l-bracket-cad-reference/verification.json).

This covers Ubuntu 24.04 under X11 software rendering in a virtual display.
Debian, Fedora, Arch, physical desktop acceptance, version-to-version
upgrade and public release packaging remain open. Full 3.0.0 parity still
requires broader PMX, analyses, results and CAD/meshing, plus the two
correctness fixes and tetrahedron gate.

The next Mac parity increment can use the tracked `L_bracket_r.step` and its
upstream geometry metadata checks to capture an original 3.0.0 reference
before attempting native import. The signed-in GitLab session again returned
404 for the documented patched Gmsh branch on 4 November. Matching source
access remains open. [Geometry fixture and checks](../../APIs/Python/Test_Scripts/Test_Model_Geometry_Metadata.py) ·
[Prior native CAD audit](native-feasibility.md) ·
[Documented Gmsh branch](https://gitlab.com/MatejB/gmsh/-/tree/prepomax-quadqs-transfinite).
