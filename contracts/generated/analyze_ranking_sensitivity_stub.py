"""GENERATED from contracts/api-v1.yaml (v1.0.0) -- do not hand-edit.
Regenerate after changing the contract, never the other way around.

F.1.5 Analyze Ranking Sensitivity.
"""

from datetime import timedelta  # noqa: F401
from typing import Optional  # noqa: F401


def analyze_ranking_sensitivity(ranking: list, *, weighted_criteria: list, sensitivity_policy: tuple[float, ...] = (0.9, 1.1)) -> dict:
    """operationId: analyzeRankingSensitivity. F.1.5 -> F.1.6 (implements SR 1.4.1.5)
    
    in: ranking. control: weighted_criteria, sensitivity_policy. out: sensitivity_finding.
    """
    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/analyze_ranking_sensitivity.py
