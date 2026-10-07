# STUB: Benchmark Data Sources
# Loads the manually entered model, provider and benchmark data from sample_data/.

import json
from pathlib import Path

SAMPLE_DATA = Path(__file__).resolve().parents[2] / "sample_data"


BENCHMARK_IDS = {
    "intelligence_index": ("quality", "intelligence_index", "index"),
    "aa_omniscience_index": ("quality", "aa_omniscience_index", "index (-100 to 100)"),
    "aa_lcr_v1_1_percent": ("quality", "aa_lcr_v1_1_percent", "%"),
    "time_to_first_answer_token_seconds": ("performance", "time_to_first_answer_token_seconds", "seconds"),
    "output_speed_tokens_per_second": ("performance", "output_speed_tokens_per_second", "tokens per second"),
}
COUNTRY_CODES = {"United States": "US"}


def _figure(value, unit, source_id, collection_date):
    # SPEC section 2 figure -- every value keeps its source and date (SN-TL-02 / 5.1.2.1)
    return {"value": value, "unit": unit, "source_id": source_id, "collection_date": collection_date}


def _to_candidates(models: list, providers: dict, benchmark: dict) -> list:
    # Converts the sample files to the SPEC section 2 candidate shape.
    scores = {m["model_id"]: m for m in benchmark["models"]}
    bench_date = benchmark["benchmark_provider"]["retrieved_date_utc"]
    residency_source = next(s for s in providers["sources"] if s["source_id"] == "anthropic_data_location")
    residency = _figure([COUNTRY_CODES[providers["data_handling"]["default_data_storage_region"]]],
                        "ISO 3166-1 alpha-2", residency_source["url"], residency_source["retrieved_date"])
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
            "data_residency": residency,
            "benchmarks": [],
        }
        b = scores.get(m["model_id"])
        if b:
            for bid, (group, key, unit) in BENCHMARK_IDS.items():
                raw = b[group][key]
                value = raw["value"] if isinstance(raw, dict) else raw
                cand["benchmarks"].append({"benchmark_id": bid,
                                           "score": _figure(value, unit, b["sources"][0]["url"], bench_date)})
        candidates.append(cand)
    return candidates


def request_model_data(confirmed_mapping: dict) -> dict:
    # UC.1.10, UC.1.11 -- call and return are the same function call (SN-TL-02 / 5.1.2.1)
    models = json.loads((SAMPLE_DATA / "model_spec.json").read_text())
    providers = json.loads((SAMPLE_DATA / "providers.json").read_text())
    benchmark = json.loads((SAMPLE_DATA / "benchmark.json").read_text())
    return {
        "models": models,
        "providers": providers,
        "benchmark": benchmark,
        "candidates": _to_candidates(models, providers, benchmark),
    }
