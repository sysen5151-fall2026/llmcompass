"""Implements F.1.1.2 -- Validate Proposed Criteria. Mechanism: C.1.1.2 Criteria Validator."""

import copy
import logging
from typing import Optional

_log = logging.getLogger(__name__)

OPERATORS = frozenset({">=", "<=", "==", "in"})
PROXY_STRENGTHS = frozenset({"strong", "moderate", "weak"})
CATEGORIES = frozenset({"capability", "cost", "compliance", "other"})
_RESPONSE_KEYS = frozenset({"requirement_id", "no_suitable_proxy", "criteria"})
_CRITERION_KEYS = ("criterion_id", "metric", "operator", "threshold", "unit", "proxy_strength", "category", "rationale")

# SPEC 3 failure path (A31): invalid responses seen per stated requirement since its last final result.
_failures: dict = {}


def configured_known_metrics() -> frozenset:
    """The configured Known metrics list: SPEC 2 candidate figure fields plus every known benchmark_id."""
    # CR 1.1.2 Accept Known metrics list (SR 1.1.8) / CR 1.3.8 (SR 1.3.3): the Benchmark Data
    # Sources' vocabulary as loaded with provide_benchmark_evidence; a list passed in replaces it.
    from provide_benchmark_evidence import BENCHMARK_IDS
    from provide_llm_selection_decision_support.retrieve_model_data import FIGURE_FIELDS
    return frozenset(FIGURE_FIELDS) | frozenset(BENCHMARK_IDS)


def resolve_known_metrics(known_metrics) -> frozenset:
    # known_metrics=None means the configured list (KnownMetricsList x-default).
    return configured_known_metrics() if known_metrics is None else frozenset(known_metrics)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def threshold_fits(operator, threshold) -> bool:
    """SPEC 3 rule: `in` takes a list; `>=` and `<=` a number or null; `==` a number, string or null."""
    if operator == "in":
        return isinstance(threshold, list)
    if operator in (">=", "<="):
        return threshold is None or _is_number(threshold)
    if operator == "==":
        return threshold is None or _is_number(threshold) or isinstance(threshold, str)
    return False


def _check_requirement_set(requirement_set) -> list:
    if not isinstance(requirement_set, list) or not requirement_set:
        raise ValueError("requirement set must be a non-empty list (flow 1.0.1)")
    for r in requirement_set:
        if not (isinstance(r, dict) and isinstance(r.get("requirement_id"), str) and r["requirement_id"]
                and isinstance(r.get("text"), str) and r["text"]):
            raise ValueError("each requirement needs a non-empty requirement_id and text (flow 1.0.1)")
    return requirement_set


def _criterion_problem(criterion, known: frozenset) -> Optional[str]:
    if not isinstance(criterion, dict):
        return "criterion is not an object"
    if set(criterion) != set(_CRITERION_KEYS):
        return f"criterion keys {sorted(criterion)} are not the SPEC 3 keys"
    if not isinstance(criterion["criterion_id"], str) or not criterion["criterion_id"]:
        return "criterion_id is not a non-empty string"
    if not isinstance(criterion["metric"], str) or criterion["metric"] not in known:
        return f"unknown metric {criterion['metric']!r}"  # CR 1.4.2: unknown criteria caught
    if not isinstance(criterion["operator"], str) or criterion["operator"] not in OPERATORS:  # D-14
        return f"unknown operator {criterion['operator']!r}"
    if not threshold_fits(criterion["operator"], criterion["threshold"]):
        return f"threshold {criterion['threshold']!r} does not fit operator {criterion['operator']}"
    if not isinstance(criterion["proxy_strength"], str) or criterion["proxy_strength"] not in PROXY_STRENGTHS:
        return f"proxy_strength {criterion['proxy_strength']!r} is not strong, moderate or weak"
    if not isinstance(criterion["category"], str) or criterion["category"] not in CATEGORIES:
        return f"category {criterion['category']!r} is not capability, cost, compliance or other"
    if not isinstance(criterion["unit"], str) or not isinstance(criterion["rationale"], str):
        return "unit and rationale must be strings"
    return None


