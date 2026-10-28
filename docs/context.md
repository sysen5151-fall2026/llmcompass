# Context

The system of interest is C.1 LLM Compass. Everything below sits outside it,
matched to the Innoslate hierarchy and context diagram (C.2–C.8). C.1 performs
F.1 Provide LLM Selection Decision Support, in
backend/provide_llm_selection_decision_support/. Module names follow the IDEF0
function verb phrases (Lab Manual 4.4); docs/traceability.md maps each function
to its module.

Only three assets hold a conduit to C.1. The remaining four contribute constraints
and priorities to the selection decision, but do not exchange anything with the
system: their input reaches it through the Technical Lead, and their view of the
result comes from the Technical Lead rather than from LLM Compass. The two groups
are listed separately below because the distinction defines the system boundary — a
reader should be able to see at a glance which assets the project must build an
interface for.

## Interfacing assets

These three hold a conduit to C.1. They are the only crossings of the system
boundary.

Technical Lead (C.6) — human actor; sole human interface
  In:      application requirements and constraints; criterion mapping edits
           (accept / reject / amend); weights
  Out:     ranked recommendation, rationale, sensitivity finding, exportable
           decision record
  Conduit: Requirements and recommendations
  Module:  backend/provide_technical_decision_oversight/ (F.6)

Benchmark Data Sources (C.7) — external service
  In:      request for model data (UC.1.10)
  Out:     model specification and benchmark data per candidate model, with
           source and collection date (UC.1.11)
  Conduit: Data request and model data with provenance
  Module:  backend/provide_benchmark_evidence/ (F.7)
  Note:    covers what used to be split across "Public Benchmark Data" and
           "Vendor Specifications"; those are now one external system.
           Increment 1 is manual entry; increment 2 is automated ingestion with
           provenance and staleness — the narrative flags anything over 90 days
           old. Increment 2 sources (SPEC.md section 2): Artificial Analysis
           API, models.dev, OpenRouter as fallback, plus manual entry. They are
           all one external system, C.7, behind the one conduit.

Language model runtime (C.8) — external service
  In:      stated requirement, submitted by LLM Compass for interpretation
           (UC.1.3)
  Out:     proposed measurable criteria derived from the requirement, with a
           proxy-strength rating per criterion (UC.1.4; StR 5.1.1.3; response
           schema in SPEC.md section 3)
  Conduit: Interpretation request and proposed criteria
  Module:  backend/provide_requirement_interpretation/ (F.8)
  Note:    this is LLM Compass's own requirement-interpretation engine (the
           local model from docs/adr/0001-initial-toolchain.md), not a
           vendor-spec or pricing feed — confirmed against the UC.1 sequence
           diagram, which shows LLM Compass (not the Technical Lead) as the
           caller on both sides of this interface.

## Contributing stakeholders

These four have no conduit to C.1 and appear on the context diagram without a
connection to it. Each performs a function in the Metafunction (F.2–F.5), so their
contribution is modeled — but the contribution reaches the system as a value the
Technical Lead states at UC.1.2, not as an exchange with the system. Adding an
interface for any of them would be a scope decision, not a drawing correction.

Application Developer (C.2)
  Contributes:         application requirements — capability and task needs
  Reaches the system:  via Technical Lead, entered at UC.1.2
  Sees the result:     via Technical Lead, outside the system
  Function:            F.2 Define Application Technical Needs
  Module:              backend/define_application_technical_needs/ (F.2)

Budget Owner (C.3)
  Contributes:         cost ceiling / budget constraint
  Reaches the system:  via Technical Lead, entered at UC.1.2 and designated a
                       hard constraint at UC.1.7
  Sees the result:     via Technical Lead, outside the system
  Function:            F.3 Define Budget Constraints
  Module:              backend/define_budget_constraints/ (F.3)

Compliance Officer (C.4)
  Contributes:         data residency, retention, and vendor-acceptability
                       constraints — hard constraints, filters not weights
  Reaches the system:  via Technical Lead, entered at UC.1.2 and designated
                       hard constraints at UC.1.7
  Sees the result:     via Technical Lead, outside the system
  Function:            F.4 Define Compliance Constraints
  Module:              backend/define_compliance_constraints/ (F.4)

Product Owner (C.5)
  Contributes:         relative priority of capability, cost, and speed —
                       informs the weighting applied during selection (per the
                       Innoslate entity description: "Accountable for the
                       application's outcomes and priorities. Sets the relative
                       importance of capability, cost, and speed, which informs
                       the weighting applied during selection.")
  Reaches the system:  via Technical Lead, who assigns the weights at UC.1.8
  Sees the result:     via Technical Lead, outside the system
  Function:            F.5 Define Product Needs and Priorities
  Module:              backend/define_product_needs_and_priorities/ (F.5)
  Open item:           four requirements exist to serve the Product Owner —
                       5.2.1.1 compute cost at volume, 5.2.2.1 provide
                       trade-off summary, 5.2.3.1 report candidate risk,
                       5.2.4.1 identify over-capability — and none currently
                       has an implementing Input/Output in the model. The
                       business-facing content those requirements describe is
                       to be carried within the existing Technical Lead conduit
                       rather than through a new interface. Tracked for the
                       next increment.

## Not in the model

Operations Lead — considered and removed from the Innoslate model.

End user of the downstream application — out of scope. Per the OpsCon narrative
(§4.3), they do not interact with LLM Compass; their experience is what the
requirements describe, represented through the Product Owner and Application
Developer.
