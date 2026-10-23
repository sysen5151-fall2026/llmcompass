"""Implements F.1 -- Provide LLM Selection Decision Support. Mechanism: C.1 LLM Compass."""

# LLM Compass (walking skeleton)
# rank, unstable_pairs, is_stale and the decision record's 6 sections are real
# logic. The other steps are still stubs that return their own section of the
# matched scenario's expected output from sample_data/.
# The F.1 ICOM defs at the end have bodies (Lab Manual 5.3).

import copy
import json
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from provide_benchmark_evidence import BENCHMARK_IDS

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"
USER_INPUTS = SAMPLE_DATA / "user_inputs.json"
EXPECTED_OUTPUTS = SAMPLE_DATA / "expected_outputs.json"
SCENARIO_CRITERIA = SAMPLE_DATA / "scenario_criteria.json"

STALE_AFTER = timedelta(days=90)
WEIGHT_FACTORS = (0.9, 1.1)  # SN-TL-05 / 5.1.4.1 -- relative +/-10%, no renormalization (SPEC 5 Q5)
SENSITIVITY_METHOD = "Each weight varied by -10% and +10% (relative), one at a time"
RECORD_SECTIONS = ("requirements", "criteria_mapping", "weights", "evidence", "ranking", "sensitivity")

# SR 1.1.4, SR 1.3.2 (SPEC section 3) -- the model contract's vocabulary.
# SPEC section 2 figure fields. With the catalog's benchmark ids (F.7's published
# vocabulary, SPEC 5 Q7) they are the known metrics of SPEC section 3.
FIGURE_FIELDS = ("input_price", "output_price", "context_window", "latency_p50",
                 "data_residency", "data_retention", "deprecation_date")
KNOWN_METRICS = frozenset(FIGURE_FIELDS) | frozenset(BENCHMARK_IDS)
OPERATORS = (">=", "<=", "==", "in")  # SR 1.1.4, SR 1.3.2 (SPEC section 3)
PROXY_STRENGTHS = ("strong", "moderate", "weak")  # SR 1.1.4, SN-TL-01 / 5.1.1.3 (scale is SPEC 5 Q4)
CATEGORIES = ("capability", "cost", "compliance", "other")  # SR 1.1.4, SR 1.3.2 (SPEC section 3)
DESIGNATIONS = ("hard", "weighted")  # SN-TL-07 / 5.1.6.1


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
        failed, evidence = [], []
        for c in hard:
            fig = _metric_figure(cand, c["metric"])
            if fig is None:
                failed.append(f"missing_data:{c['metric']}")  # SPEC section 2, missing values
                continue
            evidence.append({**fig, "metric": c["metric"], "stale": is_stale(fig["collection_date"], today)})
            if not _meets(fig["value"], c["operator"], c["threshold"]):
                failed.append(c["criterion_id"])
        if failed:
            excluded.append({"model_id": cand["model_id"], "failed_constraints": failed, "evidence": evidence})
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
    # UC.1.2 (SR 1.1.5, SN-TL-01 / 5.1.1.1) -- the requirement ID and the empty-text
    # rejection come from request_interpretation. scenario_id is None when the text
    # matches no sample scenario.
    request = request_interpretation(text)
    scenarios = json.loads(USER_INPUTS.read_text())
    scenario = next((s for s in scenarios if s["user_input"] == text), None)
    return {**request, "scenario_id": scenario["scenario_id"] if scenario else None}


def present_mapping_for_review(interpretation: dict) -> dict:
    # UC.1.6
    return interpretation


def confirm_mapping(mapping: dict) -> dict:
    # UC.1.9 (SN-TL-07 / 5.1.6.1)
    # STUB: Technical Lead confirmation -- the UI has no confirm step, so the
    # criteria and weights come from sample_data/scenario_criteria.json.
    all_criteria = json.loads(SCENARIO_CRITERIA.read_text())
    return {**mapping, "criteria": all_criteria[mapping["scenario_id"]]}


