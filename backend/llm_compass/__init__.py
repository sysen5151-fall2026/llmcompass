# STUB: LLM Compass (walking skeleton -- no real logic yet)
# No ranking logic. Each step returns its own section of the matched scenario's
# expected output from sample_data/.

import json
from pathlib import Path

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"
USER_INPUTS = SAMPLE_DATA / "user_inputs.json"
EXPECTED_OUTPUTS = SAMPLE_DATA / "expected_outputs.json"


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
    # UC.1.9
    return mapping


def present_sensitivity_finding(model_data: dict, scenario_id: str) -> dict:
    # UC.1.16 (SN-TL-05 / 5.1.4.1)
    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == scenario_id)
    return {"scenario_id": scenario_id, "comparison_result": scenario["comparison_result"]}


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
