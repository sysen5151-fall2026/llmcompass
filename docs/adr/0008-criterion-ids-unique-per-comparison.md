# ADR-0008: Criterion ids are unique per comparison (requirement-qualified)

Status: Accepted for the Lab 10.4 measurement (2026-11-15, Khai). Needs team confirmation and
Innoslate item 24 (docs/deviation-log.md D-29).

Context:
- C.1.1.1 sends one interpretation request per stated requirement (CR 1.4.1). The SPEC 3 prompt asks
  for a criterion_id "unique within this response", so each reply numbers its criteria from 1.
- C.1.1.4 rejects a confirmed mapping that repeats a criterion_id (D-13), because weights are keyed
  by criterion_id (A20) and a repeat would merge two criteria (CR 2.1.2).
- So any comparison with two or more requirements that each got a criterion failed at Confirm with
  HTTP 422 unless the Technical Lead removed duplicates. Found by the Lab 10.4 instrumented smoke run
  (5 requirement lines: REQ-1, REQ-3 and REQ-4 all returned `CRI-1`). The demo and UI tests used
  one line or distinct ids, so they never hit it.

Decision:
- The F.1.1 composition `propose_mapping` prefixes each proposed criterion_id with its
  requirement_id (`REQ-3:CRI-1`) before C.1.1.3 presents the mapping. It is the place where the
  separate replies are combined (it already owns the re-send, ADR-0006).
- Not in C.1.1.3: CR 1.2.4 requires the presenter to show the proposed criteria unchanged.
- Not in the prompt: the model cannot see the other requests' ids, and C.1.1.2 could only reject.

Consequences:
- Ids in the review page, decision record and weights now read `<requirement_id>:<id>`; still
  deterministic for the same text and replies (SR 2.1.3). Schemas unchanged (contract note A33).
- Hand-added criteria keep their `manual-<k>` ids, which cannot collide with the prefixed ones.
- Regression test: tests/test_component_criteria_mapper_reconcile.py
  `test_propose_mapping_criterion_ids_unique_across_requirements`.
