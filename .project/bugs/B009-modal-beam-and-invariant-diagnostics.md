# B009 — modal beam and signed principal-invariant diagnostics

Status: open findings; numerical investigation deferred under D061. No new solver
exception, numerical fix, tolerance relaxation or final acceptance is declared.

The tasks 0107–0110 rectangular B32R beam with a stored frequency basis followed
by modal transient point loading crashes on native Mac/Linux ARM64 (exit 139).
The pinned original Windows CalculiX 2.22 under CrossOver also crashes on the
same model (initial exit 5). Original DWARF symbols place the supplied Windows
null-write report in `nonlinmpc_ + 4360`, called by `dyna + 44680`.

The original source warns that loaded 1D/2D DOFs must appear as zero point loads
in the preceding frequency step. That requirement is now emitted through the
original user-keyword route, since CalCLoad omits zero components. Both native
ARM64 runs still fail. The final Windows zero-load deck enters the Wine crash
debugger and times out after 120 s; its partial DAT/FRD/EIG files are retained.
The initial Default/TwoD failures, final native failures, user-supplied report and
symbol lookup remain in `/tmp/prepomaxx-task0107-0110-evidence`. Root cause remains
unresolved; reference-under-CrossOver is not native Windows acceptance. The
example stays an explicitly labelled diagnostic, and failed jobs preserve model
and frozen inputs. Implicit beam transient and other connected modal-solid
workflows remain independently tested.

A separate identical-deck original Windows comparison of implicit beam transient
has one strict field mismatch at t=.45, node 32: SGN_MAX_ABS_PRI is +1.5048901e-6
on Mac and -1.5048901e-6 on the original Windows solver. The original raw S13 is
1.50489e-6 in both; normal stresses differ only around 1e-13. Principal max/min
have equal magnitude to stored precision, and Mises/Tresca match. The sign-tie
interpretation is an inference from those values, not a proven general defect.
The 3.0097802e-6 difference fails the unchanged 1e-6 absolute/relative bound and
remains explicitly false. Do not normalize the sign or alter original field math
to turn this comparison green. Mac/Linux ARM64 meet existing bounds.

The original one-DOF ARPACK case also prints *ERROR while exiting zero and leaving
nonempty output headers. This transport/completion issue is repaired in the job
runner by retaining explicit solver errors as failure; its real-process test
passes. It does not correct ARPACK or declare the failed eigenproblem valid.

See [workflow and receipt](../reports/element-family-completion.md). Preserve all
D029/B006/B007/B008, thermal/axisymmetric findings and D057–D061 obligations.
