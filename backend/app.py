"""Walking skeleton entry point. Wires the stub participants in the call order
from docs/walking-skeleton.md (UC.1). No real logic behind any of it yet.

Run: python backend/app.py
"""

from language_model_runtime import submit_requirements
from llm_compass import (
    receive_requirements,
    present_mapping_for_review,
    confirm_mapping,
    present_sensitivity_finding,
    select_model,
    generate_decision_record,
)
from benchmark_data_sources import request_model_data


def main() -> None:
    requirements = {"stub": "requirements and constraints"}

    receive_requirements(requirements)                   # 1
    criteria = submit_requirements(requirements)         # 2, 3
    mapping = present_mapping_for_review(criteria)       # 4
    confirmed = confirm_mapping(mapping)                 # 5
    spec = request_model_data(confirmed)                 # 6, 7
    finding = present_sensitivity_finding(spec)          # 8
    review = select_model(finding)                       # 9
    decision_record = generate_decision_record(review)   # 10

    print(decision_record)


if __name__ == "__main__":
    main()