def _response_problem(response, requirement_id: str, known: frozenset) -> Optional[str]:
    # CR 2.3.1 Model contract (SR 2.3.1) / CR 1.3.7: accept proposed criteria only in SPEC 3 form.
    if not isinstance(response, dict):
        return "no response, or not a JSON object"
    if set(response) != _RESPONSE_KEYS:
        return f"response keys {sorted(response)} are not the SPEC 3 keys"
    if response["requirement_id"] != requirement_id:
        return "requirement_id does not match a request in the requirement set"
    no_proxy, criteria = response["no_suitable_proxy"], response["criteria"]
    if not isinstance(no_proxy, bool) or not isinstance(criteria, list):
        return "no_suitable_proxy must be a boolean and criteria a list"
    # SPEC 3: either 1+ criteria, or no_suitable_proxy with no criteria -- never both, never neither.
    if no_proxy == bool(criteria):
        return "must have criteria or no_suitable_proxy, never both"
    for criterion in criteria:
        problem = _criterion_problem(criterion, known)
        if problem:
            return problem
    ids = [c["criterion_id"] for c in criteria]
    if len(ids) != len(set(ids)):
        return "duplicate criterion_id in one response"
    return None


def _attribute(proposed_criteria, requirement_set: list) -> dict:
    """The stated requirement a response answers (A31)."""
    rid = proposed_criteria.get("requirement_id") if isinstance(proposed_criteria, dict) else None
    for r in requirement_set:
        if r["requirement_id"] == rid:
            return r
    # A null or unattributable response: the requirement already awaiting its retry, else the first one.
    for r in requirement_set:
        if _failures.get((r["requirement_id"], r["text"])):
            return r
    return requirement_set[0]


def validate_proposed_criteria(proposed_criteria: Optional[dict], requirement_set: list, *,
                               known_metrics: Optional[frozenset[str]] = None) -> dict:
    """operationId: validateProposedCriteria. F.1.1.2 -> F.1.1.3 (flow 3.0.1).

    in: proposed_criteria, requirement_set. control: known_metrics. out: validated_criteria.
    """
    # CR 1.1.3 Accept Proposed criteria (SR 1.1.4): one runtime response, or None when there was none.
    # CR 1.1.2 Accept Known metrics list (SR 1.1.8): the list given, else the configured one.
    known = resolve_known_metrics(known_metrics)
    requirement = _attribute(proposed_criteria, _check_requirement_set(requirement_set))
    key = (requirement["requirement_id"], requirement["text"])

    # CR 1.4.2 Validate Proposed Criteria (SR 1.4.1.1): malformed or unknown criteria are caught.
    problem = _response_problem(proposed_criteria, requirement["requirement_id"], known)
    result = {"requirement_id": requirement["requirement_id"], "requirement": requirement["text"]}
    if problem is None:
        _failures.pop(key, None)
        criteria = []
        for c in proposed_criteria["criteria"]:
            checked = copy.deepcopy(c)
            checked["requirement_id"] = requirement["requirement_id"]  # SR 1.2.4: the requirement it stands for
            criteria.append(checked)
        return {**result, "status": "proposed", "no_suitable_proxy": proposed_criteria["no_suitable_proxy"],
                "criteria": criteria}

    # SPEC 3 failure path (SR 1.3.2, A31): retry once; the second failure is interpretation_failed and the
    # Technical Lead enters criteria by hand. The requirement is never dropped and no criteria are made up.
    failures = _failures.get(key, 0) + 1
    if failures >= 2:
        _failures.pop(key, None)
        status = "interpretation_failed"
    else:
        _failures[key] = failures
        status = "retry"
    _log.info("proposed criteria for %s invalid (%s): %s", key[0], problem, status)
    return {**result, "status": status, "no_suitable_proxy": False, "criteria": []}
