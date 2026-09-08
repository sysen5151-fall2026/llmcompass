# Context

External systems for LLM Compass. Will match this up against the Innoslate context
diagram once it's built.

## System Context — External Systems

Requirement Submitter
  In:  application requirements, plain language (Application Developer, Budget
       Owner, Compliance Officer, Product Owner, or Technical Lead)
  In:  weights and filters
  Out: ranked recommendation, rationale, decision record (export, increment 4)

Benchmark Source
  Out: LLM benchmark scores per model/task (increment 1: manual entry;
       increment 2: automated ingestion with provenance/staleness)

Vendor Specification Source
  Out: LLM vendor specs — pricing, latency, context length, data-residency terms
       (increment 1: manual entry; increment 2: automated ingestion)
