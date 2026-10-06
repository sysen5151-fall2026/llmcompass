# LLM Compass (walking skeleton)
# rank, unstable_pairs and is_stale are real logic. The other steps are still stubs
# that return their own section of the matched scenario's expected output from
# sample_data/.

import json
from datetime import date, timedelta
from pathlib import Path

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"
USER_INPUTS = SAMPLE_DATA / "user_inputs.json"
EXPECTED_OUTPUTS = SAMPLE_DATA / "expected_outputs.json"
SCENARIO_CRITERIA = SAMPLE_DATA / "scenario_criteria.json"

STALE_AFTER = timedelta(days=90)
WEIGHT_FACTORS = (0.9, 1.1)  # SN-TL-05 / 5.1.4.1 -- relative +/-10%, no renormalization (SPEC 5 Q5)


def is_stale(collection_date, today) -> bool:
    # SN-TL-03 / 5.1.2.2 -- older than 90 days is stale; exactly 90 is not
    return today - date.fromisoformat(str(collection_date)) > STALE_AFTER


def _metric_figure(candidate: dict, metric: str):
    # A metric is a SPEC section 2 field or a benchmark_id.
    if metric in candidate:
        return candidate[metric]
    for b in candidate.get("benchmarks", []):
        if b["benchmark_id"] == metric:
            return b["score"]
    return None


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


def _normalized(values: dict, operator: str, threshold) -> dict:
    # Min-max across the surviving candidates. Missing (None) scores 0.
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


def rank(candidates: list, criteria: list, today) -> dict:
    # SN-TL-02 / 5.1.2.1, SN-TL-04 / 5.1.3.1, SN-TL-07 / 5.1.6.2, 5.1.6.3, SN-TL-08 / 5.3.1.1
    hard = [c for c in criteria if c["designation"] == "hard"]
    weighted = [c for c in criteria if c["designation"] == "weighted"]

    survivors, excluded = [], []
    for cand in candidates:
        failed = []
        for c in hard:
            fig = _metric_figure(cand, c["metric"])
            if fig is None:
                failed.append(f"missing_data:{c['metric']}")  # SPEC section 2, missing values
            elif not _meets(fig["value"], c["operator"], c["threshold"]):
                failed.append(c["criterion_id"])
        if failed:
            excluded.append({"model_id": cand["model_id"], "failed_constraints": failed})
        else:
            survivors.append(cand)

    norm = {}
    for c in weighted:
        values = {}
        for cand in survivors:
            fig = _metric_figure(cand, c["metric"])
            values[cand["model_id"]] = fig["value"] if fig is not None else None
        norm[c["criterion_id"]] = _normalized(values, c["operator"], c.get("threshold"))

    ranked = []
    for cand in survivors:
        mid = cand["model_id"]
        contributions = {c["criterion_id"]: c["weight"] * norm[c["criterion_id"]][mid] for c in weighted}
        evidence, gaps = [], []
        for c in hard + weighted:
            fig = _metric_figure(cand, c["metric"])
            if fig is None:
                gaps.append(c["metric"])
            else:
                evidence.append({**fig, "metric": c["metric"],
                                 "stale": is_stale(fig["collection_date"], today)})
        ranked.append({"model_id": mid, "score": sum(contributions.values()),
                       "contributions": contributions, "evidence": evidence, "gaps": gaps})

    ranked.sort(key=lambda e: (-e["score"], e["model_id"]))
    return {"ranked": ranked, "excluded": excluded}


def _flips(candidates: list, criteria: list, today) -> dict:
    # SN-TL-05 / 5.1.4.1 -- vary each weight by -10% and +10%, one at a time,
    # and record which variations change the relative order of each pair.
    base = [e["model_id"] for e in rank(candidates, criteria, today)["ranked"]]
    pos = {m: i for i, m in enumerate(base)}
    flips = {}
    for i, c in enumerate(criteria):
        if c["designation"] != "weighted":
            continue
        for factor in WEIGHT_FACTORS:
            varied = [dict(x) for x in criteria]
            varied[i]["weight"] = c["weight"] * factor
            order = [e["model_id"] for e in rank(candidates, varied, today)["ranked"]]
            new = {m: j for j, m in enumerate(order)}
            for a in base:
                for b in base:
                    if pos[a] < pos[b] and new[a] > new[b]:
                        label = f"{c['criterion_id']} {round((factor - 1) * 100):+d}%"
                        flips.setdefault(frozenset((a, b)), []).append(label)
    return flips


