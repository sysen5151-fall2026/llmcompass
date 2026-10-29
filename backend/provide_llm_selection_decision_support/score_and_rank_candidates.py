"""Implements F.1.4 -- Score and Rank Candidates. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.4 (SN-TL-04 / 5.1.3.1). IDEF0 A1 of F.1, 2026-10-26.
# Sits behind contracts/api-v1.yaml: scoreAndRankCandidates.

from .apply_hard_constraints import _meets
from .retrieve_model_data import _evidence_item, _figure_metrics, _metric_figure


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
    """Function: F.1.4 -- Score and Rank Candidates. Contract operation scoreAndRankCandidates.

    in: eligible_candidates (7.2). control: weighted_criteria (5.3). out: ranking (7.4).
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
        # A gap scores 0 and is reported, never filled in silently (SPEC section 2, missing values)
        missing = [c["metric"] for c in weighted_criteria if _metric_figure(cand, c["metric"]) is None]
        # SN-TL-02 / 5.1.2.1 -- every figure of the candidate travels with it to F.1.6 (contract A11; ADR-0003)
        evidence = [_evidence_item(mid, m, _metric_figure(cand, m)) for m in _figure_metrics(cand)]
        ranking.append({"model_id": mid, "score": sum(contributions.values()), "contributions": contributions,
                        "missing_data": missing, "evidence": evidence})

    ranking.sort(key=lambda e: (-e["score"], e["model_id"]))
    return ranking
