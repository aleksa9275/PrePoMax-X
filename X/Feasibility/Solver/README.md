# Synthetic analytical solver reference

Task 0012: supplementary execution of the exact Windows solver bundled with
official PrePoMax 2.6.0, through the existing isolated CrossOver bottle. No
solver substitution, production changes, private model or native Mac claim.

`uniaxial-cube.inp` is an independently specified 1 mm cube, one C3D8, E=210000
MPa, nu=0.3, total tensile load 100 N distributed over four x=1 nodes. Symmetry
constraints on x=0/y=0/z=0 remove rigid modes while admitting uniform uniaxial
strain. Expected ux=100/210000*x, uy=-0.3*100/210000*y, uz=-0.3*100/210000*z,
stress xx=100 MPa, other stresses zero, supported-x reaction=-100 N.

```sh
python3 X/Feasibility/Solver/run-reference.py --solver /path/to/Solver/ccx_dynamic.exe --wine /Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine --bottle PrePoMax-X-reference-2.6 --output-dir /path/to/synthetic-results
```

Runs in a disposable directory, single-threaded OMP/MKL. Seven analytical checks
use tolerances appropriate to printed DAT precision (displacement 1e-9 mm,
axial stress 1e-4 MPa, transverse/shear/reaction 1e-5 in their units). Altered
displacement is a negative control. Records solver/dependency/input/output hashes
and actual reported version. Only synthetic DAT/FRD/STA/CVG are retained.
The DAT parser is specific to this fixture's requested output, not a general
production results parser. Native Linux/Mac solves, production FRD reading,
repeated-run tolerances and nonlinear/contact cases remain open.

Task 0011 adds a native Windows x64 repetition using exactly the same solver,
runtime DLLs, fixture and analytical checker:

```powershell
python X/Feasibility/Solver/run-native.py --solver 'C:\reference\Solver\ccx_dynamic.exe' --output-dir 'C:\capture\new-native-results'
```

The output directory must not already exist. The runner refuses a different
solver/runtime/fixture hash, retains the real exit status, repeats all seven
checks and the negative control, and compares DAT IDs and numerical values
with the CrossOver reference. See `.project/reports/windows-reference-validation.md`
for the observed Windows results and limits.
