"""Swing weight trade study check: local runtime (A) vs hosted GPT-6.2 Sol API (B).

Lab Manual 11.2 (alternative selection: swing weight matrix, value, life-cycle cost,
affordability, sensitivity). Traces to SPEC SR 2.4.1 Query cost (zero budget for paid
queries), SR 2.2.1 Local interpretation (EC.1 data locality), SR 1.3.2 (interpretation
response time per requirement, EC.2 / EC.3; 110 s per request is SR 1.3.2's limit, SPEC section 6)
and SR 2.1.2 Re-evaluation effort (EC.4 reproducibility).

Recomputes every number of the trade study from the raw measured data in
docs/validation/measured-behavior/ (warm-up run_id -1 excluded) plus the sourced and
assumed inputs the study states. Prints markdown tables, including a column that compares
each figure with the value printed in the study at the study's rounding. Stdlib only.

Run: python3.12 tools/swing_weight_analysis.py
"""

from __future__ import annotations

import csv
import json
import statistics
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs" / "validation" / "measured-behavior"

# ---------------------------------------------------------------------------
# Measured inputs (A), read from the raw CSVs
# ---------------------------------------------------------------------------


def _measured_rows(name: str) -> list[dict]:
    with open(DATA / name, newline="") as f:
        return [r for r in csv.DictReader(f) if r["run_id"] != "-1" and r["phase"] == "measured"]


def p95(vals: list[float]) -> float:
    # Same method as tools/compare_measured_simulated.py
    return statistics.quantiles(vals, n=20, method="inclusive")[18]


log = _measured_rows("interpretation_log.csv")
per_run = _measured_rows("per_run.csv")
uc14 = [r for r in _measured_rows("runs.csv") if r["stage_id"] == "UC.1.4"]
meta = json.loads((DATA / "runs_meta.json").read_text())

req_s = [float(r["seconds"]) for r in log]
first_valid = sum(1 for r in log if r["attempt"] == "1" and r["outcome"] == "valid")
attempts_gt1 = sum(1 for r in log if r["attempt"] != "1")
comp_s = [float(r["UC.1.4_s"]) for r in per_run]
# cross-check: per-run sum of interpretation-log seconds
by_run: dict[int, float] = {}
for r in log:
    by_run[int(r["run_id"])] = by_run.get(int(r["run_id"]), 0.0) + float(r["seconds"])
req_s_1_16 = [float(r["seconds"]) for r in log if 1 <= int(r["run_id"]) <= 16]

A_T_REQ = statistics.mean(req_s)            # mean interpretation time per request (s)
A_VALID_FIRST = 100.0 * first_valid / len(log)  # % valid on first attempt
A_T_COMP = statistics.mean(comp_s)          # mean interpretation time per comparison (s)
A_T_REQ_1_16 = statistics.mean(req_s_1_16)  # runs 1-16 (battery) per request (s)

# ---------------------------------------------------------------------------
# Sourced and assumed inputs (as stated in the trade study, Table "Input data")
# ---------------------------------------------------------------------------
B_TTFT_S = 2.00            # Sourced: Artificial Analysis (2026), GPT-6.2 Sol low effort
B_SPEED_TPS = 61.0         # Sourced: Artificial Analysis (2026), output tokens/s
B_PRICE_IN = 2.00          # Sourced: OpenAI (2026a, b, d), $ per 1M input tokens
B_PRICE_OUT = 10.00        # Sourced: OpenAI (2026a, b, d), $ per 1M output (incl. reasoning)
ANSWER_TOK = 150           # Assumption: team estimate of one proposed-criteria answer
INPUT_TOK = 1500           # Assumption: team estimate of prompt + requirement + criteria list
B_VALID_FIRST = 100.0      # Assumption: equal to A (Structured Outputs supported, OpenAI 2026a)
COMPARISONS_PER_YEAR = 1000  # Assumption: team estimate of use; life-cycle period 1 year
REQ_PER_COMPARISON = 5     # Measured scenario: 5 requirements per comparison
A_POWER_W = 140.0          # Sourced (upper bound): Apple (2023), 140 W adapter, M2 Pro MBP 16"
ELEC_PRICE_KWH = 0.1825    # Sourced: U.S. EIA (2026), summer 2026 US residential (forecast)
BUDGET_PAID_QUERY = 0.0    # SR 2.4.1 Query cost: budget for paid queries is zero

