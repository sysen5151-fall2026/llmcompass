"""Implements F.1.1 -- Propose Criteria Mapping. Mechanism: C.1.1 Criteria Mapper.

One module per second-level function (SPEC.md section 7, Form report Table 3;
contracts/api-v1.yaml A28), generated in one pass (Lab Manual 9.4, docs/deviation-log.md):
  request_interpretation.py        F.1.1.1  C.1.1.1 Interpretation Client
  validate_proposed_criteria.py    F.1.1.2  C.1.1.2 Criteria Validator
  present_criteria_mapping.py      F.1.1.3  C.1.1.3 Mapping Presenter
  distribute_confirmed_mapping.py  F.1.1.4  C.1.1.4 Mapping Distributor
The first-level F.1.1 defs (Chapter 4-7: request_interpretation(text), present_criteria_mapping,
split_confirmed_mapping, compile_decision_basis, validate_interpretation) are in _first_level.py
and re-exported here unchanged, so F.1's boundary and the SR tests keep working.
"""

# Second-level modules first: importing a submodule sets the package attribute of the same name,
# so they are loaded before the first-level defs of the same names are bound below (A28).
from . import distribute_confirmed_mapping as _c114  # noqa: F401
from . import present_criteria_mapping as _c113
from . import request_interpretation as _c111
from . import validate_proposed_criteria as _c112

from ._first_level import (  # noqa: F401 -- first-level F.1.1 defs (F.1 boundary, SPEC section 4)
    CATEGORIES,
    DESIGNATIONS,
    KNOWN_METRICS,
    OPERATORS,
    PROXY_STRENGTHS,
    _decision,
    _require,
    compile_decision_basis,
    present_criteria_mapping,
    request_interpretation,
    split_confirmed_mapping,
    validate_criterion,
    validate_interpretation,
)


def propose_mapping(stated_requirements: str, *, known_metrics=None) -> tuple:
    """F.1.1 flows 1 -> 4: Request Interpretation, send, Validate Proposed Criteria, Present Criteria Mapping.

    in: stated_requirements. control: known_metrics (None = the configured list).
    out: presented_mapping (flow 4), requirement_set (flow 1.0.1, kept for F.1.1.4).
    The re-send after a retry status sits here, in C.1.1 (ADR-0006; A31, deviation log D-25).
    """
    # CR 1.4.1, CR 1.2.3 -- one interpretation request per stated requirement (flow 2)
    requests, requirement_set = _c111.request_interpretation(stated_requirements)
    validated = []
    for request in requests:
        # One-element requirement set: the response is checked against its own request (D-10, D-11).
        own = [r for r in requirement_set if r["requirement_id"] == request["requirement_id"]]
        # SPEC section 3 failure path: an invalid or missing response is re-sent once (SR 1.3.2, CR 1.4.2)
        for _attempt in range(2):
            result = _c112.validate_proposed_criteria(_c111.send_interpretation_request(request), own,
                                                      known_metrics=known_metrics)
            if result["status"] != "retry":
                break
        validated.append(result)
    # CR 1.4.3, CR 1.2.4 -- every stated requirement with its criteria and proxy-strength ratings (flow 4)
    return _c113.present_criteria_mapping(validated), requirement_set
