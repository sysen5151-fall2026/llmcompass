"""Implements F.1.2 -- Retrieve Model Data. Mechanism: C.1 LLM Compass."""

# SR 1.4.1.2 (SN-TL-02 / 5.1.2.1, SN-TL-03 / 5.1.2.2, SN-TL-08 / 5.3.1.1). IDEF0 A1 of F.1, 2026-10-26.
# SR 1.4.1.8 (R4 fallback, ADR-0010). Sits behind contracts/api-v1.yaml: requestModelData,
# receiveModelData, checkRequestedModels.

import copy
import re
from datetime import date, timedelta
from typing import Optional

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


# --- R4 fallback: models named in the stated requirements but not in the catalog ---
# SR 1.4.1.8 (R4.M1; StR 5.1.6.3). Lab Manual 12.3, ADR-0010. contracts/api-v1.yaml
# checkRequestedModels, A34-A37. Plain code, no language model: a check run by the model
# would itself be exposed to R1 (docs/risks.md).

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_MAX_RUN = 6        # A34 -- words in one name
_MIN_KEY = 4        # A34 -- shorter keys are ignored
_MAX_TRAIL = 3      # A35 -- words after a family word
_MAX_SUGGESTIONS = 3


def _key(text: str) -> str:
    # A34 -- casefolded, spaces, hyphens, dots and underscores removed
    return re.sub(r"[\s\-._]", "", text.casefold())


def _words(text: str) -> list:
    # (word, start, end); trailing punctuation such as the full stop ending a sentence is not part of a word
    words = []
    for m in _WORD.finditer(text):
        word = m.group().rstrip("._-")
        words.append((word, m.start(), m.start() + len(word)))
    return words


def _family(name: str) -> str:
    first = name.split()[0] if name.split() else ""
    m = re.match(r"[a-z]+", first.casefold())
    return m.group() if m else ""


def _intelligence(cand: dict):
    fig = _metric_figure(cand, "intelligence_index")
    return fig["value"] if fig else None


def _suggest(catalog: list, vendor, reference) -> list:
    # A36 -- same vendor first; else nearest on the intelligence index; else highest
    ordered = list(enumerate(catalog))
    same = [(i, c) for i, c in ordered if vendor and _key(c.get("vendor", "")) == _key(vendor)]
    if same:
        same.sort(key=lambda p: (_intelligence(p[1]) is None, -(_intelligence(p[1]) or 0), p[0]))
        return [c["model_name"] for _, c in same[:_MAX_SUGGESTIONS]]
    if reference is not None:
        ordered.sort(key=lambda p: (_intelligence(p[1]) is None,
                                    abs((_intelligence(p[1]) or 0) - reference), p[0]))
    else:
        ordered.sort(key=lambda p: (_intelligence(p[1]) is None, -(_intelligence(p[1]) or 0), p[0]))
    return [c["model_name"] for _, c in ordered[:_MAX_SUGGESTIONS]]


def _text_of(requirement) -> str:
    # A19 -- a stated requirement is plain text or {requirement_id, text}
    return requirement["text"] if isinstance(requirement, dict) else str(requirement)


def check_requested_models(stated_requirements: list, candidate_evidence: list, *,
                           known_models: Optional[list]) -> dict:
    """Function: F.1.2 -- Retrieve Model Data. Contract operation checkRequestedModels.

    in: stated_requirements, candidate_evidence (7.1). control: known_models.
    out: requested_models_report (7.6).
    """
    # A37 -- no list stored: say so; never treat the check as passed
    if known_models is None:
        return {"catalog_check": "could_not_run", "requested_not_compared": []}

    keys = {}  # name key -> (in catalog, known model or None)
    for k in known_models:
        for name in (k["name"], re.sub(r"\s*\([^)]*\)\s*$", "", k["name"]), k.get("slug") or ""):
            if len(_key(name)) >= _MIN_KEY:
                keys.setdefault(_key(name), (False, k))
    for c in candidate_evidence:  # A35 -- a catalog key wins over a known-models key
        for name in (c["model_id"], c.get("model_name") or ""):
            if len(_key(name)) >= _MIN_KEY:
                keys[_key(name)] = (True, None)
    families = {}
    for k in known_models:
        families.setdefault(_family(k["name"]), []).append(k)
    families = {f: ks for f, ks in families.items() if len(f) >= 3 and len(ks) >= 2}

    report, seen = [], set()
    for requirement in stated_requirements:
        text = _text_of(requirement)
        words = _words(text)
        used = [False] * len(words)
        # A34 -- leftmost, longest run of words that matches a key
        i = 0
        while i < len(words):
            for n in range(min(_MAX_RUN, len(words) - i), 0, -1):
                hit = keys.get(_key("".join(w for w, _, _ in words[i:i + n])))
                if hit:
                    in_catalog, known = hit
                    used[i:i + n] = [True] * n
                    if not in_catalog and ("known", known["name"]) not in seen:
                        seen.add(("known", known["name"]))
                        report.append({"name_as_written": text[words[i][1]:words[i + n - 1][2]],
                                       "reason": "not_in_catalog", "known_model": known["name"],
                                       "suggestions": _suggest(candidate_evidence, known.get("vendor"),
                                                               known.get("intelligence_index"))})
                    i += n
                    break
            else:
                i += 1
        # A35 -- a family word with a version that matches nothing: not recognised
        i = 0
        while i < len(words):
            family = _family(words[i][0])
            if used[i] or family not in families:
                i += 1
                continue
            j = i + 1
            while (j < len(words) and j - i <= _MAX_TRAIL and not used[j]
                   and (words[j][0][0].isupper() or words[j][0][0].isdigit())):
                j += 1
            run = words[i:j]
            name = text[run[0][1]:run[-1][2]]
            if any(ch.isdigit() for w, _, _ in run for ch in w) and ("name", _key(name)) not in seen:
                seen.add(("name", _key(name)))
                vendors = {k.get("vendor") for k in families[family]}
                report.append({"name_as_written": name, "reason": "not_recognised", "known_model": None,
                               "suggestions": _suggest(candidate_evidence,
                                                       vendors.pop() if len(vendors) == 1 else None, None)})
            i = j
    return {"catalog_check": "ran", "requested_not_compared": report}
