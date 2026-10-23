"""Tests for the system requirements (SPEC.md section 6), one per requirement.

These verify the 14 leaf system requirements 1.1.1-1.4.1 that the Innoslate
script generated from the IDEF0-A0 of F.1 (SRD section 3). Each test is derived
from the requirement's verification criterion and MOP target in SRD Table 9/10,
not from any module body, as the Lab Manual's tests/test_functional_requirements.py
does for the kiosk. Test names are test_SR_<id>_<what it checks>.

F.1 holds the decision in progress, so every test drives F.1 in UC.1 order and
starts each decision with request_interpretation (docs/PLAN.md, "Interface
details the tests rely on"). F.8 (LM Studio) is pending, so its responses are
built here in the SPEC section 3 shape. Demonstration requirements (1.3.1,
1.4.1) are checked from logged walkthroughs in docs/validation/walkthroughs.csv.
"""

import copy
import csv
from datetime import date, timedelta
from pathlib import Path

import pytest

from provide_benchmark_evidence import provide_model_data
from provide_llm_selection_decision_support import (
    present_criteria_mapping,
    present_ranking_and_sensitivity,
    record_decision,
    request_benchmark_evidence,
    request_interpretation,
)

WALKTHROUGHS = Path(__file__).resolve().parent.parent / "docs" / "validation" / "walkthroughs.csv"

# OpsCon 4.2 reference set, one stated requirement per line.
REFERENCE_REQUIREMENTS = [
    "Summarize technical documents of around twenty pages accurately.",
    "Stay under two hundred dollars a month at five thousand requests per day.",
    "Respond within a few seconds.",
    "Process data that may not leave the United States.",
]

# The whole OpsCon 4.2 description, used as one stated requirement for the ranking path.
OPSCON_TEXT = (
    "It must summarize documents of around twenty pages accurately, stay under two "
    "hundred dollars a month at five thousand requests per day, respond within a few "
    "seconds, and process data that may not leave the United States."
)

STRENGTHS = {"strong", "moderate", "weak"}

# SPEC section 2 candidate fields (field -> required).
CANDIDATE_FIELDS = {
    "model_id": True, "vendor": True, "model_name": True,
    "input_price": True, "output_price": True, "context_window": True,
    "latency_p50": False, "data_residency": False, "data_retention": False,
    "deprecation_date": False, "benchmarks": False,
}
FIGURE_FIELDS = [f for f in CANDIDATE_FIELDS if f not in ("model_id", "vendor", "model_name", "benchmarks")]


# Helpers ---------------------------------------------------------------------

def figure(value, unit, days_old=10, source="https://example.com/source"):
    # Dated relative to today: F.1 measures staleness against today's date.
    return {
        "value": value,
        "unit": unit,
        "source_id": source,
        "collection_date": (date.today() - timedelta(days=days_old)).isoformat(),
    }


def candidate(model_id, context, price, residency=("US",), days_old=10):
    return {
        "model_id": model_id,
        "vendor": f"vendor-{model_id}",
        "model_name": model_id,
        "input_price": figure(price, "USD per 1M input tokens", days_old),
        "output_price": figure(price * 4, "USD per 1M output tokens", days_old),
        "context_window": figure(context, "tokens", days_old),
        "data_residency": figure(list(residency), "ISO 3166-1 alpha-2", days_old),
    }


def proposed(criterion_id, metric, operator, threshold, unit, strength, category):
    """One SPEC section 3 proposed criterion."""
    return {
        "criterion_id": criterion_id,
        "metric": metric,
        "operator": operator,
        "threshold": threshold,
        "unit": unit,
        "proxy_strength": strength,
        "category": category,
        "rationale": f"{metric} stands in for the stated requirement.",
    }


def response(requirement_id, criteria, no_suitable_proxy=False):
    """One SPEC section 3 response."""
    return {"requirement_id": requirement_id, "no_suitable_proxy": no_suitable_proxy,
            "criteria": criteria}


# A valid SPEC section 3 proposal for each OpsCon 4.2 reference requirement.
REFERENCE_PROPOSALS = [
    [proposed("ctx", "context_window", ">=", 100_000, "tokens", "moderate", "capability")],
    [proposed("price", "input_price", "<=", 5.0, "USD per 1M input tokens", "moderate", "cost"),
     proposed("out_price", "output_price", "<=", 15.0, "USD per 1M output tokens", "weak", "cost")],
    [proposed("latency", "latency_p50", "<=", 3.0, "seconds", "strong", "other")],
    [proposed("residency", "data_residency", "in", ["US"], "ISO 3166-1 alpha-2", "strong", "compliance")],
]


