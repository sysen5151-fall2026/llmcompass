# ADR-0004: Sensitivity Finding and Boundary Shapes Follow the Contract

Status: Accepted (2026-10-28)

Context: the remaining divergences between contracts/api-v1.yaml and the code were
smaller than those in ADR-0002 and ADR-0003, but each one changed what crosses a
boundary (contracts/check_conformance.py, before the refactor):
- 7.5 Sensitivity finding had no `ranking_is_stable` or `factors`. Its pairs came in
  the order they were found.
- The presented ranking and sensitivity had no `sensitivity` section. Its
  per-candidate scores had `gaps` where the contract says `missing_data`.
- F.1.2 returned an empty list when there was no model data at all.
- F.1.1's split defaulted its known-metrics control to the list itself, where the
  contract's generated stub has `known_metrics=None`.

Decision: the code conforms to the contract.
- 7.5 carries `method`, `factors`, `ranking_is_stable` and `unstable_pairs`.
  `ranking_is_stable` is a boolean, and is true when nothing is ranked (the record
  used to hold None for that case). Each pair is [higher, lower], listed in ranking
  order (A9).
- F.1.6's presented output and its 8.1 Selection rationale both carry
  `score_breakdown` (with `missing_data`) and `sensitivity`, the finding itself.
- `receiveModelData` raises LookupError "no model data available" when nothing is
  stored at all (SPEC section 2, A18).
- `known_metrics=None` means KNOWN_METRICS. The contract now says so in
  KnownMetricsList (`x-default: null`).
- F.1.7 rejects an empty requirements, mapping or weights section with ValueError
  (SR 1.2.2, contract 422). It always records `excluded`, an empty list when there
  are none (5.1.6.3), and records `score_breakdown` when the rationale has it.

Two corrections were made to the contract itself, not the code:
- The presented scores key was first drafted as `scores`. It is `score_breakdown`,
  because the SR 1.2.5 acceptance test, which is derived from SPEC, reads that name
  (A26).
- F.1.2's input is named `model_data_with_provenance`, after the IDEF0 arrow. The
  code already used that name.

Consequences:
- `rank()` (SPEC section 4) now flags staleness on every figure of every candidate,
  not only the criteria's figures, because F.1.4 carries every figure (ADR-0003).
- A decision record's ranking and evidence may be empty when every candidate is
  excluded (UC.1 alternate flow 10a, A27). Its requirements, mapping and weights may
  not be.
- The web path (`backend/app.py`) still runs the walking-skeleton helpers and never
  calls `receiveModelData`. When the UI moves to the F.1 ICOM defs (SR 1.3.1), it
  must catch that LookupError and show "no model data available" (SPEC section 2).

What would change this decision: a revised SR 1.4.1.7 test, or a team decision on
SPEC section 5 Q9 (do stale figures count?), would mean a contract v2 for F.1.7 or 7.1.

Model entities affected: F.1.1 (Known metrics list control), F.1.2 Retrieve Model
Data, F.1.5 Analyze Ranking Sensitivity, F.1.6 Report Selection Rationale, F.1.7
Generate and Store Decision Record; flows 7.5 Sensitivity finding and 8.1 Selection
rationale; boundary outputs Presented ranking and sensitivity and Decision record;
SR 1.2.2, SR 1.2.5, SR 1.4.1.5, SR 1.4.1.6, SR 1.4.1.7.
