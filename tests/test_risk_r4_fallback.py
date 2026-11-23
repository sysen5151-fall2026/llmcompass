"""R4 fallback: models named in the stated requirements but not in the catalog (Lab Manual 12.3).

Top risk R4 Candidate catalog incomplete (docs/risks.md; report Sections 4.3 and 4.5). The
fallback is SR 1.4.1.8 (Innoslate, 2026-11-22; satisfied by R4.M1, traces to StR 5.1.6.3),
built in F.1.2 (ADR-0010). The rules are fixed by contracts/api-v1.yaml checkRequestedModels
and A34-A37.

Tests T1-T8 are report Table 21, one per row. Following Lab Manual 12.3.3, the inputs in the
adversarial tests were generated to defeat the check:
- the same name written with different case, spacing, hyphens and dots
- a catalog name that is a prefix of a missing one ("GPT-6" in "GPT-6.2 Sol")
- a missing model inside a hard-constraint sentence
- ordinary numbers that look like versions ("within 3 seconds")
Most of them test the failure path, not only the normal path. The last tests cover the
known-models list and catalog gap that F.7 stores at refresh (SPEC section 2, Known models)
and the result-page box (UC.1.15).
"""

import copy
import importlib
from datetime import date, timedelta

import pytest

F1 = "provide_llm_selection_decision_support"


def _module(name):
    return importlib.import_module(f"{F1}.{name}")


def check_requested_models(*args, **kwargs):
    fn = getattr(_module("retrieve_model_data"), "check_requested_models", None)
    if fn is None:
        pytest.fail("not implemented: retrieve_model_data.check_requested_models")
    return fn(*args, **kwargs)


# --- fixture: a 5-model catalog and a known-models list that holds it plus 5 others ---

def _figure(value, unit):
    return {"value": value, "unit": unit, "source_id": "https://example.com/source",
            "collection_date": (date.today() - timedelta(days=5)).isoformat()}


def _candidate(model_id, vendor, name, intelligence, price, residency):
    return {"model_id": model_id, "vendor": vendor, "model_name": name,
            "input_price": _figure(price, "USD per 1M input tokens"),
            "output_price": _figure(price * 4, "USD per 1M output tokens"),
            "context_window": _figure(200_000, "tokens"),
            "data_residency": _figure(residency, "ISO 3166-1 alpha-2"),
            "benchmarks": [{"benchmark_id": "intelligence_index", "score": _figure(intelligence, "index")}]}


CATALOG = [
    _candidate("gpt-6-astra", "OpenAI", "GPT-6 Astra", 70, 3.0, ["US"]),
    _candidate("gpt-oss-120b", "OpenAI", "gpt-oss-120B (high)", 50, 0.2, ["US"]),
    _candidate("claude-sonnet-5-5", "Anthropic", "Claude Sonnet 5.5", 68, 3.0, ["US"]),
    _candidate("gemini-4-argon", "Google", "Gemini 4 Argon", 72, 2.0, ["EU"]),
    _candidate("mistral-large-4", "Mistral", "Mistral Large 4", 45, 1.0, ["EU"]),
]


def _known(name, slug, vendor, intelligence):
    return {"name": name, "slug": slug, "vendor": vendor, "intelligence_index": intelligence}


KNOWN_MODELS = [
    _known("GPT-6 Astra", "gpt-6-astra", "OpenAI", 70),
    _known("gpt-oss-120B (high)", "gpt-oss-120b", "OpenAI", 50),
    _known("Claude Sonnet 5.5", "claude-sonnet-5-5", "Anthropic", 68),
    _known("Gemini 4 Argon", "gemini-4-argon", "Google", 72),
    _known("Mistral Large 4", "mistral-large-4", "Mistral", 45),
    _known("GPT-6.2 Sol", "gpt-6-2-sol", "OpenAI", 75),
    _known("Claude Opus 5.5 (Reasoning)", "claude-opus-5-5", "Anthropic", 74),
    _known("Gemini 4 Neon", "gemini-4-neon", "Google", 60),
    _known("Grok 6", "grok-6", "xAI", 66),
    _known("Grok 5", "grok-5", "xAI", 60),
]

