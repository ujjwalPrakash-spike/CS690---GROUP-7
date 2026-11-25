"""Cell-level evaluation shared by every method (see SCORING.md).

Reads the per-cell outputs written by run_llminist.py, run_nicheagent_style.py and run_cardem.py and writes
  results/table_scores.csv         accuracy / ARI / NMI with 95% bootstrap intervals (2,000 resamples of cells)
  results/table_mcnemar.csv        paired McNemar tests, CardEM against every other method on the same cells
  results/table_naming.csv         accuracy with the method's own names vs. with the best possible names

    python evaluate.py
"""
import os

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.stats import binomtest
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

import common as cm

B = 2000


def predictions(ds):
    """Per-cell labels of every method on one dataset, as region indices (-1 = not a region)."""
    d = np.load(os.path.join(cm.RESULTS, f"{ds}_cardem_cells.npz"), allow_pickle=True)
    cells, regions, truth = list(d["cells"]), list(d["regions"]), d["truth"]
    as_idx = lambda s: s.reindex(cells).map({r: k for k, r in enumerate(regions)}).fillna(-1).astype(int).to_numpy().copy()
    tab = pd.crosstab(d["km"], truth)
    ri, ci = linear_sum_assignment(-tab.values)
    km_named = pd.Series(d["km"]).map(dict(zip(tab.index[ri], tab.columns[ci]))).fillna(-1).astype(int).values
    lm = pd.read_csv(os.path.join(cm.RESULTS, f"{ds}_llminist_cells.csv"), index_col=0)
    na = pd.read_csv(os.path.join(cm.RESULTS, f"{ds}_nicheagent_cells.csv"), index_col=0)
    preds = {
        "Majority region": np.full(len(cells), np.bincount(truth).argmax()),
        "k-means (oracle names)": km_named,
        "Nearest expert card": as_idx(na["nearest_card"]),
        "NicheAgent-style": as_idx(na["nicheagent_style_smoothed"]),
        "LLMiniST": as_idx(lm["llminist_refined"]),  # sampled cells only on MERFISH; others are -2 below
        "M1 cosine": d["m1"],
        "M2 EM": d["m2"],
        "M3 CardEM": d["m3"],
    }
    preds["LLMiniST"][~pd.Index(cells).isin(lm.index)] = -2
    return d, truth, regions, preds


def boot(truth, pred, rng):
    n = len(truth)
    out = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        out.append(((pred[i] == truth[i]).mean(), adjusted_rand_score(truth[i], pred[i]),
                    normalized_mutual_info_score(truth[i], pred[i])))
    return np.percentile(np.array(out), [2.5, 97.5], axis=0)


def oracle_accuracy(pred, truth, K):
    tab = pd.crosstab(pred, truth).reindex(index=range(K), columns=range(K), fill_value=0).values
    ri, ci = linear_sum_assignment(-tab)
    return tab[ri, ci].sum() / len(truth)


def main():
    score_rows, test_rows, name_rows = [], [], []
    for ds in ("starmap", "merfish"):
        _, truth, regions, preds = predictions(ds)
        rng = np.random.default_rng(0)
        for name, p in preds.items():
            keep = p != -2
            t, q = truth[keep], p[keep]
            s = cm.scores(t, q)
            lo, hi = boot(t, q, rng)
            score_rows.append(dict(dataset=ds, method=name, cells=int(keep.sum()),
                                   accuracy=s["accuracy"], acc_lo=lo[0], acc_hi=hi[0],
                                   ARI=s["ARI"], ARI_lo=lo[1], ARI_hi=hi[1],
                                   NMI=s["NMI"], NMI_lo=lo[2], NMI_hi=hi[2]))
        m3 = preds["M3 CardEM"]
        for name, p in preds.items():
            if name in ("M3 CardEM", "Majority region"):
                continue
            keep = p != -2
            a, b = m3[keep] == truth[keep], p[keep] == truth[keep]
            n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
            test_rows.append(dict(dataset=ds, comparison=f"M3 CardEM vs {name}", cells=int(keep.sum()),
                                  m3_right_other_wrong=n10, m3_wrong_other_right=n01,
                                  p_value=binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0))
        for name in ("Nearest expert card", "NicheAgent-style", "M1 cosine", "M2 EM", "M3 CardEM"):
            p = preds[name]
            acc = (p == truth).mean()
            orc = oracle_accuracy(p, truth, len(regions))
            name_rows.append(dict(dataset=ds, method=name, accuracy=acc, oracle_named_accuracy=orc,
                                  naming_loss=orc - acc))

    out = lambda rows, f: pd.DataFrame(rows).round(4).to_csv(os.path.join(cm.RESULTS, f), index=False)
    out(score_rows, "table_scores.csv")
    out(test_rows, "table_mcnemar.csv")
    out(name_rows, "table_naming.csv")
    pd.set_option("display.width", 200)
    for f in ("table_scores.csv", "table_mcnemar.csv", "table_naming.csv"):
        print(f"\n{f}\n" + pd.read_csv(os.path.join(cm.RESULTS, f)).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
