def request_model_data(confirmed_mapping: dict) -> dict:
    # UC.1.10, UC.1.11 -- call and return are the same function call
    return {
        "candidates": [
            {
                "model": "stub-model-1",
                "min_context_tokens": 200000,
                "usd_per_month": 150,
                "response_time_ms": 800,
                "source": "vendor spec sheet",
                "collected_on": "2026-09-01",
            }
        ]
    }
