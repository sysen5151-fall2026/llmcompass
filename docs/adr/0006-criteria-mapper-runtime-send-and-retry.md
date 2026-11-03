# ADR-0006: C.1.1.1 sends interpretation requests; F.1.1 owns the re-send

Status: Proposed (Lab 9.4 reconcile, 2026-11-03). Needs team confirmation and the Innoslate
entries in docs/deviation-log.md ("To add in Innoslate", items 5, 7, 8).

Context: SPEC 7 says C.1.1.1 Interpretation Client "assigns an identifier to each stated
requirement and sends it to the language model runtime" and is the only component that calls
the runtime. The contract (v1.1.0) gives requestInterpretation only the request and requirement
set as outputs, so no operation sends flow 2, and A31 leaves open which element re-sends after a
`retry` status. The one-pass generation added `send_interpretation_request` to
`request_interpretation.py` (deviation log D-05, D-25).

Decision:
- Keep `send_interpretation_request(interpretation_request) -> Optional[dict]` in the C.1.1.1
  module as the single call site of the F.8 adapter. It is not a contract operation, because flow
  2 and flow 3 cross the system boundary to C.8, which SPEC 3 already specifies; the internal
  contract covers exchanges between F.1.x functions.
- The re-send lives in the F.1.1 composition `propose_mapping` (package `__init__.py`): each
  request is validated against a one-element requirement set (its own request, D-10/D-11), and is
  re-sent once on `retry`, so a comparison never leaves a pending retry count behind (D-09).

Consequences: check_conformance does not check `send_interpretation_request` or
`propose_mapping`; tests do, through a fake runtime on 127.0.0.1
(tests/test_component_criteria_mapper_reconcile.py). If the team
promotes items 5 and 7, the contract can add a sendInterpretationRequest operation in v1.2.
