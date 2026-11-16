"""Compare measured UC.1 stage durations with the simulated duration settings.

Lab Manual 10.4 (comparison table and plots): reads the per-stage timings written by
tools/measure_uc1.py (runs.csv, runs_meta.json) and the human walkthrough log
(docs/validation/walkthroughs.csv), and writes comparison.md plus three plots into the
runs directory:

  stage_comparison.png               per-stage measured distribution vs simulated mean +/- 1 SD
  interpretation_vs_simulated.png    measured per-run UC.1.4 totals vs simulated N(90, 25)
  interpretation_per_requirement.png UC.1.4 per-call durations by requirement

Traces to:
  SR 1.3.2  MOP "interpretation response time per requirement" (per-requirement UC.1.4 table)
  SR 2.1.1  effort budget the simulation was traced to (hybrid end-to-end line)
  CR 2.1.1  mapping review effort budget (human stages table, UC.1.7-1.9)

Tooling only: lives outside backend/ and changes no product module (docs/PLAN.md,
"Product build: instrumentation and measured behavior").

Usage:
  .venv/bin/python tools/compare_measured_simulated.py \
      [--runs-dir docs/validation/measured-behavior] \
      [--walkthroughs docs/validation/walkthroughs.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DASH = "—"

# ---------------------------------------------------------------------------
# Simulated parameters (seconds).
# Source: SYSEN5151Modeling.pdf Table X "Duration settings for the actions of both
# scenarios" (UC.1 baseline, local runtime). Normal(mean, SD) unless stated.
# Each entry: aggregated stage key -> (name, mean, SD, distribution label).
# ---------------------------------------------------------------------------
SIMULATED = {
    "UC.1.3": ("Submit requirements for interpretation", 0.5, 0.1, "N(0.5, 0.1)"),
    "UC.1.4": ("Interpret requirements (per comparison)", 90.0, 25.0, "N(90, 25)"),
    "UC.1.5": ("Assign confidence / validate", 0.2, 0.05, "N(0.2, 0.05)"),
    "UC.1.6": ("Present proposed mapping", 1.0, 0.2, "N(1, 0.2)"),
    "UC.1.10": ("Request model data", 0.5, 0.1, "N(0.5, 0.1)"),
    # Exponential, lambda = 0.5 /s -> mean 2 s, SD 2 s.
    "UC.1.11": ("Retrieve spec and benchmark data", 2.0, 2.0, "Exp(mean 2)"),
    "UC.1.12": ("Exclude (hard constraints)", 0.2, 0.05, "N(0.2, 0.05)"),
    "UC.1.13": ("Score and rank", 0.3, 0.05, "N(0.3, 0.05)"),
    "UC.1.14": ("Sensitivity analysis", 0.5, 0.1, "N(0.5, 0.1)"),
    # Actions 15 + 16: N(1, 0.2) + N(0.5, 0.1) -> mean 1.5, SD sqrt(0.04 + 0.01).
    "UC.1.15-16": ("Present ranking and finding", 1.5, math.sqrt(0.05), "N(1,0.2)+N(0.5,0.1)"),
    "UC.1.18": ("Generate decision record", 0.5, 0.1, "N(0.5, 0.1)"),
}

# Instrumented but not modelled in the simulation (simulated column shows a dash).
UNMODELLED = {
    "C.1.1.4": "Distribute confirmed mapping (not modelled)",
    "F.1.2-receive": "Receive model data (not modelled)",
}

# Display order of aggregated stages (follows the UC.1 sequence).
STAGE_ORDER = [
    "UC.1.3", "UC.1.4", "UC.1.5", "UC.1.6", "C.1.1.4", "UC.1.10", "UC.1.11",
    "F.1.2-receive", "UC.1.12", "UC.1.13", "UC.1.14", "UC.1.15-16", "UC.1.18",
]

# Raw stage_id -> aggregated stage key (split stages are summed per run).
RAW_TO_STAGE = {
    "UC.1.6a": "UC.1.6", "UC.1.6b": "UC.1.6",
    "UC.1.15-16a": "UC.1.15-16", "UC.1.15-16b": "UC.1.15-16",
}

REQUEST_IDS = ("REQ:POST /", "REQ:POST /confirm")

# Technical Lead actions, Table X: UC.1.7 review 240/60, UC.1.8 weight 120/30, UC.1.9 confirm 15/5.
HUMAN_REVIEW = [(240.0, 60.0), (120.0, 30.0), (15.0, 5.0)]
HUMAN_REVIEW_MEAN = sum(m for m, _ in HUMAN_REVIEW)                     # 375 s
HUMAN_REVIEW_SD = math.sqrt(sum(s * s for _, s in HUMAN_REVIEW))        # sqrt(4525) s

# All 7 Technical Lead actions, Table X: 1 initiate 30/10, 2 enter 300/60, 7, 8, 9,
# 17 review recommendation 180/45, 19 export 20/5  -> 905 s (Table X branch share).
HUMAN_ALL = [(30.0, 10.0), (300.0, 60.0), *HUMAN_REVIEW, (180.0, 45.0), (20.0, 5.0)]
HUMAN_ALL_MEAN = sum(m for m, _ in HUMAN_ALL)
HUMAN_ALL_VAR = sum(s * s for _, s in HUMAN_ALL)

# Modeling report Monte Carlo results (100 runs per scenario), minutes.
MC_BASELINE_MEAN_MIN, MC_BASELINE_SD_MIN = 16.84, 1.74
MC_UC1A_MEAN_MIN, MC_UC1A_SD_MIN = 15.42, 1.76

# Colourblind-safe pair (validated reference categorical slots 1 and 2); the same two
# colours mean "measured" and "simulated" in every plot.
C_MEASURED = "#2a78d6"
C_SIMULATED = "#eb6834"
C_INK = "#0b0b0b"
C_MUTED = "#52514e"
C_GRID = "#d9d8d4"


def sim_system_total() -> tuple[float, float]:
    """Simulated system total: sum of stage means, SD = sqrt(sum of variances)."""
    mean = sum(v[1] for v in SIMULATED.values())
    sd = math.sqrt(sum(v[2] ** 2 for v in SIMULATED.values()))
    return mean, sd


# ---------------------------------------------------------------------------
# Formatting and statistics helpers
# ---------------------------------------------------------------------------
def fmt(x: float | None, sig: int = 4) -> str:
    """Fixed-point with `sig` significant figures (0.0001234 -> 0.0001234, 152.37 -> 152.4)."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return DASH
    if x == 0:
        return "0"
    decimals = max(0, sig - 1 - math.floor(math.log10(abs(x))))
    return f"{x:,.{decimals}f}"