def confirmed_criteria():
    """The Technical Lead's confirmed mapping (UC.1.9) for the ranking fixture."""
    return [
        {**proposed("ctx", "context_window", ">=", 100_000, "tokens", "strong", "capability"),
         "designation": "weighted", "weight": 0.52},
        {**proposed("price", "input_price", "<=", 5.0, "USD per 1M input tokens", "moderate", "cost"),
         "designation": "weighted", "weight": 0.48},
        {**proposed("residency", "data_residency", "in", ["US"], "ISO 3166-1 alpha-2", "strong", "compliance"),
         "designation": "hard"},
    ]


def known_answer_candidates():
    # Known-answer fixture for 1.2.5. All three pass the hard residency constraint.
    # Min-max normalisation across the three (docs/PLAN.md "Rules and assumptions"):
    #   context_window (>=, higher better): 200k -> 1.0, 150k -> 0.5, 100k -> 0.0
    #   input_price    (<=, lower better):  1.0  -> 1.0,             3.0  -> 0.0
    #   model-1: ctx 1.0, price 0.0 -> 0.52*1.0 + 0.48*0.0 = 0.52
    #   model-2: ctx 0.0, price 1.0 -> 0.52*0.0 + 0.48*1.0 = 0.48
    #   model-3: ctx 0.5, price 0.0 -> 0.52*0.5 + 0.48*0.0 = 0.26
    # Base ranking: model-1, model-2, model-3.
    return [
        candidate("model-1", 200_000, 3.0),
        candidate("model-2", 100_000, 1.0),
        candidate("model-3", 150_000, 3.0),
    ]


# Each weight x0.9 and x1.1, one at a time, no renormalisation (PLAN, SPEC section 5 Q5):
#   ctx   x0.9 = 0.468: model-1 0.468 < model-2 0.480 -> model-1/model-2 flips
#   ctx   x1.1 = 0.572: model-1 0.572 > model-2 0.480 -> no flip
#   price x0.9 = 0.432: model-1 0.520 > model-2 0.432 -> no flip
#   price x1.1 = 0.528: model-2 0.528 > model-1 0.520 -> model-1/model-2 flips
#   model-3 ranges 0.234-0.286, below model-2's lowest (0.432): never flips.
KNOWN_UNSTABLE_PAIRS = {frozenset({"model-1", "model-2"})}


def start_decision(text, criteria):
    """UC.1.2-1.6: state the requirement, then present a valid proposal of `criteria`."""
    request = request_interpretation(text)
    proposal = [{k: v for k, v in c.items() if k not in ("designation", "weight")} for c in criteria]
    presented = present_criteria_mapping(response(request["requirement_id"], proposal))
    return request, presented


def rank_fixture(candidates, criteria):
    """UC.1.2-1.16 on `candidates`, with `criteria` as the confirmed mapping."""
    start_decision(OPSCON_TEXT, criteria)
    request_benchmark_evidence(confirmed_criteria_mapping=criteria)
    return present_ranking_and_sensitivity(candidates, confirmed_criteria_mapping=criteria)


def walkthrough_minutes(scenario):
    if not WALKTHROUGHS.exists():
        pytest.fail(f"no timed walkthroughs logged yet: {WALKTHROUGHS}")
    with WALKTHROUGHS.open() as f:
        minutes = [float(r["minutes"]) for r in csv.DictReader(f) if r["scenario"] == scenario]
    if not minutes:
        pytest.fail(f"no '{scenario}' walkthrough logged in {WALKTHROUGHS.name}")
    return minutes


def assert_figure(fig, where):
    assert isinstance(fig, dict), where
    assert set(fig) >= {"value", "unit", "source_id", "collection_date"}, where
    assert isinstance(fig["value"], (int, float, str, list)), where
    assert isinstance(fig["unit"], str), where
    assert isinstance(fig["source_id"], str) and fig["source_id"], where
    date.fromisoformat(fig["collection_date"])
    if "stale" in fig:
        assert isinstance(fig["stale"], bool), where


# 1.1 Input requirements ---------------------------------------------------------

def test_SR_1_1_1_accepts_designated_criteria_rejects_weighted_without_weight():
    # "Every criterion in a submitted mapping is accepted with its hard or weighted designation. A weighted criterion without a weight is rejected."
    criteria = confirmed_criteria()
    start_decision(OPSCON_TEXT, criteria)
    submitted = copy.deepcopy(criteria)
    data_request = request_benchmark_evidence(confirmed_criteria_mapping=submitted)
    assert submitted == criteria, "the mapping's designations and weights must be kept as submitted"
    assert {c["metric"] for c in criteria} <= set(data_request["metrics"])

    weighted = criteria[0]
    no_weight = {k: v for k, v in weighted.items() if k != "weight"}
    for bad in (no_weight, {**weighted, "weight": None}, {**weighted, "designation": "preferred"}):
        start_decision(OPSCON_TEXT, criteria)
        with pytest.raises(ValueError):
            request_benchmark_evidence(confirmed_criteria_mapping=[bad] + criteria[1:])


