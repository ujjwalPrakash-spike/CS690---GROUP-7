"""PROST niches on MERFISH (Bregma -0.14), then the top-10 Wilcoxon markers. Needs a CUDA GPU.

Settings: init="kmeans"; n_clusters=8 = number of annotated regions (oracle choice, disclosed);
k_neighbors=15 to match BANKSY's default graph width (PROST's default is 7). Sweeping k_neighbors (6-75),
epochs and init changed little, so this is reported as PROST's result on this slice.
Expected: ARI 0.428, NMI 0.528.

Writes results/MERFISH/prost_merfish_labels.csv, results/MERFISH/PROST_MERFISH.xlsx and results/MERFISH/merfish_prost_best.png.
"""
import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
from sklearn.metrics import adjusted_rand_score as ARI
from sklearn.metrics import normalized_mutual_info_score as NMI

from common import load, marker_tables, res, save_markers
from prost_common import prepare, run

raw = load("merfish")
raw = raw[raw.obs["Region"].notna()].copy()       # PROST is scored on the annotated cells only
a = prepare(raw)
gt = a.obs["Region"].astype(str)

raw.obs["niche"] = pd.Categorical(run(a, n_clusters=8, k_neighbors=15).values)
print("niches", raw.obs["niche"].nunique(), "| ARI", round(ARI(gt, raw.obs["niche"]), 3),
      "| NMI", round(NMI(gt, raw.obs["niche"]), 3))
raw.obs[["Region", "niche"]].to_csv(res("MERFISH", "prost_merfish_labels.csv"))

# same marker recipe as BANKSY (raw counts, CP10k + log1p), so only the clustering differs
save_markers(res("MERFISH", "PROST_MERFISH.xlsx"), *marker_tables(raw, "niche"))

fig_, ax = plt.subplots(1, 2, figsize=(13, 5))
sc.pl.embedding(raw, basis="spatial", color="Region", s=8, ax=ax[0], show=False, title="MERFISH -0.14 ground truth")
sc.pl.embedding(raw, basis="spatial", color="niche", s=8, ax=ax[1], show=False,
                title=f"PROST 8 niches  ARI {ARI(gt, raw.obs['niche']):.3f}")
for x in ax:
    x.set_aspect("equal"); x.axis("off")
plt.savefig(res("MERFISH", "merfish_prost_best.png"), dpi=200, bbox_inches="tight")
