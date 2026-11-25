"""CellCharter niches on Visium DLPFC 151673, with the settings of the authors' individual.py,
then the top-10 Wilcoxon markers per niche.

Writes results/Visium/cellcharter_dlpfc_labels.csv, results/Visium/top10_niche_cellcharter.csv and
results/Visium/cellcharter_autok_stability.png. Runs much faster on a GPU (scVI).

    python dlpfc_cellcharter.py                 # main run
    python dlpfc_cellcharter.py --sensitivity   # also report ARI for k = 5, 6, 7
"""
import argparse

import cellcharter as cc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import scvi
import squidpy as sq
from sklearn.metrics import adjusted_rand_score

from common import load, marker_tables, res

ap = argparse.ArgumentParser()
ap.add_argument("--sensitivity", action="store_true", help="post-hoc ARI for k = 5, 6, 7")
args = ap.parse_args()

raw = load("dlpfc")
raw.var_names_make_unique()
raw = raw[raw.obs["Region"].notna()].copy()        # same 3,611 spots as BANKSY
counts = raw.copy()                                # kept for the marker step

# Preprocessing follows individual.py: drop genes/cells with <3 counts, keep raw counts for scVI,
# CPM (1e6) + log1p, 5000 HVGs with seurat_v3 on the raw counts
a = raw.copy()
sc.pp.filter_genes(a, min_counts=3)
sc.pp.filter_cells(a, min_counts=3)
a.layers["counts"] = a.X.copy()
sc.pp.normalize_total(a, target_sum=1e6)
sc.pp.log1p(a)
sc.pp.highly_variable_genes(a, n_top_genes=5000, subset=True, layer="counts", flavor="seurat_v3")

# scVI latent space, n_latent=5 as in the authors' script; seed 12345 (early stopping ended at epoch 303)
scvi.settings.seed = 12345
scvi.model.SCVI.setup_anndata(a, layer="counts")
model = scvi.model.SCVI(a, n_latent=5)
model.train(early_stopping=True, plan_kwargs=dict(optimizer="AdamW", reduce_lr_on_plateau=True))
a.obsm["X_scVI"] = model.get_latent_representation(a).astype(np.float32)

# coord_type="grid", n_neighs=6: Visium spots sit on a hexagonal grid
# n_layers=4: aggregate up to 4 rings of neighbours (authors' setting)
sq.gr.spatial_neighbors(a, coord_type="grid", n_neighs=6)
cc.gr.aggregate_neighbors(a, n_layers=4, use_rep="X_scVI", out_key="X_cellcharter")

# AutoK fits k = 2..10 and scores how stable each k is across 10 runs
autok = cc.tl.ClusterAutoK(n_clusters=(2, 10), max_runs=10, convergence_tol=0.001)
autok.fit(a, use_rep="X_cellcharter")
cc.pl.autok_stability(autok)
plt.savefig(res("Visium", "cellcharter_autok_stability.png"), dpi=150, bbox_inches="tight")
plt.close("all")
print("AutoK best k:", autok.best_k)

# k = 6: the most stable k once the trivial k = 2 split is excluded (stability 0.692).
# Read off the stability plot, without using the Region labels. Expected ARI 0.430.
K = 6
a.obs["niche_cellcharter"] = autok.predict(a, use_rep="X_cellcharter", k=K)
print(f"k={K}  ARI={adjusted_rand_score(a.obs['Region'], a.obs['niche_cellcharter']):.3f}")

if args.sensitivity:
    # post-hoc check only; k was fixed above (original run: k=5 0.497, k=7 0.434)
    for k in (5, 7):
        labs = autok.predict(a, use_rep="X_cellcharter", k=k)
        print(f"k={k}  ARI={adjusted_rand_score(a.obs['Region'], labs):.3f}")

lab = a.obs["niche_cellcharter"].astype(str)
counts = counts[lab.index].copy()                  # spots kept by the <3-count filter
counts.obs["niche_cellcharter"] = pd.Categorical(lab)
counts.obs[["Region", "niche_cellcharter"]].to_csv(res("Visium", "cellcharter_dlpfc_labels.csv"))

# top-10 genes per niche, one column per niche (pasted into the prompts)
genes, _, _ = marker_tables(counts, "niche_cellcharter")
genes.columns = [f"niche_{c}" for c in genes.columns]
genes.to_csv(res("Visium", "top10_niche_cellcharter.csv"))
