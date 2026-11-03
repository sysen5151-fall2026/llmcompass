"""Milestone 2 UI wiring: the web UI calls C.1.1 live (docs/PLAN.md, "Milestone 2 UI wiring").

Written from the PLAN route/form-field interface and SPEC.md only, before the routes exist.
Traces: SR 1.3.1, SR 1.1.1, SR 1.1.5, CR 1.1.1, CR 1.1.2, CR 1.2.4, CR 1.3.6, CR 1.4.3,
CR 2.1.2, SPEC section 3 (failure path), UC.1.2-UC.1.9, A27.

The round trip is driven like a browser: POST / with the requirements, collect the review
page's form fields with their default values (hidden `pending`, checked boxes, selected
options), override the documented fields, and POST /confirm.

The language model runtime is a stdlib HTTPServer on 127.0.0.1 (the reconcile tests' pattern);
the benchmark data stays in file mode (the stored catalog in sample_data/, 3 models).
"""

import html
import json
import re
import threading
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

pytest.importorskip("flask")

from app import app  # noqa: E402  (backend/ is on sys.path via pytest.ini pythonpath)
from provide_llm_selection_decision_support import retrieve_decision_record  # noqa: E402

SAMPLE_DATA = Path(__file__).resolve().parent.parent / "sample_data"
CATALOG_IDS = [m["model_id"] for m in json.loads((SAMPLE_DATA / "model_spec.json").read_text())]


# --- fake language model runtime (SPEC 3 Adapter: POST {LLM_RUNTIME_URL}/chat/completions) ---

@pytest.fixture
def runtime(monkeypatch):
    """replies[n] answers the n-th POST: a dict, or a callable taking the request's requirement_id."""
    state = {"replies": [], "requests": []}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append(body)
            n = len(state["requests"]) - 1
            reply = state["replies"][n] if n < len(state["replies"]) else {"exhausted": True}
            content = reply(_rid_of(body)) if callable(reply) else reply
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]}).encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("LLM_RUNTIME_URL", f"http://127.0.0.1:{server.server_port}/v1")
    yield state
    server.shutdown()


@pytest.fixture
def client(runtime, monkeypatch):
    monkeypatch.delenv("BENCHMARK_SOURCE", raising=False)  # file mode: the stored catalog
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _rid_of(body):
    """The prompt the adapter sends carries a line `requirement_id: <id>` (SPEC 3 Adapter)."""
    text = "\n".join(str(m.get("content", "")) for m in body.get("messages", []))
    match = re.search(r"requirement_id:\s*(\S+)", text)
    return match.group(1) if match else ""


def _crit(cid, metric, operator, threshold, unit, category, strength="strong", rationale=None):
    return {"criterion_id": cid, "metric": metric, "operator": operator, "threshold": threshold,
            "unit": unit, "proxy_strength": strength, "category": category,
            "rationale": rationale or f"rationale for {cid}"}


COST = _crit("cost_in", "input_price", "<=", 5, "USD per 1M input tokens", "cost", "strong",
             "Input price stands for operating cost.")
CTX = _crit("ctx", "context_window", ">=", 100000, "tokens", "capability", "moderate",
            "Context window stands for long-document handling.")
OUT = _crit("cost_out", "output_price", "<=", 20, "USD per 1M output tokens", "cost", "weak",
            "Output price is a partial proxy for cost.")
RESIDENCY = _crit("eu_only", "data_residency", "in", ["DE", "FR"], "ISO 3166-1 alpha-2", "compliance",
                  "strong", "Residency stands for the EU-only policy.")


def valid(*criteria):
    """A SPEC 3 valid reply for whichever requirement_id the request carries."""
    return lambda rid: {"requirement_id": rid, "no_suitable_proxy": False, "criteria": list(criteria)}


INVALID = {"not": "the SPEC 3 schema"}


# --- browser-like form handling ---

