"""Acceptance tests for the Technical Lead needs (SN-TL-01 to SN-TL-09). See SPEC.md section 1."""

import csv
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import candidate, impl

WALKTHROUGHS = Path(__file__).resolve().parent.parent / "docs" / "validation" / "walkthroughs.csv"

# OpsCon 4.2 scenario, one stated requirement per line.
REFERENCE_REQUIREMENTS = [
    "Summarize technical documents of around twenty pages accurately.",
    "Stay under two hundred dollars a month at five thousand requests per day.",
    "Respond within a few seconds.",
    "Process data that may not leave the United States.",
]


def walkthrough_minutes(scenario):
    if not WALKTHROUGHS.exists():
        pytest.fail(f"no timed walkthroughs logged yet: {WALKTHROUGHS}")
    with WALKTHROUGHS.open() as f:
        minutes = [float(r["minutes"]) for r in csv.DictReader(f) if r["scenario"] == scenario]
    if not minutes:
        pytest.fail(f"no '{scenario}' walkthrough logged in {WALKTHROUGHS.name}")
    return minutes


# SN-TL-01 -------------------------------------------------------------------

def test_SN_TL_01_5_1_1_1_accepts_text_requirement():
    receive = impl("llm_compass", "receive_requirements")
    result = receive("Summarize twenty-page technical documents accurately.")
    assert isinstance(result.get("requirement_id"), str) and result["requirement_id"]


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_SN_TL_01_5_1_1_1_rejects_empty_requirement(text):
    receive = impl("llm_compass", "receive_requirements")
    with pytest.raises(ValueError):
        receive(text)


@pytest.mark.parametrize("i,text", list(enumerate(REFERENCE_REQUIREMENTS)))
def test_SN_TL_01_5_1_1_2_reference_set_has_criterion_or_no_proxy(i, text):
    submit = impl("language_model_runtime", "submit_requirements")
    response = submit({"requirement_id": f"REF-{i}", "text": text})
    has_criteria = len(response.get("criteria", [])) >= 1
    no_proxy = response.get("no_suitable_proxy") is True
    assert has_criteria != no_proxy


def test_SN_TL_01_5_1_1_2_rejects_response_with_neither():
    validate = impl("llm_compass", "validate_interpretation")
    assert not validate({"requirement_id": "R1", "no_suitable_proxy": False, "criteria": []})
    assert validate({"requirement_id": "R1", "no_suitable_proxy": True, "criteria": []})


def test_SN_TL_01_5_1_1_3_every_criterion_has_proxy_strength():
    validate = impl("llm_compass", "validate_interpretation")
    base = {
        "criterion_id": "c1",
        "metric": "context_window",
        "operator": ">=",
        "threshold": 100_000,
        "unit": "tokens",
        "category": "capability",
        "rationale": "20-page documents need a long context.",
    }
    for strength in ("strong", "moderate", "weak"):
        response = {"requirement_id": "R1", "no_suitable_proxy": False,
                    "criteria": [{**base, "proxy_strength": strength}]}
        assert validate(response), strength
    for bad in (None, "high", ""):
        response = {"requirement_id": "R1", "no_suitable_proxy": False,
                    "criteria": [{**base, "proxy_strength": bad}]}
        assert not validate(response), bad


# SN-TL-02 -------------------------------------------------------------------

def test_SN_TL_02_5_1_2_1_every_ranked_figure_has_provenance(candidates, criteria, today):
    rank = impl("llm_compass", "rank")
    result = rank(candidates, criteria, today)
    assert result["ranked"]
    for entry in result["ranked"]:
        assert entry["evidence"], entry["model_id"]
        for fig in entry["evidence"]:
            assert fig.get("source_id"), entry["model_id"]
            assert fig.get("collection_date"), entry["model_id"]


# SN-TL-03 -------------------------------------------------------------------

def test_SN_TL_03_5_1_2_2_stale_after_90_days(today):
    is_stale = impl("llm_compass", "is_stale")
    assert is_stale((today - timedelta(days=91)).isoformat(), today) is True
    assert is_stale((today - timedelta(days=90)).isoformat(), today) is False
    assert is_stale(today.isoformat(), today) is False


# SN-TL-04 -------------------------------------------------------------------

def test_SN_TL_04_5_1_3_1_contribution_per_weighted_criterion(candidates, criteria, today):
    rank = impl("llm_compass", "rank")
    weighted = {c["criterion_id"] for c in criteria if c["designation"] == "weighted"}
    result = rank(candidates, criteria, today)
    for entry in result["ranked"]:
        assert set(entry["contributions"]) == weighted, entry["model_id"]


# SN-TL-05 -------------------------------------------------------------------

