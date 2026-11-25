"""Oracle partition on the CosMx SMI slice: the top-10 Wilcoxon markers of the 8 expert regions
themselves, with the region names blinded to letters A-H. These tables feed the `gt` arm of run_gemini.py.

Writes results/CosMX/gt_top10_blinded.csv, results/CosMX/gt_log2fc_blinded.csv and results/CosMX/gt_region_key.csv
(the region -> letter answer key, used for scoring and never sent to the LLM).
"""
import random

import pandas as pd
import scanpy as sc

from common import load, res

# Same marker recipe as the clustering arm: drop the NegPrb negative-control probes,
# CP10k + log1p, one-vs-rest Wilcoxon. Here the groups are the expert regions.
ad = load("smi")
ad = ad[:, ~ad.var_names.str.startswith("NegPrb")].copy()
sc.pp.normalize_total(ad, target_sum=1e4)
sc.pp.log1p(ad)
print(ad.shape, ad.obs["Region"].nunique(), "regions")

sc.tl.rank_genes_groups(ad, "Region", method="wilcoxon")
rg = ad.uns["rank_genes_groups"]
regions = list(rg["names"].dtype.names)
top10 = pd.DataFrame({r: [rg["names"][r][i] for i in range(10)] for r in regions})
lfc = pd.DataFrame({r: [round(float(rg["logfoldchanges"][r][i]), 2) for i in range(10)] for r in regions})

# Shuffle the regions with a fixed seed (7) and relabel them A-H, so neither the names nor
# their alphabetical order leak into the prompt.
rng = random.Random(7)
shuffled = regions[:]
rng.shuffle(shuffled)
key = {r: chr(65 + i) for i, r in enumerate(shuffled)}

blind10 = top10[list(key)].rename(columns=key).sort_index(axis=1)
blindfc = lfc[list(key)].rename(columns=key).sort_index(axis=1)
blind10.to_csv(res("CosMX", "gt_top10_blinded.csv"), index=False)
blindfc.to_csv(res("CosMX", "gt_log2fc_blinded.csv"), index=False)
pd.Series(key, name="letter").rename_axis("region").to_csv(res("CosMX", "gt_region_key.csv"))
print(blind10.to_markdown(index=False))
