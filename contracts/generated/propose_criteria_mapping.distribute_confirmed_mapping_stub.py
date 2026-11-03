"""GENERATED from contracts/api-v1.yaml (v1.1.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.1.4 Distribute Confirmed Mapping.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def distribute_confirmed_mapping(confirmed_criteria_mapping: list, requirement_set: list, *, known_metrics: Optional[frozenset[str]] = None) -> tuple[list, list, list, dict]:
    """operationId: distributeConfirmedMapping. F.1.1.4 -> F.1.2, F.1.3, F.1.4, F.1.5, F.1.7 (flows 5.1-5.4) (implements CR 1.4.4, CR 2.1.2)
    
    in: confirmed_criteria_mapping, requirement_set. control: known_metrics. out: required_metrics, hard_constraints, weighted_criteria, decision_basis.
    raises: ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/propose_criteria_mapping/distribute_confirmed_mapping.py