class _FormFields(HTMLParser):
    """Collects what a browser would submit: inputs with values (checkboxes/radios only when
    checked), each select's selected (else first) option, textareas. Entities are unescaped."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fields = {}
        self._select = None
        self._select_first = None
        self._select_chosen = None
        self._option_value = None
        self._option_selected = False
        self._option_text = ""
        self._textarea = None
        self._textarea_text = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "input" and a.get("name"):
            kind = (a.get("type") or "text").lower()
            if kind in ("checkbox", "radio"):
                if "checked" in a:
                    self.fields[a["name"]] = a.get("value") or "on"
            elif kind not in ("submit", "button", "reset", "image", "file"):
                self.fields[a["name"]] = a.get("value") or ""
        elif tag == "select" and a.get("name"):
            self._select, self._select_first, self._select_chosen = a["name"], None, None
        elif tag == "option" and self._select:
            self._option_value = a.get("value")
            self._option_selected = "selected" in a
            self._option_text = ""
        elif tag == "textarea" and a.get("name"):
            self._textarea, self._textarea_text = a["name"], ""

    def handle_data(self, data):
        if self._select:
            self._option_text += data
        if self._textarea:
            self._textarea_text += data

    def _close_option(self):
        if self._select is None:
            return
        value = self._option_value if self._option_value is not None else self._option_text.strip()
        if self._select_first is None:
            self._select_first = value
        if self._option_selected:
            self._select_chosen = value
        self._option_value, self._option_selected, self._option_text = None, False, ""

    def handle_endtag(self, tag):
        if tag == "option":
            self._close_option()
        elif tag == "select" and self._select:
            chosen = self._select_chosen if self._select_chosen is not None else self._select_first
            self.fields[self._select] = chosen if chosen is not None else ""
            self._select = None
        elif tag == "textarea" and self._textarea:
            self.fields[self._textarea] = self._textarea_text
            self._textarea = None


def form_fields(page):
    parser = _FormFields()
    parser.feed(page)
    parser.close()
    return parser.fields


def text_of(page):
    """Page text with tags removed and entities unescaped: assertions don't depend on markup."""
    return html.unescape(re.sub(r"<[^>]+>", " ", page))


def has_field(page, name):
    return re.search(r"""name\s*=\s*["']?%s["'\s/>]""" % re.escape(name), page) is not None


def review(client, requirements):
    resp = client.post("/", data={"requirements": requirements})
    return resp, resp.get_data(as_text=True)


def pending_of(page):
    fields = form_fields(page)
    assert "pending" in fields, "review page has no hidden `pending` field"
    json.loads(fields["pending"])  # PLAN: hidden JSON {"requirement_set", "presented_mapping"}
    return fields


def confirm(client, fields, **overrides):
    """POST /confirm with the review page's defaults, then overrides; a value of None drops the field."""
    data = dict(fields)
    for k, v in overrides.items():
        if v is None:
            data.pop(k, None)
        else:
            data[k] = v
    resp = client.post("/confirm", data=data)
    return resp, resp.get_data(as_text=True)


# record_id regex (documented): on the tag-free page text, the label "record_id" / "record id" /
# "Record ID" (any case, separated by space, _ or -), an optional ':' or '=', then a token of
# letters, digits, '_' or '-'. Every match is tried; the first one the store returns wins.
RECORD_ID = re.compile(r"record[\s_-]*id\s*[:=]?\s*([A-Za-z0-9][A-Za-z0-9_\-]*)", re.IGNORECASE)


def stored_record(page):
    for token in RECORD_ID.findall(text_of(page)):
        try:
            return retrieve_decision_record(token)
        except Exception:  # not a stored id; try the next match
            continue
    return None


def by_metric(record):
    return {c["metric"]: c for c in record["criteria_mapping"]}


# --- POST /: the mapping review page (UC.1.2-UC.1.6) ---

def test_SR_1_3_1_post_requirements_shows_mapping_review_page(client, runtime):
    # SR 1.3.1 / CR 1.3.6 / UC.1.2-UC.1.6: stated requirements in, presented mapping out, through the UI
    runtime["replies"] = [valid(COST)]
    resp, page = review(client, "Keep operating cost low.")
    assert resp.status_code == 200
    assert len(runtime["requests"]) == 1  # SR 1.2.3: one interpretation request per requirement
    text = text_of(page)
    assert "Keep operating cost low." in text
    assert "proposed" in text
    pending = json.loads(pending_of(page)["pending"])
    assert "requirement_set" in pending and "presented_mapping" in pending
    assert [r["text"] for r in pending["requirement_set"]] == ["Keep operating cost low."]


