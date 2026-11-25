# Cell-level niche annotation and LLM label scoring

This folder holds Shreya's part of the project:

- `label_scoring/`: Exact / Partial / Miss summary of LLM answers that name clusters or regions
  (DLPFC web chats, CosMx templates).
- `cell_level/`: methods that give every cell a region without clustering.
  - LLMiniST zero-shot
  - our NicheAgent-style re-implementation
  - CardEM (M1, M2, M3)
  - shared evaluation and figures

`SCORING.md` describes how the results in this folder are scored.

## Installation

Python 3.10 or newer.

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The Gemini calls need an API key from Google AI Studio:

```
export GOOGLE_API_KEY=...
```

Every script also runs with `--offline`. In that mode it reuses the Gemini answers we saved in
`cell_level/cache/`, so no key is needed to reproduce the tables and figures.

## Data

| Dataset | What | Source |
|---|---|---|
| STARmap BZ5, BZ9, BZ14 | mouse mPFC, 166 genes, 15 cell types, 4 expert layers (BZ5: 1,049 cells) | Wang et al. 2018, as shipped in the [LLMiniST repository](https://github.com/wJDKnight/LLMiniST/tree/main/examples/starmap) |
| MERFISH Bregma -0.14 | mouse hypothalamic preoptic area, 155 genes, 5,926 cells with an expert region, 8 regions | Moffitt et al. 2018, h5ad at https://ndownloader.figshare.com/files/40038532 |
| DLPFC 151673 | human cortex, Visium | only the cluster marker lists in `prompts/` are used here |
| CosMx lung tumour | 8 expert regions | only the graded Gemini answers in `label_scoring/graded_answers/` are used here |

To download the first two into `cell_level/data/`:

```
cd cell_level
python fetch_data.py
```

## Reproducing the results

From `cell_level/`:

```
python run_llminist.py --dataset starmap --offline
python run_llminist.py --dataset merfish --offline
python run_nicheagent_style.py --dataset starmap --offline
python run_nicheagent_style.py --dataset merfish --offline
python run_cardem.py --dataset starmap --offline
python run_cardem.py --dataset merfish --offline
python evaluate.py          # bootstrap intervals, McNemar tests, grouping vs naming (about 2 min)
python make_figures.py      # report figures
```

Each run writes the per-cell labels and a score table to `cell_level/results/`. `make_figures.py`
writes `figures/fig_cardem_pipeline`, `fig_performance`, `fig_starmap` and `fig_merfish` (PDF and PNG).

Drop `--offline` to query Gemini again (model `gemini-flash-lite-latest`). Answers are added to `cache/`
as they arrive, so a run stopped by the free-tier limit can be restarted.

From `label_scoring/`:

```
python score_labels.py
```

### Expected numbers (offline)

| Dataset | Method | Accuracy | ARI | NMI |
|---|---|---|---|---|
| STARmap | LLMiniST (refined) | 0.891 | 0.840 | 0.809 |
| STARmap | NicheAgent-style (smoothed) | 0.943 | 0.854 | 0.811 |
| STARmap | M3 CardEM | 0.937 | 0.833 | 0.800 |
| MERFISH | LLMiniST (refined, 800 cells) | 0.262 | 0.112 | 0.237 |
| MERFISH | NicheAgent-style (smoothed) | 0.533 | 0.296 | 0.408 |
| MERFISH | M3 CardEM | 0.207 | 0.368 | 0.445 |

The original MERFISH CardEM run gave 0.208 / 0.377 / 0.444. The difference comes from the cache. We kept
only the average of the three card runs, not each run, so offline the card-run disagreement signal is zero.
Everything else reproduces exactly.

## Folder structure

```
code/
  README.md
  SCORING.md                 scoring rules for the results in this folder
  requirements.txt
  prompts/
    dlpfc_web_prompts.md     the three DLPFC prompt styles, BANKSY and CellCharter markers
  label_scoring/
    score_labels.py
    graded_answers/          graded answers (one row per LLM answer) and expert labels
    results/                 summary tables
  cell_level/
    common.py                data loading, neighbourhoods, Gemini wrapper, metrics
    fetch_data.py            downloads STARmap and MERFISH into data/
    run_llminist.py          LLMiniST zero-shot, one Gemini call per cell
    run_nicheagent_style.py  NicheCards from held-out tissue + Gemini + smoothing
    run_cardem.py            LLM-written cards, M1 / M2 / M3 and ablations
    evaluate.py              shared cell-level evaluation
    make_figures.py
    cache/                   saved Gemini answers (cell id -> answer, cards, rename check)
    results/                 per-cell labels and score tables
    figures/
```
