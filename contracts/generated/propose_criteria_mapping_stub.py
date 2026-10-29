"""GENERATED from contracts/api-v1.yaml (v1.0.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.1 Propose Criteria Mapping.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def split_confirmed_mapping(confirmed_criteria_mapping: list, *, known_metrics: Optional[frozenset[str]] = None) -> tuple[list, list, list]:
    """operationId: splitConfirmedMapping. F.1.1 -> F.1.2, F.1.3, F.1.4, F.1.5 (implements SR 1.4.1.1)
    
    in: confirmed_criteria_mapping. control: known_metrics. out: weighted_criteria, hard_constraints, required_metrics.
    raises: ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/propose_criteria_mapping.py


def compile_decision_basis(stated_requirements: list, confirmed_criteria_mapping: list, *, known_metrics: Optional[frozenset[str]] = None) -> dict:
    """operationId: compileDecisionBasis. F.1.1 -> F.1.7 (implements SR 1.4.1.1; feeds SR 1.4.1.7)
    
    in: stated_requirements, confirmed_criteria_mapping. control: known_metrics. out: decision_basis.
    raises: ValueError.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/propose_criteria_mapping.py
