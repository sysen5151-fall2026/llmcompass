"""Implements F.1.4 -- Score and Rank Candidates. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.4 (SN-TL-04 / 5.1.3.1). IDEF0 A1 of F.1, 2026-10-26.

from .apply_hard_constraints import _meets
from .retrieve_model_data import _metric_figure


def _normalized(values: dict, operator: str, threshold) -> dict:
    # Min-max across the eligible candidates. Missing (None) scores 0.
    present = {k: v for k, v in values.items() if v is not None}
    if operator in ("==", "in"):
        return {k: float(_meets(v, operator, threshold)) if v is not None else 0.0 for k, v in values.items()}
    lo, hi = (min(present.values()), max(present.values())) if present else (0, 0)
    out = {}
    for k, v in values.items():
        if v is None:
            out[k] = 0.0
        elif hi == lo:
            out[k] = 1.0
        elif operator == "<=":
            out[k] = (hi - v) / (hi - lo)
        else:
            out[k] = (v - lo) / (hi - lo)
    return out


def score_and_rank_candidates(eligible_candidates: list, *, weighted_criteria: list) -> list:
    """Function: F.1.4 -- Score and Rank Candidates.

    in: eligible_candidates. control: weighted_criteria. out: ranking.
    """
    norm = {}
    for c in weighted_criteria:
        values = {}
        for cand in eligible_candidates:
            fig = _metric_figure(cand, c["metric"])
            values[cand["model_id"]] = fig["value"] if fig is not None else None
        norm[c["criterion_id"]] = _normalized(values, c["operator"], c.get("threshold"))

    ranking = []
    for cand in eligible_candidates:
        mid = cand["model_id"]
        # SR 1.4.1.4 (SN-TL-04 / 5.1.3.1) -- one contribution per weighted criterion; the score is their sum
        contributions = {c["criterion_id"]: c["weight"] * norm[c["criterion_id"]][mid] for c in weighted_criteria}
        # SN-TL-02 / 5.1.2.1 -- the figures it was judged on: F.1.3's hard-constraint evidence, then these.
        # A gap scores 0 and is reported, never filled in silently (SPEC section 2, missing values).
        evidence, gaps = list(cand.get("evidence", [])), []
        for c in weighted_criteria:
            fig = _metric_figure(cand, c["metric"])
            if fig is None:
                gaps.append(c["metric"])
            else:
                evidence.append({**fig, "metric": c["metric"]})
        ranking.append({"model_id": mid, "score": sum(contributions.values()), "contributions": contributions,
                        # F.1.5 re-scores from these (docs/PLAN.md "F.1 decomposition")
                        "normalized": {cid: norm[cid][mid] for cid in norm},
                        "evidence": evidence, "gaps": gaps})

    ranking.sort(key=lambda e: (-e["score"], e["model_id"]))
    return ranking