RESIDENCY_US = {"criterion_id": "R1-residency", "metric": "data_residency", "operator": "in", "threshold": ["US"],
                "unit": "ISO 3166-1 alpha-2", "proxy_strength": "strong", "category": "compliance",
                "rationale": "Data may not leave the US.", "designation": "hard"}
PRICE = {"criterion_id": "R1-price", "metric": "input_price", "operator": "<=", "threshold": 5.0,
         "unit": "USD per 1M input tokens", "proxy_strength": "moderate", "category": "cost",
         "rationale": "Cost.", "designation": "weighted", "weight": 1.0}


def _report(text, known=KNOWN_MODELS):
    evidence = _module("retrieve_model_data").receive_model_data(copy.deepcopy(CATALOG))
    return check_requested_models([text], evidence, known_models=copy.deepcopy(known))


def _entries(report):
    return report["requested_not_compared"]


def _run_f12_to_f17(text, known=KNOWN_MODELS, hard=(RESIDENCY_US,)):
    """F.1.2 -> F.1.7 on the fixture, with the R4 check between F.1.2 and F.1.3 (UC.1.11 -> UC.1.12)."""
    evidence = _module("retrieve_model_data").receive_model_data(copy.deepcopy(CATALOG))
    report = check_requested_models([text], evidence, known_models=copy.deepcopy(known))
    eligible, exclusions = _module("apply_hard_constraints").apply_hard_constraints(
        evidence, hard_constraints=list(hard))
    ranking = _module("score_and_rank_candidates").score_and_rank_candidates(eligible, weighted_criteria=[PRICE])
    finding = _module("analyze_ranking_sensitivity").analyze_ranking_sensitivity(ranking, weighted_criteria=[PRICE])
    presented, rationale = _module("report_selection_rationale").report_selection_rationale(
        ranking, exclusions, finding, report)
    basis = {"requirements": [text], "criteria_mapping": [RESIDENCY_US, PRICE], "weights": {"R1-price": 1.0}}
    record = _module("generate_and_store_decision_record").generate_and_store_decision_record(
        rationale, None, basis)
    return {"report": report, "exclusions": exclusions, "presented": presented, "record": record}


# --- Table 21 ---

def test_T1_model_in_index_not_in_catalog_is_flagged_with_alternatives_in_page_and_record():
    # Failure path: the named model would have dropped out of the ranking silently (R4).
    out = _run_f12_to_f17("We are evaluating GPT-6.2 Sol for summarising contracts.")
    expected = [{"name_as_written": "GPT-6.2 Sol", "reason": "not_in_catalog", "known_model": "GPT-6.2 Sol",
                 "suggestions": ["GPT-6 Astra", "gpt-oss-120B (high)"]}]  # same vendor, highest index first
    assert out["report"] == {"catalog_check": "ran", "requested_not_compared": expected}
    assert out["presented"]["requested_models"] == out["report"]  # the box above the ranking (UC.1.15)
    assert out["record"]["requested_models"] == out["report"]  # the decision record (UC.1.18, StR 5.1.6.3)


def test_T2_only_catalog_models_named_nothing_flagged_and_ranking_unchanged():
    # Normal path: catalog models, by display name and by model_id.
    text = "Compare GPT-6 Astra, claude-sonnet-5-5 and Gemini 4 Argon."
    out = _run_f12_to_f17(text)
    assert out["report"] == {"catalog_check": "ran", "requested_not_compared": []}
    without = _run_f12_to_f17("Compare the models.")
    assert out["presented"]["ranking"] == without["presented"]["ranking"]
    assert out["presented"]["excluded"] == without["presented"]["excluded"]


