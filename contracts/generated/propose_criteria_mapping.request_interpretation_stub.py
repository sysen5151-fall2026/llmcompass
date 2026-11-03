"""GENERATED from contracts/api-v1.yaml (v1.1.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.1.1 Request Interpretation.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def request_interpretation(stated_requirements: str) -> tuple[list, list]:
    """operationId: requestInterpretation. F.1.1.1 -> runtime (flow 2), F.1.1.2 and F.1.1.4 (flow 1.0.1) (implements CR 1.4.1, CR 1.2.3)
    
    in: stated_requirements. control: -. out: interpretation_requests, requirement_set.
    raises: ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/propose_criteria_mapping/request_interpretation.py
