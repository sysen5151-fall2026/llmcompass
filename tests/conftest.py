"""Shared fixtures for the SPEC.md acceptance tests.

Every test is named test_<need ID>_<StR ID>_<what it checks>. Tests fail with
"not implemented: <module>.<function>" until the function from SPEC.md section 4
exists.
"""

import importlib
from datetime import date, timedelta

import pytest

TODAY = date(2026, 10, 4)


def impl(module_name, attr):
    """Get a function the SPEC says should exist, or fail the test if it doesn't."""
    module = importlib.import_module(module_name)
    fn = getattr(module, attr, None)
    if fn is None:
        pytest.fail(f"not implemented: {module_name}.{attr}")
    return fn


def figure(value, unit, days_old=10, source="https://example.com/source"):
    return {
        "value": value,
        "unit": unit,
        "source_id": source,
        "collection_date": (TODAY - timedelta(days=days_old)).isoformat(),
    }


def candidate(model_id, input_price, output_price, context, score, residency):
    return {
        "model_id": model_id,
        "vendor": f"vendor-{model_id}",
        "model_name": model_id,
        "input_price": figure(input_price, "USD per 1M input tokens"),
        "output_price": figure(output_price, "USD per 1M output tokens"),
        "context_window": figure(context, "tokens"),
        "data_residency": figure(residency, "ISO 3166-1 alpha-2"),
        "benchmarks": [{"benchmark_id": "long_context_qa", "score": figure(score, "%")}],
    }


@pytest.fixture
def today():
    return TODAY


@pytest.fixture
def candidates():
    # A beats everyone on every weighted criterion but is hosted outside the US.
    return [
        candidate("model-a", 0.10, 0.20, 1_000_000, 95.0, ["DE"]),
        candidate("model-b", 3.00, 15.00, 200_000, 85.0, ["US"]),
        candidate("model-c", 1.00, 4.00, 100_000, 70.0, ["US"]),  # exactly at thresholds
        candidate("model-d", 0.50, 1.50, 32_000, 60.0, ["US"]),
    ]


@pytest.fixture
def criteria():
    return [
        {
            "criterion_id": "ctx",
            "metric": "context_window",
            "operator": ">=",
            "threshold": 100_000,
            "unit": "tokens",
            "category": "capability",
            "designation": "weighted",
            "weight": 0.3,
        },
        {
            "criterion_id": "lcqa",
            "metric": "long_context_qa",
            "operator": ">=",
            "threshold": 70.0,
            "unit": "%",
            "category": "capability",
            "designation": "weighted",
            "weight": 0.5,
        },
        {
            "criterion_id": "price",
            "metric": "input_price",
            "operator": "<=",
            "threshold": 5.00,
            "unit": "USD per 1M input tokens",
            "category": "cost",
            "designation": "weighted",
            "weight": 0.2,
        },
        {
            "criterion_id": "residency",
            "metric": "data_residency",
            "operator": "in",
            "threshold": ["US"],
            "unit": "ISO 3166-1 alpha-2",
            "category": "compliance",
            "designation": "hard",
        },
    ]


@pytest.fixture
def usage():
    return {"requests_per_day": 5_000, "input_tokens": 8_000, "output_tokens": 500}


@pytest.fixture
def sample_record(candidates, criteria):
    return {
        "requirements": ["Summarize technical documents of around twenty pages accurately."],
        "criteria_mapping": criteria,
        "weights": {c["criterion_id"]: c["weight"] for c in criteria if c["designation"] == "weighted"},
        "evidence": [candidates[1]["context_window"], candidates[1]["input_price"]],
        "ranking": ["model-b", "model-c", "model-d"],
        "sensitivity": [["model-c", "model-d"]],
        "selected_model": "model-b",
    }
