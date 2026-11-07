# B008: original structural example diagnostics

Status: open; retained under D061. No numerical fix or gate closure.

Tasks 0105/0106 connect original shell/membrane/beam/truss workflows. Independent
checks reveal observations reproduced by the pinned original Windows CalculiX
2.22 on identical decks. Root causes are not established; this record does not
classify every observation as a solver defect rather than discretization,
constraints or original result semantics.

- Quadratic membrane prescribed-strain example: maximum displacement mismatch
  .000176919 and stress mismatch 1.458886; both strict diagnostics are false.
  The earlier free-load example has very large responses and remains separate.
- T3D3 axial example: maximum displacement error .0026859 against u=.001x;
  the other seven tested line forms meet that expectation. No cross-section
  scaling or alternate formulation is silently substituted.
- CIRC B32R beam: tip -.65153 versus Euler–Bernoulli -.6366197723675813;
  the rectangular case meets its -.25 solution. No tolerance is widened.
- Stored line-example RF1 resultant over printed source root/tip sets is -.045;
  stored shell-pressure root RF3 is .00009833334 versus continuum .0001.
  Original expanded-element force/result semantics require investigation before
  treating these quantities as physical whole-model resultants or normalizing them.
- Separate alias finding: T2D3 is retained in mesh/deck text, but both unchanged
  native and original Windows solvers explicitly report unknown element type.
  This adds no solver exception and closes no required function.

Evidence: [workflow and receipt](../reports/structural-elements-workflow.md),
`/tmp/prepomaxx-task0105-0106-evidence`, its original-Windows comparison and
`t2d3/verification.json`. All original inputs, failed checks and initial outputs
are retained. Proposed post-parity work: isolate topology/section expansion,
constraint mapping, shape integration and output averaging with independent
single-formulation and integration-point studies before changing engineering code.