def test_CR_1_4_3_review_page_shows_each_criterion_with_its_rating(client, runtime):
    # CR 1.2.4 / CR 1.4.3 / SR 1.2.4: every proposed criterion shown with its rating and editable
    # fields; n is 0-based across requirements in presented order, k is the requirement index
    runtime["replies"] = [valid(COST, CTX), valid(OUT)]
    resp, page = review(client, "Keep operating cost low.\nHandle long documents.")
    assert resp.status_code == 200
    assert len(runtime["requests"]) == 2
    text = text_of(page)
    assert "Keep operating cost low." in text and "Handle long documents." in text
    fields = form_fields(page)
    for n, c in enumerate((COST, CTX, OUT)):
        for key in ("metric", "operator", "unit", "proxy_strength", "category", "rationale"):
            assert str(c[key]) in text, f"{c['criterion_id']}: {key} {c[key]!r} not shown"
        # the threshold may be shown as text or as the editable threshold_<n> field's value
        shown = (r"\b%s\b" % c["threshold"], r"\b%s\b" % "{:,}".format(c["threshold"]))
        as_text = any(re.search(s, text) for s in shown)
        as_field = re.sub(r"\.0+$", "", fields.get(f"threshold_{n}", "").strip()) == str(c["threshold"])
        assert as_text or as_field, f"{c['criterion_id']}: threshold not shown"
    for n in range(3):
        for field in ("keep", "designation", "weight", "threshold"):
            assert has_field(page, f"{field}_{n}"), f"missing editable field {field}_{n}"
    for k in range(2):
        for part in ("metric", "operator", "threshold", "unit", "designation", "weight"):
            assert has_field(page, f"new_{k}_{part}"), f"missing manual-row field new_{k}_{part}"
    assert not has_field(page, "keep_3")


def test_CR_1_4_3_review_page_defaults_compliance_hard_others_weighted_weight_1(client, runtime):
    # PLAN defaults on the review page: compliance -> hard; every other category -> weighted, weight 1
    runtime["replies"] = [valid(COST, RESIDENCY)]
    _, page = review(client, "Cost little and keep data in the EU.")
    fields = pending_of(page)
    assert fields.get("designation_0") == "weighted"
    assert float(fields.get("weight_0")) == 1
    assert fields.get("designation_1") == "hard"


# --- SPEC 3 failure path ---

def test_SPEC3_invalid_reply_is_resent_once(client, runtime):
    # SPEC 3 / SR 1.1.4 / SR 1.3.2: a bad response is retried once; the valid retry is presented
    runtime["replies"] = [INVALID, valid(COST)]
    resp, page = review(client, "Keep operating cost low.")
    assert resp.status_code == 200
    assert len(runtime["requests"]) == 2
    text = text_of(page)
    assert "interpretation_failed" not in text
    assert "input_price" in text and "proposed" in text


def test_SPEC3_interpretation_failed_shows_manual_entry(client, runtime):
    # SPEC 3: fails twice -> interpretation_failed, not dropped, no criteria made up; manual entry
    runtime["replies"] = [INVALID, INVALID, valid(COST)]
    resp, page = review(client, "Keep operating cost low.")
    assert resp.status_code == 200
    assert len(runtime["requests"]) == 2  # retried once, no more
    text = text_of(page)
    assert "interpretation_failed" in text
    assert "Keep operating cost low." in text
    assert has_field(page, "new_0_metric")
    assert not has_field(page, "keep_0")  # no proposed criterion was made up

    # the Technical Lead enters the criterion by hand and confirms (UC.1.9)
    fields = pending_of(page)
    resp, result = confirm(client, fields, new_0_metric="input_price", new_0_operator="<=",
                           new_0_threshold="", new_0_unit="USD per 1M input tokens",
                           new_0_designation="weighted", new_0_weight="1")
    assert resp.status_code == 200
    record = stored_record(result)
    assert record is not None, "no retrievable record_id on the result page"
    assert list(by_metric(record)) == ["input_price"]
    assert by_metric(record)["input_price"]["designation"] == "weighted"


