"""Niche vs expert layer on DLPFC 151673: cross-tabs (used to score the LLM labels) and the
side-by-side spatial figure. Run after dlpfc_banksy.py and dlpfc_cellcharter.py.

Writes results/Visium/crosstab_{banksy,cellcharter}_vs_region.csv and results/Visium/spatial_region_banksy_cellcharter.png.
"""
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from common import load, res

a = load("dlpfc")
a.var_names_make_unique()
a = a[a.obs["Region"].notna()].copy()

for col, f in [("niche_banksy", "banksy_dlpfc_labels.csv"), ("niche_cellcharter", "cellcharter_dlpfc_labels.csv")]:
    lab = pd.read_csv(res("Visium", f), index_col=0)[col].astype(str)
    a.obs[col] = lab.reindex(a.obs_names).fillna("filtered")   # CellCharter drops spots with <3 counts

titles = {"Region": "Expert layers"}
for col, out, name in [("niche_banksy", "crosstab_banksy_vs_region.csv", "BANKSY"),
                       ("niche_cellcharter", "crosstab_cellcharter_vs_region.csv", "CellCharter k=6")]:
    ct = pd.crosstab(a.obs[col], a.obs["Region"])
    ct.index.name, ct.columns.name = col, "Region"
    ct.to_csv(res("Visium", out))
    print(f"\n=== {out} ===\n", ct)
    titles[col] = f"{name} (ARI {adjusted_rand_score(a.obs['Region'], a.obs[col]):.3f})"

x, y = a.obsm["spatial"][:, 0], -a.obsm["spatial"][:, 1]   # flip y for anatomical orientation
fig_, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, col in zip(axes, ["Region", "niche_banksy", "niche_cellcharter"]):
    cats = sorted(a.obs[col].astype(str).unique())
    cmap = {c: plt.cm.tab10(i % 10) for i, c in enumerate(cats)}
    ax.scatter(x, y, c=[cmap[v] for v in a.obs[col].astype(str)], s=4)
    for c in cats:
        ax.scatter([], [], c=[cmap[c]], label=c)
    ax.set_title(titles[col]); ax.set_aspect("equal"); ax.axis("off")
    ax.legend(bbox_to_anchor=(1, 1), fontsize=7, markerscale=1.5, frameon=False)
plt.tight_layout()
plt.savefig(res("Visium", "spatial_region_banksy_cellcharter.png"), dpi=200, bbox_inches="tight")
