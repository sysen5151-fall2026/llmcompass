# Context

External systems for LLM Compass, matched to the Innoslate hierarchy/context diagram
(C.1 LLM Compass; C.2–C.8 external systems).

## System Context — External Systems

Application Developer (C.2)
  In:  application requirements — capability/task needs
  Out: ranked recommendation, rationale, decision record

Budget Owner (C.3)
  In:  cost ceiling / budget constraint
  Out: ranked recommendation, rationale, decision record

Compliance Officer (C.4)
  In:  data residency, retention, and vendor-acceptability constraints
       (hard constraints — filter, not weight)
  Out: ranked recommendation, rationale, decision record

Product Owner (C.5)
  In:  relative priority of capability, cost, and speed — informs the
       weighting applied during selection (per Innoslate entity description:
       "Accountable for the application's outcomes and priorities. Sets the
       relative importance of capability, cost, and speed, which informs the
       weighting applied during selection.")
  Out: ranked recommendation, rationale, decision record

Technical Lead (C.6)
  In:  application requirements and constraints; criterion mapping edits
       (accept/reject/amend); weights
  Out: ranked recommendation, rationale, sensitivity finding, exportable
       decision record

Benchmark Data Sources (C.7)
  In:  request for model data (UC.1.10)
  Out: model specification and benchmark data per candidate model, with
       source and collection date (UC.1.11) — covers what used to be split
       across "Public Benchmark Data" and "Vendor Specifications"; those are
       now one external system (increment 1: manual entry; increment 2:
       automated ingestion with provenance/staleness — narrative flags
       anything over 90 days old)

Language model runtime (C.8)
  In:  stated requirement, submitted by LLM Compass for interpretation
       (UC.1.3)
  Out: proposed measurable criteria derived from the requirement, with a
       proxy-strength rating per criterion (UC.1.4; StR 5.1.1.3, response
       schema in SPEC.md section 3)
  Note: this is LLM Compass's own requirement-interpretation engine (the
       local model from docs/adr/0001-initial-toolchain.md), not a
       vendor-spec/pricing feed — confirmed against the UC.1 sequence
       diagram, which shows LLM Compass (not Technical Lead) as the caller
       on both sides of this interface.

Dropped from this list: Operations Lead (removed from the Innoslate model).

Out of scope: the end user of the downstream application. Per the OpsCon
narrative (§4.3), they don't interact with LLM Compass directly — their
experience is only what the requirements describe.