@pytest.mark.parametrize("text", ["", "   \n  "])
def test_SR_1_1_5_empty_requirements_rejected_on_form(client, runtime, text):
    # SR 1.1.5: empty input is rejected -- the form again with the rejection message, HTTP 200
    blank_form = client.get("/").get_data(as_text=True)
    resp, page = review(client, text)
    assert resp.status_code == 200
    assert runtime["requests"] == []  # nothing sent for interpretation
    assert has_field(page, "requirements")
    assert not has_field(page, "pending")  # not the review page
    assert text_of(page) != text_of(blank_form)  # a rejection message was added


# --- POST /confirm (UC.1.7-UC.1.9 and the ranking chain) ---

def test_CR_1_1_1_confirm_ranks_with_the_confirmed_mapping_and_stores_record(client, runtime):
    # CR 1.1.1 / SR 1.1.1 / CR 2.1.2: ranking uses only the confirmed mapping; the record holds it unmodified
    runtime["replies"] = [valid(COST, CTX)]
    _, page = review(client, "Cheap with a long context.")
    fields = pending_of(page)
    resp, result = confirm(client, fields, keep_0="on", designation_0="weighted", weight_0="2",
                           threshold_0="5", keep_1="on", designation_1="weighted", weight_1="1",
                           threshold_1="100000")
    assert resp.status_code == 200
    assert any(mid in result for mid in CATALOG_IDS)
    record = stored_record(result)
    assert record is not None, "no retrievable record_id on the result page"
    mapping = by_metric(record)
    assert set(mapping) == {"input_price", "context_window"}
    assert mapping["input_price"]["designation"] == "weighted"
    assert float(mapping["input_price"]["weight"]) == 2
    assert float(mapping["input_price"]["threshold"]) == 5
    assert mapping["context_window"]["operator"] == ">="
    assert float(mapping["context_window"]["threshold"]) == 100000
    assert {k: float(v) for k, v in record["weights"].items()} == {
        mapping["input_price"]["criterion_id"]: 2.0, mapping["context_window"]["criterion_id"]: 1.0}
    assert record["ranking"], "file-mode catalog should rank"
    for mid in record["ranking"]:
        assert mid in result  # ranked model ids shown
    assert record["selected_model"] is None  # UC.1.17 stays planned (A22)


def test_CR_1_1_1_edited_weight_and_removed_criterion_are_applied(client, runtime):
    # CR 1.1.1 / UC.1.7-UC.1.8: an unchecked keep_<n> removes the criterion; edits are applied
    runtime["replies"] = [valid(COST, CTX, OUT)]
    _, page = review(client, "Cheap, long context, cheap output.")
    fields = pending_of(page)
    resp, result = confirm(client, fields, keep_0="on", designation_0="weighted", weight_0="3",
                           keep_1="on", designation_1="weighted", weight_1="1", threshold_1="200000",
                           keep_2=None)
    assert resp.status_code == 200
    record = stored_record(result)
    assert record is not None, "no retrievable record_id on the result page"
    mapping = by_metric(record)
    assert set(mapping) == {"input_price", "context_window"}  # output_price removed
    assert float(mapping["input_price"]["weight"]) == 3
    assert float(mapping["context_window"]["threshold"]) == 200000
    assert set(record["weights"]) == {mapping["input_price"]["criterion_id"],
                                      mapping["context_window"]["criterion_id"]}


