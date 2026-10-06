"""UC.1 walking skeleton: UC.1.16 now computes the ranking and sensitivity finding
from sample_data/ (SN-TL-05 / 5.1.4.1). The computed ranking must still match each
scenario's expected output."""

import json
from pathlib import Path

import pytest

from conftest import TODAY
from benchmark_data_sources import request_model_data
from llm_compass import (confirm_mapping, generate_decision_record, present_sensitivity_finding,
                         select_model)

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample_data"
USER_INPUTS = json.loads((SAMPLE_DATA / "user_inputs.json").read_text())
EXPECTED = {s["scenario_id"]: s for s in json.loads((SAMPLE_DATA / "expected_outputs.json").read_text())}


TEXT = {s["scenario_id"]: s["user_input"] for s in USER_INPUTS}


def run_finding(scenario_id):
    confirmed = confirm_mapping({"scenario_id": scenario_id})
    data = request_model_data(confirmed)
    requirements = {"scenario_id": scenario_id, "text": TEXT[scenario_id]}
    return present_sensitivity_finding(data, confirmed, requirements, TODAY)


def finding(scenario_id):
    return run_finding(scenario_id)["comparison_result"]


@pytest.mark.parametrize("scenario_id", ["SCENARIO_01", "SCENARIO_02", "SCENARIO_03"])
def test_SN_TL_05_5_1_4_1_skeleton_ranking_matches_expected(scenario_id):
    result = finding(scenario_id)
    assert result["ranking"] == EXPECTED[scenario_id]["comparison_result"]["ranking"]
    for row in result["sensitivity"]:
        assert set(row["models"]) <= set(result["ranking"])
        assert row["flipped_by"]
    assert result["ranking_is_stable"] == (not result["sensitivity"])


@pytest.mark.parametrize("scenario_id", ["SCENARIO_01", "SCENARIO_02", "SCENARIO_03"])
def test_SN_TL_04_5_1_3_1_skeleton_shows_score_breakdown(scenario_id):
    result = finding(scenario_id)
    weighted = {c["criterion_id"] for c in confirm_mapping({"scenario_id": scenario_id})["criteria"]
                if c["designation"] == "weighted"}
    assert [row["model"] for row in result["score_breakdown"]] == result["ranking"]
    for row in result["score_breakdown"]:
        assert weighted <= set(row)


@pytest.mark.parametrize("scenario_id", ["SCENARIO_01", "SCENARIO_02", "SCENARIO_03"])
def test_SN_TL_02_5_1_2_1_skeleton_shows_evidence_provenance(scenario_id):
    result = finding(scenario_id)
    assert set(result["ranking"]) <= {row["model"] for row in result["evidence"]}
    for row in result["evidence"]:
        assert row["source_id"] and row["collection_date"] and isinstance(row["stale"], bool)


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


@pytest.mark.parametrize("scenario_id", ["SCENARIO_01", "SCENARIO_02", "SCENARIO_03"])
def test_SN_TL_09_5_1_3_2_skeleton_record_has_all_sections(scenario_id):
    record = generate_decision_record(select_model(run_finding(scenario_id)))
    for section in ("requirements", "criteria_mapping", "weights", "evidence", "ranking", "sensitivity"):
        assert record.get(section), f"missing or empty: {section}"
    assert record["requirements"] == [TEXT[scenario_id]]
    assert record["ranking"] == finding(scenario_id)["ranking"]
    assert record["selected_model"] == record["ranking"][0]
    for fig in record["evidence"]:
        assert fig["source_id"] and fig["collection_date"]


def test_SN_TL_09_5_1_3_2_skeleton_record_without_selection():
    # UC alt flow 15a -- every candidate excluded, so the record has no selection
    record = generate_decision_record(select_model(run_finding("SCENARIO_04")))
    assert record["selected_model"] is None
    assert record["ranking"] == []
    assert {row["failed_constraints"][0] for row in record["excluded"]} == {"eu_only_data"}
    assert record["evidence"]  # the residency figure that excluded them, with provenance