def unstable_pairs(candidates: list, criteria: list, today) -> set:
    # SN-TL-05 / 5.1.4.1
    return set(_flips(candidates, criteria, today))


def receive_requirements(text: str) -> dict:
    # UC.1.2 (SN-TL-01 / 5.1.1.1) -- empty or whitespace-only text is rejected
    if not text.strip():
        raise ValueError("Requirements text is empty.")
    scenarios = json.loads(USER_INPUTS.read_text())
    scenario = next(s for s in scenarios if s["user_input"] == text)
    return {"scenario_id": scenario["scenario_id"], "text": text}


def present_mapping_for_review(interpretation: dict) -> dict:
    # UC.1.6
    return interpretation


def confirm_mapping(mapping: dict) -> dict:
    # UC.1.9 (SN-TL-07 / 5.1.6.1)
    # STUB: Technical Lead confirmation -- the UI has no confirm step, so the
    # criteria and weights come from sample_data/scenario_criteria.json.
    all_criteria = json.loads(SCENARIO_CRITERIA.read_text())
    return {**mapping, "criteria": all_criteria[mapping["scenario_id"]]}


def present_sensitivity_finding(model_data: dict, confirmed: dict, scenario_id: str, today=None) -> dict:
    # UC.1.16 (SN-TL-05 / 5.1.4.1) -- ranking and sensitivity are computed;
    # candidate_assessment and tradeoffs are still the scenario's expected output.
    today = today or date.today()
    candidates, criteria = model_data["candidates"], confirmed["criteria"]
    names = {c["model_id"]: c["model_name"] for c in candidates}

    result = rank(candidates, criteria, today)
    flips = _flips(candidates, criteria, today)
    order = [e["model_id"] for e in result["ranked"]]

    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == scenario_id)
    comparison = dict(scenario["comparison_result"])
    comparison.update({
        "ranking": [names[m] for m in order] or None,  # None = every candidate excluded (UC alt flow 10a)
        # SN-TL-04 / 5.1.3.1 -- one row per ranked model, one column per weighted criterion
        "score_breakdown": [{"rank": i + 1, "model": names[e["model_id"]], "score": round(e["score"], 3),
                             **{cid: round(v, 3) for cid, v in e["contributions"].items()},
                             "missing_data": e["gaps"]}
                            for i, e in enumerate(result["ranked"])],
        # SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2 -- every figure used, with source, date and stale flag
        "evidence": [{"model": names[e["model_id"]], "metric": f["metric"], "value": f["value"],
                      "unit": f["unit"], "source": f["source_id"], "collected": f["collection_date"],
                      "stale": f["stale"]}
                     for e in result["ranked"] for f in e["evidence"]],
        "excluded": [{"model": names[e["model_id"]], "failed_constraints": e["failed_constraints"]}
                     for e in result["excluded"]],
        "sensitivity_method": "Each weight varied by -10% and +10% (relative), one at a time",
        "sensitivity": [{"models": [names[m] for m in sorted(pair, key=order.index)],
                         "flipped_by": labels}
                        for pair, labels in flips.items()],
        "ranking_is_stable": not flips,
    })
    return {"scenario_id": scenario_id, "comparison_result": comparison}


def select_model(finding: dict) -> dict:
    # UC.1.17
    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == finding["scenario_id"])
    return {"scenario_id": finding["scenario_id"], "selection_result": scenario["selection_result"]}


def generate_decision_record(interpretation: dict, finding: dict, selection: dict) -> dict:
    # UC.1.18 (SN-TL-09 / 5.1.3.2)
    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == selection["scenario_id"])
    return {
        "scenario_id": selection["scenario_id"],
        "interpreted_requirements": interpretation["interpreted_requirements"],
        "comparison_result": finding["comparison_result"],
        "selection_result": selection["selection_result"],
        "decision_record": scenario["decision_record"],
    }
