"""BANKSY niches on STARmap BZ5 (mouse mPFC), K forced to the 4 annotated layers,
over 5 seeds; the seed-0 run is the one passed to the LLM.

Writes results/STARMAP/banksy_starmap_seeds.csv, results/STARMAP/banksy_starmap_labels.csv,
results/STARMAP/Banksy_StarMAP.xlsx and results/STARMAP/starmap_banksy_best.png.
"""
import tempfile

import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
from banksy.initialize_banksy import initialize_banksy
from banksy.run_banksy import run_banksy_multiparam
from sklearn.metrics import adjusted_rand_score as ARI
from sklearn.metrics import normalized_mutual_info_score as NMI

from common import load, marker_tables, res, save_markers, seed_all

KEYS = ("x", "y", "spatial")
COLORS = list(plt.cm.tab20.colors) + list(plt.cm.tab20b.colors)

s = load("starmap")
s.obs["Region"] = s.obs["Region"].astype(str).astype("category")   # stored as ints


def run(a, seed, lam=0.8, k_geom=15, n_clusters=4):
    """Normalise + log1p on all panel genes (no HVG step, the panel is small).
    max_m=1 adds the gradient (AGF) term. max_labels forces Leiden to exactly n_clusters
    (K = number of annotated layers: an oracle choice, disclosed in the report)."""
    seed_all(seed)                                 # BANKSY's PCA is unseeded; partition_seed seeds Leiden
    a = a.copy()
    sc.pp.normalize_total(a); sc.pp.log1p(a)
    a.obs["x"], a.obs["y"] = a.obsm["spatial"][:, 0], a.obsm["spatial"][:, 1]
    a.obs["cluster_name"] = a.obs["Region"]        # used only to report ARI
    bd = initialize_banksy(a, KEYS, k_geom, nbr_weight_decay="scaled_gaussian", max_m=1,
                           plt_edge_hist=False, plt_nbr_weights=False, plt_agf_angles=False, plt_theta=False)
    df = run_banksy_multiparam(a, bd, [lam], [], color_list=COLORS, max_m=1, filepath=tempfile.mkdtemp(),
                               key=KEYS, pca_dims=[20], annotation_key="cluster_name",
                               cluster_algorithm="leiden", partition_seed=1234, max_labels=n_clusters,
                               match_labels=False, savefig=False, add_nonspatial=False)
    plt.close("all")
    return [str(x) for x in df.iloc[0]["labels"].dense]


# Five seeds show how much ARI moves with the PCA seed
rows, labels = [], {}
for seed in [0, 1, 42, 1234, 2024]:
    labels[seed] = run(s, seed)
    rows.append({"seed": seed, "ARI": round(ARI(s.obs["Region"], labels[seed]), 3),
                 "NMI": round(NMI(s.obs["Region"], labels[seed]), 3)})
seeds = pd.DataFrame(rows)
seeds.to_csv(res("STARMAP", "banksy_starmap_seeds.csv"), index=False)
print(seeds, "\nmean ARI", seeds.ARI.mean().round(3), "±", seeds.ARI.std().round(3))

# seed 0 is the run passed to the LLM
s.obs["niche"] = pd.Categorical(labels[0])
s.obs[["Region", "niche"]].to_csv(res("STARMAP", "banksy_starmap_labels.csv"))
save_markers(res("STARMAP", "Banksy_StarMAP.xlsx"), *marker_tables(s, "niche"))

ari, nmi = ARI(s.obs["Region"], s.obs["niche"]), NMI(s.obs["Region"], s.obs["niche"])
fig_, ax = plt.subplots(1, 2, figsize=(13, 5))
sc.pl.embedding(s, basis="spatial", color="Region", s=30, ax=ax[0], show=False, title="STARmap BZ5 ground truth (4 layers)")
sc.pl.embedding(s, basis="spatial", color="niche", s=30, ax=ax[1], show=False,
                title=f"BANKSY k=4 (seed 0)  ARI {ari:.3f}  NMI {nmi:.3f}")
for x in ax:
    x.set_aspect("equal"); x.axis("off")
plt.savefig(res("STARMAP", "starmap_banksy_best.png"), dpi=200, bbox_inches="tight")