# Derived (study's stated method)
B_REASON_TOK = B_TTFT_S * B_SPEED_TPS                     # assumption: TTFT spent reasoning
B_T_REQ = B_TTFT_S + ANSWER_TOK / B_SPEED_TPS
B_COST_REQ = (INPUT_TOK * B_PRICE_IN + (ANSWER_TOK + B_REASON_TOK) * B_PRICE_OUT) / 1e6
B_COST_COMP = REQ_PER_COMPARISON * B_COST_REQ

# ---------------------------------------------------------------------------
# Objective functions (study section 2.2.2), each returns 0..100
# ---------------------------------------------------------------------------
EC4_LEVELS = {"may change without notice": 0, "dated versions retired": 50, "pinned weights": 100}
EC5_LEVELS = {"one laptop": 0, "shared team server": 50, "managed service": 100}


def clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def v_ec1(share_pct: float) -> float:            # 0% -> 0, 100% -> 100, linear
    return clamp(share_pct)


def v_ec2(t_s: float, worst: float = 110.0, best: float = 1.0) -> float:  # 110 s -> 0, 1 s -> 100
    return clamp(100.0 * (worst - t_s) / (worst - best))


def v_ec3(valid_pct: float, floor: float = 80.0) -> float:  # floor -> 0, 100% -> 100
    return clamp(100.0 * (valid_pct - floor) / (100.0 - floor))


def v_ec4(level: str) -> float:
    return float(EC4_LEVELS[level])


def v_ec5(level: str) -> float:
    return float(EC5_LEVELS[level])


CRIT = ["EC.1", "EC.2", "EC.3", "EC.4", "EC.5"]
NAMES = {"EC.1": "Data locality", "EC.2": "Interpretation response time",
         "EC.3": "Interpretation quality", "EC.4": "Reproducibility", "EC.5": "Availability"}
SWING = {"EC.1": 100, "EC.2": 25, "EC.3": 40, "EC.4": 50, "EC.5": 70}
MATRIX = {  # (importance, variation) -> cell weight, and placement, as in the study
    ("High", "Large"): 100, ("High", "Medium"): 75, ("High", "Small"): 40,
    ("Medium", "Large"): 70, ("Medium", "Medium"): 50, ("Medium", "Small"): 25,
    ("Low", "Large"): 40, ("Low", "Medium"): 20, ("Low", "Small"): 10,
}
PLACEMENT = {"EC.1": ("High", "Large"), "EC.2": ("Medium", "Small"), "EC.3": ("High", "Small"),
             "EC.4": ("Medium", "Medium"), "EC.5": ("Medium", "Large")}


def scores(a_t=None, b_t=None, a_valid=None, b_valid=None, floor=80.0,
           a_ec4="pinned weights", b_ec4="dated versions retired",
           a_ec5="one laptop", b_ec5="managed service", b_ec2_override=None):
    a_t = A_T_REQ if a_t is None else a_t
    b_t = B_T_REQ if b_t is None else b_t
    a_valid = A_VALID_FIRST if a_valid is None else a_valid
    b_valid = B_VALID_FIRST if b_valid is None else b_valid
    A = {"EC.1": v_ec1(100.0), "EC.2": v_ec2(a_t), "EC.3": v_ec3(a_valid, floor),
         "EC.4": v_ec4(a_ec4), "EC.5": v_ec5(a_ec5)}
    B = {"EC.1": v_ec1(0.0), "EC.2": v_ec2(b_t) if b_ec2_override is None else b_ec2_override,
         "EC.3": v_ec3(b_valid, floor), "EC.4": v_ec4(b_ec4), "EC.5": v_ec5(b_ec5)}
    return A, B


TOTAL_SWING = sum(SWING.values())
W = {c: SWING[c] / TOTAL_SWING for c in CRIT}


def total(s: dict, w: dict = W) -> float:
    return sum(w[c] * s[c] for c in CRIT)


SA, SB = scores()
TA, TB = total(SA), total(SB)

# ---------------------------------------------------------------------------
# Life-cycle cost, one year
# ---------------------------------------------------------------------------
A_KWH = A_POWER_W * A_T_COMP * COMPARISONS_PER_YEAR / 3.6e6
A_ELEC = A_KWH * ELEC_PRICE_KWH
B_API = B_COST_COMP * COMPARISONS_PER_YEAR