def describe(values: list[float]) -> dict:
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "median": None, "p95": None, "min": None, "max": None}
    p95 = statistics.quantiles(vals, n=20, method="inclusive")[18] if n >= 2 else vals[0]
    return {
        "n": n,
        "mean": statistics.fmean(vals),
        "sd": statistics.stdev(vals) if n >= 2 else None,
        "median": statistics.median(vals),
        "p95": p95,
        "min": vals[0],
        "max": vals[-1],
    }


def within_2sd(measured_mean, sim_mean, sim_sd) -> str:
    if measured_mean is None or sim_mean is None:
        return DASH
    lo, hi = sim_mean - 2 * sim_sd, sim_mean + 2 * sim_sd
    if lo <= measured_mean <= hi:
        return "yes"
    return "no (above)" if measured_mean > hi else "no (below)"


def ratio(measured_mean, sim_mean) -> str:
    if measured_mean is None or not sim_mean:
        return DASH
    return fmt(measured_mean / sim_mean, 3)


def md_table(headers: list[str], rows: list[list[str]], align: list[str] | None = None) -> str:
    align = align or ["l"] + ["r"] * (len(headers) - 1)
    sep = ["---:" if a == "r" else "---" for a in align]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def req_sort_key(req: str):
    tail = req.rsplit("-", 1)[-1]
    return (0, int(tail), req) if tail.isdigit() else (1, 0, req)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_runs(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["duration_s"] = float(r["duration_s"])
    return rows


def load_meta(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def meta_fields(meta) -> dict[str, list[str]]:
    """Collect scalar fields whose key mentions 'runtime' or 'model', from a dict, a list of
    per-run dicts, or a dict with a 'runs' list. Values are de-duplicated."""
    found: dict[str, list[str]] = {}

    def visit(d):
        if not isinstance(d, dict):
            return
        for k, v in d.items():
            if isinstance(v, dict):
                visit(v)
            elif isinstance(v, list):
                for item in v:
                    visit(item)
            elif any(tok in k.lower() for tok in ("runtime", "model")) and v is not None:
                vals = found.setdefault(k, [])
                if str(v) not in vals:
                    vals.append(str(v))

    if isinstance(meta, list):
        for item in meta:
            visit(item)
    else:
        visit(meta)
    return found


def load_walkthroughs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("scenario", "").startswith("mapping_review")]


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def per_run_stage_totals(rows: list[dict]) -> dict[str, dict[str, float]]:
    """run_id -> {aggregated stage key | 'System total' | 'Request wall time' | 'Unattributed'}.

    UC.1.4 and UC.1.5 are summed over all calls in the run (the simulation models one
    interpretation per comparison); split stages a+b are summed; RENDER:* rows are kept
    under their own key and excluded from the system total (they may nest inside UC.1.6b /
    UC.1.15-16b)."""
    out: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        sid = r["stage_id"]
        key = RAW_TO_STAGE.get(sid, sid)
        out[r["run_id"]][key] += r["duration_s"]
    for run_id, d in out.items():
        d["System total"] = sum(d[k] for k in STAGE_ORDER if k in d)
        if any(k in d for k in REQUEST_IDS):
            d["Request wall time"] = sum(d.get(k, 0.0) for k in REQUEST_IDS)
            d["Unattributed"] = d["Request wall time"] - d["System total"]
    return {k: dict(v) for k, v in out.items()}


def stage_values(per_run: dict[str, dict[str, float]], run_ids: list[str], key: str) -> list[float]:
    return [per_run[r][key] for r in run_ids if key in per_run.get(r, {})]


def date_range(rows: list[dict]) -> str:
    stamps = []
    for r in rows:
        s = (r.get("t_entry_wall") or "").strip()
        if not s:
            continue
        try:
            stamps.append(datetime.fromisoformat(s.replace("Z", "+00:00")))
        except ValueError:
            continue
    if not stamps:
        return DASH
    return f"{min(stamps).isoformat(timespec='seconds')} to {max(stamps).isoformat(timespec='seconds')}"


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------
def stage_rows_spec(extra_keys: list[str]) -> list[tuple[str, str, float | None, float | None]]:
    """(key, name, sim mean, sim SD) for every row of the per-stage table, in order."""
    spec = []
    for k in STAGE_ORDER:
        if k in SIMULATED:
            name, mu, sd, _ = SIMULATED[k]
            spec.append((k, name, mu, sd))
        else:
            spec.append((k, UNMODELLED[k], None, None))
    for k in extra_keys:
        spec.append((k, "Render (informational, not in system total)", None, None))
    st_mu, st_sd = sim_system_total()
    spec.append(("System total", "Sum of stage rows above (modelled + unmodelled)", st_mu, st_sd))
    spec.append(("Request wall time", "REQ:POST / + REQ:POST /confirm", None, None))
    spec.append(("Unattributed", "Request wall time - system total", None, None))
    return spec


def build_stage_table(per_run, measured_ids, spec) -> tuple[str, dict]:
    headers = ["Stage", "Name", "Sim mean (s)", "Sim SD (s)", "n", "Mean (s)", "SD (s)",
               "Median (s)", "p95 (s)", "Min (s)", "Max (s)", "Meas/Sim", "Within sim ±2SD?"]
    rows, stats = [], {}
    for key, name, mu, sd in spec:
        d = describe(stage_values(per_run, measured_ids, key))
        stats[key] = d
        label = f"**{key}**" if key in ("System total", "Request wall time", "Unattributed") else key
        rows.append([
            label, name, fmt(mu), fmt(sd), d["n"], fmt(d["mean"]), fmt(d["sd"]), fmt(d["median"]),
            fmt(d["p95"]), fmt(d["min"]), fmt(d["max"]), ratio(d["mean"], mu),
            within_2sd(d["mean"], mu, sd) if mu is not None else DASH,
        ])
    align = ["l", "l"] + ["r"] * 10 + ["l"]
    return md_table(headers, rows, align), stats


def build_warmup_table(per_run, warmup_ids, stats, spec) -> str:
    if not warmup_ids:
        return "_No warm-up run in runs.csv._"
    headers = ["Stage", "Sim mean (s)"] + [f"Warm-up {w} (s)" for w in warmup_ids] + [
        "Measured mean (s)", "Warm-up / measured mean"]
    rows = []
    for key, _name, mu, _sd in spec:
        vals = [per_run.get(w, {}).get(key) for w in warmup_ids]
        m = stats[key]["mean"]
        first = vals[0]
        rows.append([key, fmt(mu)] + [fmt(v) for v in vals] + [
            fmt(m), fmt(first / m, 3) if (first is not None and m) else DASH])
    return md_table(headers, rows)


def build_requirement_table(measured_rows, measured_ids) -> tuple[str, dict]:
    calls = [r for r in measured_rows if r["stage_id"] == "UC.1.4"]
    by_req: dict[str, list[float]] = defaultdict(list)
    per_run_req: dict[tuple[str, str], int] = defaultdict(int)
    for r in calls:
        req = (r.get("requirement_id") or "").strip() or "(none)"
        by_req[req].append(r["duration_s"])
        per_run_req[(r["run_id"], req)] += 1
    headers = ["Requirement", "n calls", "Mean (s)", "SD (s)", "Median (s)", "Min (s)", "Max (s)",
               "Runs with re-send"]
    rows = []
    for req in sorted(by_req, key=req_sort_key):
        d = describe(by_req[req])
        resends = sum(1 for (run, rq), c in per_run_req.items() if rq == req and c > 1)
        rows.append([req, d["n"], fmt(d["mean"]), fmt(d["sd"]), fmt(d["median"]), fmt(d["min"]),
                     fmt(d["max"]), resends])
    overall = describe([r["duration_s"] for r in calls])
    total_resends = sum(1 for c in per_run_req.values() if c > 1)
    rows.append(["**All calls**", overall["n"], fmt(overall["mean"]), fmt(overall["sd"]),
                 fmt(overall["median"]), fmt(overall["min"]), fmt(overall["max"]), total_resends])
    calls_per_run = [sum(c for (run, _), c in per_run_req.items() if run == rid) for rid in measured_ids]
    cpr = describe(calls_per_run)
    note = (f"Calls per run: mean {fmt(cpr['mean'], 3)}, min {cpr['min']}, max {cpr['max']} "
            f"(n = {cpr['n']} runs). Overall per-call p95 {fmt(overall['p95'])} s. "
            "Model rationale (Table X): about 15-20 s per requirement on a laptop.")
    return md_table(headers, rows) + "\n\n" + note, by_req


def build_human_table(walk_rows) -> str:
    secs = [float(r["minutes"]) * 60.0 for r in walk_rows if r.get("minutes", "").strip()]
    d = describe(secs)
    headers = ["Stages", "Source", "n", "Mean (s)", "SD (s)", "Min (s)", "Max (s)", "Sim mean (s)",
               "Sim SD (s)", "Meas/Sim", "Within sim ±2SD?"]
    row = ["UC.1.7-1.9 review, weight, confirm", "walkthroughs.csv (mapping_review*)", d["n"],
           fmt(d["mean"]), fmt(d["sd"]), fmt(d["min"]), fmt(d["max"]), fmt(HUMAN_REVIEW_MEAN),
           fmt(HUMAN_REVIEW_SD), ratio(d["mean"], HUMAN_REVIEW_MEAN),
           within_2sd(d["mean"], HUMAN_REVIEW_MEAN, HUMAN_REVIEW_SD)]
    caveat = ("Separate small sample of timed walkthroughs, recorded by an operator to the nearest "
              "minute; not harness-measured. CR 2.1.1 budget: 10 min (600 s).")
    return md_table(headers, [row], ["l", "l"] + ["r"] * 8 + ["l"]) + "\n\n" + caveat


def build_hybrid(stats) -> str:
    st = stats["System total"]
    if st["mean"] is None:
        return "_No measured system total._"
    hyb_mean_s = st["mean"] + HUMAN_ALL_MEAN
    hyb_sd_s = math.sqrt((st["sd"] or 0.0) ** 2 + HUMAN_ALL_VAR)
    headers = ["Scenario", "Mean (min)", "SD (min)", "Basis"]
    rows = [
        ["**Hybrid (measured system + estimated human)**", fmt(hyb_mean_s / 60), fmt(hyb_sd_s / 60),
         f"measured system total {fmt(st['mean'])} s + Table X Technical Lead means "
         f"{fmt(HUMAN_ALL_MEAN)} s (7 actions)"],
        ["UC.1 baseline, Monte Carlo (100 runs)", f"{MC_BASELINE_MEAN_MIN:g}", f"{MC_BASELINE_SD_MIN:g}",
         "SYSEN5151Modeling.pdf Monte Carlo results"],
        ["UC.1A hosted runtime, Monte Carlo (100 runs)", f"{MC_UC1A_MEAN_MIN:g}", f"{MC_UC1A_SD_MIN:g}",
         "SYSEN5151Modeling.pdf Monte Carlo results"],
    ]
    note = ("Hybrid SD = sqrt(measured system-total variance + sum of Table X human variances). "
            "Human time is estimated, not measured; the harness accepts every default (zero human "
            "time by construction).")
    return md_table(headers, rows, ["l", "r", "r", "l"]) + "\n\n" + note


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def _style(ax):
    ax.grid(True, axis="x", color=C_GRID, linewidth=0.6, which="major")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=C_MUTED, labelsize=9)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(C_MUTED)


