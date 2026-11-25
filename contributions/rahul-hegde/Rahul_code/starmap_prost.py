"""PROST niches on STARmap BZ5, K forced to the 4 annotated layers. Needs a CUDA GPU.

    python starmap_prost.py               # adopted run + markers + figure
    python starmap_prost.py --seed-check  # also kmeans vs mclust initialisation over 5 seeds (needs R + mclust)

Settings: init="kmeans", k_neighbors=30 (oracle-tuned, disclosed), seed 0. Expected ARI 0.809.
Writes results/STARMAP/prost_starmap_labels.csv, results/STARMAP/PROST_StarMAP.xlsx, results/STARMAP/prost_starmap.png
(and results/STARMAP/prost_starmap_seed_check.csv with --seed-check).
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score as ARI
from sklearn.metrics import normalized_mutual_info_score as NMI

from common import load, marker_tables, res, save_markers
from prost_common import prepare, run

ap = argparse.ArgumentParser()
ap.add_argument("--seed-check", action="store_true", help="kmeans vs mclust over 5 seeds")
args = ap.parse_args()

raw = load("starmap")
a = prepare(raw)
gs = a.obs["Region"].astype(str)


def patch_mclust():
    """PROST's built-in mclust call did not work here. This replacement passes the matrix to R
    explicitly (column-major), seeds R, and is patched into PROST."""
    import PROST
    import PROST.model as pm
    import PROST.utils as pu
    import rpy2.robjects as ro

    def mclust_fixed(data, num_cluster, modelNames="EEE", random_seed=818):
        np.random.seed(random_seed)
        d = np.asarray(data, dtype=np.float64)
        nr, nc = d.shape
        ro.r("library(mclust)")
        ro.globalenv["Xflat"] = ro.FloatVector(d.ravel(order="F"))
        ro.r(f"X <- matrix(Xflat, nrow={nr}, ncol={nc})")
        ro.r(f"set.seed({random_seed})")
        ro.r(f'res <- Mclust(X, {num_cluster}, "{modelNames}")')
        return np.array(ro.r("res$classification")).astype(int)

    pm.mclust = pu.mclust = PROST.mclust = mclust_fixed


if args.seed_check:
    # Seed stability of the two initialisations; mclust was unstable, which is why kmeans is used
    patch_mclust()
    rows = []
    for init in ["mclust", "kmeans"]:
        for sd in [0, 42, 818, 1234, 2024]:
            lab = run(a, n_clusters=4, k_neighbors=30, init=init, seed=sd)
            rows.append({"init": init, "seed": sd, "clusters": lab.nunique(),
                         "ARI": round(ARI(gs, lab), 3), "NMI": round(NMI(gs, lab), 3)})
            print(rows[-1])
    r = pd.DataFrame(rows)
    r.to_csv(res("STARMAP", "prost_starmap_seed_check.csv"), index=False)
    print(r.groupby("init")["ARI"].agg(["mean", "std", "min", "max"]).round(3))

raw.obs["niche"] = pd.Categorical(run(a, n_clusters=4, k_neighbors=30, seed=0).values)
ari = ARI(gs, raw.obs["niche"])
print("ARI", round(ari, 3), "NMI", round(NMI(gs, raw.obs["niche"]), 3))
raw.obs[["Region", "niche"]].to_csv(res("STARMAP", "prost_starmap_labels.csv"))
save_markers(res("STARMAP", "PROST_StarMAP.xlsx"), *marker_tables(raw, "niche"))

fig_, ax = plt.subplots(1, 2, figsize=(13, 6))
for axi, col, ttl in zip(ax, ["Region", "niche"], ["Ground truth", f"PROST (ARI {ari:.3f})"]):
    for g in sorted(raw.obs[col].astype(str).unique()):
        m = (raw.obs[col].astype(str) == g).values
        axi.scatter(raw.obsm["spatial"][m, 0], raw.obsm["spatial"][m, 1], s=12, label=g)
    axi.set_title(ttl); axi.set_aspect("equal"); axi.axis("off")
    axi.legend(markerscale=2, fontsize=8, loc="center left", bbox_to_anchor=(1, 0.5))
plt.tight_layout()
plt.savefig(res("STARMAP", "prost_starmap.png"), dpi=150)
