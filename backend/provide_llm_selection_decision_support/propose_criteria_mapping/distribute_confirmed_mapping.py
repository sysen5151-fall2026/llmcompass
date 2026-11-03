"""Implements F.1.1.4 -- Distribute Confirmed Mapping. Mechanism: C.1.1.4 Mapping Distributor."""

import copy
from typing import Optional

from .validate_proposed_criteria import OPERATORS, resolve_known_metrics, threshold_fits

DESIGNATIONS = frozenset({"hard", "weighted"})


def _check_criterion(criterion, known: frozenset) -> None:
    if not isinstance(criterion, dict):
        raise ValueError("each confirmed criterion must be an object")
    cid = criterion.get("criterion_id")
    if not isinstance(cid, str) or not cid:
        raise ValueError("confirmed criterion has no criterion_id")
    # CR 1.1.2 / CR 1.3.8 (SR 1.1.8): confirmed or hand-added criteria are checked against the known metrics list.
    if criterion.get("metric") not in known:
        raise ValueError(f"criterion {cid}: metric {criterion.get('metric')!r} is not on the known metrics list")
    if criterion.get("operator") not in OPERATORS:
        raise ValueError(f"criterion {cid}: operator {criterion.get('operator')!r} is not >=, <=, == or in")
    if not threshold_fits(criterion["operator"], criterion.get("threshold")):
        raise ValueError(f"criterion {cid}: threshold does not fit operator {criterion['operator']} (SPEC 3)")
    if criterion.get("designation") not in DESIGNATIONS:
        raise ValueError(f"criterion {cid}: designation must be hard or weighted")
    if criterion["designation"] == "weighted":
        weight = criterion.get("weight")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
            raise ValueError(f"criterion {cid}: a weighted criterion needs a non-negative numeric weight (A20)")


def distribute_confirmed_mapping(confirmed_criteria_mapping: list, requirement_set: list, *,
                                 known_metrics: Optional[frozenset[str]] = None) -> tuple[list, list, list, dict]:
    """operationId: distributeConfirmedMapping. F.1.1.4 -> F.1.2, F.1.3, F.1.4, F.1.5, F.1.7 (flows 5.1-5.4).

    in: confirmed_criteria_mapping, requirement_set. control: known_metrics.
    out: required_metrics, hard_constraints, weighted_criteria, decision_basis.
    raises: ValueError.
    """
    # CR 1.1.1 Accept Confirmed criteria mapping (SR 1.1.1): only what the Technical Lead confirmed.
    if not isinstance(confirmed_criteria_mapping, list):
        raise ValueError("confirmed criteria mapping must be a list")
    if not isinstance(requirement_set, list) or not requirement_set:
        raise ValueError("requirement set is empty (flow 1.0.1)")
    for r in requirement_set:
        if not (isinstance(r, dict) and isinstance(r.get("requirement_id"), str) and r["requirement_id"]
                and isinstance(r.get("text"), str) and r["text"]):
            raise ValueError("each requirement needs a non-empty requirement_id and text (flow 1.0.1)")

    # CR 2.1.2 Mapping consistency (SR 2.1.3): work on a private copy; no confirmed criterion is changed,
    # and every outflow gets its own copy so no receiver can alter what another one sees.
    mapping = copy.deepcopy(confirmed_criteria_mapping)
    known = resolve_known_metrics(known_metrics)
    for criterion in mapping:
        _check_criterion(criterion, known)
    ids = [c["criterion_id"] for c in mapping]
    if len(ids) != len(set(ids)):
        # Weights are keyed by criterion_id (A20); a repeated id would silently merge two criteria (CR 2.1.2).
        raise ValueError("confirmed criteria mapping repeats a criterion_id")

    # CR 1.4.4 Distribute Confirmed Mapping (SR 1.4.1.1): split by designation, mapping order kept.
    # CR 1.2.5 / CR 1.3.5 -> Evidence Retriever: every metric of a hard or weighted criterion, once (A25).
    required_metrics = list(dict.fromkeys(c["metric"] for c in mapping))
    # CR 1.2.2 / CR 1.3.4 -> Constraint Filter.
    hard_constraints = [copy.deepcopy(c) for c in mapping if c["designation"] == "hard"]
    # CR 1.2.6 / CR 1.3.3, CR 1.3.2 -> Ranking Engine and Sensitivity Analyzer: one list, the same weights.
    weighted_criteria = [copy.deepcopy(c) for c in mapping if c["designation"] == "weighted"]
    # CR 1.2.1 / CR 1.3.1 -> Decision Recorder: the requirement set, the confirmed mapping and its weights.
    decision_basis = {
        "requirements": [{"requirement_id": r["requirement_id"], "text": r["text"]} for r in requirement_set],
        "criteria_mapping": copy.deepcopy(mapping),
        "weights": {c["criterion_id"]: c["weight"] for c in weighted_criteria},
    }
    return required_metrics, hard_constraints, weighted_criteria, decision_basis
