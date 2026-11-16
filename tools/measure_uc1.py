"""Measured behavior harness for UC.1 (Lab Manual 10.4; docs/PLAN.md "Product build: instrumentation
and measured behavior").

Traces: SR 1.3.2 (MOP: interpretation response time per requirement), SR 2.1.1 / CR 2.1.1 (effort
budgets the simulation was traced to). Tooling, changes no product module: the stage callables are
wrapped at run time (module attributes) and the real web path is driven with the Flask test client.

  .venv/bin/python tools/measure_uc1.py --check
  .venv/bin/python tools/measure_uc1.py --runs 30 --warmup 1
  .venv/bin/python tools/measure_uc1.py --fake-runtime 0.2 --runs 3 --out /tmp/x   (no LM Studio)
"""

import argparse
import csv
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from provide_benchmark_evidence.__main__ import load_dotenv  # noqa: E402

load_dotenv()  # values already in the environment win

import app  # noqa: E402
import provide_benchmark_evidence as f7  # noqa: E402
from provide_llm_selection_decision_support import propose_criteria_mapping as pcm  # noqa: E402
from provide_requirement_interpretation import DEFAULT_RUNTIME_URL, LOCAL_HOSTS  # noqa: E402

# Sample SCENARIO_03 + SCENARIO_04 sentences, verbatim, one per line (PLAN: fixed for all runs)
SCENARIO_TEXT = "\n".join([
    "This is a high-volume customer assistant handling relatively straightforward requests.",
    "Keeping cost low and responding quickly are more important than having the strongest reasoning model.",
    "Our application handles EU customer data.",
    "Company policy requires customer data to be stored and processed only within the EU.",
    "This requirement is non-negotiable.",
])

HEADER = ["run_id", "phase", "stage_id", "stage_name", "boundary", "call_index", "requirement_id",
          "t_entry_wall", "t_entry_ns", "t_exit_ns", "duration_s", "ok", "error"]

TEMPLATE_STAGES = {  # render_template name -> (stage_id, stage_name, boundary)
    "review.html": ("UC.1.6b", "Present mapping (render review.html)", "C.1->TL"),
    "result.html": ("UC.1.15-16b", "Present ranking and finding (render result.html)", "C.1->TL"),
}


# --- recorder and wrappers ---

class Recorder:
    def __init__(self):
        self.rows, self.capture, self.run_id, self.phase = [], {}, 0, ""
        self._counts = {}

    def start_run(self, run_id, phase):
        self.rows, self.capture, self.run_id, self.phase, self._counts = [], {}, run_id, phase, {}

    def time(self, stage, fn, *args, requirement_id="", **kwargs):
        """Call fn, recording one row; exit is recorded on exception too (ok=0), which is re-raised."""
        stage_id, stage_name, boundary = stage
        index = self._counts.get(stage_id, 0)
        self._counts[stage_id] = index + 1
        wall, t0 = datetime.now(timezone.utc).isoformat(), time.perf_counter_ns()
        error = ""
        try:
            return fn(*args, **kwargs)
        except BaseException as e:
            error = type(e).__name__
            raise
        finally:
            t1 = time.perf_counter_ns()
            self.rows.append({"run_id": self.run_id, "phase": self.phase, "stage_id": stage_id,
                              "stage_name": stage_name, "boundary": boundary, "call_index": index,
                              "requirement_id": requirement_id, "t_entry_wall": wall, "t_entry_ns": t0,
                              "t_exit_ns": t1, "duration_s": f"{(t1 - t0) / 1e9:.6f}",
                              "ok": 0 if error else 1, "error": error})


REC = Recorder()


def wrap(owner, attr, stage, hook=None):
    """Replace owner.attr with a timed wrapper. hook(args, kwargs, result) captures run facts."""
    original = getattr(owner, attr)

    def wrapper(*args, **kwargs):
        rid = ""
        if attr == "send_interpretation_request" and args and isinstance(args[0], dict):
            rid = args[0].get("requirement_id", "")
        result = REC.time(stage, original, *args, requirement_id=rid, **kwargs)
        if hook:
            hook(args, kwargs, result)
        return result

    wrapper.__wrapped__ = original
    setattr(owner, attr, wrapper)


