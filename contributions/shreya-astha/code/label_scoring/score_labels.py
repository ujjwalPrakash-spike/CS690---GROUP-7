"""Label-level scoring: summarise graded LLM answers as Exact / Partial / Miss rates (see SCORING.md).

Every answer was graded against the expert region that holds most of the cluster's (or region's) cells,
using the written rules in SCORING.md. This script only counts; it never re-grades.

    python score_labels.py      -> results/*.csv
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


def wilson(k, n, conf=0.95):
    if n == 0:
        return np.nan, np.nan
    z = norm.ppf(0.5 + conf / 2)
    p = k / n
    mid = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return mid - half, mid + half


def summarise(df, by, unit_cols):
    """Rates per group; consistency = share of units (same niche, prompt, model) whose repeats all got one grade."""
    rows = []
    for key, g in df.groupby(by):
        n = len(g)
        counts = g["grade"].value_counts()
        e, p, m = (int(counts.get(x, 0)) for x in ("exact", "partial", "miss"))
        lo, hi = wilson(e, n)
        same = g.groupby(unit_cols)["grade"].nunique().eq(1).mean()
        key = key if isinstance(key, tuple) else (key,)
        rows.append(dict(zip(by, key), labels=n, exact=e / n, exact_lo=lo, exact_hi=hi,
                         partial=p / n, miss=m / n, consistent=same))
    return pd.DataFrame(rows).round(3)


def main():
    web = pd.read_csv(os.path.join(HERE, "graded_answers", "dlpfc_web_labels.csv"))
    web["grade"] = web["score"].str.lower()
    unit = ["ai", "method", "strategy", "niche"]
    tables = {
        "dlpfc_by_model": summarise(web, ["ai"], unit),
        "dlpfc_by_model_and_prompt": summarise(web, ["ai", "strategy"], unit),
        "dlpfc_by_clustering": summarise(web, ["method"], unit),
    }
    cosmx = pd.read_csv(os.path.join(HERE, "graded_answers", "cosmx_gemini_labels.csv"))
    cosmx["grade"] = cosmx["grade"].str.lower()
    tables["cosmx_by_template"] = summarise(cosmx, ["template"], ["template", "region"])

    for name, t in tables.items():
        t.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
        print(f"\n{name}\n{t.to_string(index=False)}")


if __name__ == "__main__":
    main()
