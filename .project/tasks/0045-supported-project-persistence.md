# Task 0045 — Supported project save/reopen boundary (next; not started)

Prepared 3 November 2026 after task 0044. The first editor holds a supported
static-solid definition in memory and retains submitted run inputs. Those job
snapshots do not constitute project persistence or original PMX compatibility.

First prepare a concrete, reviewable persistence design for the supported state:
original mesh/IDs/sets/units/material/section/support/load/step definitions and
their result/source links. Revisit the retained original PMX/PMH type, history,
clone and Windows-reference evidence. Compare an original-compatible boundary
against an explicit versioned supported-slice exchange container. Establish what
can round-trip, how unsupported content is detected/preserved/rejected, and how
future upstream 3.0.0 fields/history can evolve without silent data loss.

The default format/compatibility policy remains an explicit maintainer decision.
Do not silently relabel the current analysis JSON as PMX, enable unsafe legacy
serialization, replace the original model graph or claim full PMX reconstruction
from record inventories. Prepare the proof/contract and tradeoff before proposing
that decision; independent adapter/fixture work can proceed within accepted scope.

After the persistence decision, implement save/close/reopen for the declared
slice, safe path/overwrite/version handling, and a packaged edit → save/reopen →
solve comparison. Preserve original identities/units/engineering ownership and
the existing source/precision/frontend/backend/correctness/four-target gates.
