from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.fuzzy_engine import infer

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "ranking_exercise.csv"
OUT = ROOT / "results" / "ranking_exercise.json"


def score(row) -> dict:
    r = infer(row.dspd, row.ltbf, row.qd).to_dict()
    fired = [a for a in r["rule_activations"] if a["firing_strength"] > 0]
    return {
        "squad": row.squad,
        "dspd": row.dspd,
        "ltbf": row.ltbf,
        "qd": row.qd,
        "rules": [{"id": a["id"], "strength": round(a["firing_strength"], 3)} for a in fired],
        "phs": round(r["phs"], 2),
        "state": r["linguistic_state"],
        "expert_rank": int(row.expert_rank),
    }


def exact_p(statistic, x, y) -> float:
    observed = abs(statistic(x, y))
    values = [abs(statistic(x, list(p))) for p in itertools.permutations(y)]
    return float(np.mean(np.array(values) >= observed - 1e-12))


def spearman(x, y) -> float:
    return float(stats.spearmanr(x, y).statistic)


def kendall(x, y) -> float:
    return float(stats.kendalltau(x, y).statistic)


def critical_value(n: int, alpha: float) -> float:
    base = list(range(1, n + 1))
    values = np.sort(np.abs([spearman(base, list(p)) for p in itertools.permutations(base)]))
    for v in np.unique(values):
        if np.mean(values >= v - 1e-12) <= alpha:
            return float(v)
    return float("nan")


def main() -> int:
    df = pd.read_csv(DATA)
    rows = [score(r) for r in df.itertuples()]
    phs = np.array([r["phs"] for r in rows])
    dss_rank = stats.rankdata(-phs, method="average")
    expert = np.array([r["expert_rank"] for r in rows], dtype=float)
    for r, k in zip(rows, dss_rank):
        r["dss_rank"] = float(k)
        r["d"] = float(k - r["expert_rank"])
    d2 = [(r["squad"], r["d"] ** 2) for r in rows]
    single = {}
    for name, values in (("dspd", -df.dspd.to_numpy()), ("ltbf", df.ltbf.to_numpy()), ("qd", -df.qd.to_numpy())):
        ranks = stats.rankdata(values, method="average")
        single[name] = {"spearman": round(spearman(ranks, expert), 4), "p_exact": round(exact_p(spearman, ranks, expert), 4)}
    leave_one_out = {}
    for i, r in enumerate(rows):
        keep = [j for j in range(len(rows)) if j != i]
        leave_one_out[r["squad"]] = round(spearman(stats.rankdata(-phs[keep]), stats.rankdata(expert[keep])), 4)
    tied = [i for i, k in enumerate(dss_rank) if k != int(k) or list(dss_rank).count(k) > 1]
    slots = sorted(stats.rankdata(-phs, method="ordinal")[tied])
    broken = []
    for order in itertools.permutations(slots):
        strict = dss_rank.copy()
        strict[tied] = order
        broken.append(spearman(strict, expert))
    out = {
        "squads": rows,
        "n": len(rows),
        "spearman": round(spearman(dss_rank, expert), 4),
        "spearman_p_exact": round(exact_p(spearman, dss_rank, expert), 4),
        "spearman_p_t": round(float(stats.spearmanr(dss_rank, expert).pvalue), 4),
        "kendall_tau_b": round(kendall(dss_rank, expert), 4),
        "kendall_p_exact": round(exact_p(kendall, dss_rank, expert), 4),
        "sum_d2": sum(v for _, v in d2),
        "largest_d2": max(d2, key=lambda t: t[1]),
        "critical_spearman_0.05": round(critical_value(len(rows), 0.05), 4),
        "tied_scores": {str(v): int(c) for v, c in zip(*np.unique(phs, return_counts=True)) if c > 1},
        "single_input": single,
        "leave_one_out": leave_one_out,
        "tie_break_range": [round(min(broken), 4), round(max(broken), 4)],
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    for r in rows:
        print(f"{r['squad']:<8} {r['phs']:>6.2f} {r['state']:<18} {'+'.join(x['id'] for x in r['rules']):<6} dss {r['dss_rank']:.0f} expert {r['expert_rank']}")
    print(f"spearman {out['spearman']} exact p {out['spearman_p_exact']} | kendall {out['kendall_tau_b']} exact p {out['kendall_p_exact']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
