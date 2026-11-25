"""BANKSY niches on Visium DLPFC 151673, with the settings of the authors' DLPFC tutorial
(DLPFC_concatenate_multisample.py), then the top-10 Wilcoxon markers per niche.

Writes results/Visium/banksy_dlpfc_labels.csv and results/Visium/top10_niche_banksy.csv.
"""
import tempfile

import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
from banksy.initialize_banksy import initialize_banksy
from banksy.run_banksy import run_banksy_multiparam

from common import load, marker_tables, res, seed_all

HVG_URL = ("https://raw.githubusercontent.com/prabhakarlab/Banksy_py/main/"
           "data/DLPFC/simple_concat/output_hvg_median_library.csv")

raw = load("dlpfc")
raw.var_names_make_unique()
raw = raw[raw.obs["Region"].notna()].copy()        # 3,639 -> 3,611 annotated spots
counts = raw.copy()                                # kept for the marker step

a = raw.copy()
a.var_names = a.var_names.str.upper()
sc.pp.normalize_total(a)                           # tutorial: no target_sum and no log1p (X is raw counts)

# HVGs: the authors' published list (~5000 genes), upper-cased to match var_names
hvg = pd.read_csv(HVG_URL)["hvgs"].str.upper()
hvg = [g for g in hvg if g in a.var_names]
print(len(hvg), "HVGs kept")
a = a[:, hvg].copy()

a.obs["x_pixel"] = a.obsm["spatial"][:, 0]
a.obs["y_pixel"] = a.obsm["spatial"][:, 1]
coord_keys = ("x_pixel", "y_pixel", "spatial")
# Region is passed only so BANKSY can report ARI; it is not used for clustering
a.obs["cluster_name"] = a.obs["Region"].astype(str).astype("category")

# k_geom=6: the six direct neighbours on the Visium hexagonal grid
# max_m=0: no azimuthal Gabor filter, as in the tutorial
banksy_dict = initialize_banksy(
    a, coord_keys=coord_keys, num_neighbours=6,
    nbr_weight_decay="scaled_gaussian", max_m=0,
    plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False, plt_theta=False,
)

# lambda=0.2 (authors' value for cell-typing-like domains), resolution=0.6, pca_dims=20 from the tutorial.
# add_nonspatial=True also runs lambda=0 as a non-spatial baseline (ARI ~0.33).
# partition_seed seeds Leiden; seed_all seeds BANKSY's PCA, which the library leaves unseeded.
seed_all(1234)
results_df = run_banksy_multiparam(
    a, banksy_dict=banksy_dict,
    lambda_list=[0.2], resolutions=[0.6], pca_dims=[20],
    color_list=list(plt.cm.tab20.colors) + list(plt.cm.tab20b.colors),
    max_m=0, filepath=tempfile.mkdtemp(), key=coord_keys,
    partition_seed=1234, match_labels=False, savefig=False,
    annotation_key="cluster_name", cluster_algorithm="leiden", add_nonspatial=True,
)
plt.close("all")
print(results_df[["decay", "lambda_param", "resolution", "num_labels", "ari"]])

# keep the spatial run (lambda 0.2, resolution 0.6); expected: 6 niches, ARI 0.602
lab = results_df.loc["scaled_gaussian_pc20_nc0.20_r0.60", "labels"]
counts.obs["niche_banksy"] = pd.Categorical([str(x) for x in lab.dense])
counts.obs[["Region", "niche_banksy"]].to_csv(res("Visium", "banksy_dlpfc_labels.csv"))

# top-10 genes per niche, one column per niche (pasted into the prompts)
genes, _, _ = marker_tables(counts, "niche_banksy")
genes.columns = [f"niche_{c}" for c in genes.columns]
genes.to_csv(res("Visium", "top10_niche_banksy.csv"))
