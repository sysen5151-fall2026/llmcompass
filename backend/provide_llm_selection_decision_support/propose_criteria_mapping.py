"""Implements F.1.1 -- Propose Criteria Mapping. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.1 (SN-TL-01 / 5.1.1.2, 5.1.1.3, SN-TL-07 / 5.1.6.1). IDEF0 A1 of F.1, 2026-10-26.

import uuid

from provide_benchmark_evidence import BENCHMARK_IDS

from .retrieve_model_data import FIGURE_FIELDS

# SR 1.1.4, SR 1.3.2 (SPEC section 3) -- the model contract's vocabulary.
# With the catalog's benchmark ids (F.7's published vocabulary, SPEC 5 Q7), F.1.2's
# FIGURE_FIELDS are the known metrics of SPEC section 3.
KNOWN_METRICS = frozenset(FIGURE_FIELDS) | frozenset(BENCHMARK_IDS)
OPERATORS = (">=", "<=", "==", "in")  # SR 1.1.4, SR 1.3.2 (SPEC section 3)
PROXY_STRENGTHS = ("strong", "moderate", "weak")  # SR 1.1.4, SN-TL-01 / 5.1.1.3 (scale is SPEC 5 Q4)
CATEGORIES = ("capability", "cost", "compliance", "other")  # SR 1.1.4, SR 1.3.2 (SPEC section 3)
DESIGNATIONS = ("hard", "weighted")  # SN-TL-07 / 5.1.6.1


# SR 1.2.2 -- the decision in progress, held by mechanism C.1 (docs/PLAN.md "Interface
# details the tests rely on"), so the record is built from what was actually ranked.
# request_interpretation starts a new one, so it lives here; F.1's boundary defs share it.
_decision = {}


def _require(key: str, step: str) -> None:
    # UC.1 order: a step that needs an earlier one's result says which step is missing.
    if key not in _decision:
        raise RuntimeError(f"{step} has not been called for this decision.")


def _threshold_fits(operator: str, threshold) -> bool:
    # SR 1.1.4, SR 1.3.2 (SPEC section 3) -- the threshold type each operator can compare against
    if operator == "in":
        return isinstance(threshold, list)
    if operator in (">=", "<="):
        return threshold is None or (isinstance(threshold, (int, float)) and not isinstance(threshold, bool))
    return threshold is None or (isinstance(threshold, (int, float, str)) and not isinstance(threshold, bool))


def validate_interpretation(response, *, known_metrics: frozenset = KNOWN_METRICS) -> bool:
    # SR 1.1.4, SR 1.3.2 (SN-TL-01 / 5.1.1.2, 5.1.1.3) -- the SPEC section 3 response schema.
    # known_metrics is the F.1 control "Known metrics list" (IDEF0, 2026-10-26).
    if not isinstance(response, dict):
        return False
    criteria, no_proxy = response.get("criteria"), response.get("no_suitable_proxy")
    if not (isinstance(response.get("requirement_id"), str) and response["requirement_id"]):
        return False
    if not isinstance(no_proxy, bool) or not isinstance(criteria, list):
        return False
    if bool(criteria) == no_proxy:  # 1+ criteria, or no_suitable_proxy with none -- not both, not neither
        return False
    for c in criteria:
        if not isinstance(c, dict):
            return False
        if not (isinstance(c.get("criterion_id"), str) and c["criterion_id"]):
            return False
        if c.get("metric") not in known_metrics or c.get("operator") not in OPERATORS:
            return False
        if "threshold" not in c or not isinstance(c["threshold"], (int, float, str, list, type(None))):
            return False
        if not _threshold_fits(c["operator"], c["threshold"]):
            return False
        if not isinstance(c.get("unit"), str) or not isinstance(c.get("rationale"), str):
            return False
        if c.get("proxy_strength") not in PROXY_STRENGTHS or c.get("category") not in CATEGORIES:
            return False
    return True


def validate_criterion(criterion: dict) -> None:
    # SR 1.1.1 (SN-TL-07 / 5.1.6.1) -- hard or weighted, and a weighted criterion needs a weight
    if criterion.get("designation") not in DESIGNATIONS:
        raise ValueError(f"{criterion.get('criterion_id')}: designation must be hard or weighted.")
    weight = criterion.get("weight")
    if criterion["designation"] == "weighted" and (isinstance(weight, bool) or not isinstance(weight, (int, float))):
        raise ValueError(f"{criterion.get('criterion_id')}: a weighted criterion needs a numeric weight.")


def request_interpretation(stated_requirements: str) -> dict:
    """Function: F.1.1 -- Propose Criteria Mapping (F.1 boundary output). Signature from Chapter 4.

    in: stated_requirements. out: interpretation_request.
    """
    # UC.1.2-1.3 (SR 1.1.5, SN-TL-01 / 5.1.1.1; SR 1.2.3, SN-TL-01 / 5.1.1.2) -- one
    # SPEC section 3 request per stated requirement, with its own ID and the text unaltered
    if not isinstance(stated_requirements, str):
        raise ValueError("Requirements must be text.")
    if not stated_requirements.strip():
        raise ValueError("Requirements text is empty.")
    requirement_id = f"REQ-{uuid.uuid4().hex}"
    _decision.clear()
    _decision.update({"requirement_id": requirement_id, "text": stated_requirements, "invalid_responses": {}})
    return {"requirement_id": requirement_id, "text": stated_requirements}


def present_criteria_mapping(proposed_criteria: dict, *, known_metrics: frozenset = KNOWN_METRICS) -> dict:
    """Function: F.1.1 -- Propose Criteria Mapping (F.1 boundary output). Signature from Chapter 4.

    in: proposed_criteria. control: known_metrics. out: presented_mapping.
    """
    # UC.1.4-1.6 (SR 1.1.4, SR 1.2.4, SR 1.3.2, SN-TL-01 / 5.1.1.2, 5.1.1.3)
    _require("requirement_id", "request_interpretation")
    requirement_id, text = _decision["requirement_id"], _decision["text"]
    presented = {"requirement_id": requirement_id, "requirement": text}
    attempts = _decision["invalid_responses"]
    # None = no response or a timeout, handled like an invalid response (SR 1.3.2).
    # SR 1.3.2 -- a response must answer the request it was sent for (same requirement_id).
    if not (validate_interpretation(proposed_criteria, known_metrics=known_metrics)
            and proposed_criteria["requirement_id"] == requirement_id):
        attempts[requirement_id] = attempts.get(requirement_id, 0) + 1
        # First invalid response: the caller re-sends the request. Second: the
        # requirement is kept for the Technical Lead to map by hand (SPEC section 3).
        status = "retry" if attempts[requirement_id] == 1 else "interpretation_failed"
        return {**presented, "status": status, "no_suitable_proxy": False, "criteria": []}
    attempts.pop(requirement_id, None)  # SR 1.1.4 -- a later invalid response gets its retry again
    # SR 1.2.4 -- every criterion shows the requirement it stands for and its proxy_strength
    criteria = [{**c, "requirement": text} for c in proposed_criteria["criteria"]]
    return {**presented, "status": "proposed", "no_suitable_proxy": proposed_criteria["no_suitable_proxy"],
            "criteria": criteria}


def split_confirmed_mapping(confirmed_criteria_mapping: list, *, known_metrics: frozenset = KNOWN_METRICS) -> tuple:
    """Function: F.1.1 -- Propose Criteria Mapping.

    in: confirmed_criteria_mapping. control: known_metrics. out: weighted_criteria, hard_constraints, required_metrics.
    """
    # SR 1.4.1.1 (SN-TL-07 / 5.1.6.1) -- a weighted criterion without a weight is rejected (validate_criterion),
    # and so is a metric off the known metrics list (derived from that control on F.1.1; kept 2026-10-28)
    for c in confirmed_criteria_mapping:
        validate_criterion(c)
        if c.get("metric") not in known_metrics:
            raise ValueError(f"{c.get('criterion_id')}: {c.get('metric')!r} is not a known metric.")
    weighted = [c for c in confirmed_criteria_mapping if c["designation"] == "weighted"]  # to F.1.4, F.1.5
    hard = [c for c in confirmed_criteria_mapping if c["designation"] == "hard"]  # to F.1.3
    required_metrics = list(dict.fromkeys(c["metric"] for c in confirmed_criteria_mapping))  # to F.1.2, each once
    return weighted, hard, required_metrics
