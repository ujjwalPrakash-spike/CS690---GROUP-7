"""BANKSY + Harmony niches on the CosMx SMI lung tumour slice (global_z0), then the top-10
Wilcoxon markers per niche.

    python smi_banksy.py           # untuned reference + adopted (oracle-tuned) run + markers + figure
    python smi_banksy.py --grid    # also the oracle-tuned grid (k_geom x resolution x 3 seeds, slow)
    python smi_banksy.py --check   # also run one config twice to confirm the seeding is deterministic

Writes results/banksy_smi_labels.csv, results/Banksy_SMI.xlsx, results/banksy_smi_purity.csv,
results/banksy_smi_untuned.csv, figures/banksy_smi_vs_truth.png (and results/banksy_smi_grid_seeded.csv with --grid).
"""
import argparse

import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
from banksy.cluster_methods import run_Leiden_partition
from banksy.embed_banksy import generate_banksy_matrix
from banksy.initialize_banksy import initialize_banksy
from banksy_utils.umap_pca import pca_umap
from harmony import harmonize
from sklearn.metrics import adjusted_rand_score as ari
from sklearn.metrics import normalized_mutual_info_score as nmi

from common import fig, load, marker_tables, res, save_markers, seed_all

ap = argparse.ArgumentParser()
ap.add_argument("--grid", action="store_true", help="run the oracle-tuned grid")
ap.add_argument("--check", action="store_true", help="determinism check")
args = ap.parse_args()

# Drop the 20 NegPrb negative-control probes (980 -> 960 genes) and cells with no Region.
# Region is used only for evaluation (ARI/NMI, scoring), never for clustering.
ad = load("smi")
ad = ad[:, ~ad.var_names.str.startswith("NegPrb")].copy()
ad = ad[ad.obs["Region"].notna()].copy()
counts = ad.copy()                                 # raw counts, kept for the marker step
# spatial_global holds slide-wide coordinates, so neighbours are found across all 4 FOV batches
ad.obs["cx_g"] = ad.obsm["spatial_global"][:, 0]
ad.obs["cy_g"] = ad.obsm["spatial_global"][:, 1]
COORDS = ("cx_g", "cy_g", "spatial_global")
sc.pp.normalize_total(ad, target_sum=1e4)          # CP10k + log1p, as in the BANKSY vignette
sc.pp.log1p(ad)
print(ad.shape)                                    # (18895, 960)


def run(kg, resolutions, seed=0):
    """One BANKSY + Harmony run, fully seeded. Returns the Leiden results table.

    Fixed: lambda=0.8 (authors' value for domain segmentation), max_m=1, pca_dims=50,
    Harmony on the 'batch' key (removes the FOV batch effect).
    Seeds are reset before each random step: BANKSY's PCA is unseeded, and
    harmony-pytorch uses torch's random generator, not numpy's.
    """
    seed_all(seed)
    b = initialize_banksy(ad, COORDS, kg, nbr_weight_decay="scaled_gaussian", max_m=1,
                          plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False, plt_theta=False)
    b, _ = generate_banksy_matrix(ad, b, [0.8], max_m=1)
    seed_all(seed)
    pca_umap(b, pca_dims=[50], add_umap=False, plt_remaining_var=False)
    s = b["scaled_gaussian"][0.8]["adata"]
    seed_all(seed)
    s.obsm["reduced_pc_50"] = harmonize(s.obsm["reduced_pc_50"], s.obs, batch_key="batch")
    r, _ = run_Leiden_partition(b, resolutions, num_nn=50, num_iterations=-1,
                                partition_seed=1234, match_labels=False)
    plt.close("all")
    return r


def scores(r, kg, seed):
    out = []
    for i in r.index:
        lab = [str(x) for x in r.loc[i, "labels"].dense]
        out.append(dict(k_geom=kg, seed=seed, res=r.loc[i, "resolution"], k=r.loc[i, "num_labels"],
                        ARI=round(ari(ad.obs["Region"], lab), 3), NMI=round(nmi(ad.obs["Region"], lab), 3)))
    return out