def _boxprops(color):
    return dict(
        patch_artist=True,
        boxprops=dict(facecolor=color + "33", edgecolor=color, linewidth=1.2),
        medianprops=dict(color=color, linewidth=2),
        whiskerprops=dict(color=color, linewidth=1),
        capprops=dict(color=color, linewidth=1),
        flierprops=dict(marker="o", markersize=3.5, markerfacecolor=color, markeredgecolor="none",
                        alpha=0.7),
    )


def plot_stage_comparison(per_run, measured_ids, spec, out: Path):
    keys = [s for s in spec if s[0] != "Unattributed"]  # can be negative; not loggable
    data, labels, sims = [], [], []
    for key, name, mu, sd in keys:
        vals = [v for v in stage_values(per_run, measured_ids, key) if v > 0]
        data.append(vals if vals else [float("nan")])
        labels.append(key)
        sims.append((mu, sd))
    n = len(keys)
    fig, ax = plt.subplots(figsize=(9, 0.42 * n + 1.8), dpi=150)
    positions = list(range(n, 0, -1))  # first stage at top
    ax.boxplot(data, positions=positions, orientation="horizontal", widths=0.55,
               **_boxprops(C_MEASURED))
    all_pos = [v for d in data for v in d if v == v and v > 0]
    lo_axis = min(all_pos + [m - s for m, s in sims if m is not None and m - s > 0]) / 2
    hi_axis = max(all_pos + [m + s for m, s in sims if m is not None]) * 2
    clipped = False
    for pos, (mu, sd) in zip(positions, sims):
        if mu is None:
            continue
        left = mu - sd
        if left <= 0:
            left, clipped = lo_axis, True
        ax.errorbar(mu, pos + 0.3, xerr=[[mu - left], [sd]], fmt="D", color=C_SIMULATED,
                    markersize=6, capsize=3, elinewidth=1.4, zorder=5)
    ax.set_xscale("log")
    ax.set_xlim(lo_axis, hi_axis)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9, color=C_INK)
    ax.set_ylim(0.3, n + 0.8)
    # Separate the per-stage rows from the summary rows.
    n_stage_rows = sum(1 for k in keys if k[0] not in ("System total", "Request wall time"))
    ax.axhline(n - n_stage_rows + 0.5, color=C_MUTED, linewidth=0.8, linestyle=":")
    ax.set_xlabel("Duration per run (seconds, log scale)", color=C_INK)
    ax.set_title(f"UC.1 stage durations: measured (n = {len(measured_ids)} runs) vs simulated",
                 color=C_INK, fontsize=11, loc="left", pad=30)
    _style(ax)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=C_MEASURED + "33", edgecolor=C_MEASURED, label="Measured (box: IQR, line: median)"),
        Line2D([], [], color=C_SIMULATED, marker="D", linestyle="-", label="Simulated mean ± 1 SD"),
    ]
    # Legend above the axes so it never covers a stage row.
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=8.5,
              frameon=False)
    if clipped:
        fig.text(0.01, 0.01, "UC.1.11 is Exp(mean 2): mean - 1 SD = 0, bar clipped at the axis edge.",
                 fontsize=7.5, color=C_MUTED)
    fig.tight_layout(rect=(0, 0.03 if clipped else 0, 1, 1))
    fig.savefig(out)
    plt.close(fig)


