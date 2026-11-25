"""NicheAgent-style annotation (our re-implementation; the authors' code is not public).

1. NicheCards: the mean neighbourhood of each region, measured on held-out labelled tissue
   (STARmap: sections BZ9 + BZ14; MERFISH: the other half of the same section).
2. Gemini reads a batch of cells and matches each neighbourhood to a card.
3. Majority smoothing over the spatial neighbours.
The no-LLM control assigns every cell to its most similar card (cosine).

    python run_nicheagent_style.py --dataset starmap [--offline]
"""
import argparse
import os

import numpy as np
import pandas as pd

import common as cm

HINTS = {
    "starmap": "layer 1 is cell-sparse and rich in astrocytes, vascular cells and Reln cells; "
               "deep layers hold oligodendrocytes",
    "merfish": "fiber tracts are dominated by oligodendrocytes; the ventricle is lined by ependymal cells",
}
SETTINGS = {
    "starmap": dict(batch=10, temperature=0.2, min_frac=1e-9),
    "merfish": dict(batch=20, temperature=1.0, min_frac=0.05),
}


def make_cards(comp, truth, regions):
    proto = comp.groupby(truth.values).mean().reindex(regions)
    overall = comp.mean().clip(lower=1e-3)
    lines = []
    for reg, row in proto.iterrows():
        top = row.sort_values(ascending=False)[:5]
        distinct = [t for t in (row / overall).sort_values(ascending=False).index[:3] if row[t] > 0.03]
        lines.append(f"- {reg}: typical neighbourhood = " + ", ".join(f"{t} {v:.0%}" for t, v in top.items())
                     + f". Most distinctive: {', '.join(distinct)}.")
    return proto, "\n".join(lines)


def prompt(dataset, sec, rows, cards, regions, min_frac):
    cells = "\n".join(f"cell_{k + 1}: {sec.describe(i, min_frac)}" for k, i in enumerate(rows))
    if dataset == "starmap":
        head = ("You annotate spatial niches in the mouse medial prefrontal cortex (STARmap).\n"
                "Each cell is described by the cell types in its spatial neighbourhood (fractions).\n"
                "Below are reference NicheCards: the typical neighbourhood of each cortical layer, "
                "measured in other tissue sections.")
    else:
        head = ("You annotate spatial niches in the mouse hypothalamic preoptic region (MERFISH).\n"
                f"Each cell is described by the cell types within {sec.radius} microns of it (fractions).\n"
                "Below are reference NicheCards: the typical neighbourhood of each region, "
                "measured in the other half of the tissue.\n"
                f"Region names: {cm.MERFISH_REGIONS}.")
    return (f"{head}\n\nNicheCards:\n{cards}\n\n"
            f"For each cell, compare its neighbourhood with the NicheCards and choose exactly one of: "
            f"{', '.join(regions)}.\nUse biology too (e.g. {HINTS[dataset]}).\n\nCells:\n{cells}\n\n"
            f'Answer ONLY with JSON like {{"cell_1": "{regions[0]}", "cell_2": "{regions[-1]}"}} '
            f"with one entry per cell.")


def nearest_card(comp, proto):
    sim = comp.values @ proto.values.T
    sim /= np.linalg.norm(comp.values, axis=1, keepdims=True) * np.linalg.norm(proto.values, axis=1) + 1e-9
    return proto.index[sim.argmax(1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["starmap", "merfish"], required=True)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    sec = cm.load(args.dataset)
    regions = cm.regions_of(sec)
    s = SETTINGS[args.dataset]

    # groups of cells that share one set of cards
    if args.dataset == "starmap":
        refs = [cm.load_starmap(b) for b in ("BZ9", "BZ14")]
        ref_comp = pd.concat([r.comp for r in refs]).reindex(columns=sec.types, fill_value=0)
        ref_truth = pd.concat([r.truth for r in refs])
        groups = [(np.arange(len(sec)), make_cards(ref_comp, ref_truth, regions))]
    else:
        half = (sec.xy[:, 0] > np.median(sec.xy[:, 0])).astype(int)
        groups = [(np.where(half == h)[0], make_cards(sec.comp[half != h], sec.truth[half != h], regions))
                  for h in (0, 1)]

    nearest = pd.Series(index=sec.cells, dtype=object)
    for idx, (proto, _) in groups:
        nearest.iloc[idx] = nearest_card(sec.comp.iloc[idx], proto)

    cache = os.path.join(cm.CACHE, f"{args.dataset}_nicheagent.csv")
    answers = cm.read_answers(cache)
    llm = cm.Gemini(offline=args.offline)
    for idx, (_, cards) in groups:
        todo = [i for i in idx if sec.cells[i] not in answers]
        for b in range(0, len(todo), s["batch"]):
            rows = todo[b:b + s["batch"]]
            text = llm.ask(prompt(args.dataset, sec, rows, cards, regions, s["min_frac"]),
                           max_tokens=6000, temperature=s["temperature"])
            if text is None:
                break
            got = cm.parse_cells(text)
            for k, i in enumerate(rows):
                if k + 1 in got:  # skipped cells are asked again on the next run
                    answers[sec.cells[i]] = cm.to_region(got[k + 1], regions)
            cm.write_answers(answers, cache)

    res = pd.DataFrame({"truth": sec.truth, "nearest_card": nearest})
    res = res.join(pd.Series(answers, name="nicheagent_style"), how="inner")
    res["nicheagent_style_smoothed"] = cm.majority_smooth(res["nicheagent_style"], sec)
    res.to_csv(os.path.join(cm.RESULTS, f"{args.dataset}_nicheagent_cells.csv"))
    rows = [dict(dataset=args.dataset, method=m, cells=len(res), **cm.scores(res.truth, res[m]))
            for m in ("nearest_card", "nicheagent_style", "nicheagent_style_smoothed")]
    cm.report(rows, os.path.join(cm.RESULTS, f"{args.dataset}_nicheagent_scores.csv"))


if __name__ == "__main__":
    main()
