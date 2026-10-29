"""Implements F.1 -- Provide LLM Selection Decision Support. Mechanism: C.1 LLM Compass."""

# LLM Compass (walking skeleton)
# F.1's sub-functions F.1.1-F.1.7 are one module each (IDEF0 A1, 2026-10-26). This
# package holds F.1's boundary: the ICOM defs at the end compose them, and rank and
# unstable_pairs (SPEC section 4) compose F.1.3-F.1.5. The walking-skeleton steps
# in between are still stubs that return their own section of the matched
# scenario's expected output from sample_data/.

import copy
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# F.1 sub-functions (IDEF0 A1, 2026-10-26), one module each (docs/PLAN.md "F.1 decomposition")
from .analyze_ranking_sensitivity import WEIGHT_FACTORS, analyze_ranking_sensitivity
from .analyze_ranking_sensitivity import _flips as _ranking_flips
from .apply_hard_constraints import apply_hard_constraints
from .propose_criteria_mapping import (  # noqa: F401 -- F.1 boundary and SPEC section 4 re-exports
    CATEGORIES,
    DESIGNATIONS,
    KNOWN_METRICS,
    OPERATORS,
    PROXY_STRENGTHS,
    _decision,
    _require,
    present_criteria_mapping,
    request_interpretation,
    compile_decision_basis,
    split_confirmed_mapping,
    validate_criterion,
    validate_interpretation,
)
from .generate_and_store_decision_record import (  # noqa: F401 -- SPEC section 4 re-exports
    RECORD_SECTIONS,
    generate_and_store_decision_record,
    retrieve_decision_record,
    store_decision_record,
)
from .retrieve_model_data import (  # noqa: F401 -- SPEC section 4 re-export (is_stale)
    STALE_AFTER,
    _figure_metrics,
    _flag_stale,
    is_stale,
    receive_model_data,
    request_model_data,
)
from .report_selection_rationale import report_selection_rationale
from .score_and_rank_candidates import score_and_rank_candidates

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"
USER_INPUTS = SAMPLE_DATA / "user_inputs.json"
EXPECTED_OUTPUTS = SAMPLE_DATA / "expected_outputs.json"
SCENARIO_CRITERIA = SAMPLE_DATA / "scenario_criteria.json"

SENSITIVITY_METHOD = "Each weight varied by -10% and +10% (relative), one at a time"

def rank(candidates: list, criteria: list, today, *, staleness_threshold: timedelta = STALE_AFTER) -> dict:
    # SN-TL-02 / 5.1.2.1, SN-TL-04 / 5.1.3.1, SN-TL-07 / 5.1.6.2, 5.1.6.3, SN-TL-08 / 5.3.1.1
    # SPEC section 4 composition of F.1.3 then F.1.4 (IDEF0 A1, 2026-10-26).
    hard = [c for c in criteria if c["designation"] == "hard"]
    weighted = [c for c in criteria if c["designation"] == "weighted"]
    # F.1.2's stale flag on every figure, against the given day (F.1.4 carries every figure)
    candidate_evidence = [_flag_stale(cand, _figure_metrics(cand), today, staleness_threshold)
                          for cand in candidates]

    eligible, excluded = apply_hard_constraints(candidate_evidence, hard_constraints=hard)  # F.1.3
    ranked = score_and_rank_candidates(eligible, weighted_criteria=weighted)  # F.1.4
    return {"ranked": ranked, "excluded": excluded}


def _flips(candidates: list, criteria: list, today, *, sensitivity_policy: tuple = WEIGHT_FACTORS) -> dict:
    # SN-TL-05 / 5.1.4.1 -- F.1.5 on rank's ranking: {pair: the weight changes that flip it}
    weighted = [c for c in criteria if c["designation"] == "weighted"]
    return _ranking_flips(rank(candidates, criteria, today)["ranked"], weighted, sensitivity_policy)


def unstable_pairs(candidates: list, criteria: list, today, *, sensitivity_policy: tuple = WEIGHT_FACTORS) -> set:
    # SN-TL-05 / 5.1.4.1 -- SPEC section 4 composition of F.1.3-F.1.5
    return set(_flips(candidates, criteria, today, sensitivity_policy=sensitivity_policy))


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
                             "missing_data": e["missing_data"]}
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

def request_benchmark_evidence(confirmed_criteria_mapping: list) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: confirmed_criteria_mapping. out: data_request.
    """
    # UC.1.9-1.10 (SR 1.1.1, SR 1.2.1, SN-TL-07 / 5.1.6.1, SN-TL-08 / 5.3.1.1)
    _, _, required_metrics = split_confirmed_mapping(confirmed_criteria_mapping)  # F.1.1
    return request_model_data(required_metrics)  # F.1.2


def present_ranking_and_sensitivity(model_data_with_provenance: list, confirmed_criteria_mapping: list, *,
                                    staleness_threshold: timedelta = STALE_AFTER,
                                    sensitivity_policy: tuple = WEIGHT_FACTORS) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: model_data_with_provenance, confirmed_criteria_mapping.
    control: staleness_threshold, sensitivity_policy. out: presented_ranking_and_sensitivity.
    """
    # UC.1.11-1.16 (SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2, SN-TL-04 / 5.1.3.1, SN-TL-05 / 5.1.4.1, SN-TL-07 / 5.1.6.2)
    # SR 1.1.2, SR 1.2.5, SR 1.3.3
    _require("requirement_id", "request_interpretation")
    criteria = confirmed_criteria_mapping
    weighted, hard, _ = split_confirmed_mapping(criteria)  # F.1.1
    candidate_evidence = receive_model_data(model_data_with_provenance,
                                            staleness_threshold=staleness_threshold)  # F.1.2
    eligible, exclusions = apply_hard_constraints(candidate_evidence, hard_constraints=hard)  # F.1.3
    ranking = score_and_rank_candidates(eligible, weighted_criteria=weighted)  # F.1.4
    finding = analyze_ranking_sensitivity(ranking, weighted_criteria=weighted,
                                          sensitivity_policy=sensitivity_policy)  # F.1.5
    presented, selection_rationale = report_selection_rationale(ranking, exclusions, finding)  # F.1.6

    _decision["confirmed_criteria_mapping"] = copy.deepcopy(criteria)  # SR 1.2.2 -- the mapping ranked
    _decision["selection_rationale"] = selection_rationale
    return presented


def record_decision(model_selection: Optional[str], confirmed_criteria_mapping: list) -> dict:
    """Function: F.1 -- Provide LLM Selection Decision Support. Signature from Chapter 4; body added this increment.

    in: model_selection, confirmed_criteria_mapping. out: decision_record.
    """
    # UC.1.17-1.18 (SR 1.1.3, SR 1.2.2, SN-TL-09 / 5.1.3.2, SN-TL-07 / 5.1.6.3)
    _require("selection_rationale", "present_ranking_and_sensitivity")
    # SR 1.2.2 -- the record's mapping and weights are the ones the ranking used
    if confirmed_criteria_mapping != _decision["confirmed_criteria_mapping"]:
        raise ValueError("The criteria mapping differs from the one the ranking used.")
    # Flow 5.4 Decision basis, F.1.1 -> F.1.7 (ADR-0002). Validates the mapping too (SR 1.1.1).
    decision_basis = compile_decision_basis([_decision["text"]], confirmed_criteria_mapping)  # F.1.1
    return generate_and_store_decision_record(_decision["selection_rationale"], model_selection,
                                              decision_basis)  # F.1.7