def test_SR_1_1_2_figures_stored_with_source_and_date_unsourced_rejected():
    # "Every figure received is stored with a non-null source and collection date. A figure missing either one is rejected when it is entered."
    criteria = confirmed_criteria()
    candidates = known_answer_candidates()
    result = rank_fixture(copy.deepcopy(candidates), criteria)
    stored = {(e["model_id"], e["metric"]): e for e in result["evidence"]}
    for cand in candidates:
        for metric in {c["metric"] for c in criteria}:
            entry = stored.get((cand["model_id"], metric))
            assert entry is not None, f"not stored: {cand['model_id']} {metric}"
            assert entry["source_id"] == cand[metric]["source_id"]
            assert entry["collection_date"] == cand[metric]["collection_date"]

    for field in ("source_id", "collection_date"):
        for missing in ("absent", None):
            bad = copy.deepcopy(candidates)
            if missing == "absent":
                del bad[1]["context_window"][field]
            else:
                bad[1]["context_window"][field] = None
            with pytest.raises(ValueError):
                rank_fixture(bad, criteria)


@pytest.mark.parametrize("pick", [0, 1, 2])
def test_SR_1_1_3_selection_appears_unchanged_in_record(pick):
    # "The candidate the Technical Lead selects appears unchanged in the decision record."
    criteria = confirmed_criteria()
    result = rank_fixture(known_answer_candidates(), criteria)
    selection = result["ranking"][pick]
    record = record_decision(selection, confirmed_criteria_mapping=criteria)
    assert record["selected_model"] == selection


@pytest.mark.parametrize("kind", ["valid", "no_proxy", "neither", "unknown_metric",
                                  "bad_proxy_strength", "missing_proxy_strength"])
@pytest.mark.parametrize("i", range(len(REFERENCE_REQUIREMENTS)))
def test_SR_1_1_4_reference_responses_accepted_or_retried_then_flagged(i, kind):
    # "For each requirement in the reference set, a response is accepted only if it has at least one criterion or reports no suitable proxy, uses known metrics, and rates every criterion's proxy strength. An invalid response is retried once, then marked as an interpretation failure."
    text = REFERENCE_REQUIREMENTS[i]
    request = request_interpretation(text)
    rid = request["requirement_id"]
    good = copy.deepcopy(REFERENCE_PROPOSALS[i])

    if kind in ("valid", "no_proxy"):
        reply = response(rid, good) if kind == "valid" else response(rid, [], no_suitable_proxy=True)
        presented = present_criteria_mapping(reply)
        assert presented["status"] == "proposed"
        assert presented["requirement_id"] == rid
        assert presented["no_suitable_proxy"] is (kind == "no_proxy")
        expected = [c["metric"] for c in reply["criteria"]]
        assert [c["metric"] for c in presented["criteria"]] == expected
        return

    if kind == "neither":
        reply = response(rid, [])
    elif kind == "unknown_metric":
        reply = response(rid, [{**good[0], "metric": "summarization_vibes"}])
    elif kind == "bad_proxy_strength":
        reply = response(rid, [{**good[0], "proxy_strength": "high"}])
    else:
        reply = response(rid, [{k: v for k, v in good[0].items() if k != "proxy_strength"}])

    first = present_criteria_mapping(copy.deepcopy(reply))
    assert first["status"] == "retry"
    second = present_criteria_mapping(copy.deepcopy(reply))
    assert second["status"] == "interpretation_failed"
    assert second["criteria"] == []
    # Not dropped: the requirement stays, for the Technical Lead to map by hand.
    assert second["requirement_id"] == rid
    assert second["requirement"] == text


@pytest.mark.parametrize("text,accepted", [
    *[(t, True) for t in REFERENCE_REQUIREMENTS],
    ("Stay under $200/month  at 5,000 req/day;\nkeep data in the US.", True),
    ("", False),
    ("   ", False),
    ("\n\t", False),
])
def test_SR_1_1_5_text_gets_id_without_reformatting_empty_rejected(text, accepted):
    # "Non-empty plain-language text is accepted and given an ID without reformatting. Empty input is rejected."
    if not accepted:
        with pytest.raises(ValueError):
            request_interpretation(text)
        return
    request = request_interpretation(text)
    assert isinstance(request["requirement_id"], str) and request["requirement_id"]
    assert request["text"] == text