@pytest.mark.parametrize("written", ["gpt 6.2 sol", "GPT-6-2-SOL", "Gpt6.2Sol", "gpt_6_2 Sol", "GPT 6 2 Sol"])
def test_T3_same_missing_model_in_any_case_spacing_or_hyphens_is_flagged(written):
    # Adversarial: spelling variants must neither be missed nor fall back to the catalog's GPT-6 Astra.
    entries = _entries(_report(f"Must we use {written}?"))
    assert [(e["known_model"], e["reason"]) for e in entries] == [("GPT-6.2 Sol", "not_in_catalog")]
    assert entries[0]["name_as_written"].casefold().replace("?", "") == written.casefold()


def test_T3_same_missing_model_named_several_ways_is_flagged_once():
    entries = _entries(_report("GPT-6.2 Sol is preferred; if gpt-6-2-sol is too slow, GPT 6.2 SOL with caching."))
    assert [e["known_model"] for e in entries] == ["GPT-6.2 Sol"]


def test_T4_one_catalog_and_one_missing_model_only_the_missing_one_is_flagged():
    entries = _entries(_report("Shortlist: GPT-6 Astra and Claude Opus 5.5."))
    assert entries == [{"name_as_written": "Claude Opus 5.5", "reason": "not_in_catalog",
                        "known_model": "Claude Opus 5.5 (Reasoning)", "suggestions": ["Claude Sonnet 5.5"]}]


def test_T4_catalog_name_that_prefixes_a_missing_name_does_not_hide_it():
    # Adversarial: "GPT-6" (catalog GPT-6 Astra's family) is a prefix of "GPT-6.2 Sol".
    entries = _entries(_report("Either GPT-6 Astra or GPT-6.2 Sol."))
    assert [e["known_model"] for e in entries] == ["GPT-6.2 Sol"]


def test_T5_model_in_neither_catalog_nor_index_is_flagged_not_recognised():
    entries = _entries(_report("The team wants Gemini 9 Ultra for long documents."))
    assert entries == [{"name_as_written": "Gemini 9 Ultra", "reason": "not_recognised", "known_model": None,
                        "suggestions": ["Gemini 4 Argon"]}]  # same vendor as the Gemini family


def test_T5_numbers_in_ordinary_requirements_are_not_flagged():
    # Adversarial: version-like numbers with no model family word are not models.
    text = "Respond within 3 seconds, handle 20 pages, cost under 200 dollars at 5000 requests per day."
    assert _report(text) == {"catalog_check": "ran", "requested_not_compared": []}


def test_T6_no_known_models_list_states_the_check_could_not_run():
    # Failure path: no refresh has stored the list, so nothing may pass silently.
    out = _run_f12_to_f17("We are evaluating GPT-6.2 Sol.", known=None)
    could_not_run = {"catalog_check": "could_not_run", "requested_not_compared": []}
    assert out["report"] == could_not_run
    assert out["presented"]["requested_models"] == could_not_run
    assert out["record"]["requested_models"] == could_not_run


def test_T6_rationale_built_without_a_report_says_could_not_run():
    # A37: F.1.6 never presents an unchecked result as checked.
    report = _module("report_selection_rationale").report_selection_rationale
    presented, rationale = report([], [], {"method": "x", "ranking_is_stable": None, "unstable_pairs": []})
    assert presented["requested_models"]["catalog_check"] == "could_not_run"
    assert rationale["requested_models"] == presented["requested_models"]


def test_T7_missing_model_inside_a_hard_constraint_sentence_is_flagged_and_constraint_still_applies():
    text = "Data may not leave the United States, so Grok 6 is acceptable only if hosted in the US."
    out = _run_f12_to_f17(text)
    # xAI has no catalog model: the catalog models nearest Grok 6's index of 66
    assert _entries(out["report"]) == [{"name_as_written": "Grok 6", "reason": "not_in_catalog",
                                        "known_model": "Grok 6",
                                        "suggestions": ["Claude Sonnet 5.5", "GPT-6 Astra", "Gemini 4 Argon"]}]
    excluded = {e["model_id"]: e["failed_constraints"] for e in out["exclusions"]}
    assert excluded == {"gemini-4-argon": ["R1-residency"], "mistral-large-4": ["R1-residency"]}
    assert out["exclusions"] == _run_f12_to_f17("Data may not leave the United States.")["exclusions"]


