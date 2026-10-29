# ADR-0002: Decision Basis Becomes an Internal Flow, F.1.1 -> F.1.7

Status: Accepted (team, 2026-10-28). The Innoslate model update is pending.

Context: SR 1.2.2 (SN-TL-09 / 5.1.3.2) needs the decision record to contain the
requirements, the criteria mapping and the weights. In the first-level IDEF0
(SYSEN5151_ArchitectureDefinitionReport.pdf, Fig. 8, Table 7), F.1.7 receives only
8.1 Selection rationale and the boundary input Model selection. Selection rationale
"carries the ranking, its evidence and the sensitivity finding into the decision
record" (report p9). So no arrow brought the three sections to F.1.7. The code filled
the gap without a model decision: `record_decision` merged F.1's internal state
(`_decision`) into the rationale before calling F.1.7. The 7.4.1 consistency check
surfaced this, and writing contracts/api-v1.yaml from the flow list made it concrete.

Decision: the team adds an internal flow, **5.4 Decision basis** (the stated
requirements, the confirmed criteria mapping and the weights), from F.1.1 to F.1.7,
arriving at F.1.7 as an input. The contract has it as operation
`compileDecisionBasis` (F.1.1), and `generateAndStoreDecisionRecord` takes it as a
third input. It is optional in v1, for one reason: the SR 1.4.1.7 acceptance test
calls F.1.7 with only (rationale, selection), and tests aren't edited to fit an
implementation. When the basis is absent, the three sections come from the
rationale's same-named keys (contract A3, A4). `record_decision` now sends 5.4,
and the state merge is gone.

Consequences: F.1.7's record sections now trace to arrows. Two things stay as
mechanism C.1 state between UC.1 steps, because the boundary defs are separate
calls: F.1.1 keeping the stated requirements until the record is made, and
`_decision` keeping the selection rationale. If a later SR 1.4.1.7 test passes the
basis explicitly, the A4 fallback can go in contract v2.

What would change this decision: if the team instead widens 8.1 Selection rationale
to carry these sections (with arrows from F.1.1 into F.1.6), 5.4 goes away in
contract v2.

Model entities affected: F.1.1 Propose Criteria Mapping (new output), F.1.7 Generate
and Store Decision Record (new input), new internal flow 5.4 Decision basis, 8.1
Selection rationale (its description is unchanged), SR 1.2.2, SR 1.4.1.1, SR 1.4.1.7.
