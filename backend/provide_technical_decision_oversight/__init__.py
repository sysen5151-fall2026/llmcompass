# STUB: Technical Lead
"""Implements F.6 -- Provide Technical Decision Oversight. Mechanism: C.6 Technical Lead."""

from typing import Optional


def state_requirements(application_technical_needs: str, *, budget_constraints: list, compliance_constraints: list) -> str:
    """in: application_technical_needs. control: budget_constraints, compliance_constraints. out: stated_requirements."""
    # UC.1.2
    raise NotImplementedError


def confirm_criteria_mapping(presented_mapping: dict, product_priorities: dict, *, budget_constraints: list, compliance_constraints: list) -> list:
    """in: presented_mapping, product_priorities. control: budget_constraints, compliance_constraints. out: confirmed_criteria_mapping."""
    # UC.1.7-1.9
    raise NotImplementedError


def choose_model(presented_ranking_and_sensitivity: dict, *, budget_constraints: list, compliance_constraints: list) -> Optional[str]:
    """in: presented_ranking_and_sensitivity. control: budget_constraints, compliance_constraints. out: model_selection."""
    # UC.1.17
    raise NotImplementedError


def keep_decision_record(decision_record: dict) -> None:
    """in: decision_record. control: none. out: none -- the model shows no output for this input (finding for the team, see docs/PLAN.md)."""
    # after UC.1.18
    raise NotImplementedError
