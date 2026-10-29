"""Implements F.1.6 -- Report Selection Rationale. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.6 (SN-TL-02 / 5.1.2.1, SN-TL-04 / 5.1.3.1, SN-TL-05 / 5.1.4.1, SN-TL-07 / 5.1.6.3).
# IDEF0 A1 of F.1, 2026-10-26. Sits behind contracts/api-v1.yaml: reportSelectionRationale.


def report_selection_rationale(ranking: list, exclusions: list, sensitivity_finding: dict) -> tuple:
    """Function: F.1.6 -- Report Selection Rationale. Contract operation reportSelectionRationale.

    in: ranking (7.4), exclusions (7.3), sensitivity_finding (7.5).
    out: presented_ranking_and_sensitivity, selection_rationale (8.1).
    """
    order = [e["model_id"] for e in ranking]
    # SN-TL-07 / 5.1.6.3 -- every excluded candidate with the constraints it failed
    excluded = [{"model_id": e["model_id"], "failed_constraints": e["failed_constraints"]} for e in exclusions]
    # SN-TL-04 / 5.1.3.1 -- one contribution per weighted criterion. Gaps are shown,
    # never filled in silently (SPEC section 2, missing values).
    score_breakdown = [{"model_id": e["model_id"], "score": e["score"], "contributions": e["contributions"],
                        "missing_data": e.get("missing_data", [])} for e in ranking]
    # SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2 -- every figure, ranked and excluded, once each, with
    # source, date and stale flag (stale stored figures are still used)
    evidence, shown = [], set()
    for e in ranking + exclusions:
        for item in e.get("evidence", []):
            if (item["model_id"], item["metric"]) not in shown:
                shown.add((item["model_id"], item["metric"]))
                evidence.append(item)
    unstable = sensitivity_finding["unstable_pairs"]  # SN-TL-05 / 5.1.4.1

    presented = {"ranking": order, "score_breakdown": score_breakdown, "excluded": excluded,
                 "evidence": evidence, "unstable_pairs": unstable, "sensitivity": sensitivity_finding}
    # SR 1.4.1.6 -- the rationale carries the same ranking, exclusions, evidence and sensitivity finding to F.1.7
    selection_rationale = {"ranking": order, "score_breakdown": score_breakdown, "excluded": excluded,
                           "evidence": evidence, "unstable_pairs": unstable, "sensitivity": sensitivity_finding}
    return presented, selection_rationale
