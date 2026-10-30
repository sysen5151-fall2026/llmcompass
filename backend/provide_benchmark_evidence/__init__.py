# STUB: Benchmark Data Sources
# Loads the manually entered model, provider and benchmark data from sample_data/.
"""Implements F.7 -- Provide Benchmark Evidence. Mechanism: C.7 Benchmark Data Sources."""

import json
from pathlib import Path

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"


# SPEC section 2, SPEC 5 Q7 -- the benchmark vocabulary and which source field feeds each id
# live in sample_data/benchmark_map.json (team, 2026-10-28), not in code.
BENCHMARK_MAP = json.loads((SAMPLE_DATA / "benchmark_map.json").read_text())["benchmarks"]
BENCHMARK_IDS = {bid: (*b["stored"], b["unit"]) for bid, b in BENCHMARK_MAP.items()}
# SPEC section 2 -- manual-entry fields (data residency, retention, deprecation), one entry per
# catalog model with its source, or a gap with the reason (sample_data/manual_entries.json).
MANUAL_FIELDS = ("data_residency", "data_retention", "deprecation_date")


def _figure(value, unit, source_id, collection_date):
    # SPEC section 2 figure -- every value keeps its source and date (SN-TL-02 / 5.1.2.1)
    return {"value": value, "unit": unit, "source_id": source_id, "collection_date": collection_date}


def _to_candidates(models: list, providers: dict, benchmark: dict) -> list:
    # Converts the sample files to the SPEC section 2 candidate shape.
    scores = {m["model_id"]: m for m in benchmark["models"]}
    bench_date = benchmark["benchmark_provider"]["retrieved_date_utc"]
    manual = json.loads((SAMPLE_DATA / "manual_entries.json").read_text())["models"]
    candidates = []
    for m in models:
        src, when = m["source_url"], m["retrieved_date"]
        cand = {
            "model_id": m["model_id"],
            "vendor": m["provider"],
            "model_name": m["model_name"],
            "input_price": _figure(m["input_price_per_1m_tokens_usd"], "USD per 1M input tokens", src, when),
            "output_price": _figure(m["output_price_per_1m_tokens_usd"], "USD per 1M output tokens", src, when),
            "context_window": _figure(m["context_window_tokens"], "tokens", src, when),
            "benchmarks": [],
        }
        for field in MANUAL_FIELDS:  # a gap stays absent, never filled in (SPEC section 2)
            entry = manual.get(m["model_id"], {}).get(field) or {}
            if "value" in entry:
                cand[field] = _figure(entry["value"], entry["unit"], entry["source_id"], entry["collection_date"])
        b = scores.get(m["model_id"])
        if b:
            for bid, (group, key, unit) in BENCHMARK_IDS.items():
                raw = b[group][key]
                value = raw["value"] if isinstance(raw, dict) else raw
                cand["benchmarks"].append({"benchmark_id": bid,
                                           "score": _figure(value, unit, b["sources"][0]["url"], bench_date)})
        candidates.append(cand)
    return candidates


def _load_catalog():
    # The stored catalog: increment 1 is manual entry in sample_data/ (SPEC section 2).
    models = json.loads((SAMPLE_DATA / "model_spec.json").read_text())
    providers = json.loads((SAMPLE_DATA / "providers.json").read_text())
    benchmark = json.loads((SAMPLE_DATA / "benchmark.json").read_text())
    return models, providers, benchmark


def request_model_data(confirmed_mapping: dict) -> dict:
    # UC.1.10, UC.1.11 -- call and return are the same function call (SN-TL-02 / 5.1.2.1)
    models, providers, benchmark = _load_catalog()
    return {
        "models": models,
        "providers": providers,
        "benchmark": benchmark,
        "candidates": _to_candidates(models, providers, benchmark),
    }


# --- F.7 ICOM signature (Lab Manual 4.4); body added in Chapter 5 (5.3) ---


def provide_model_data(*, data_request: dict) -> list:
    """Function: F.7 -- Provide Benchmark Evidence. Signature from Chapter 4; body added this increment.

    control: data_request. out: model_data_with_provenance.
    """
    # SR 1.3.3, SR 1.2.1 (catalog side), SR 1.4.1 (catalog side), SN-TL-02 / 5.1.2.1
    # UC.1.10, UC.1.11 -- no live source in increment 1, so the stored catalog answers.
    candidates = _to_candidates(*_load_catalog())
    # SR 1.2.1 -- "all" requests every candidate in the catalog; a list requests those model_ids.
    if data_request["models"] == "all":
        return candidates
    return [c for c in candidates if c["model_id"] in data_request["models"]]
