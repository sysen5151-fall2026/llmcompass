"""UC.1 walking skeleton: UC.1.16 now computes the ranking and sensitivity finding
from sample_data/ (SN-TL-05 / 5.1.4.1). The computed ranking must still match each
scenario's expected output."""

import json
from pathlib import Path

import pytest

from conftest import TODAY
from benchmark_data_sources import request_model_data
from llm_compass import confirm_mapping, present_sensitivity_finding

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample_data"
USER_INPUTS = json.loads((SAMPLE_DATA / "user_inputs.json").read_text())
EXPECTED = {s["scenario_id"]: s for s in json.loads((SAMPLE_DATA / "expected_outputs.json").read_text())}


def finding(scenario_id):
    confirmed = confirm_mapping({"scenario_id": scenario_id})
    data = request_model_data(confirmed)
    return present_sensitivity_finding(data, confirmed, scenario_id, TODAY)["comparison_result"]


@pytest.mark.parametrize("scenario_id", ["SCENARIO_01", "SCENARIO_02", "SCENARIO_03"])
def test_SN_TL_05_5_1_4_1_skeleton_ranking_matches_expected(scenario_id):
    result = finding(scenario_id)
    assert result["ranking"] == EXPECTED[scenario_id]["comparison_result"]["ranking"]
    for row in result["sensitivity"]:
        assert set(row["models"]) <= set(result["ranking"])
        assert row["flipped_by"]
    assert result["ranking_is_stable"] == (not result["sensitivity"])


def test_SN_TL_07_5_1_6_3_skeleton_eu_scenario_excludes_all():
    result = finding("SCENARIO_04")
    assert result["ranking"] is None
    assert len(result["excluded"]) == 3
    for row in result["excluded"]:
        assert row["failed_constraints"] == ["eu_only_data"]


@pytest.mark.parametrize("scenario", USER_INPUTS, ids=lambda s: s["scenario_id"])
def test_skeleton_runs_end_to_end(scenario):
    pytest.importorskip("flask")  # CI installs pytest only
    from app import run_uc1
    record = run_uc1(scenario["user_input"])
    assert "sensitivity" in record["comparison_result"]
