"""Implements F.1.5 -- Analyze Ranking Sensitivity. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.5 (SN-TL-05 / 5.1.4.1). IDEF0 A1 of F.1, 2026-10-26.
# Sits behind contracts/api-v1.yaml: analyzeRankingSensitivity.

WEIGHT_FACTORS = (0.9, 1.1)  # SN-TL-05 / 5.1.4.1 -- relative +/-10%, no renormalization (SPEC 5 Q5)


def _flips(ranking: list, weighted_criteria: list, sensitivity_policy: tuple) -> dict:
    # SN-TL-05 / 5.1.4.1 -- vary each weight by each policy factor, one at a time, and record
    # which variations change the relative order of each pair: {pair: [labels]}.
    # Re-scores from the ranking's contributions, which scale with their weight (contract A10).
    # A pair flips when the lower-ranked candidate's score becomes strictly greater (A8).
    flips = {}
    for c in weighted_criteria:
        cid = c["criterion_id"]
        for factor in sensitivity_policy:
            scores = [sum(v * factor if k == cid else v for k, v in e["contributions"].items()) for e in ranking]
            for i, higher in enumerate(ranking):
                for j in range(i + 1, len(ranking)):
                    if scores[j] > scores[i]:
                        label = f"{cid} {round((factor - 1) * 100):+d}%"
                        flips.setdefault((higher["model_id"], ranking[j]["model_id"]), []).append(label)
    return flips


def analyze_ranking_sensitivity(ranking: list, *, weighted_criteria: list,
                                sensitivity_policy: tuple = WEIGHT_FACTORS) -> dict:
    """Function: F.1.5 -- Analyze Ranking Sensitivity. Contract operation analyzeRankingSensitivity.

    in: ranking (7.4). control: weighted_criteria (5.3), sensitivity_policy. out: sensitivity_finding (7.5).
    """
    # SR 1.4.1.5 (SN-TL-05 / 5.1.4.1)
    pos = {e["model_id"]: i for i, e in enumerate(ranking)}
    # Each pair as [higher, lower], listed in ranking order (A9)
    pairs = sorted(_flips(ranking, weighted_criteria, sensitivity_policy), key=lambda p: (pos[p[0]], pos[p[1]]))
    changes = " and ".join(f"{round((f - 1) * 100):+d}%" for f in sensitivity_policy)
    return {"method": f"Each weight varied by {changes} (relative), one at a time",
            "factors": list(sensitivity_policy),
            "ranking_is_stable": not pairs,
            "unstable_pairs": [list(p) for p in pairs]}