def wrap_render_template():
    original = app.render_template

    def wrapper(name, **context):
        stage = TEMPLATE_STAGES.get(name, (f"RENDER:{name}", f"Render {name}", "C.1->TL"))
        if name == "result.html":
            REC.capture["record_stored"] = context.get("record") is not None
            REC.capture["record_error"] = context.get("record_error")
        return REC.time(stage, original, name, **context)

    app.render_template = wrapper


def _capture_rationale(args, kwargs, result):
    REC.capture["n_ranked"], REC.capture["n_excluded"] = len(args[0]), len(args[1])


def instrument():
    # Targets are the objects called at run time: propose_mapping looks up pcm._c111.x / _c112 / _c113
    # at call time; app.py binds the F.1.2-F.1.7 names with `from ... import`, so its module attributes.
    c111, c112, c113 = pcm._c111, pcm._c112, pcm._c113
    wrap(c111, "request_interpretation", ("UC.1.3", "Submit requirements", "C.1"))
    wrap(c111, "send_interpretation_request", ("UC.1.4", "Interpret (per requirement)", "C.1<->C.8"))
    wrap(c112, "validate_proposed_criteria", ("UC.1.5", "Assign confidence / validate", "C.1"))
    wrap(c113, "present_criteria_mapping", ("UC.1.6a", "Present mapping (C.1.1.3)", "C.1"))
    wrap_render_template()
    wrap(app._c114, "distribute_confirmed_mapping", ("C.1.1.4", "Distribute confirmed mapping", "C.1"))
    wrap(app, "retrieve_model_data_request", ("UC.1.10", "Request model data", "C.1->C.7"))
    wrap(app, "provide_model_data", ("UC.1.11", "Retrieve spec and benchmark data", "C.1<->C.7"))
    wrap(app, "receive_model_data", ("F.1.2-receive", "Receive model data", "C.1"))
    wrap(app, "apply_hard_constraints", ("UC.1.12", "Exclude (hard constraints)", "C.1"))
    wrap(app, "score_and_rank_candidates", ("UC.1.13", "Score and rank", "C.1"))
    wrap(app, "analyze_ranking_sensitivity", ("UC.1.14", "Sensitivity", "C.1"))
    wrap(app, "report_selection_rationale", ("UC.1.15-16a", "Present ranking and finding (F.1.6)", "C.1"),
         hook=_capture_rationale)
    wrap(app, "generate_and_store_decision_record", ("UC.1.18", "Generate decision record", "C.1->TL"))


# --- review page form fields (what a browser submits with every default accepted) ---

