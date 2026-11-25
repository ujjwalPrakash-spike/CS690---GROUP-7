"""Shared pieces: folder paths, seeding, and the top-10 Wilcoxon marker tables used for every prompt."""
import os
import random

import matplotlib
matplotlib.use("Agg")  # scripts save figures instead of showing them
import numpy as np
import pandas as pd
import scanpy as sc

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(HERE, "figures")
for _d in (RESULTS, FIGURES):
    os.makedirs(_d, exist_ok=True)

# file names written by fetch_data.py
FILES = {
    "dlpfc": "dlpfc_151673.h5ad",
    "smi": "cosmx_lung_global_z0.h5ad",
    "merfish": "merfish_bregma_-0.14.h5ad",
    "starmap": "starmap_BZ5.h5ad",
}


def load(name):
    return sc.read_h5ad(os.path.join(DATA, FILES[name]))


def res(name):
    return os.path.join(RESULTS, name)


def fig(name):
    return os.path.join(FIGURES, name)


def seed_all(seed):
    """BANKSY's PCA and harmony-pytorch are not seeded inside the libraries, so seed numpy and torch."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass


def marker_tables(adata_counts, groupby, n=10):
    """One-vs-rest Wilcoxon on raw counts after CP10k + log1p (the Hou & Ji 2024 marker step).

    Returns (genes, log2fc, long): top-n genes per niche, their log2 fold-changes, and a long table.
    """
    a = sc.AnnData(adata_counts.X.copy(), obs=adata_counts.obs[[groupby]].copy(), var=adata_counts.var.copy())
    a.obs[groupby] = a.obs[groupby].astype(str).astype("category")
    sc.pp.normalize_total(a, target_sum=1e4)
    sc.pp.log1p(a)
    sc.tl.rank_genes_groups(a, groupby, method="wilcoxon")
    groups = a.obs[groupby].cat.categories.tolist()
    long = pd.concat([sc.get.rank_genes_groups_df(a, group=g).head(n).assign(niche=g) for g in groups])
    long = long[["niche", "names", "logfoldchanges", "scores", "pvals_adj"]]
    long.columns = ["niche", "gene", "log2FC", "score", "padj"]
    genes = pd.DataFrame({g: long.loc[long.niche == g, "gene"].values for g in groups})
    lfc = pd.DataFrame({g: long.loc[long.niche == g, "log2FC"].round(3).values for g in groups})
    return genes, lfc, long


def save_markers(path, genes, lfc, long):
    """Three sheets: top10_genes (pasted into the prompts), log2FC (template 4), full."""
    with pd.ExcelWriter(path) as w:
        genes.to_excel(w, sheet_name="top10_genes", index=False)
        lfc.to_excel(w, sheet_name="log2FC", index=False)
        long.to_excel(w, sheet_name="full", index=False)
    print("wrote", path)
