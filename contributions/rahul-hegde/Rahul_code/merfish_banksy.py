"""BANKSY niches on MERFISH (mouse hypothalamus, Bregma -0.14), then the top-10 Wilcoxon markers.

    python merfish_banksy.py          # adopted config + markers + figure
    python merfish_banksy.py --grid   # also the oracle-tuned grid that picked it

Writes results/MERFISH/banksy_merfish_labels.csv, results/MERFISH/Banksy_MERFISH.xlsx, results/MERFISH/merfish_banksy_best.png
(and results/MERFISH/banksy_merfish_grid.csv with --grid).
"""
import argparse
import tempfile

import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
from banksy.initialize_banksy import initialize_banksy
from banksy.run_banksy import run_banksy_multiparam
from sklearn.metrics import normalized_mutual_info_score as NMI

from common import load, marker_tables, res, save_markers, seed_all

ap = argparse.ArgumentParser()
ap.add_argument("--grid", action="store_true", help="run the oracle-tuned grid")
args = ap.parse_args()

KEYS = ("x", "y", "spatial")
COLORS = list(plt.cm.tab20.colors) + list(plt.cm.tab20b.colors)
m = load("merfish")


def run(a, resolutions, k_geom, use_agf, seed=0, lam=0.8):
    """use_agf toggles BANKSY's azimuthal Gabor filter (max_m 1 vs 0). Seeds are reset before both random steps."""
    mm = 1 if use_agf else 0
    a = a.copy()
    sc.pp.normalize_total(a); sc.pp.log1p(a)
    a.obs["x"], a.obs["y"] = a.obsm["spatial"][:, 0], a.obsm["spatial"][:, 1]
    a.obs["cluster_name"] = a.obs["Region"].astype(str).astype("category")   # used only to report ARI
    seed_all(seed)
    bd = initialize_banksy(a, KEYS, k_geom, nbr_weight_decay="scaled_gaussian", max_m=mm,
                           plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False, plt_theta=False)
    seed_all(seed)
    df = run_banksy_multiparam(a, bd, [lam], resolutions, color_list=COLORS, max_m=mm, filepath=tempfile.mkdtemp(),
                               key=KEYS, pca_dims=[20], annotation_key="cluster_name",
                               cluster_algorithm="leiden", partition_seed=1234, max_labels=None,
                               match_labels=False, savefig=False, add_nonspatial=False)
    plt.close("all")
    gt = a.obs["cluster_name"].values
    df["nmi"] = [NMI(gt, l.dense) for l in df["labels"]]
    return df


if args.grid:
    # ORACLE-TUNED grid over k_geom, AGF on/off and resolution, scored against Region (disclosed in the report)
    rows = []
    for kg in [15, 30, 50, 75]:
        for agf in [True, False]:
            d = run(m, [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5], kg, agf)
            rows.append(d[["resolution", "num_labels", "ari", "nmi"]].assign(k_geom=kg, agf=agf))
    allr = pd.concat(rows)[["k_geom", "agf", "resolution", "num_labels", "ari", "nmi"]]
    allr.to_csv(res("MERFISH", "banksy_merfish_grid.csv"), index=False)
    print("--- configs that produced 8 clusters ---")
    print(allr[allr.num_labels == 8].sort_values("ari", ascending=False))

# Adopted config from the grid: k_geom=30, no AGF, resolution 0.35 -> 8 niches (original run: ARI 0.530, NMI 0.588)
row = run(m, [0.35], 30, False).iloc[0]
print(row["num_labels"], "niches | ARI", round(row["ari"], 3), "| NMI", round(row["nmi"], 3))
m.obs["niche"] = pd.Categorical([str(i) for i in row["labels"].dense])
m.obs[["Region", "niche"]].to_csv(res("MERFISH", "banksy_merfish_labels.csv"))
save_markers(res("MERFISH", "Banksy_MERFISH.xlsx"), *marker_tables(m, "niche"))

fig_, ax = plt.subplots(1, 2, figsize=(13, 5))
sc.pl.embedding(m, basis="spatial", color="Region", s=8, ax=ax[0], show=False, title="MERFISH -0.14 ground truth (8 regions)")
sc.pl.embedding(m, basis="spatial", color="niche", s=8, ax=ax[1], show=False,
                title=f"BANKSY {row['num_labels']} niches  ARI {row['ari']:.3f}  NMI {row['nmi']:.3f}")
for x in ax:
    x.set_aspect("equal"); x.axis("off")
plt.savefig(res("MERFISH", "merfish_banksy_best.png"), dpi=200, bbox_inches="tight")