def test_T8_reopened_decision_record_still_lists_the_missing_models():
    out = _run_f12_to_f17("Compare Claude Opus 5.5 with what we have.")
    store = importlib.reload(_module("generate_and_store_decision_record"))  # a restart (SR 1.4.1.7)
    reopened = store.retrieve_decision_record(out["record"]["record_id"])
    assert reopened["requested_models"] == out["report"]
    assert [e["known_model"] for e in _entries(reopened["requested_models"])] == ["Claude Opus 5.5 (Reasoning)"]


# --- step 1 of the fallback: F.7 stores the known-models list and reports the catalog gap ---

def test_refresh_stores_every_listed_model_as_known_models_and_reports_catalog_gap(tmp_path, monkeypatch):
    f7 = importlib.import_module("provide_benchmark_evidence")
    monkeypatch.setenv("BENCHMARK_SNAPSHOT_DB", str(tmp_path / "s.sqlite3"))
    catalog_ids = {e["artificial_analysis_id"] for e in f7._catalog_entries()}
    listed = [{"id": aa_id, "name": f"Catalog {i}", "slug": f"catalog-{i}", "model_creator": {"name": "V"},
               "evaluations": {"artificial_analysis_intelligence_index": 10 + i}}
              for i, aa_id in enumerate(sorted(catalog_ids))]
    listed += [{"id": "new-1", "name": "Frontier 9", "slug": "frontier-9", "model_creator": {"name": "X"},
                "evaluations": {"artificial_analysis_intelligence_index": 99}},
               {"id": "new-2", "name": "Small 1", "slug": "small-1", "model_creator": {"name": "X"},
                "evaluations": {"artificial_analysis_intelligence_index": None}}]
    known, gap = f7._known_models_from({r["id"]: r for r in listed})
    assert {k["name"] for k in known} == {r["name"] for r in listed}
    assert next(k for k in known if k["name"] == "Small 1") == {
        "name": "Small 1", "slug": "small-1", "vendor": "X", "intelligence_index": None}
    assert gap == ["Frontier 9"]  # the only top-20 model not in the catalog (Table 18 indicator)

    conn = f7._connect()
    try:
        f7._insert_pull(conn, "ok", {"catalog_gap": gap}, [], "2026-11-22T00:00:00+00:00", known_models=known)
    finally:
        conn.close()
    assert f7.provide_known_models() == known


def test_no_stored_known_models_list_is_none(tmp_path, monkeypatch):
    f7 = importlib.import_module("provide_benchmark_evidence")
    monkeypatch.setenv("BENCHMARK_SNAPSHOT_DB", str(tmp_path / "empty.sqlite3"))
    assert f7.provide_known_models() is None


# --- UC.1.15: the result page box ---

def test_result_page_shows_requested_but_not_compared_box():
    pytest.importorskip("flask")
    from app import app

    report = {"catalog_check": "ran", "requested_not_compared": [
        {"name_as_written": "GPT-6.2 Sol", "reason": "not_in_catalog", "known_model": "GPT-6.2 Sol",
         "suggestions": ["GPT-6 Astra"]}]}
    presented = {"ranking": [], "score_breakdown": [], "excluded": [], "evidence": [], "unstable_pairs": [],
                 "sensitivity": {"method": "x", "ranking_is_stable": None, "unstable_pairs": []},
                 "requested_models": report}
    with app.test_request_context():
        from flask import render_template
        page = render_template("result.html", requirement_set=[], confirmed=[], presented=presented,
                               record=None, record_error=None)
        assert "Requested but not compared" in page
        assert "GPT-6.2 Sol" in page and "GPT-6 Astra" in page
        presented["requested_models"] = {"catalog_check": "could_not_run", "requested_not_compared": []}
        page = render_template("result.html", requirement_set=[], confirmed=[], presented=presented,
                               record=None, record_error=None)
        assert "catalog check could not run" in page
