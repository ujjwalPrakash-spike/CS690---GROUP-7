# Niche detection, marker genes and LLM naming through the Gemini API

This folder holds Rahul's part of the project:

1. **Niche detection.** Spatial niches from three existing methods (BANKSY, CellCharter, PROST) on four datasets.
2. **Marker genes.** The top-10 Wilcoxon marker genes per niche: the tables that go into the LLM prompts. Also the
   niche vs expert-region cross-tabs used to build the scoring key.
3. **LLM naming through the API.** Gemini names the CosMx SMI niches, and also the ground-truth regions themselves
   (an oracle partition), from markers alone. The chat-interface runs were done by other team members and live in
   their folders.

Expert region labels (`obs['Region']`) are never used for clustering. They are used to report ARI and NMI, to build the
scoring key, and to make the oracle partition. Runs where the number of niches or another setting was chosen by looking
at ARI are marked **oracle-tuned** below and in the report.

## Installation

Python 3.10 or newer.

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install --no-deps git+https://github.com/Tang-Lab-super/PROST.git   # PROST pins very old versions, so no deps
export GEMINI_API_KEY=...                                               # only for new LLM calls (Google AI Studio)
```

Only `starmap_prost.py --seed-check` needs R with the `mclust` package (`install.packages("mclust")`).

`dlpfc_cellcharter.py` is much faster on a GPU, and the PROST scripts need a CUDA GPU (CPU and GPU floats differ,
which breaks exact reproducibility). A free Colab T4 is enough for both. Everything else runs on a CPU.

## Data

All four datasets are the h5ad files distributed by SDMBench on figshare.

| Dataset | What | figshare file |
|---|---|---|
| DLPFC 151673 | 10x Visium, human dorsolateral prefrontal cortex, 3,611 annotated spots, 7 layers (Maynard et al. 2021) | [40016365](https://ndownloader.figshare.com/files/40016365) |
| CosMx SMI lung, global_z0 | NanoString CosMx, human lung tumour, 18,895 cells, 960 genes, 8 regions (He et al. 2022) | [40016455](https://ndownloader.figshare.com/files/40016455) |
| MERFISH Bregma -0.14 | mouse hypothalamic preoptic area, 155 genes, 8 regions (Moffitt et al. 2018) | [40038532](https://ndownloader.figshare.com/files/40038532) |
| STARmap BZ5 | mouse mPFC, 4 layers (Wang et al. 2018) | [40038637](https://ndownloader.figshare.com/files/40038637) |

To download them into `data/`:

```
python fetch_data.py
```

## Reproducing the results

Run everything from this folder.

### 1. Niches and marker genes

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

Each run prints its ARI and NMI and writes three things:

- the niche labels: `<method>_<dataset>_labels.csv`
- the marker tables: `<Method>_<Dataset>.xlsx`, with sheets `top10_genes`, `log2FC` and `full`. For DLPFC, the tables
  are `top10_niche_banksy.csv` and `top10_niche_cellcharter.csv`.
- a ground truth vs niches figure

All of these go into `results/<dataset>/`, where the dataset folder is `Visium`, `CosMX`, `MERFISH` or `STARMAP`.

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

The marker tables in `results/` are the exact ones that were pasted into the LLM prompts, so the LLM results match
them even if a rerun shifts a niche slightly.

### 2. LLM naming through the Gemini API (CosMx SMI)

There are two arms on the same slice:

| Arm | Groups sent to the LLM | Labels | Why |
|---|---|---|---|
| `gt` (oracle partition) | the 8 expert regions themselves | A-H, shuffled with seed 7 | no clustering error, so this is the ceiling for naming from markers alone |
| `banksy` | the 7 BANKSY + Harmony niches from `smi_banksy.py` | A-G | the realistic case: niches come from a clustering method |

The prompts never name the dataset's regions or the clustering method. Each arm sends four templates, each 5 times:

- T1: baseline
- T2: + tissue context
- T3: + "a niche, not a cell type"
- T4: + log2 fold-changes

That makes 20 calls per arm.

To run it (the BANKSY arm needs `results/CosMX/Banksy_SMI.xlsx` from `smi_banksy.py`):

```
python smi_oracle_markers.py                 # blinded ground-truth marker tables + answer key -> results/CosMX/gt_*.csv
python run_gemini.py --arm gt
python run_gemini.py --arm banksy
python run_gemini.py --arm gt --dry-run      # writes the prompts only, no key needed
```

The free tier allows about 20 calls a day, so each arm takes one day. When the daily quota is hit, the script stops
cleanly. Run it again the next day: answers already in `responses/` are skipped.

The answers we scored are saved in `responses/`, so the analysis can be checked without a key. LLM answers are not
deterministic, so a new run will not reproduce them word for word. Scoring against the pre-registered key is done
separately and is not part of this folder.

**Model.** We requested `gemini-3.5-flash` at temperature 0, but the API reported **`gemini-3.6-flash`** as the
serving model for every call. The code therefore names 3.6. Gemini 3.6 ignores sampling parameters such as
temperature, so none are sent. Variability is measured across the 5 repeats instead. Both arms were served by the same
model, so the comparison holds. `run_index.csv` records the model version the API reported for each call.

**Known issues:**

- **Region-count line in the BANKSY prompts.** In T2–T4 of the BANKSY arm, the tissue-context line still says "8
  spatially distinct regions, labelled A-H", although the table has 7 columns (A-G). The code that should have changed
  that line never matched it. `run_gemini.py` keeps this behaviour, so it reproduces the prompts that were actually
  sent. T1 states the count correctly.
- **One missing answer.** The BANKSY arm has 19 of 20 answers: `T4 run5` was cut off by the daily quota.

## Folder structure

```
Rahul_code/
  README.md
  requirements.txt
  fetch_data.py                   downloads the four datasets into data/
  common.py                       paths, seeding, the Wilcoxon marker tables
  prost_common.py                 PROST preprocessing and run settings
  dlpfc_banksy.py
  dlpfc_cellcharter.py
  dlpfc_figure.py                 cross-tabs + DLPFC figure
  smi_banksy.py
  merfish_banksy.py
  starmap_banksy.py
  merfish_prost.py
  starmap_prost.py
  smi_oracle_markers.py           oracle partition: blinded ground-truth region markers + answer key
  run_gemini.py                   prompts + Gemini API calls (resumable)
  prompt_templates.py             templates T1-T4
  results/
    Visium/                       DLPFC labels, top-10 marker CSVs, cross-tabs, figure
    CosMX/                        SMI labels, Banksy_SMI.xlsx, purity, grid, gt_*.csv, figure
    MERFISH/                      BANKSY + PROST labels, marker .xlsx, figures
    STARMAP/                      BANKSY + PROST labels, marker .xlsx, figures
```