class FormFields(HTMLParser):
    """Inputs with values (checkboxes/radios only when checked), each select's selected (else first)
    option, textareas. Same rules as tests/test_mapping_review_ui.py's parser."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fields, self._select, self._textarea, self._text = {}, None, None, ""
        self._first = self._chosen = self._opt_value = None
        self._opt_selected = False

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
            self._select, self._first, self._chosen = a["name"], None, None
        elif tag == "option" and self._select:
            self._opt_value, self._opt_selected, self._text = a.get("value"), "selected" in a, ""
        elif tag == "textarea" and a.get("name"):
            self._textarea, self._text = a["name"], ""

    def handle_data(self, data):
        if self._select or self._textarea:
            self._text += data

    def handle_endtag(self, tag):
        if tag == "option" and self._select:
            value = self._opt_value if self._opt_value is not None else self._text.strip()
            self._first = value if self._first is None else self._first
            self._chosen = value if self._opt_selected else self._chosen
            self._opt_value, self._opt_selected, self._text = None, False, ""
        elif tag == "select" and self._select:
            chosen = self._chosen if self._chosen is not None else self._first
            self.fields[self._select] = chosen if chosen is not None else ""
            self._select = None
        elif tag == "textarea" and self._textarea:
            self.fields[self._textarea], self._textarea = self._text, None


def form_fields(page):
    parser = FormFields()
    parser.feed(page)
    parser.close()
    return parser.fields


# --- fake OpenAI-compatible runtime (harness check without LM Studio) ---

EU = ["EU", "AT", "BE", "DE", "DK", "ES", "FI", "FR", "IE", "IT", "NL", "PL", "SE"]
FAKE_CRITERIA = {  # requirement number -> one valid SPEC 3 criterion (metric, operator, threshold, unit, category)
    1: ("latency_p50", "<=", 2, "seconds", "capability"),
    2: ("input_price", "<=", 5, "USD per 1M input tokens", "cost"),
    3: ("data_residency", "in", EU, "ISO 3166-1 alpha-2", "compliance"),
    4: ("data_residency", "in", EU, "ISO 3166-1 alpha-2", "compliance"),
    5: ("output_price", "<=", 20, "USD per 1M output tokens", "cost"),
}


def fake_reply(rid):
    m = re.search(r"(\d+)$", rid)
    metric, op, threshold, unit, category = FAKE_CRITERIA.get(int(m.group(1)) if m else 0, FAKE_CRITERIA[2])
    return {"requirement_id": rid, "no_suitable_proxy": False,
            "criteria": [{"criterion_id": f"{rid}-{metric}", "metric": metric, "operator": op,
                          "threshold": threshold, "unit": unit, "proxy_strength": "strong",
                          "category": category, "rationale": f"fake runtime: {metric} stands for {rid}"}]}


def start_fake_runtime(delay_s):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, payload):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        def do_GET(self):
            self._send({"object": "list", "data": [{"id": "fake-runtime", "object": "model"}]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            text = "\n".join(str(m.get("content", "")) for m in body.get("messages", []))
            m = re.search(r"requirement_id:\s*(\S+)", text)
            time.sleep(delay_s)
            self._send({"choices": [{"message": {"content": json.dumps(fake_reply(m.group(1) if m else ""))}}]})

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}/v1"


# --- preflight ---

def runtime_url():
    return os.environ.get("LLM_RUNTIME_URL") or DEFAULT_RUNTIME_URL


def list_models(base_url):
    if urlparse(base_url).hostname not in LOCAL_HOSTS:  # SR 2.2.1 -- never contact a non-local runtime
        return {"error": f"LLM_RUNTIME_URL host {urlparse(base_url).hostname!r} is not local"}
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models", timeout=5) as r:
            return {"models": [m.get("id") for m in json.loads(r.read().decode()).get("data", [])]}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"error": f"{type(e).__name__}: {getattr(e, 'reason', e)}"}


def data_source():
    db = f7._snapshot_db()
    return {"benchmark_source": os.environ.get("BENCHMARK_SOURCE") or "api (default)",
            "snapshot_db": str(db), "snapshot_db_exists": db.exists(),
            "snapshot_db_mtime": datetime.fromtimestamp(db.stat().st_mtime, timezone.utc).isoformat()
            if db.exists() else None}


def check():
    url = runtime_url()
    models, source = list_models(url), data_source()
    print(f"LLM_RUNTIME_URL  {url}")
    print(f"LLM_MODEL        {os.environ.get('LLM_MODEL') or '(default)'}")
    print(f"/models          {models.get('models', models.get('error'))}")
    for k, v in source.items():
        print(f"{k:<16} {v}")
    ok = "models" in models and (source["benchmark_source"] == "file" or source["snapshot_db_exists"])
    print("preflight:", "OK" if ok else "NOT READY")
    return 0 if ok else 1


# --- runs ---

def one_run(client, run_id, phase):
    REC.start_run(run_id, phase)
    info = {"run_id": run_id, "phase": phase, "status_post": None, "status_confirm": None,
            "n_requirements": None, "n_uc14_calls": 0, "n_ranked": None, "n_excluded": None,
            "record_stored": False, "error": None}
    try:
        resp = REC.time(("REQ:POST /", "Request POST /", "REQ"), client.post, "/",
                        data={"requirements": SCENARIO_TEXT})
        info["status_post"] = resp.status_code
        if resp.status_code != 200:
            raise RuntimeError(f"POST / returned {resp.status_code}")
        fields = form_fields(resp.get_data(as_text=True))
        info["n_requirements"] = len(json.loads(fields["pending"])["requirement_set"])
        resp = REC.time(("REQ:POST /confirm", "Request POST /confirm", "REQ"), client.post, "/confirm",
                        data=fields)
        info["status_confirm"] = resp.status_code
        if resp.status_code != 200:
            raise RuntimeError(f"POST /confirm returned {resp.status_code}")
        info["error"] = REC.capture.get("record_error")
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
    info["n_uc14_calls"] = sum(r["stage_id"] == "UC.1.4" for r in REC.rows)
    for k in ("n_ranked", "n_excluded", "record_stored"):
        info[k] = REC.capture.get(k, info[k])
    return info


def git_sha():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_dirty():
    # Uncommitted tracked changes under test (e.g. the D-29 fix before it is committed), so the
    # commit hash alone never misdescribes the code that was measured.
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
        return [line[3:] for line in out.splitlines()]
    except (OSError, subprocess.CalledProcessError):
        return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--runs", type=int, default=30)
    p.add_argument("--warmup", type=int, default=1)
    p.add_argument("--out", type=Path, default=ROOT / "docs" / "validation" / "measured-behavior")
    p.add_argument("--fake-runtime", type=float, metavar="DELAY_S")
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)

    if args.fake_runtime is not None:
        _server, os.environ["LLM_RUNTIME_URL"] = start_fake_runtime(args.fake_runtime)
    if args.check:
        return check()

    os.environ["DECISION_RECORD_DIR"] = tempfile.mkdtemp(prefix="uc1_records_")  # keep data/ untouched
    instrument()
    args.out.mkdir(parents=True, exist_ok=True)
    meta = {"start_wall": datetime.now(timezone.utc).isoformat(), "end_wall": None, "git_commit": git_sha(), "git_dirty_paths": git_dirty(),
            "python": platform.python_version(), "llm_runtime_url": runtime_url(),
            "llm_model": os.environ.get("LLM_MODEL"), "runtime_models": list_models(runtime_url()),
            **data_source(), "decision_record_dir": os.environ["DECISION_RECORD_DIR"],
            "scenario_text": SCENARIO_TEXT, "runs": args.runs, "warmup": args.warmup,
            "fake_runtime": args.fake_runtime is not None, "fake_runtime_delay_s": args.fake_runtime,
            "per_run": []}
    meta_path = args.out / "runs_meta.json"
    schedule = [(-(k + 1), "warmup") for k in range(args.warmup)] + [(n, "measured")
                                                                     for n in range(1, args.runs + 1)]
    with open(args.out / "runs.csv", "w", newline="") as f, app.app.test_client() as client:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for run_id, phase in schedule:
            info = one_run(client, run_id, phase)
            writer.writerows(REC.rows)
            f.flush()  # a crash keeps completed runs
            meta["per_run"].append(info)
            meta_path.write_text(json.dumps(meta, indent=2))
            post = next((float(r["duration_s"]) for r in REC.rows if r["stage_id"] == "REQ:POST /"), float("nan"))
            print(f"run {run_id:>3} {phase:<8} POST / {post:7.2f} s  UC.1.4 calls {info['n_uc14_calls']}  "
                  f"HTTP {info['status_post']}/{info['status_confirm']}"
                  + (f"  error: {info['error']}" if info["error"] else ""), flush=True)
    meta["end_wall"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