# ---------------------------------------------------------------------------
# One-at-a-time weight sensitivity: w_i in [0,1], others keep proportions.
# T_k(w) = w*s_ik + (1-w)*R_k,  R_k = sum_{j!=i} W_j s_jk / (1 - W_i)
# Tie: w* = D / (D - d), D = R_A - R_B, d = s_iA - s_iB; valid only if 0 <= w* <= 1.
# ---------------------------------------------------------------------------
def tie_point(c: str):
    rest = 1.0 - W[c]
    ra = sum(W[j] * SA[j] for j in CRIT if j != c) / rest
    rb = sum(W[j] * SB[j] for j in CRIT if j != c) / rest
    D, d = ra - rb, SA[c] - SB[c]
    if D - d == 0:
        return None, None, "parallel lines: no tie"
    w = D / (D - d)
    if d == 0:
        return None, None, "s_A = s_B on this criterion: totals converge only at w = 1 (tie at 100)"
    if not 0.0 <= w <= 1.0:
        return None, None, f"no tie in [0,1] (line intersection at w = {w:.3f})"
    others = TOTAL_SWING - SWING[c]
    swing_eq = w * others / (1.0 - w)   # swing weight giving normalised w, others fixed
    return w, swing_eq, ""


# ---------------------------------------------------------------------------
# Assumption tests (one change at a time, base weights)
# ---------------------------------------------------------------------------
TESTS = [
    ("Base case", {}),
    ("GPT-6.2 Sol never changes its model (EC.4: B = 100)", {"b_ec4": "pinned weights"}),
    ("GPT-6.2 Sol answers instantly (EC.2: B = 100)", {"b_ec2_override": 100.0}),
    (f"A as slow as in runs 1 to 16 ({A_T_REQ_1_16:.2f} s per request)", {"a_t": A_T_REQ_1_16}),
    ("A as slow as in runs 1 to 16, study's rounded 8.33 s", {"a_t": 8.33}),
    ("EC.3 floor lowered from 80% to 50%", {"floor": 50.0}),
    ("GPT-6.2 Sol valid on only 90% of first attempts", {"b_valid": 90.0}),
    ("A moved to a shared team server (EC.5: A = 50)", {"a_ec5": "shared team server"}),
    ("Both of the first two changes together", {"b_ec4": "pinned weights", "b_ec2_override": 100.0}),
]


