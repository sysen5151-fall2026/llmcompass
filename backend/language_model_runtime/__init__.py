def submit_requirements(requirements: dict) -> dict:
    # UC.1.3, UC.1.4 -- call and return are the same function call
    return {
        "proposed_criteria": [
            {"criterion": "min_context_tokens", "derived_from": "capability_needs", "confidence": "high"},
            {"criterion": "usd_per_month", "derived_from": "cost_limits", "confidence": "high"},
            {"criterion": "response_time_ms", "derived_from": "latency_expectations", "confidence": "medium"},
        ]
    }