def present_sensitivity_finding(model_data: dict, confirmed: dict, requirements: dict, today=None) -> dict:
    # UC.1.16 (SN-TL-05 / 5.1.4.1) -- ranking and sensitivity are computed;
    # candidate_assessment and tradeoffs are still the scenario's expected output.
    today = today or date.today()
    scenario_id = requirements["scenario_id"]
    candidates, criteria = model_data["candidates"], confirmed["criteria"]
    names = {c["model_id"]: c["model_name"] for c in candidates}

    result = rank(candidates, criteria, today)
    flips = _flips(candidates, criteria, today)
    order = [e["model_id"] for e in result["ranked"]]
    stable = not flips if order else None  # None = nothing ranked, so nothing to compare
    sensitivity = [{"models": [names[m] for m in sorted(pair, key=order.index)], "flipped_by": labels}
                   for pair, labels in flips.items()]
    # SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2 -- every figure used (ranked and excluded), with provenance
    evidence = [{"model": names[e["model_id"]], "metric": f["metric"], "value": f["value"], "unit": f["unit"],
                 "source_id": f["source_id"], "collection_date": f["collection_date"], "stale": f["stale"]}
                for e in result["ranked"] + result["excluded"] for f in e["evidence"]]
    excluded = [{"model": names[e["model_id"]], "failed_constraints": e["failed_constraints"]}
                for e in result["excluded"]]

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
        "evidence": evidence,
        "excluded": excluded,
        "sensitivity_method": SENSITIVITY_METHOD,
        "sensitivity": sensitivity,
        "ranking_is_stable": stable,
    })
    # The sections UC.1.18 needs for the decision record (SN-TL-09 / 5.1.3.2)
    record_inputs = {
        "requirements": [requirements["text"]],
        "criteria_mapping": criteria,
        "weights": {c["criterion_id"]: c["weight"] for c in criteria if c["designation"] == "weighted"},
        "evidence": evidence,
        "ranking": [names[m] for m in order],
        "sensitivity": {
            "method": SENSITIVITY_METHOD,
            "ranking_is_stable": stable,
            "unstable_pairs": [f"{' vs '.join(r['models'])} (flipped by {', '.join(r['flipped_by'])})"
                               for r in sensitivity],
        },
        "excluded": excluded,
    }
    return {"scenario_id": scenario_id, "comparison_result": comparison, "record_inputs": record_inputs}


def select_model(finding: dict) -> dict:
    # UC.1.17
    # STUB: Technical Lead selection -- the UI has no select step, so the
    # scenario's expected recommendation is taken as the selection.
    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == finding["scenario_id"])
    selection_result = scenario["selection_result"]
    recommended = selection_result["recommended_model"]
    return {
        **finding["record_inputs"],
        "scenario_id": finding["scenario_id"],
        "selection_result": selection_result,
        "selected_model": recommended["model_name"] if recommended else None,  # None = UC alt flow 15a
    }


def generate_decision_record(selection: dict) -> dict:
    # UC.1.18 (SN-TL-09 / 5.1.3.2) -- the 6 required sections plus the selection made.
    record = {section: selection[section] for section in RECORD_SECTIONS}
    record["selected_model"] = selection.get("selected_model")  # None = no model selected (UC alt flow 15a)
    if "excluded" in selection:
        record["excluded"] = selection["excluded"]  # SN-TL-07 / 5.1.6.3
    if "scenario_id" in selection:
        # STUB: written narrative -- summary, limitations and next action are still
        # the scenario's expected output.
        scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
        scenario = next(s for s in scenarios if s["scenario_id"] == selection["scenario_id"])
        record.update(scenario["decision_record"])
    return record


# --- F.1 ICOM signatures (Lab Manual 4.4); bodies added in Chapter 5 (Lab Manual 5.3) ---

# SR 1.2.2 -- the decision in progress, held by mechanism C.1 (docs/PLAN.md "Interface
# details the tests rely on"), so the record is built from what was actually ranked.
# request_interpretation starts a new one.
_decision = {}


def _require(key: str, step: str) -> None:
    # UC.1 order: a step that needs an earlier one's result says which step is missing.
    if key not in _decision:
        raise RuntimeError(f"{step} has not been called for this decision.")


def _threshold_fits(operator: str, threshold) -> bool:
    # SR 1.1.4, SR 1.3.2 (SPEC section 3) -- the threshold type each operator can compare against
    if operator == "in":
        return isinstance(threshold, list)
    if operator in (">=", "<="):
        return threshold is None or (isinstance(threshold, (int, float)) and not isinstance(threshold, bool))
    return threshold is None or (isinstance(threshold, (int, float, str)) and not isinstance(threshold, bool))


def validate_interpretation(response) -> bool:
    # SR 1.1.4, SR 1.3.2 (SN-TL-01 / 5.1.1.2, 5.1.1.3) -- the SPEC section 3 response schema
    if not isinstance(response, dict):
        return False
    criteria, no_proxy = response.get("criteria"), response.get("no_suitable_proxy")
    if not (isinstance(response.get("requirement_id"), str) and response["requirement_id"]):
        return False
    if not isinstance(no_proxy, bool) or not isinstance(criteria, list):
        return False
    if bool(criteria) == no_proxy:  # 1+ criteria, or no_suitable_proxy with none -- not both, not neither
        return False
    for c in criteria:
        if not isinstance(c, dict):
            return False
        if not (isinstance(c.get("criterion_id"), str) and c["criterion_id"]):
            return False
        if c.get("metric") not in KNOWN_METRICS or c.get("operator") not in OPERATORS:
            return False
        if "threshold" not in c or not isinstance(c["threshold"], (int, float, str, list, type(None))):
            return False
        if not _threshold_fits(c["operator"], c["threshold"]):
            return False
        if not isinstance(c.get("unit"), str) or not isinstance(c.get("rationale"), str):
            return False
        if c.get("proxy_strength") not in PROXY_STRENGTHS or c.get("category") not in CATEGORIES:
            return False
    return True


