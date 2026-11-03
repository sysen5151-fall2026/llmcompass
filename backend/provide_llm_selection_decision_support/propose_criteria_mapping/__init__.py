"""Implements F.1.1 -- Propose Criteria Mapping. Mechanism: C.1.1 Criteria Mapper.

Package of the four second-level functions (SPEC.md section 7; contracts/api-v1.yaml A28):
request_interpretation.py (F.1.1.1, C.1.1.1), validate_proposed_criteria.py (F.1.1.2, C.1.1.2),
present_criteria_mapping.py (F.1.1.3, C.1.1.3), distribute_confirmed_mapping.py (F.1.1.4, C.1.1.4).
The first-level F.1.1 defs are re-exported here unchanged (prep step before the Lab 9.4 generation).
"""

from ._first_level import *  # noqa: F401,F403
from ._first_level import (  # noqa: F401
    CATEGORIES, DESIGNATIONS, KNOWN_METRICS, OPERATORS, PROXY_STRENGTHS, _decision, _require,
    compile_decision_basis, present_criteria_mapping, request_interpretation, split_confirmed_mapping,
    validate_criterion, validate_interpretation,
)
