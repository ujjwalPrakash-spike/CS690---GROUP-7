"""Figures for the report (run evaluate.py first).

    python make_figures.py      -> figures/fig_*.pdf and .png
"""
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy.optimize import linear_sum_assignment

import common as cm
from evaluate import predictions

OUT = os.path.join(cm.HERE, "figures")
os.makedirs(OUT, exist_ok=True)
mpl.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#888", "axes.titlesize": 10,
                     "axes.titleweight": "bold", "axes.titlelocation": "left",
                     "savefig.dpi": 300, "savefig.bbox": "tight"})
INK, MUTED, GRID = "#222222", "#6b6b6b", "#e6e6e6"
GREY, LLMC = "#9a9a9a", "#e08a2e"
M1C, M2C, M3C = "#9ecae1", "#4292c6", "#08306b"
ERR = "#d62728"
PAL = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#555555"]

ORDER = ["Majority region", "k-means (oracle names)", "Nearest expert card", "NicheAgent-style",
         "LLMiniST", "M1 cosine", "M2 EM", "M3 CardEM"]
COLOUR = dict(zip(ORDER, [GREY, GREY, GREY, LLMC, LLMC, M1C, M2C, M3C]))
USES_LABELS = {"k-means (oracle names)", "Nearest expert card", "NicheAgent-style"}


def save(fig, name):
    fig.savefig(os.path.join(OUT, f"{name}.pdf"))
    fig.savefig(os.path.join(OUT, f"{name}.png"))
    plt.close(fig)


def spatial(ax, xy, z, title, s=6, flip=False):
    ax.scatter(xy[:, 0], xy[:, 1], c=[PAL[k] if k >= 0 else "#cccccc" for k in z], s=s, lw=0)
    ax.set_title(title, fontsize=9)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    if flip:
        ax.invert_yaxis()


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(14, 3.8))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 4.4)
    ax.axis("off")
    styles = {"llm": ("#fde0c5", "#e6862e"), "math": ("#dbe9f6", "#2c6fb3"), "data": ("#eeeeee", "#888888"),
              "out": ("#d9f0d3", "#3a9a3a")}

    def box(x, y, w, h, title, body, kind):
        fc, ec = styles[kind]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.4))
        ax.text(x + 0.15, y + h - 0.2, title, fontsize=9.5, fontweight="bold", va="top", color=INK)
        ax.text(x + 0.15, y + h - 0.6, body, fontsize=7.8, va="top", color=MUTED, linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, color="#666", lw=1.3))

    box(0.1, 2.3, 2.3, 1.9, "Input", "cell types and x, y\ngene panel\nregion names only\n(no labels, no clusters)", "data")
    box(0.1, 0.1, 2.3, 1.8, "Neighbourhoods", "cell-type mix within\nradius R of each cell,\nmean marker expression", "data")
    box(2.8, 2.3, 2.6, 1.9, "1  LLM cards", "Gemini writes each region's\nexpected mix and 5-10\npanel markers (3 runs)", "llm")
    box(5.8, 2.3, 2.9, 1.9, "2  MAP-EM", "multinomial likelihood with\nthe card as Dirichlet prior;\ntau from the design effect,\nlambda by anchoring", "math")
    box(5.8, 0.1, 2.9, 1.8, "3  Rename check", "Gemini compares its cards\nwith the refined ones and\nmay swap region names", "llm")
    box(9.1, 2.3, 2.8, 1.9, "4  Review", "cells ranked by entropy and\ncard-run disagreement;\nGemini relabels the top 20%", "llm")
    box(9.1, 0.1, 2.8, 1.8, "5  Edge-aware Potts", "neighbour smoothing weighted\nby Jensen-Shannon similarity;\nbeta by pseudo-likelihood", "math")
    box(12.3, 1.0, 2.6, 2.2, "Output", "a region name for every\ncell, with its uncertainty", "out")
    arrow(2.4, 3.25, 2.8, 3.25)
    arrow(5.4, 3.25, 5.8, 3.25)
    arrow(2.4, 1.0, 5.8, 2.5)
    arrow(7.25, 2.3, 7.25, 1.9)
    arrow(8.7, 1.4, 9.1, 2.5)
    arrow(10.5, 2.3, 10.5, 1.9)
    arrow(11.9, 1.0, 12.3, 1.6)
    save(fig, "fig_cardem_pipeline")


