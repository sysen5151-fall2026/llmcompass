# STUB: Language model runtime
# No LLM call. Returns the matched scenario's interpreted_requirements from
# sample_data/expected_outputs.json.

import json
from pathlib import Path

EXPECTED_OUTPUTS = Path(__file__).resolve().parents[2] / "sample_data" / "expected_outputs.json"


def submit_requirements(requirements: dict) -> dict:
    # UC.1.3, UC.1.4 -- call and return are the same function call (SN-TL-01 / 5.1.1.2)
    scenarios = json.loads(EXPECTED_OUTPUTS.read_text())
    scenario = next(s for s in scenarios if s["scenario_id"] == requirements["scenario_id"])
    return {
        "scenario_id": requirements["scenario_id"],
        "interpreted_requirements": scenario["interpreted_requirements"],
    }