# 1.2 Output requirements --------------------------------------------------------

def test_SR_1_2_1_data_request_issued_for_every_candidate_in_catalog_of_10():
    # "In a catalog of at least 10 candidates, a data request is issued for every candidate."
    criteria = confirmed_criteria()
    start_decision(OPSCON_TEXT, criteria)
    data_request = request_benchmark_evidence(confirmed_criteria_mapping=criteria)
    catalog = provide_model_data(data_request=data_request)
    ids = [c["model_id"] for c in catalog]
    assert len(set(ids)) >= 10, f"catalog has {len(set(ids))} candidates, needs at least 10"
    requested = data_request["models"]
    assert requested == "all" or set(ids) <= set(requested), "not every candidate is requested"


@pytest.mark.parametrize("pick", [0, 1, 2])
def test_SR_1_2_2_record_has_seven_sections_and_sourced_evidence(pick):
    # "Every completed selection produces a record with all six sections filled in (requirements, mapping, weights, evidence, ranking, sensitivity, selection), and every evidence item has a source and date."
    # The criterion says six but lists seven, and the MOP says 7 of 7: the seven listed are checked.
    criteria = confirmed_criteria()
    result = rank_fixture(known_answer_candidates(), criteria)
    record = record_decision(result["ranking"][pick], confirmed_criteria_mapping=criteria)
    for section in ("requirements", "criteria_mapping", "weights", "evidence", "ranking",
                    "sensitivity", "selected_model"):
        assert record.get(section), f"missing or empty: {section}"
    for item in record["evidence"]:
        assert item.get("source_id") and item.get("collection_date"), item


def test_SR_1_2_3_one_request_per_requirement_with_id_and_unaltered_text():
    # "Exactly one interpretation request is issued for each stated requirement, carrying its ID and unaltered text."
    requests = [request_interpretation(text) for text in REFERENCE_REQUIREMENTS]
    for text, request in zip(REFERENCE_REQUIREMENTS, requests):
        assert isinstance(request, dict), "one request (a dict) per stated requirement"
        assert set(request) == {"requirement_id", "text"}
        assert isinstance(request["requirement_id"], str) and request["requirement_id"]
        assert request["text"] == text
    ids = [r["requirement_id"] for r in requests]
    assert len(set(ids)) == len(ids), "each stated requirement carries its own ID"


@pytest.mark.parametrize("i", range(len(REFERENCE_REQUIREMENTS)))
def test_SR_1_2_4_presented_criterion_shows_requirement_and_strength(i):
    # "Every presented criterion shows the requirement it stands for and a rating of strong, moderate or weak."
    text = REFERENCE_REQUIREMENTS[i]
    request = request_interpretation(text)
    proposal = copy.deepcopy(REFERENCE_PROPOSALS[i])
    presented = present_criteria_mapping(response(request["requirement_id"], proposal))
    assert len(presented["criteria"]) == len(proposal)
    for shown, sent in zip(presented["criteria"], proposal):
        assert shown["requirement"] == text, shown
        assert shown["proxy_strength"] in STRENGTHS, shown
        assert shown["proxy_strength"] == sent["proxy_strength"], shown


def test_SR_1_2_5_contributions_and_unstable_pairs_match_known_answer():
    # "Each ranked candidate shows one contribution entry per weighted criterion. On a fixture with a known answer, the reported unstable pairs exactly match those found by changing each weight by -10% and +10%, one at a time."
    criteria = confirmed_criteria()
    weighted = {c["criterion_id"] for c in criteria if c["designation"] == "weighted"}
    result = rank_fixture(known_answer_candidates(), criteria)

    assert result["ranking"] == ["model-1", "model-2", "model-3"]  # the fixture's known base order
    breakdown = {e["model_id"]: e for e in result["score_breakdown"]}
    assert set(breakdown) == set(result["ranking"])
    for model_id, entry in breakdown.items():
        assert set(entry["contributions"]) == weighted, model_id

    reported = {frozenset(pair) for pair in result["unstable_pairs"]}
    assert reported == KNOWN_UNSTABLE_PAIRS


# 1.3 Interface requirements -----------------------------------------------------

def test_SR_1_3_1_uc1_walkthrough_through_interface_logged():
    # "The Technical Lead completes UC.1, from stated requirements to decision record, entirely through the system's interface." (6 of 6 exchanges)
    # A logged 'full_comparison' walkthrough is the record that UC.1 was completed
    # through the web interface. The CSV has no column for the exchanges completed.
    minutes = walkthrough_minutes("full_comparison")
    assert minutes


