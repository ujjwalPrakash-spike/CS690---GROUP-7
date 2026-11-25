"""LLMiniST zero-shot (Li et al., ACL 2025) with Gemini instead of GPT-4o-mini.

Each cell is sent on its own: the prompt lists the cell types around it and asks for one region.
The answers are then refined: a cell takes its neighbours' label when more than half of them agree.

    python run_llminist.py --dataset starmap
    python run_llminist.py --dataset merfish --offline
"""
import argparse
import os

import numpy as np
import pandas as pd

import common as cm

# the prompt text follows zeroshot_celltype() in the LLMiniST repo (src/prompt.py)
PROMPT = ("You are tasked with identifying the type of microenvironment of a given cell using the provided cell types "
          "in the neighborhood of the given cell. Cell types are ordered from most frequent to least frequent.{freq} "
          "All cells are from the {tissue}. You should consider how different combinations of cell types form "
          "microenvironments. The target cell can only be one of the {n} microenvironments: {regions}. "
          "Below are the cell's neighbor cell-types.\n {{{types}}}\n "
          'Only output the most possible microenvironment in json format like this: {{"microenvironment": "{first}"}} ')

# STARmap: repo settings (config_zeroshot_starmap.yaml), with frequencies and white matter as a fifth option.
# MERFISH: the repo has no config for this section, so we keep the same wording without numbers.
SETTINGS = {
    "starmap": dict(tissue="mPFC region of mice", numbers=True, min_frac=0.0,
                    options=["Layer 1", "Layer 2/3", "Layer 5", "Layer 6", "WM"], sample=None),
    "merfish": dict(tissue="mouse hypothalamic preoptic region", numbers=False, min_frac=0.1,
                    options=None, sample=800),  # one call per cell, so a random 800-cell sample on the free tier
}


def prompt_for(sec, i, s, options):
    row = sec.comp.iloc[i].sort_values(ascending=False)[:10]
    row = row[row > s["min_frac"]]
    if s["numbers"]:
        types = ", ".join(f"{t}: {float(f'{v:.3g}')}" for t, v in row.items())
    else:
        types = ", ".join(row.index)
    return PROMPT.format(freq=" The frequencies of cell types are also provided." if s["numbers"] else "",
                         tissue=s["tissue"], n=len(options), regions=", ".join(options),
                         types=types, first=options[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["starmap", "merfish"], required=True)
    ap.add_argument("--offline", action="store_true", help="only reuse saved answers from cache/")
    args = ap.parse_args()

    sec = cm.load(args.dataset)
    s = SETTINGS[args.dataset]
    regions = cm.regions_of(sec)
    options = s["options"] or regions

    idx = np.arange(len(sec))
    if s["sample"]:
        idx = np.sort(np.random.default_rng(0).choice(len(sec), s["sample"], replace=False))

    cache = os.path.join(cm.CACHE, f"{args.dataset}_llminist.csv")
    answers = cm.read_answers(cache)
    llm = cm.Gemini(offline=args.offline)
    todo = [i for i in idx if sec.cells[i] not in answers]
    print(f"{len(idx) - len(todo)} cells already answered, {len(todo)} to ask")
    for n, i in enumerate(todo):
        text = llm.ask(prompt_for(sec, i, s, options), max_tokens=2000)
        if text is None:
            print("No answer from Gemini (offline, or the daily limit); stopping here.")
            break
        d = cm.parse_json(text) or {}
        answers[sec.cells[i]] = cm.to_region(d.get("microenvironment", text), options)
        if n % 20 == 0:
            cm.write_answers(answers, cache)
    cm.write_answers(answers, cache)

    done = [c for c in sec.cells[idx] if c in answers]
    res = pd.DataFrame({"truth": sec.truth[done], "llminist": pd.Series(answers)[done]})
    res["llminist_refined"] = cm.majority_smooth(res["llminist"], sec)
    res.to_csv(os.path.join(cm.RESULTS, f"{args.dataset}_llminist_cells.csv"))
    rows = [dict(dataset=args.dataset, method=m, cells=len(res), **cm.scores(res.truth, res[m]))
            for m in ("llminist", "llminist_refined")]
    cm.report(rows, os.path.join(cm.RESULTS, f"{args.dataset}_llminist_scores.csv"))
    print(pd.crosstab(res.truth, res.llminist_refined))


if __name__ == "__main__":
    main()
