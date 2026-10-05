# STUB: LLM Compass (walking skeleton -- no real logic yet)


def receive_requirements(requirements: dict) -> dict:
    # UC.1.2
    return {"received": True}


def present_mapping_for_review(criteria: dict) -> dict:
    # UC.1.6
    return {"for_review": criteria["proposed_criteria"]}


def confirm_mapping(mapping: dict) -> dict:
    # UC.1.9
    return {"confirmed": True}


def present_sensitivity_finding(spec: dict) -> dict:
    # UC.1.16
    return {"finding": "ranking flips at a 5% change in cost weighting", "close_candidates": ["stub-model-1", "stub-model-2"]}


def select_model(review: dict) -> dict:
    # UC.1.17
    return {"selected_model": "stub-model-1"}


def generate_decision_record(selection: dict) -> dict:
    # UC.1.18
    return {
        "requirements": {"stub": "requirements and constraints"},
        "criteria_mapping": ["min_context_tokens", "usd_per_month", "response_time_ms"],
        "weights": {"min_context_tokens": 0.3, "usd_per_month": 0.4, "response_time_ms": 0.3},
        "data_used": {"source": "vendor spec sheet", "collected_on": "2026-09-01"},
        "ranking": ["stub-model-1", "stub-model-2"],
        "sensitivity": "ranking flips at a 5% change in cost weighting",
        "selected_model": selection["selected_model"],
    }