def validate_criterion(criterion: dict) -> None:
    # SR 1.1.1 (SN-TL-07 / 5.1.6.1) -- hard or weighted, and a weighted criterion needs a weight
    if criterion.get("designation") not in DESIGNATIONS:
        raise ValueError(f"{criterion.get('criterion_id')}: designation must be hard or weighted.")
    weight = criterion.get("weight")
    if criterion["designation"] == "weighted" and (isinstance(weight, bool) or not isinstance(weight, (int, float))):
        raise ValueError(f"{criterion.get('criterion_id')}: a weighted criterion needs a numeric weight.")


def request_interpretation(stated_requirements: str) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: stated_requirements. out: interpretation_request.
    """
    # UC.1.2-1.3 (SR 1.1.5, SN-TL-01 / 5.1.1.1; SR 1.2.3, SN-TL-01 / 5.1.1.2) -- one
    # SPEC section 3 request per stated requirement, with its own ID and the text unaltered
    if not isinstance(stated_requirements, str):
        raise ValueError("Requirements must be text.")
    if not stated_requirements.strip():
        raise ValueError("Requirements text is empty.")
    requirement_id = f"REQ-{uuid.uuid4().hex}"
    _decision.clear()
    _decision.update({"requirement_id": requirement_id, "text": stated_requirements, "invalid_responses": {}})
    return {"requirement_id": requirement_id, "text": stated_requirements}


def present_criteria_mapping(proposed_criteria: dict) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: proposed_criteria. out: presented_mapping.
    """
    # UC.1.4-1.6 (SR 1.1.4, SR 1.2.4, SR 1.3.2, SN-TL-01 / 5.1.1.2, 5.1.1.3)
    _require("requirement_id", "request_interpretation")
    requirement_id, text = _decision["requirement_id"], _decision["text"]
    presented = {"requirement_id": requirement_id, "requirement": text}
    attempts = _decision["invalid_responses"]
    # None = no response or a timeout, handled like an invalid response (SR 1.3.2).
    # SR 1.3.2 -- a response must answer the request it was sent for (same requirement_id).
    if not (validate_interpretation(proposed_criteria) and proposed_criteria["requirement_id"] == requirement_id):
        attempts[requirement_id] = attempts.get(requirement_id, 0) + 1
        # First invalid response: the caller re-sends the request. Second: the
        # requirement is kept for the Technical Lead to map by hand (SPEC section 3).
        status = "retry" if attempts[requirement_id] == 1 else "interpretation_failed"
        return {**presented, "status": status, "no_suitable_proxy": False, "criteria": []}
    attempts.pop(requirement_id, None)  # SR 1.1.4 -- a later invalid response gets its retry again
    # SR 1.2.4 -- every criterion shows the requirement it stands for and its proxy_strength
    criteria = [{**c, "requirement": text} for c in proposed_criteria["criteria"]]
    return {**presented, "status": "proposed", "no_suitable_proxy": proposed_criteria["no_suitable_proxy"],
            "criteria": criteria}