if args.check:
    rows = scores(run(30, [0.2, 0.3, 0.4]), 30, 0) + scores(run(30, [0.2, 0.3, 0.4]), 30, 0)
    print("determinism check (both halves must match):\n", pd.DataFrame(rows).to_string(index=False))

# Untuned reference: the BANKSY vignette's resolution 0.6 with k_geom=30, chosen without ground truth
untuned = pd.DataFrame(scores(run(30, [0.6]), 30, 0))
untuned.to_csv(res("banksy_smi_untuned.csv"), index=False)
print("untuned reference:\n", untuned.to_string(index=False))

if args.grid:
    # ORACLE-TUNED grid, scored against Region (disclosed in the report).
    # NMI is flat (0.28-0.36) across the grid, while ARI mostly tracks the number of clusters.
    rows = []
    for kg in [30, 50, 75]:
        for sd in [0, 1, 42]:
            rows += scores(run(kg, [0.2, 0.3, 0.4, 0.5], seed=sd), kg, sd)
    g = pd.DataFrame(rows)
    g.to_csv(res("banksy_smi_grid_seeded.csv"), index=False)
    print(g.groupby(["k_geom", "res"])
           .agg(k_mean=("k", "mean"), k_sd=("k", "std"), ARI=("ARI", "mean"), ARI_sd=("ARI", "std"),
                NMI=("NMI", "mean"), NMI_sd=("NMI", "std"))
           .round(3).sort_values("ARI", ascending=False).to_string())

# Adopted (oracle-tuned) config: k_geom 30, resolution 0.3, seed 0. Expected: 7 niches, ARI 0.248, NMI 0.323
r = run(30, [0.3], seed=0)
ad.obs["banksy"] = pd.Categorical([str(x) for x in r.loc[r.index[0], "labels"].dense])
print("adopted: k", r.loc[r.index[0], "num_labels"],
      "| ARI", round(ari(ad.obs["Region"], ad.obs["banksy"]), 3),
      "| NMI", round(nmi(ad.obs["Region"], ad.obs["banksy"]), 3))
ad.obs[["banksy", "Region", "cx_g", "cy_g", "batch"]].to_csv(res("banksy_smi_labels.csv"))

# Markers from raw counts (CP10k + log1p) on all 960 genes, not from the BANKSY matrix
counts.obs["banksy"] = ad.obs["banksy"].values
save_markers(res("Banksy_SMI.xlsx"), *marker_tables(counts, "banksy"))

# Purity and majority region per niche: the input to the pre-registered scoring key
ct = pd.crosstab(ad.obs["banksy"], ad.obs["Region"])
purity = pd.DataFrame({"maps_to": ct.idxmax(axis=1), "purity": (ct.max(axis=1) / ct.sum(axis=1)).round(2),
                       "n": ct.sum(axis=1)})
pd.concat([purity, ct], axis=1).to_csv(res("banksy_smi_purity.csv"))
print(purity)

# Figure. These niche names are OUR reading of the markers, for the legend only; they are not LLM output.
names = {"0": "0 macrophages", "1": "1 alveolar stroma", "2": "2 fibroblast stroma", "3": "3 tumour interior",
         "4": "4 inflammatory myeloid", "5": "5 lymphoid structure", "6": "6 airway epithelium"}
ad.obs["banksy_named"] = ad.obs["banksy"].astype(str).map(names)
xy = ad.obsm["spatial_global"]
fig_, axes = plt.subplots(1, 2, figsize=(22, 4.5), sharex=True, sharey=True)
for ax, col, title in zip(axes, ["Region", "banksy_named"],
                          ["Ground truth (Region), 8 regions",
                           "BANKSY + Harmony, 7 niches (k_geom 30, λ=0.8, res 0.3)"]):
    for k in sorted(ad.obs[col].astype(str).unique()):
        m = (ad.obs[col].astype(str) == k).values
        ax.scatter(xy[m, 0], xy[m, 1], s=1.5, label=k, rasterized=True)
    ax.set_title(title, fontsize=10); ax.set_aspect("equal")
    ax.legend(markerscale=8, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=4, frameon=False)
plt.tight_layout()
plt.savefig(fig("banksy_smi_vs_truth.png"), dpi=200, bbox_inches="tight")
