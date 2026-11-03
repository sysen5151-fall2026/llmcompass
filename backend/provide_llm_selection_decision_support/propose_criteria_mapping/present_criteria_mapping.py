"""Implements F.1.1.3 -- Present Criteria Mapping. Mechanism: C.1.1.3 Mapping Presenter."""

import copy


def present_criteria_mapping(validated_criteria: list) -> dict:
    """operationId: presentCriteriaMapping. F.1.1.3 -> Technical Lead (flow 4).

    in: validated_criteria. control: -. out: presented_mapping.
    """
    if not isinstance(validated_criteria, list) or not validated_criteria:
        raise ValueError("validated criteria must be a non-empty list (flow 3.0.1)")
    # CR 1.4.3 Present Criteria Mapping / CR 1.2.4 Provide Presented mapping (SR 1.4.1.1, SR 1.2.4) and
    # CR 1.3.6 (SR 1.3.1): every stated requirement once, with its status, no-proxy result and each
    # criterion's proxy-strength rating, in the order each requirement first appears in the
    # validated criteria. When a requirement was validated more than once (retry), its latest result is shown.
    latest = {}
    for entry in validated_criteria:
        if not isinstance(entry, dict) or not entry.get("requirement_id"):  # D-17: contract 422
            raise ValueError("each validated criteria entry needs a requirement_id (flow 3.0.1)")
        latest[entry["requirement_id"]] = entry
    return {"requirements": [copy.deepcopy(entry) for entry in latest.values()]}