# ---------------------------------------------------------------------------
# Comparison with the study (value printed, decimals printed)
# ---------------------------------------------------------------------------
def rnd(x: float, nd: int) -> Decimal:
    return Decimal(repr(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


rows: list[tuple[str, str, float, int]] = []


def claim(label: str, study: str, value: float, nd: int):
    rows.append((label, study, value, nd))


def main() -> int:
    print("# Swing weight trade study: recomputation\n")
    print(f"Data: `{DATA.relative_to(DATA.parents[2])}`; model id used in the runs "
          f"(runs_meta.json llm_model): `{meta['llm_model']}`; runtime URL `{meta['llm_runtime_url']}`\n")

    print("## 1. Measured inputs (A), warm-up excluded\n")
    print("| Quantity | n | Mean | Max | p95 | Min |")
    print("|---|---|---|---|---|---|")
    print(f"| Interpretation time per request (s) | {len(req_s)} | {A_T_REQ:.4f} | {max(req_s):.4f} | "
          f"{p95(req_s):.4f} | {min(req_s):.4f} |")
    print(f"| Interpretation time per comparison, UC.1.4 (s) | {len(comp_s)} | {A_T_COMP:.4f} | "
          f"{max(comp_s):.4f} | {p95(comp_s):.4f} | {min(comp_s):.4f} |")
    print(f"| Per request, runs 1-16 (s) | {len(req_s_1_16)} | {A_T_REQ_1_16:.4f} | {max(req_s_1_16):.4f} | "
          f"{p95(req_s_1_16):.4f} | {min(req_s_1_16):.4f} |")
    sums = [by_run[k] for k in sorted(by_run)]
    print(f"| Cross-check: per-run sum of log seconds (s) | {len(sums)} | {statistics.mean(sums):.4f} | "
          f"{max(sums):.4f} | {p95(sums):.4f} | {min(sums):.4f} |")
    print(f"\nValid on first attempt: {first_valid} of {len(log)} ({A_VALID_FIRST:.1f}%); "
          f"rows with attempt > 1: {attempts_gt1}. Runs: {len(per_run)}.\n")

    print("## 2. Derived inputs (B) and cost\n")
    print("| Quantity | Value |")
    print("|---|---|")
    print(f"| B reasoning tokens (TTFT x speed) | {B_REASON_TOK:.1f} |")
    print(f"| B output tokens billed per request | {ANSWER_TOK + B_REASON_TOK:.1f} |")
    print(f"| B time per request (s) | {B_T_REQ:.4f} |")
    print(f"| B cost per request ($) | {B_COST_REQ:.6f} |")
    print(f"| B cost per comparison ($) | {B_COST_COMP:.6f} |")
    print(f"| A - B time per request (s) | {A_T_REQ - B_T_REQ:.4f} |\n")

    print("## 3. Swing weight matrix check\n")
    print("| Criterion | Placement | Cell weight | Swing weight used | Consistent |")
    print("|---|---|---|---|---|")
    for c in CRIT:
        cell = MATRIX[PLACEMENT[c]]
        print(f"| {c} {NAMES[c]} | {PLACEMENT[c][0]} / {PLACEMENT[c][1]} | {cell} | {SWING[c]} | "
              f"{'yes' if cell == SWING[c] else 'NO'} |")
    imp, var = ["High", "Medium", "Low"], ["Large", "Medium", "Small"]
    viol = [(a, b) for a in MATRIX for b in MATRIX
            if imp.index(a[0]) <= imp.index(b[0]) and var.index(a[1]) <= var.index(b[1])
            and a != b and MATRIX[a] < MATRIX[b]]
    print(f"\nDominance violations (a cell at least as important and at least as large with a lower "
          f"weight): {viol if viol else 'none'}\n")

    print("## 4. Scores, weights, weighted values\n")
    print("| Criterion | Swing | Normalised | A value | B value | A weighted | B weighted |")
    print("|---|---|---|---|---|---|---|")
    for c in CRIT:
        print(f"| {c} {NAMES[c]} | {SWING[c]} | {W[c]:.4f} | {SA[c]:.3f} | {SB[c]:.3f} | "
              f"{W[c]*SA[c]:.3f} | {W[c]*SB[c]:.3f} |")
    print(f"| Total | {TOTAL_SWING} | {sum(W.values()):.4f} | | | {TA:.3f} | {TB:.3f} |")
    print(f"\nA - B = {TA - TB:.3f}. Sum of A weighted values rounded to 0.1 as printed: "
          f"{sum(float(rnd(W[c]*SA[c], 1)) for c in CRIT):.1f}; B: "
          f"{sum(float(rnd(W[c]*SB[c], 1)) for c in CRIT):.1f}\n")

    print("## 5. Life-cycle cost (1 year) and affordability (SR 2.4.1)\n")
    print("| Element | A | B |")
    print("|---|---|---|")
    print(f"| Electricity ({A_KWH:.4f} kWh upper bound) | ${A_ELEC:.4f} | $0.00 |")
    print(f"| API usage | $0.00 | ${B_API:.4f} |")
    print(f"| Life-cycle cost | ${A_ELEC:.4f} | ${B_API:.4f} |")
    print(f"| Study basis '$0.029 x 1,000' evaluates to | | ${0.029 * COMPARISONS_PER_YEAR:.2f} |")
    print(f"| Affordable (paid query cost <= ${BUDGET_PAID_QUERY:.2f}) | yes | "
          f"{'yes' if B_COST_COMP <= BUDGET_PAID_QUERY else 'no'} |\n")

    print("## 6. One-at-a-time weight sensitivity (tie points)\n")
    print("| Criterion | Base weight | Tie weight | Equivalent swing weight (others fixed) | Note |")
    print("|---|---|---|---|---|")
    ties = {}
    for c in CRIT:
        w, sw, note = tie_point(c)
        ties[c] = (w, sw)
        print(f"| {c} {NAMES[c]} | {W[c]:.4f} | {'none' if w is None else f'{w:.4f}'} | "
              f"{'-' if sw is None else f'{sw:.1f}'} | {note} |")
    print()

    print("## 7. Tests of the assumptions\n")
    print("| Test | A total | B total | Preferred | Change in A | Change in B |")
    print("|---|---|---|---|---|---|")
    test_out = {}
    for name, kw in TESTS:
        a, b = scores(**kw)
        ta, tb = total(a), total(b)
        test_out[name] = (ta, tb)
        print(f"| {name} | {ta:.3f} | {tb:.3f} | {'A' if ta > tb else 'B' if tb > ta else 'tie'} | "
              f"{ta - TA:+.3f} | {tb - TB:+.3f} |")
    print()

    # ---- claims printed in the study --------------------------------------------------
    claim("A mean time per request (s)", "7.01", A_T_REQ, 2)
    claim("A valid on first attempt (%)", "100", A_VALID_FIRST, 0)
    claim("A mean time per comparison (s)", "35.05", A_T_COMP, 2)
    claim("A mean per request, runs 1-16 (s)", "8.33", A_T_REQ_1_16, 2)
    claim("B reasoning tokens", "122", B_REASON_TOK, 0)
    claim("B output tokens billed", "272", ANSWER_TOK + B_REASON_TOK, 0)
    claim("B time per request (s)", "4.46", B_T_REQ, 2)
    claim("B cost per request ($)", "0.0057", B_COST_REQ, 4)
    claim("B cost per comparison ($)", "0.029", B_COST_COMP, 3)
    claim("A - B time per request (s)", "2.6", A_T_REQ - B_T_REQ, 1)
    for c, n in zip(CRIT, ["0.351", "0.088", "0.140", "0.175", "0.246"]):
        claim(f"{c} normalised weight", n, W[c], 3)
    for c, sa, sb in zip(CRIT, ["100", "94.5", "100", "100", "0"], ["0", "96.8", "100", "50", "100"]):
        claim(f"{c} A value", sa, SA[c], len(sa.split(".")[1]) if "." in sa else 0)
        claim(f"{c} B value", sb, SB[c], len(sb.split(".")[1]) if "." in sb else 0)
    for c, wa, wb in zip(CRIT, ["35.1", "8.3", "14.0", "17.5", "0.0"], ["0.0", "8.5", "14.0", "8.8", "24.6"]):
        claim(f"{c} A weighted", wa, W[c] * SA[c], 1)
        claim(f"{c} B weighted", wb, W[c] * SB[c], 1)
    claim("A total value", "75.0", TA, 1)
    claim("B total value", "55.9", TB, 1)
    claim("A - B total", "19.1", TA - TB, 1)
    claim("B gain on response time (weighted)", "0.2", W["EC.2"] * (SB["EC.2"] - SA["EC.2"]), 1)
    claim("A electricity, 1 year ($)", "0.25", A_ELEC, 2)
    claim("B API usage, 1 year ($)", "28.60", B_API, 2)
    claim("B API usage per stated basis $0.029 x 1,000 ($)", "28.60", 0.029 * COMPARISONS_PER_YEAR, 2)
    for c, bw in zip(CRIT, ["0.35", "0.09", "0.14", "0.18", "0.25"]):
        claim(f"{c} base weight (sensitivity table)", bw, W[c], 2)
    claim("EC.1 tie weight", "0.20", ties["EC.1"][0], 2)
    claim("EC.1 tie as swing weight ('about 46')", "46", ties["EC.1"][1], 0)
    claim("EC.2 tie weight", "0.90", ties["EC.2"][0], 2)
    claim("EC.5 tie weight", "0.37", ties["EC.5"][0], 2)
    claim("EC.5 tie as swing weight ('about 124')", "124", ties["EC.5"][1], 0)
    study_tests = {
        "Base case": ("75.0", "55.9"),
        "GPT-6.2 Sol never changes its model (EC.4: B = 100)": ("75.0", "64.6"),
        "GPT-6.2 Sol answers instantly (EC.2: B = 100)": ("75.0", "56.1"),
        f"A as slow as in runs 1 to 16 ({A_T_REQ_1_16:.2f} s per request)": ("74.8", "55.9"),
        "A as slow as in runs 1 to 16, study's rounded 8.33 s": ("74.8", "55.9"),
        "EC.3 floor lowered from 80% to 50%": ("75.0", "55.9"),
        "GPT-6.2 Sol valid on only 90% of first attempts": ("75.0", "48.8"),
        "A moved to a shared team server (EC.5: A = 50)": ("87.2", "55.9"),
        "Both of the first two changes together": ("75.0", "64.9"),
    }
    for name, (sa, sb) in study_tests.items():
        ta, tb = test_out[name]
        claim(f"Test '{name}': A", sa, ta, 1)
        claim(f"Test '{name}': B", sb, tb, 1)
    shared = test_out["A moved to a shared team server (EC.5: A = 50)"][0] - TA
    claim("Largest change from team-judgement tests ('at most 12 points')", "12", shared, 0)

    print("## 8. Comparison with the study\n")
    print("| Claim | Study | Recomputed (study's rounding) | Unrounded | Match |")
    print("|---|---|---|---|---|")
    n_bad = 0
    for label, study, value, nd in rows:
        got = rnd(value, nd)
        ok = got == Decimal(study).quantize(Decimal(1).scaleb(-nd))
        n_bad += not ok
        print(f"| {label} | {study} | {got} | {value:.6g} | {'yes' if ok else '**NO**'} |")
    print(f"\n{len(rows) - n_bad} of {len(rows)} claims reproduce; {n_bad} do not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
