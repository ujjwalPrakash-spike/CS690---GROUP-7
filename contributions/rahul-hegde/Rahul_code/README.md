# Niche detection and marker genes

This folder holds Yahu's part of the project:

- Spatial niches from three existing methods (BANKSY, CellCharter, PROST) on four datasets
- The top-10 Wilcoxon marker genes per niche, which are the tables pasted into the LLM prompts
- The niche vs expert-region cross-tabs used to build the scoring key

Expert region labels (`obs['Region']`) are never used for clustering. They are used to report ARI and NMI and to score
the LLM answers. Runs where the number of niches or another setting was chosen by looking at ARI are marked
**oracle-tuned** below and in the report.

## Installation

Python 3.10 or newer.

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install --no-deps git+https://github.com/Tang-Lab-super/PROST.git   # PROST pins very old versions, so no deps
```

Only `starmap_prost.py --seed-check` needs R with the `mclust` package (`install.packages("mclust")`).

`dlpfc_cellcharter.py` is much faster on a GPU, and the PROST scripts need a CUDA GPU (CPU and GPU floats differ, which
breaks exact reproducibility). A free Colab T4 is enough for both. Everything else runs on a CPU.

## Data

All four are the h5ad files distributed by SDMBench on figshare.

| Dataset | What | figshare file |
|---|---|---|
| DLPFC 151673 | 10x Visium, human dorsolateral prefrontal cortex, 3,611 annotated spots, 7 layers (Maynard et al. 2021) | [40016365](https://ndownloader.figshare.com/files/40016365) |
| CosMx SMI lung, global_z0 | NanoString CosMx, human lung tumour, 18,895 cells, 960 genes, 8 regions (He et al. 2022) | [40016455](https://ndownloader.figshare.com/files/40016455) |
| MERFISH Bregma -0.14 | mouse hypothalamic preoptic area, 155 genes, 8 regions (Moffitt et al. 2018) | [40038532](https://ndownloader.figshare.com/files/40038532) |
| STARmap BZ5 | mouse visual cortex, 4 layers (Wang et al. 2018) | [40038637](https://ndownloader.figshare.com/files/40038637) |

To download them into `data/`:

```
python fetch_data.py
```

## Reproducing the results

Run from this folder:

```
python dlpfc_banksy.py
python dlpfc_cellcharter.py            # add --sensitivity for the post-hoc k = 5, 7 check
python dlpfc_figure.py                 # cross-tabs and spatial figure (needs the two runs above)
python smi_banksy.py                   # add --grid for the oracle-tuned grid (slow), --check for the determinism check
python merfish_banksy.py               # add --grid for the oracle-tuned grid
python starmap_banksy.py
python merfish_prost.py                # GPU
python starmap_prost.py                # GPU; add --seed-check for kmeans vs mclust
```

Each run prints its ARI and NMI and writes:

- the niche labels: `results/<method>_<dataset>_labels.csv`
- the marker tables: `results/<Method>_<Dataset>.xlsx`, with sheets `top10_genes`, `log2FC` and `full`
- a ground truth vs niches figure in `figures/`

### Settings and expected numbers

| Dataset | Method | Settings | Tuned? | Niches | ARI | NMI |
|---|---|---|---|---|---|---|
| DLPFC | BANKSY | authors' DLPFC tutorial: λ=0.2, k_geom=6, res 0.6, published HVG list | no | 6 | 0.602 | |
| DLPFC | CellCharter | authors' `individual.py`: scVI n_latent=5, 4 neighbour layers, k=6 from AutoK stability | no | 6 | 0.430 | |
| SMI | BANKSY + Harmony | vignette res 0.6, k_geom=30, λ=0.8 | no | | printed | printed |
| SMI | BANKSY + Harmony | k_geom=30, λ=0.8, res 0.3, seed 0 | oracle | 7 | 0.248 | 0.323 |
| MERFISH | BANKSY | k_geom=30, no AGF, λ=0.8, res 0.35 | oracle | 8 | 0.530 | 0.588 |
| MERFISH | PROST | kmeans init, K=8, k_neighbors=15 | K only | 8 | 0.428 | 0.528 |
| STARmap | BANKSY | λ=0.8, k_geom=15, K=4, seed 0 (5 seeds reported) | K only | 4 | printed | printed |
| STARmap | PROST | kmeans init, K=4, k_neighbors=30, seed 0 | oracle | 4 | 0.809 | |

Two runs now set seeds that the original notebook runs did not set, so their numbers can differ slightly from the
original runs:

- DLPFC BANKSY: numpy is now seeded before BANKSY's PCA.
- The untuned SMI reference: torch is now seeded for Harmony. The original run gave ARI 0.140.

The marker tables in `results/` are the exact ones that were pasted into the LLM prompts, so the LLM results match them
even if a rerun shifts a niche slightly.

## Folder structure

```
niche_clustering/
  README.md
  requirements.txt
  common.py               paths, seeding, the Wilcoxon marker tables
  prost_common.py         PROST preprocessing and run settings
  fetch_data.py           downloads the four datasets into data/
  dlpfc_banksy.py
  dlpfc_cellcharter.py
  dlpfc_figure.py         cross-tabs + DLPFC figure
  smi_banksy.py
  merfish_banksy.py
  starmap_banksy.py
  merfish_prost.py
  starmap_prost.py
  results/                niche labels, marker tables (.xlsx), cross-tabs, grids
  figures/
```
