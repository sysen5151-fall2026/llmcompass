"""Implements F.1.3 -- Apply Hard Constraints. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.3 (SN-TL-07 / 5.1.6.2, 5.1.6.3). IDEF0 A1 of F.1, 2026-10-26.

from .retrieve_model_data import _metric_figure


def _meets(value, operator: str, threshold) -> bool:
    if operator == ">=":
        return value >= threshold
    if operator == "<=":
        return value <= threshold
    if operator == "==":
        return value == threshold
    if operator == "in":
        values = value if isinstance(value, list) else [value]
        return bool(values) and all(v in threshold for v in values)
    raise ValueError(f"unknown operator: {operator}")


def apply_hard_constraints(candidate_evidence: list, *, hard_constraints: list) -> tuple:
    """Function: F.1.3 -- Apply Hard Constraints.

    in: candidate_evidence. control: hard_constraints. out: eligible_candidates, exclusions.
    """
    # SR 1.4.1.3 (SN-TL-07 / 5.1.6.2) -- a candidate failing any hard constraint is not eligible,
    # however well it would score
    eligible, exclusions = [], []
    for cand in candidate_evidence:
        failed, evidence = [], []
        for c in hard_constraints:
            fig = _metric_figure(cand, c["metric"])
            if fig is None:
                failed.append(f"missing_data:{c['metric']}")  # SPEC section 2, missing values
                continue
            evidence.append({**fig, "metric": c["metric"]})  # keeps F.1.2's stale flag
            if not _meets(fig["value"], c["operator"], c["threshold"]):
                failed.append(c["criterion_id"])
        if failed:
            # SN-TL-07 / 5.1.6.3 -- each exclusion names the constraints it failed
            exclusions.append({"model_id": cand["model_id"], "failed_constraints": failed, "evidence": evidence})
        else:
            eligible.append({**cand, "evidence": evidence})  # F.1.4 reports these with its own
    return eligible, exclusions