def fig_performance(scores):
    fig, axs = plt.subplots(2, 2, figsize=(11, 6.2), sharey="row", gridspec_kw=dict(hspace=0.6))
    for row, (ds, title) in enumerate([("starmap", "STARmap BZ5 (mouse cortex, 1,049 cells)"),
                                       ("merfish", "MERFISH -0.14 (mouse hypothalamus, 5,926 cells)")]):
        sub = scores[scores.dataset == ds].set_index("method").loc[ORDER]
        y = np.arange(len(ORDER))
        for col, metric in enumerate(["accuracy", "ARI"]):
            ax = axs[row, col]
            v = sub[metric].values
            lo = v - sub[f"{'acc' if metric == 'accuracy' else metric}_lo"].values
            hi = sub[f"{'acc' if metric == 'accuracy' else metric}_hi"].values - v
            bars = ax.barh(y, v, color=[COLOUR[m] for m in ORDER], height=0.65,
                           xerr=[lo, hi], error_kw=dict(ecolor="#444", lw=0.9, capsize=2))
            for b, m in zip(bars, ORDER):
                if m in USES_LABELS:
                    b.set_hatch("///")
                    b.set_edgecolor("white")
            for yi, vi, h in zip(y, v, hi):
                ax.text(vi + h + 0.01, yi, f"{vi:.2f}", va="center", fontsize=8)
            ax.set_xlim(0, 1.08)
            ax.xaxis.grid(True, color=GRID)
            ax.set_axisbelow(True)
            ax.set_xlabel("Accuracy (fraction of cells)" if metric == "accuracy" else "Adjusted Rand index")
            if col == 0:
                ax.set_yticks(y)
                ax.set_yticklabels(ORDER)
                ax.invert_yaxis()
                ax.set_title(title)
    save(fig, "fig_performance")


def fig_starmap():
    d, truth, regions, preds = predictions("starmap")
    xy = d["xy"]
    fig = plt.figure(figsize=(12, 3.3))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 1.1], wspace=0.12)
    panels = [("Expert layers", truth), ("LLMiniST", preds["LLMiniST"]),
              ("NicheAgent-style", preds["NicheAgent-style"]), ("M3 CardEM", preds["M3 CardEM"])]
    for k, (title, z) in enumerate(panels):
        ax = fig.add_subplot(gs[0, k])
        acc = "\n " if k == 0 else f"\naccuracy {(z == truth).mean():.2f}"
        spatial(ax, xy, z, title + acc, s=7, flip=True)
        wrong = (z != truth) & (k > 0)
        ax.scatter(xy[wrong, 0], xy[wrong, 1], facecolors="none", edgecolors=ERR, s=12, lw=0.5)
    handles = [plt.Line2D([], [], marker="o", ls="", color=PAL[i], label=r) for i, r in enumerate(regions)]
    handles.append(plt.Line2D([], [], marker="o", ls="", color="#cccccc", label="white matter (not present)"))
    handles.append(plt.Line2D([], [], marker="o", ls="", mfc="none", mec=ERR, label="wrong cell"))
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.4, -0.08))

    ax = fig.add_subplot(gs[0, 4])
    Q0, P3, real = d["Q0"][0], d["P3"][0], d["real"][0]  # Layer 1
    types = list(d["types"])
    top = np.argsort(-(Q0 + real))[:6]
    w = 0.27
    yy = np.arange(len(top))
    ax.barh(yy - w, Q0[top], w, color=GREY, label="Gemini card")
    ax.barh(yy, P3[top], w, color=M3C, label="after CardEM")
    ax.barh(yy + w, real[top], w, color="#fdae6b", label="measured")
    ax.set_yticks(yy)
    ax.set_yticklabels([types[i].replace(" interneurons", " int.").replace("excitatory ", "exc. ") for i in top],
                       fontsize=8)
    ax.yaxis.tick_right()
    ax.invert_yaxis()
    ax.set_xlabel("Share of a Layer 1 neighbourhood")
    ax.set_title("Layer 1 card")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    save(fig, "fig_starmap")


