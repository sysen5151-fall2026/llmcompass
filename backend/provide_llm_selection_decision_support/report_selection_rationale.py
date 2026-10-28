"""Implements F.1.6 -- Report Selection Rationale. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.6 (SN-TL-02 / 5.1.2.1, SN-TL-04 / 5.1.3.1, SN-TL-05 / 5.1.4.1, SN-TL-07 / 5.1.6.3).
# IDEF0 A1 of F.1, 2026-10-26.


def report_selection_rationale(ranking: list, exclusions: list, sensitivity_finding: dict) -> tuple:
    """Function: F.1.6 -- Report Selection Rationale.

    in: ranking, exclusions, sensitivity_finding. out: presented_ranking_and_sensitivity, selection_rationale.
    """
    order = [e["model_id"] for e in ranking]
    # SN-TL-07 / 5.1.6.3 -- every excluded candidate with the constraints it failed
    excluded = [{"model_id": e["model_id"], "failed_constraints": e["failed_constraints"]} for e in exclusions]
    # SN-TL-04 / 5.1.3.1 -- one contribution per weighted criterion. Gaps are shown,
    # never filled in silently (SPEC section 2, missing values).
    score_breakdown = [{"model_id": e["model_id"], "score": e["score"], "contributions": e["contributions"],
                        "gaps": e["gaps"]} for e in ranking]
    # SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2 -- every figure used, ranked and excluded, once each, with
    # source, date and stale flag (stale stored figures are still used)
    evidence, shown = [], set()
    for e in ranking + exclusions:
        for f in e["evidence"]:
            if (e["model_id"], f["metric"]) not in shown:
                shown.add((e["model_id"], f["metric"]))
                evidence.append({"model_id": e["model_id"], "metric": f["metric"], "value": f["value"],
                                 "unit": f["unit"], "source_id": f["source_id"],
                                 "collection_date": f["collection_date"], "stale": f["stale"]})
    unstable = sensitivity_finding["unstable_pairs"]  # SN-TL-05 / 5.1.4.1

    presented = {"ranking": order, "excluded": excluded, "score_breakdown": score_breakdown,
                 "unstable_pairs": unstable, "evidence": evidence}
    # SR 1.4.1.6 -- the rationale carries the same ranking, exclusions, evidence and sensitivity finding to F.1.7
    selection_rationale = {
        "ranking": order,
        "excluded": excluded,
        "evidence": evidence,
        "unstable_pairs": unstable,
        "sensitivity": {
            "method": sensitivity_finding["method"],
            "ranking_is_stable": not unstable if order else None,  # None = nothing ranked
            "unstable_pairs": unstable,
        },
    }
    return presented, selection_rationale