def plot_interpretation_hist(per_run, measured_ids, out: Path):
    vals = stage_values(per_run, measured_ids, "UC.1.4")
    if not vals:
        return
    mu, sd = SIMULATED["UC.1.4"][1], SIMULATED["UC.1.4"][2]
    n = len(vals)
    nbins = max(5, min(15, round(math.sqrt(n)) + 2))
    vmin, vmax = min(vals), max(vals)
    width = (vmax - vmin) / nbins if vmax > vmin else 1.0
    edges = [vmin + i * width for i in range(nbins + 1)]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    ax.hist(vals, bins=edges, color=C_MEASURED, alpha=0.75, edgecolor="white", linewidth=1.5,
            label=f"Measured per-run UC.1.4 total (n = {n})")
    x0 = min(vmin, mu - 3.5 * sd)
    x1 = max(vmax, mu + 3.5 * sd)
    xs = [x0 + (x1 - x0) * i / 400 for i in range(401)]
    scale = n * width
    ys = [scale * math.exp(-0.5 * ((x - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi)) for x in xs]
    ax.plot(xs, ys, color=C_SIMULATED, linewidth=2,
            label=f"Simulated N({mu:g}, {sd:g}) pdf, scaled to n × bin width")
    m = statistics.fmean(vals)
    ax.axvline(m, color=C_MEASURED, linestyle="--", linewidth=1.4, label=f"Measured mean {fmt(m)} s")
    ax.axvline(mu, color=C_SIMULATED, linestyle="--", linewidth=1.4, label=f"Simulated mean {mu:g} s")
    ax.set_xlim(x0, x1)
    ax.set_xlabel("UC.1.4 interpretation time per comparison (seconds)", color=C_INK)
    ax.set_ylabel("Runs (count)", color=C_INK)
    ax.set_title("UC.1.4 interpretation per comparison: measured vs simulated", color=C_INK,
                 fontsize=11, loc="left")
    _style(ax)
    ax.grid(True, axis="y", color=C_GRID, linewidth=0.6)
    # Headroom so the legend sits above the bars and the curve.
    counts = [sum(1 for v in vals if lo <= v < hi or (hi == edges[-1] and v == hi))
              for lo, hi in zip(edges, edges[1:])]
    ax.set_ylim(0, max(max(counts), max(ys)) * 1.65)
    ax.legend(fontsize=8.5, loc="upper left", frameon=True, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_per_requirement(by_req: dict[str, list[float]], out: Path):
    if not by_req:
        return
    reqs = sorted(by_req, key=req_sort_key)
    data = [by_req[r] for r in reqs]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    ax.axhspan(15, 20, color=C_SIMULATED, alpha=0.18, zorder=0,
               label="Model rationale: 15-20 s per requirement (Table X)")
    ax.boxplot(data, positions=list(range(1, len(reqs) + 1)), widths=0.5, **_boxprops(C_MEASURED))
    # Jittered points so individual calls (incl. re-sends) are visible.
    for i, vals in enumerate(data, start=1):
        k = len(vals)
        xs = [i - 0.18 + 0.36 * (j / max(1, k - 1)) for j in range(k)]
        ax.scatter(xs, vals, s=10, color=C_MEASURED, alpha=0.45, edgecolors="none", zorder=3)
    ax.set_xticks(list(range(1, len(reqs) + 1)))
    ax.set_xticklabels([f"{r}\n(n = {len(by_req[r])})" for r in reqs], fontsize=9, color=C_INK)
    ax.set_xlabel("Stated requirement (calls incl. re-sends)", color=C_INK)
    ax.set_ylabel("UC.1.4 duration per call (seconds)", color=C_INK)
    ax.set_title("UC.1.4 interpretation response time per requirement (SR 1.3.2 MOP)",
                 color=C_INK, fontsize=11, loc="left")
    _style(ax)
    ax.grid(False, axis="x")
    ax.grid(True, axis="y", color=C_GRID, linewidth=0.6)
    ax.set_ylim(0, max(max(v) for v in data) * 1.3)  # headroom for the legend
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=C_MEASURED + "33", edgecolor=C_MEASURED,
                     label="Measured per call (box: IQR, line: median; dots: calls)"),
               Patch(facecolor=C_SIMULATED, alpha=0.3, label="Model rationale: 15-20 s per requirement")]
    ax.legend(handles=handles, fontsize=8.5, loc="upper right", frameon=True, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs-dir", type=Path, default=Path("docs/validation/measured-behavior"))
    ap.add_argument("--walkthroughs", type=Path, default=Path("docs/validation/walkthroughs.csv"))
    args = ap.parse_args(argv)

    rows = load_runs(args.runs_dir / "runs.csv")
    meta = load_meta(args.runs_dir / "runs_meta.json")
    walk = load_walkthroughs(args.walkthroughs)

    def ids_for(phase):
        seen = []
        for r in rows:
            if r["phase"] == phase and r["run_id"] not in seen:
                seen.append(r["run_id"])
        return seen

    measured_ids, warmup_ids = ids_for("measured"), ids_for("warmup")
    measured_rows = [r for r in rows if r["phase"] == "measured"]
    per_run = per_run_stage_totals(rows)

    render_keys = sorted({r["stage_id"] for r in rows if r["stage_id"].startswith("RENDER:")})
    spec = stage_rows_spec(render_keys)
    stage_table, stats = build_stage_table(per_run, measured_ids, spec)
    warmup_table = build_warmup_table(per_run, warmup_ids, stats, spec)
    req_table, by_req = build_requirement_table(measured_rows, measured_ids)
    human_table = build_human_table(walk)
    hybrid = build_hybrid(stats)

    failed = [r for r in measured_rows if r.get("ok", "").strip().lower() not in ("1", "true", "yes")]
    failed_note = (f"{len(failed)} measured stage call(s) recorded ok = false "
                   f"({', '.join(sorted({r['stage_id'] for r in failed}))}); their durations are included."
                   if failed else "All measured stage calls recorded ok = true.")

    st_mu, st_sd = sim_system_total()
    header = [
        "# Measured vs simulated behaviour (Lab Manual 10.4)",
        "",
        "Generated by `tools/compare_measured_simulated.py`. Traces to SR 1.3.2, SR 2.1.1, CR 2.1.1.",
        "",
        f"- Runs: {len(measured_ids)} measured + {len(warmup_ids)} warm-up (warm-up excluded from statistics)",
        f"- Date range (t_entry_wall, all runs): {date_range(rows)}",
    ]
    for k, vals in meta_fields(meta).items():
        header.append(f"- {k}: {', '.join(vals)}")
    if meta is None:
        header.append("- runs_meta.json: not found")
    header += [
        f"- {failed_note}",
        "- Simulated values: SYSEN5151Modeling.pdf Table X duration settings (seconds). "
        f"Simulated system total = sum of modelled stage means {fmt(st_mu)} s, "
        f"SD = sqrt(sum of variances) {fmt(st_sd)} s.",
        "- Per-run aggregation: UC.1.4 and UC.1.5 summed over all calls in a run; UC.1.6 = a + b; "
        "UC.1.15-16 = a + b; System total = sum of stage rows; Unattributed = request wall time - "
        "system total.",
        "- Within sim ±2SD? tests the measured mean against simulated mean ± 2 simulated SD. For "
        "UC.1.11 (exponential, SD = mean) the lower bound is negative, so any faster mean passes.",
    ]

    md = "\n".join(header) + "\n\n"
    md += "## Per-stage comparison (measured runs, seconds per run)\n\n" + stage_table + "\n\n"
    md += "## Warm-up run (excluded from statistics above)\n\n" + warmup_table + "\n\n"
    md += ("## UC.1.4 interpretation response time per requirement (SR 1.3.2 MOP)\n\n"
           "Per call, measured runs only. A re-send is a run with more than one call for the "
           "requirement.\n\n" + req_table + "\n\n")
    md += "## Human stages (UC.1.7-1.9, CR 2.1.1), separate sample\n\n" + human_table + "\n\n"
    md += "## Hybrid end-to-end estimate (SR 2.1.1)\n\n" + hybrid + "\n\n"
    md += ("## Plots\n\n"
           "- `stage_comparison.png`: per-stage measured distribution (log axis) with simulated mean ± 1 SD\n"
           "- `interpretation_vs_simulated.png`: measured per-run UC.1.4 totals vs simulated N(90, 25)\n"
           "- `interpretation_per_requirement.png`: UC.1.4 per-call durations by requirement\n")

    (args.runs_dir / "comparison.md").write_text(md)
    plot_stage_comparison(per_run, measured_ids, spec, args.runs_dir / "stage_comparison.png")
    plot_interpretation_hist(per_run, measured_ids, args.runs_dir / "interpretation_vs_simulated.png")
    plot_per_requirement(by_req, args.runs_dir / "interpretation_per_requirement.png")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
