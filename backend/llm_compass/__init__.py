def interpret_requirements(runtime_ack: dict) -> dict:
    # UC.1.3
    return {"proposed_criteria": ["context_length", "cost_ceiling", "latency_p95"]}


def present_mapping_for_review(criteria: dict) -> dict:
    # UC.1.5
    return {
        "context_length": "min_context_tokens",
        "cost_ceiling": "usd_per_month",
        "latency_p95": "response_time_ms",
    }


def retrieve_model_spec_and_benchmark_data(confirmed_mapping: dict) -> dict:
    # UC.1.9
    return {"model": "stub-model-1", "context_length": 200000, "cost_usd_per_month": 150}


def present_sensitivity_finding(spec: dict) -> dict:
    # UC.1.14
    return {"finding": "ranking flips at a 5% change in cost weighting"}


def select_model(review: dict) -> dict:
    # UC.1.15
    return {"selected_model": "stub-model-1"}


def generate_decision_record(selection: dict) -> dict:
    # UC.1.16 -- self-call, produces the walking skeleton's final output
    return {
        "model": selection["selected_model"],
        "criteria": ["context_length", "cost_ceiling", "latency_p95"],
        "sensitivity": "ranking flips at a 5% change in cost weighting",
    }
