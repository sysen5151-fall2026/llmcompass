# STUB: Benchmark Data Sources
# Return shape follows the SPEC.md section 2 data contract.


def request_model_data(confirmed_mapping: dict) -> dict:
    # UC.1.10, UC.1.11 -- call and return are the same function call
    def figure(value, unit):
        return {
            "value": value,
            "unit": unit,
            "source_id": "vendor spec sheet",
            "collection_date": "2026-09-01",
        }

    return {
        "candidates": [
            {
                "model_id": "stub-model-1",
                "vendor": "stub-vendor",
                "model_name": "stub-model-1",
                "input_price": figure(1.00, "USD per 1M input tokens"),
                "output_price": figure(4.00, "USD per 1M output tokens"),
                "context_window": figure(200000, "tokens"),
                "latency_p50": figure(0.8, "seconds"),
                "benchmarks": [],
            }
        ]
    }
