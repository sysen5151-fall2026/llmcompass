"""GENERATED from contracts/api-v1.yaml (v1.0.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.3 Apply Hard Constraints.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def apply_hard_constraints(candidate_evidence: list, *, hard_constraints: list) -> tuple[list, list]:
    """operationId: applyHardConstraints. F.1.3 -> F.1.4, F.1.6 (implements SR 1.4.1.3)
    
    in: candidate_evidence. control: hard_constraints. out: eligible_candidates, exclusions.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/apply_hard_constraints.py
