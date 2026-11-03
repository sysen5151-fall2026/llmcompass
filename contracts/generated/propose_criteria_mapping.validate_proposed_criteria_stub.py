"""GENERATED from contracts/api-v1.yaml (v1.1.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.1.2 Validate Proposed Criteria.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def validate_proposed_criteria(proposed_criteria: Optional[dict], requirement_set: list, *, known_metrics: Optional[frozenset[str]] = None) -> dict:
    """operationId: validateProposedCriteria. F.1.1.2 -> F.1.1.3 (flow 3.0.1) (implements CR 1.4.2, CR 1.1.3, CR 1.1.2)
    
    in: proposed_criteria, requirement_set. control: known_metrics. out: validated_criteria.
    raises: ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/propose_criteria_mapping/validate_proposed_criteria.py