def fig_merfish(naming):
    d, truth, regions, preds = predictions("merfish")
    K = len(regions)
    fig = plt.figure(figsize=(13, 4.2))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.1, 1.0, 1, 1], wspace=0.45)

    ax = fig.add_subplot(gs[0, 0])
    real = d["real"]
    n = np.linalg.norm(real, axis=1)
    sim = real @ real.T / np.outer(n, n)
    ax.imshow(sim, cmap="Blues", vmin=0, vmax=1)
    for i in range(K):
        for j in range(K):
            ax.text(j, i, f"{sim[i, j]:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if sim[i, j] > 0.6 else INK)
    ax.set_xticks(range(K))
    ax.set_yticks(range(K))
    ax.set_xticklabels(regions, rotation=90, fontsize=7.5)
    ax.set_yticklabels(regions, fontsize=7.5)
    ax.set_xlabel("Region")
    ax.set_ylabel("Region")
    ax.set_title("A  Region mix cosine")

    ax = fig.add_subplot(gs[0, 1])
    sub = naming[naming.dataset == "merfish"].set_index("method")
    names = ["Nearest expert card", "M1 cosine", "M2 EM", "M3 CardEM"]
    cols = [GREY, M1C, M2C, M3C]
    for i, (m, c) in enumerate(zip(names, cols)):
        ax.barh(i, sub.loc[m, "oracle_named_accuracy"], color="white", edgecolor=c, hatch="////", height=0.6)
        ax.barh(i, sub.loc[m, "accuracy"], color=c, height=0.6)
        ax.text(sub.loc[m, "oracle_named_accuracy"] + 0.01, i, f"{sub.loc[m, 'oracle_named_accuracy']:.2f}",
                va="center", fontsize=8, color=MUTED)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(["Expert card", "M1", "M2", "M3 CardEM"], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.8)
    ax.set_xlabel("Accuracy (solid: own names,\nhatched: best possible names)")
    ax.set_title("B  Grouping vs naming")
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)

    xy = d["xy"]
    z = preds["M3 CardEM"]
    tab = pd.crosstab(z, truth).reindex(index=range(K), columns=range(K), fill_value=0).values
    ri, ci = linear_sum_assignment(-tab)
    renamed = np.array([dict(zip(ri, ci))[k] for k in z])
    spatial(fig.add_subplot(gs[0, 2]), xy, truth, "C  Expert regions\n ", s=2)
    spatial(fig.add_subplot(gs[0, 3]), xy, z, f"D  CardEM names\naccuracy {(z == truth).mean():.2f}", s=2)
    handles = [plt.Line2D([], [], marker="o", ls="", color=PAL[i], label=r) for i, r in enumerate(regions)]
    fig.legend(handles=handles, loc="upper right", ncol=4, frameon=False, bbox_to_anchor=(0.9, 0.2), fontsize=8)
    save(fig, "fig_merfish")
    print(f"MERFISH CardEM with best names: {(renamed == truth).mean():.3f}")


if __name__ == "__main__":
    scores = pd.read_csv(os.path.join(cm.RESULTS, "table_scores.csv"))
    naming = pd.read_csv(os.path.join(cm.RESULTS, "table_naming.csv"))
    fig_pipeline()
    fig_performance(scores)
    fig_starmap()
    fig_merfish(naming)
    print("figures written to", OUT)