def request_benchmark_evidence(*, confirmed_criteria_mapping: list) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    control: confirmed_criteria_mapping. out: data_request.
    """
    # UC.1.9-1.10 (SR 1.1.1, SR 1.2.1, SN-TL-07 / 5.1.6.1, SN-TL-08 / 5.3.1.1)
    for c in confirmed_criteria_mapping:
        validate_criterion(c)
    metrics = list(dict.fromkeys(c["metric"] for c in confirmed_criteria_mapping))
    return {"models": "all", "metrics": metrics}  # every candidate in the catalog


def present_ranking_and_sensitivity(model_data_with_provenance: list, *, confirmed_criteria_mapping: list) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: model_data_with_provenance. control: confirmed_criteria_mapping. out: presented_ranking_and_sensitivity.
    """
    # UC.1.11-1.16 (SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2, SN-TL-04 / 5.1.3.1, SN-TL-05 / 5.1.4.1, SN-TL-07 / 5.1.6.2)
    # SR 1.1.2, SR 1.2.5, SR 1.3.3
    _require("requirement_id", "request_interpretation")
    candidates, criteria = model_data_with_provenance, confirmed_criteria_mapping
    for c in criteria:
        validate_criterion(c)
    # SR 1.1.2 (SN-TL-02 / 5.1.2.1, SPEC section 2) -- a figure that isn't a figure, or has
    # no source_id or collection_date, is rejected at entry
    for cand in candidates:
        figures = [(f, cand[f]) for f in FIGURE_FIELDS if f in cand]
        for b in cand.get("benchmarks", []):
            if not isinstance(b, dict):
                raise ValueError(f"{cand['model_id']}: benchmark entry is not a benchmark_id and score.")
            figures.append((b.get("benchmark_id"), b.get("score")))
        for field, fig in figures:
            if not isinstance(fig, dict):
                raise ValueError(f"{cand['model_id']}.{field}: not a figure with source and date.")
            if not fig.get("source_id") or not fig.get("collection_date"):
                raise ValueError(f"{cand['model_id']}.{field}: figure has no source_id or collection_date.")

    today = date.today()  # the clock belongs to mechanism C.1
    result = rank(candidates, criteria, today)
    flips = _flips(candidates, criteria, today)
    ranking = [e["model_id"] for e in result["ranked"]]
    excluded = [{"model_id": e["model_id"], "failed_constraints": e["failed_constraints"]}
                for e in result["excluded"]]
    # SN-TL-04 / 5.1.3.1 -- one contribution per weighted criterion. Gaps are shown,
    # never filled in silently (SPEC section 2, missing values).
    score_breakdown = [{"model_id": e["model_id"], "score": e["score"], "contributions": e["contributions"],
                        "gaps": e["gaps"]} for e in result["ranked"]]
    # SN-TL-05 / 5.1.4.1 -- each pair in ranking order
    unstable = [sorted(pair, key=ranking.index) for pair in flips]
    # SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2 -- every criterion metric's figure, ranked
    # and excluded, with source, date and stale flag (stale stored figures are still used)
    by_id = {cand["model_id"]: cand for cand in candidates}
    metrics = list(dict.fromkeys(c["metric"] for c in criteria))
    evidence = []
    for model_id in ranking + [e["model_id"] for e in excluded]:
        for metric in metrics:
            fig = _metric_figure(by_id[model_id], metric)
            if fig is not None:
                evidence.append({"model_id": model_id, "metric": metric, "value": fig["value"],
                                 "unit": fig["unit"], "source_id": fig["source_id"],
                                 "collection_date": fig["collection_date"],
                                 "stale": is_stale(fig["collection_date"], today)})

    presented = {"ranking": ranking, "excluded": excluded, "score_breakdown": score_breakdown,
                 "unstable_pairs": unstable, "evidence": evidence}
    _decision["confirmed_criteria_mapping"] = copy.deepcopy(criteria)  # SR 1.2.2 -- the mapping ranked
    _decision["presented_ranking"] = presented
    return presented


def record_decision(model_selection: Optional[str], *, confirmed_criteria_mapping: list) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: model_selection. control: confirmed_criteria_mapping. out: decision_record.
    """
    # UC.1.17-1.18 (SR 1.1.3, SR 1.2.2, SN-TL-09 / 5.1.3.2, SN-TL-07 / 5.1.6.3)
    _require("presented_ranking", "present_ranking_and_sensitivity")
    presented = _decision["presented_ranking"]
    for c in confirmed_criteria_mapping:
        validate_criterion(c)  # SR 1.1.1 (SN-TL-07 / 5.1.6.1)
    # SR 1.2.2 -- the record's mapping and weights are the ones the ranking used
    criteria = _decision["confirmed_criteria_mapping"]
    if confirmed_criteria_mapping != criteria:
        raise ValueError("The criteria mapping differs from the one the ranking used.")
    if model_selection is not None and model_selection not in presented["ranking"]:
        raise ValueError(f"{model_selection} is not in the ranking.")
    ranking = presented["ranking"]
    selection = {
        "requirements": [_decision["text"]],
        "criteria_mapping": criteria,
        "weights": {c["criterion_id"]: c["weight"] for c in criteria if c["designation"] == "weighted"},
        "evidence": presented["evidence"],
        "ranking": ranking,
        "sensitivity": {
            "method": SENSITIVITY_METHOD,
            "ranking_is_stable": not presented["unstable_pairs"] if ranking else None,  # None = nothing ranked
            "unstable_pairs": presented["unstable_pairs"],
        },
        "excluded": presented["excluded"],
        "selected_model": model_selection,  # SR 1.1.3 -- unchanged; None = UC alt flow 15a
    }
    return generate_decision_record(selection)
