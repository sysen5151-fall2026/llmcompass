"""Acceptance tests for the Product Owner needs (SN-PO-01 to SN-PO-07). See SPEC.md section 1."""

import json

import pytest

from conftest import impl

DATA_CONTRACT_FIELDS = [
    "model_id", "input_price", "output_price", "context_window", "latency_p50",
    "data_residency", "data_retention", "deprecation_date", "benchmark_id",
]


def monthly_cost_formula(c, requests_per_day, input_tokens, output_tokens):
    return requests_per_day * 30 * (
        input_tokens * c["input_price"]["value"] + output_tokens * c["output_price"]["value"]
    ) / 1_000_000


# SN-PO-01 / SN-PO-07 --------------------------------------------------------

def test_SN_PO_01_5_2_2_1_summaries_have_no_technical_terms(candidates, criteria, today):
    rank = impl("llm_compass", "rank")
    summaries = impl("llm_compass", "tradeoff_summaries")
    result = rank(candidates, criteria, today)
    out = summaries(result)

    top3 = [e["model_id"] for e in result["ranked"][:3]]
    assert set(out) == set(top3)

    text = json.dumps(out).lower()
    banned = DATA_CONTRACT_FIELDS + [
        b["benchmark_id"] for c in candidates for b in c["benchmarks"]
    ]
    for term in banned:
        assert term.lower() not in text, term


# SN-PO-02 -------------------------------------------------------------------

@pytest.mark.parametrize("requests_per_day", [100, 10_000])
def test_SN_PO_02_5_2_1_1_monthly_cost_across_volumes(candidates, usage, requests_per_day):
    monthly_cost = impl("llm_compass", "monthly_cost")
    for c in candidates:
        got = monthly_cost(c, requests_per_day, usage["input_tokens"], usage["output_tokens"])
        want = monthly_cost_formula(c, requests_per_day, usage["input_tokens"], usage["output_tokens"])
        assert got == pytest.approx(want, abs=0.01), c["model_id"]


# SN-PO-03 -------------------------------------------------------------------

def test_SN_PO_03_5_2_2_1_states_gains_and_losses(candidates, criteria, today):
    rank = impl("llm_compass", "rank")
    summaries = impl("llm_compass", "tradeoff_summaries")
    result = rank(candidates, criteria, today)
    out = summaries(result)

    top3 = [e["model_id"] for e in result["ranked"][:3]]
    for model in top3:
        for other in top3:
            if other == model:
                continue
            comparison = out[model][other]
            assert comparison["gains"], (model, other)
            assert comparison["gives_up"], (model, other)


# SN-PO-04 -------------------------------------------------------------------

def test_SN_PO_04_5_2_3_1_risk_fields_reported(candidates):
    risk_report = impl("llm_compass", "risk_report")
    for c in candidates:
        report = risk_report(c)
        for field in ("vendor_dependence", "switching_cost", "deprecation_risk"):
            assert report.get(field) is not None, (c["model_id"], field)


# SN-PO-06 -------------------------------------------------------------------

def test_SN_PO_06_5_2_4_1_flags_over_capability_with_premium(candidates, criteria, usage, today):
    rank = impl("llm_compass", "rank")
    over_capability = impl("llm_compass", "over_capability")
    monthly_cost = impl("llm_compass", "monthly_cost")

    # model-b exceeds every capability threshold (ctx >= 100k, lcqa >= 70).
    # model-c meets them exactly and is cheaper. model-a is excluded.
    result = rank(candidates, criteria, today)
    flagged = over_capability(result, candidates, criteria, usage)

    by_id = {c["model_id"]: c for c in candidates}

    def cost(model_id):
        return monthly_cost(by_id[model_id], usage["requests_per_day"],
                            usage["input_tokens"], usage["output_tokens"])

    cheapest_passing = min(cost("model-b"), cost("model-c"))
    assert "model-b" in flagged
    assert flagged["model-b"] == pytest.approx(cost("model-b") - cheapest_passing, abs=0.01)
    assert "model-c" not in flagged  # meets but doesn't exceed
    assert "model-a" not in flagged  # excluded by a hard constraint
    assert "model-d" not in flagged  # fails the capability thresholds