def _order(rank, candidates, criteria, today):
    return [e["model_id"] for e in rank(candidates, criteria, today)["ranked"]]


def test_SN_TL_05_5_1_4_1_unstable_pairs_match_brute_force(candidates, criteria, today):
    # Assumes relative +/-10% (w * 0.9, w * 1.1). See SPEC.md open question 7.
    rank = impl("llm_compass", "rank")
    unstable_pairs = impl("llm_compass", "unstable_pairs")

    base = _order(rank, candidates, criteria, today)
    expected = set()
    for i, c in enumerate(criteria):
        if c["designation"] != "weighted":
            continue
        for factor in (0.9, 1.1):
            varied = [dict(x) for x in criteria]
            varied[i]["weight"] = c["weight"] * factor
            order = _order(rank, candidates, varied, today)
            for a in base:
                for b in base:
                    if a < b and (base.index(a) < base.index(b)) != (order.index(a) < order.index(b)):
                        expected.add(frozenset((a, b)))

    assert set(unstable_pairs(candidates, criteria, today)) == expected


# SN-TL-06 -------------------------------------------------------------------

def test_SN_TL_06_5_1_3_3_stored_record_round_trips(sample_record):
    store = impl("llm_compass", "store_decision_record")
    retrieve = impl("llm_compass", "retrieve_decision_record")
    record_id = store(sample_record)
    assert retrieve(record_id) == sample_record


def test_SN_TL_06_5_1_5_1_unknown_record_is_not_found():
    retrieve = impl("llm_compass", "retrieve_decision_record")
    with pytest.raises(LookupError):
        retrieve("does-not-exist")


def test_SN_TL_06_5_1_5_2_rerun_uses_current_data(sample_record, candidates, today):
    store = impl("llm_compass", "store_decision_record")
    rerun = impl("llm_compass", "rerun_decision")
    record_id = store(sample_record)
    newer = candidates + [candidate("model-e", 0.05, 0.10, 2_000_000, 99.0, ["US"])]
    result = rerun(record_id, newer, today)
    assert result["ranked"][0]["model_id"] == "model-e"


def test_SN_TL_06_5_1_5_2_rerun_walkthrough_within_10_minutes():
    minutes = walkthrough_minutes("rerun")
    assert max(minutes) <= 10, minutes


# SN-TL-07 -------------------------------------------------------------------

def test_SN_TL_07_5_1_6_1_criterion_designation(criteria):
    validate = impl("llm_compass", "validate_criterion")
    for c in criteria:
        validate(c)
    weighted_without_weight = {k: v for k, v in criteria[0].items() if k != "weight"}
    with pytest.raises(ValueError):
        validate(weighted_without_weight)
    with pytest.raises(ValueError):
        validate({**criteria[0], "designation": "preferred"})


def test_SN_TL_07_5_1_6_2_hard_constraint_removes_top_scorer(candidates, criteria, today):
    rank = impl("llm_compass", "rank")
    result = rank(candidates, criteria, today)
    ranked_ids = [e["model_id"] for e in result["ranked"]]
    assert "model-a" not in ranked_ids
    assert ranked_ids  # the US-hosted models are still ranked


def test_SN_TL_07_5_1_6_3_exclusion_names_constraint(candidates, criteria, today):
    rank = impl("llm_compass", "rank")
    result = rank(candidates, criteria, today)
    excluded = {e["model_id"]: e for e in result["excluded"]}
    assert "residency" in excluded["model-a"]["failed_constraints"]
    for entry in result["excluded"]:
        assert entry["failed_constraints"], entry["model_id"]


# SN-TL-08 -------------------------------------------------------------------

def test_SN_TL_08_5_3_1_1_compares_at_least_10_candidates(criteria, today):
    rank = impl("llm_compass", "rank")
    many = [candidate(f"model-{i:02d}", 1.0 + i, 2.0 + i, 128_000, 70.0 + i, ["US"]) for i in range(10)]
    result = rank(many, criteria, today)
    assert len(result["ranked"]) + len(result["excluded"]) >= 10


def test_SN_TL_08_5_3_1_1_full_comparison_walkthrough_within_30_minutes():
    minutes = walkthrough_minutes("full_comparison")
    assert max(minutes) <= 30, minutes


# SN-TL-09 -------------------------------------------------------------------

def test_SN_TL_09_5_1_3_2_decision_record_has_all_sections(sample_record):
    generate = impl("llm_compass", "generate_decision_record")
    record = generate(sample_record)
    for section in ("requirements", "criteria_mapping", "weights", "evidence", "ranking", "sensitivity"):
        assert record.get(section), f"missing or empty: {section}"
    for fig in record["evidence"]:
        assert fig.get("source_id") and fig.get("collection_date")
