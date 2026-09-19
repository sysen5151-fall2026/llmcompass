"""Walking skeleton entry point. Wires the stub participants in the call order
from docs/walking-skeleton.md (UC.1). No real logic behind any of it yet.

Run: python backend/app.py
"""

from language_model_runtime import enter_requirements
from llm_compass import (
    interpret_requirements,
    present_mapping_for_review,
    retrieve_model_spec_and_benchmark_data,
    present_sensitivity_finding,
    select_model,
    generate_decision_record,
)
from benchmark_data_sources import confirm_mapping


def main() -> None:
    requirements = {"stub": "requirements and constraints"}

    runtime_ack = enter_requirements(requirements)              # 1, 2
    criteria = interpret_requirements(runtime_ack)              # 3
    mapping = present_mapping_for_review(criteria)              # 4
    confirmed = confirm_mapping(mapping)                        # 5, 6
    spec = retrieve_model_spec_and_benchmark_data(confirmed)    # 7
    finding = present_sensitivity_finding(spec)                 # 8
    review = select_model({"finding": finding})                 # 9
    decision_record = generate_decision_record(review)          # 10

    print(decision_record)


if __name__ == "__main__":
    main()
