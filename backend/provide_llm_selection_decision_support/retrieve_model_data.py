"""Implements F.1.2 -- Retrieve Model Data. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.2 (SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2, SN-TL-08 / 5.3.1.1). IDEF0 A1 of F.1, 2026-10-26.
# Sits behind contracts/api-v1.yaml: requestModelData, receiveModelData.

import copy
from datetime import date, timedelta

STALE_AFTER = timedelta(days=90)

# SPEC section 2 figure fields. With the catalog's benchmark ids (F.7's published
# vocabulary, SPEC 5 Q7) they are the known metrics of SPEC section 3.
FIGURE_FIELDS = ("input_price", "output_price", "context_window", "latency_p50",
                 "data_residency", "data_retention", "deprecation_date")


def is_stale(collection_date, today, *, staleness_threshold: timedelta = STALE_AFTER) -> bool:
    # SN-TL-03 / 5.1.2.2 -- older than 90 days is stale; exactly 90 is not.
    # staleness_threshold is the F.1 control "Staleness threshold" (IDEF0, 2026-10-26).
    return today - date.fromisoformat(str(collection_date)) > staleness_threshold


def _metric_figure(candidate: dict, metric: str):
    # A metric is a SPEC section 2 field or a benchmark_id.
    if metric in candidate:
        return candidate[metric]
    for b in candidate.get("benchmarks", []):
        if b["benchmark_id"] == metric:
            return b["score"]
    return None


def _figure_metrics(candidate: dict) -> list:
    # Every metric the candidate has a figure for: SPEC section 2 fields, then benchmark ids.
    return [f for f in FIGURE_FIELDS if f in candidate] + [b["benchmark_id"] for b in candidate.get("benchmarks", [])]


def _evidence_item(model_id: str, metric: str, fig: dict) -> dict:
    # contracts/api-v1.yaml EvidenceItem: one figure flattened with its candidate and metric (5.1.2.1)
    return {"model_id": model_id, "metric": metric, "value": fig["value"], "unit": fig["unit"],
            "source_id": fig["source_id"], "collection_date": fig["collection_date"], "stale": fig.get("stale")}


def _flag_stale(candidate: dict, metrics: list, today, staleness_threshold: timedelta) -> dict:
    # SN-TL-03 / 5.1.2.2 -- a copy of the candidate, each of these metrics' figures with its stale flag
    flagged = copy.deepcopy(candidate)
    for metric in metrics:
        fig = _metric_figure(flagged, metric)
        if fig is not None:
            fig["stale"] = is_stale(fig["collection_date"], today, staleness_threshold=staleness_threshold)
    return flagged


def request_model_data(required_metrics: list) -> dict:
    """Function: F.1.2 -- Retrieve Model Data. Contract operation requestModelData.

    in: required_metrics (5.1). out: data_request.
    """
    # SR 1.4.1.2, SR 1.2.1 (SN-TL-08 / 5.3.1.1) -- every candidate in the catalog, each required metric once
    return {"models": "all", "metrics": list(dict.fromkeys(required_metrics))}


def receive_model_data(model_data_with_provenance: list, *, staleness_threshold: timedelta = STALE_AFTER) -> list:
    """Function: F.1.2 -- Retrieve Model Data. Contract operation receiveModelData.

    in: model_data_with_provenance. control: staleness_threshold. out: candidate_evidence (7.1).
    """
    # SPEC section 2, source unavailable -- nothing stored at all: "no model data available", don't rank
    if not model_data_with_provenance:
        raise LookupError("no model data available")
    # SR 1.4.1.2, SR 1.1.2 (SN-TL-02 / 5.1.2.1, SPEC section 2) -- a figure that isn't a figure, or has
    # no source_id or collection_date, is rejected at entry
    for cand in model_data_with_provenance:
        figures = [(f, cand[f]) for f in FIGURE_FIELDS if f in cand]
        for b in cand.get("benchmarks", []):
            if not isinstance(b, dict):
                raise ValueError(f"{cand['model_id']}: benchmark entry is not a benchmark_id and score.")
            figures.append((b.get("benchmark_id"), b.get("score")))
        for field, fig in figures:
            if not isinstance(fig, dict):
                raise ValueError(f"{cand['model_id']}.{field}: not a figure with source and date.")
            if not fig.get("source_id") or not fig.get("collection_date"):
                raise ValueError(f"{cand['model_id']}.{field}: figure has no source_id or collection_date.")

    # SR 1.4.1.2 (SN-TL-03 / 5.1.2.2) -- every figure keeps its source and date and gets its stale flag.
    # Stale figures are still used.
    today = date.today()  # the clock belongs to mechanism C.1
    return [_flag_stale(cand, _figure_metrics(cand), today, staleness_threshold)
            for cand in model_data_with_provenance]
