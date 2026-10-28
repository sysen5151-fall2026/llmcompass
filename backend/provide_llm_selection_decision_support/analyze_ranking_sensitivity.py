"""Implements F.1.5 -- Analyze Ranking Sensitivity. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.5 (SN-TL-05 / 5.1.4.1). IDEF0 A1 of F.1, 2026-10-26.

WEIGHT_FACTORS = (0.9, 1.1)  # SN-TL-05 / 5.1.4.1 -- relative +/-10%, no renormalization (SPEC 5 Q5)


def _order(ranking: list, weights: dict) -> list:
    # Re-scores from each entry's normalized values, as F.1.4 scores (score = sum of weight x normalized).
    scores = {e["model_id"]: sum(w * e["normalized"][cid] for cid, w in weights.items()) for e in ranking}
    return sorted(scores, key=lambda m: (-scores[m], m))


def _flips(ranking: list, weighted_criteria: list, sensitivity_policy: tuple) -> dict:
    # SN-TL-05 / 5.1.4.1 -- vary each weight by each policy factor, one at a time,
    # and record which variations change the relative order of each pair.
    base = [e["model_id"] for e in ranking]
    pos = {m: i for i, m in enumerate(base)}
    weights = {c["criterion_id"]: c["weight"] for c in weighted_criteria}
    flips = {}
    for c in weighted_criteria:
        for factor in sensitivity_policy:
            new = {m: j for j, m in enumerate(_order(ranking, {**weights, c["criterion_id"]: c["weight"] * factor}))}
            for a in base:
                for b in base:
                    if pos[a] < pos[b] and new[a] > new[b]:
                        label = f"{c['criterion_id']} {round((factor - 1) * 100):+d}%"
                        flips.setdefault(frozenset((a, b)), []).append(label)
    return flips


def analyze_ranking_sensitivity(ranking: list, *, weighted_criteria: list,
                                sensitivity_policy: tuple = WEIGHT_FACTORS) -> dict:
    """Function: F.1.5 -- Analyze Ranking Sensitivity.

    in: ranking. control: weighted_criteria, sensitivity_policy. out: sensitivity_finding.
    """
    # SR 1.4.1.5 (SN-TL-05 / 5.1.4.1)
    order = [e["model_id"] for e in ranking]
    changes = " and ".join(f"{round((f - 1) * 100):+d}%" for f in sensitivity_policy)
    return {"method": f"Each weight varied by {changes} (relative), one at a time",
            "unstable_pairs": [sorted(pair, key=order.index)  # each pair in ranking order
                               for pair in _flips(ranking, weighted_criteria, sensitivity_policy)]}