@pytest.mark.parametrize("invalid", ["not json", "missing_criteria", "bad_operator"])
def test_SR_1_3_2_model_contract_conformance_and_timeout_as_invalid(invalid):
    # "Every request and response conforms to the language model runtime's model contract, and a timeout is handled the same way as an invalid response."
    text = REFERENCE_REQUIREMENTS[0]
    good = copy.deepcopy(REFERENCE_PROPOSALS[0])

    def bad_reply(rid):
        if invalid == "not json":
            return "not json"
        if invalid == "missing_criteria":
            return {"requirement_id": rid, "no_suitable_proxy": False}
        return response(rid, [{**good[0], "operator": "~="}])

    # The request conforms: exactly requirement_id and text (SPEC section 3).
    request = request_interpretation(text)
    assert set(request) == {"requirement_id", "text"}
    assert isinstance(request["requirement_id"], str) and request["text"] == text
    # A conforming response is accepted.
    assert present_criteria_mapping(response(request["requirement_id"], good))["status"] == "proposed"

    # A timeout (None) and a non-conforming response are handled the same way,
    # in either order: retried once, then marked as an interpretation failure.
    for first_is_timeout in (False, True):
        for second_is_timeout in (False, True):
            rid = request_interpretation(text)["requirement_id"]
            first = present_criteria_mapping(None if first_is_timeout else bad_reply(rid))
            assert first["status"] == "retry", (first_is_timeout, second_is_timeout)
            second = present_criteria_mapping(None if second_is_timeout else bad_reply(rid))
            assert second["status"] == "interpretation_failed", (first_is_timeout, second_is_timeout)
            assert second["criteria"] == []


def test_SR_1_3_3_data_contract_and_stored_figures_shown_dated_and_flagged():
    # "Every data exchange conforms to the data contract. If the source is unavailable, the ranking uses the last stored figures, each shown with its date and staleness flag."
    criteria = confirmed_criteria()
    start_decision(OPSCON_TEXT, criteria)
    data_request = request_benchmark_evidence(confirmed_criteria_mapping=criteria)
    catalog = provide_model_data(data_request=data_request)
    assert catalog, "no model data available"
    benchmark_ids = set()
    for cand in catalog:
        for field, required in CANDIDATE_FIELDS.items():
            if required:
                assert field in cand, f"{cand.get('model_id')}: missing {field}"
        for field in ("model_id", "vendor", "model_name"):
            assert isinstance(cand[field], str) and cand[field]
        for field in FIGURE_FIELDS:
            if field in cand:
                assert_figure(cand[field], f"{cand['model_id']}.{field}")
        for bench in cand.get("benchmarks", []):
            assert isinstance(bench["benchmark_id"], str) and bench["benchmark_id"]
            assert_figure(bench["score"], f"{cand['model_id']}.{bench['benchmark_id']}")
            benchmark_ids.add(bench["benchmark_id"])
    known_metrics = set(FIGURE_FIELDS) | benchmark_ids
    assert set(data_request["metrics"]) <= known_metrics

    # Last stored figures: model-2's were collected 120 days ago, the others 10 days ago.
    stored = known_answer_candidates()
    stored[1] = candidate("model-2", 100_000, 1.0, days_old=120)
    result = present_ranking_and_sensitivity(stored, confirmed_criteria_mapping=criteria)
    assert "model-2" in result["ranking"], "the stale stored figures must still be used"
    used = {c["metric"] for c in criteria}
    by_key = {(e["model_id"], e["metric"]): e for e in result["evidence"]}
    for cand in stored:
        for metric in used:
            entry = by_key[(cand["model_id"], metric)]
            assert entry["collection_date"] == cand[metric]["collection_date"]
            assert entry["stale"] is (cand["model_id"] == "model-2"), entry


# 1.4 Functional requirement ----------------------------------------------------

def test_SR_1_4_1_full_comparison_walkthrough_within_30_minutes():
    # "All leaf-level requirements pass, and a timed walkthrough of UC.1 with at least 10 candidates takes 30 minutes or less."
    minutes = walkthrough_minutes("full_comparison")
    assert max(minutes) <= 30, minutes
    # The walkthrough runs on the stored catalog, so it can only have had 10
    # candidates if the catalog has at least 10.
    criteria = confirmed_criteria()
    start_decision(OPSCON_TEXT, criteria)
    catalog = provide_model_data(data_request=request_benchmark_evidence(confirmed_criteria_mapping=criteria))
    assert len({c["model_id"] for c in catalog}) >= 10