def test_CR_1_1_1_hard_designation_excludes_failing_model(client, runtime):
    # CR 1.1.1 / CR 1.2.2: a criterion designated hard filters; the exclusion is shown and recorded
    runtime["replies"] = [valid(COST, CTX)]
    _, page = review(client, "Cheap with a long context.")
    fields = pending_of(page)
    resp, result = confirm(client, fields, keep_0="on", designation_0="hard", threshold_0="5",
                           weight_0="", keep_1="on", designation_1="weighted", weight_1="1")
    assert resp.status_code == 200
    record = stored_record(result)
    assert record is not None, "no retrievable record_id on the result page"
    assert by_metric(record)["input_price"]["designation"] == "hard"
    # claude-fable-5-1 costs 10.0 USD per 1M input tokens in the stored catalog
    assert "claude-fable-5-1" not in record["ranking"]
    assert "claude-fable-5-1" in json.dumps(record["excluded"])
    assert "claude-fable-5-1" in result  # exclusions shown


def test_CR_1_1_1_manual_row_is_added_to_the_confirmed_mapping(client, runtime):
    # CR 1.1.1 / UC.1.7: a manual row k stands for requirement k and joins the confirmed mapping
    runtime["replies"] = [valid(COST)]
    _, page = review(client, "Keep operating cost low.")
    fields = pending_of(page)
    resp, result = confirm(client, fields, keep_0="on", designation_0="weighted", weight_0="1",
                           new_0_metric="output_price", new_0_operator="<=", new_0_threshold="",
                           new_0_unit="USD per 1M output tokens", new_0_designation="weighted",
                           new_0_weight="2")
    assert resp.status_code == 200
    record = stored_record(result)
    assert record is not None, "no retrievable record_id on the result page"
    mapping = by_metric(record)
    assert set(mapping) == {"input_price", "output_price"}
    assert mapping["output_price"]["threshold"] is None  # blank threshold -> null
    assert float(mapping["output_price"]["weight"]) == 2
    rid = json.loads(fields["pending"])["requirement_set"][0]["requirement_id"]
    if "requirement_id" in mapping["output_price"]:
        assert mapping["output_price"]["requirement_id"] == rid


def test_CR_1_1_2_unknown_metric_in_manual_row_rejected_422(client, runtime):
    # CR 1.1.2 / CR 1.4.4: the confirmed mapping is checked against the known metrics list
    runtime["replies"] = [valid(COST)]
    _, page = review(client, "Keep operating cost low.")
    fields = pending_of(page)
    resp, again = confirm(client, fields, keep_0="on", designation_0="weighted", weight_0="1",
                          new_0_metric="vibes_index", new_0_operator=">=", new_0_threshold="",
                          new_0_unit="index", new_0_designation="weighted", new_0_weight="1")
    assert resp.status_code == 422
    assert has_field(again, "pending")  # the review page again, with the message
    assert stored_record(again) is None


def test_SR_1_1_1_weighted_criterion_without_weight_rejected_422(client, runtime):
    # SR 1.1.1: "A weighted criterion without a weight is rejected."
    runtime["replies"] = [valid(COST)]
    _, page = review(client, "Keep operating cost low.")
    fields = pending_of(page)
    resp, again = confirm(client, fields, keep_0="on", designation_0="weighted", weight_0="")
    assert resp.status_code == 422
    assert has_field(again, "pending")
    assert stored_record(again) is None


def test_A27_hard_only_mapping_shows_ranking_without_record(client, runtime):
    # PLAN / A27 / D-23: a record F.1.7 rejects (no weighted criterion) shows the ranking with the
    # rejection message instead of a record_id
    runtime["replies"] = [valid(CTX)]
    _, page = review(client, "Handle long documents.")
    fields = pending_of(page)
    resp, result = confirm(client, fields, keep_0="on", designation_0="hard", threshold_0="1",
                           weight_0="")
    assert resp.status_code == 200
    assert any(mid in result for mid in CATALOG_IDS)  # the ranking is still shown
    assert stored_record(result) is None


@pytest.mark.parametrize("pending", [None, "", "{not json"])
def test_UC_1_9_confirm_route_exists_and_requires_pending(client, runtime, pending):
    # UC.1.9: POST /confirm exists; without a valid `pending` from the review page nothing is ranked
    data = {} if pending is None else {"pending": pending}
    resp = client.post("/confirm", data=data)
    assert resp.status_code not in (404, 405)
    assert 400 <= resp.status_code < 500
    assert stored_record(resp.get_data(as_text=True)) is None
