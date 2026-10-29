# ADR-0003: The Ranking Carries Contributions and Figures, Not Scoring Internals

Status: Accepted (2026-10-28)

Context: contracts/api-v1.yaml was written from the IDEF0 flow list, not from the
code (Lab Manual 7.4.3). Checked against it, the F.1.3-F.1.6 code had drifted
(contracts/check_conformance.py, before the refactor):
- 7.2 Eligible candidates carried an extra `evidence` key that F.1.3 attached.
- 7.4 Ranking entries carried `normalized` (F.1.4's scoring internals), which F.1.5
  used to re-score, and `gaps` where the contract says `missing_data`.
- Evidence items had no `model_id`.

The model gives F.1.5 only the ranking and the weighted criteria. It gives F.1.4
only the eligible candidates and the weighted criteria, so F.1.4 can't know which
hard-constraint figures were used.

Decision: the code conforms to the contract.
- F.1.3 passes eligible candidates on unchanged. Its exclusions carry the
  hard-constraint figures they were judged on, as contract EvidenceItems with `model_id`.
- F.1.4's ranking entries carry `model_id`, `score`, `contributions`, `missing_data`
  and `evidence`. The evidence is every figure of the candidate (contract A11),
  because F.1.4 has no hard-constraint arrow. `normalized` is no longer sent.
- F.1.5 re-scores from the contributions, which scale linearly with their weight
  (contract A10). A pair counts as a flip only when the lower-ranked candidate's
  score becomes strictly greater, so ties don't count (A8).

Consequences:
- The presented ranking's evidence, and the record's, now shows every figure of each
  ranked candidate, not only the figures of criteria metrics. For each excluded
  candidate it still shows the hard-constraint figures that excluded it. This is
  more than SN-TL-02 / 5.1.2.1 ("every figure used") needs, but never less. The SR
  1.1.2, 1.3.3 and 1.4.1.6 tests still pass.
- A tie under a weight change is no longer reported as unstable. The known-answer
  fixtures have no ties, so their results are unchanged.

What would change this decision: if the team wants only the figures that were used
shown, contract v1.1 adds a used-metrics list to 7.4, or carries the hard-constraint
figures through 7.2.

Model entities affected: F.1.3 Apply Hard Constraints, F.1.4 Score and Rank
Candidates, F.1.5 Analyze Ranking Sensitivity, F.1.6 Report Selection Rationale; flows
7.2 Eligible candidates, 7.3 Exclusions, 7.4 Ranking; SR 1.4.1.3-1.4.1.6.
