# Context

External systems for LLM Compass, per the OpsCon narrative in README.md. Will match
this up against the Innoslate context diagram once it's built.

## System Context — External Systems

Application Developer
  In:  application requirements — capability/task needs
  Out: ranked recommendation, rationale, decision record

Technical Lead / Architect
  In:  application requirements and constraints; criterion mapping edits
       (accept/reject/amend); weights
  Out: ranked recommendation, rationale, sensitivity finding, exportable
       decision record

Budget Owner
  In:  cost ceiling / budget constraint
  Out: ranked recommendation, rationale, decision record

Compliance Officer
  In:  data residency, retention, and vendor-acceptability constraints
       (hard constraints — filter, not weight)
  Out: ranked recommendation, rationale, decision record

Operations Lead
  In:  latency, rate-limit, reliability, and deprecation-risk concerns
  Out: ranked recommendation, rationale, decision record

Public Benchmark Data
  Out: benchmark scores per model/task, with source and collection date
       (increment 1: manual entry; increment 2: automated ingestion with
       provenance/staleness — narrative flags anything over 90 days old)

Vendor Specifications
  Out: vendor-published specs — pricing, latency, context length,
       data-residency terms (increment 1: manual entry; increment 2:
       automated ingestion)

Out of scope: the end user of the downstream application. Per the OpsCon
narrative (§4.3), they don't interact with LLM Compass directly — their
experience is only what the requirements describe.
