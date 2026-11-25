# Composition niches from neighbourhood cell-state fractions, with LLM niche labelling

## What we implemented

A niche here is defined by who lives next to whom. Cells are first grouped into anonymous cell states from their own expression. Each cell is then described by the fraction of its spatial neighbours that fall in each state, and cells with similar neighbourhood compositions form a niche. Plain BANKSY clustering groups cells by a blend of their own and neighbour expression, so its niches tend to follow cell type. Here the clustering input is composition only, which separates niches by cell-state mix rather than by cell identity.

The niche notebook (`m1_phase1.ipynb`) does the following, in order. Values marked "adjustable" are set in its CONFIG cell; the others are fixed in the code.

- Install cell: run it, then restart the runtime and run from the CONFIG cell.
- Load the CosMx SMI file, drop `NegPrb` probes, drop cells without a `Region` value, keep raw counts in a layer, and log-normalise (10,000 counts per cell).
- Cell states: all genes, scale (clipped at 10), PCA with 50 components (fixed), Harmony on `batch`, neighbour graph with 30 neighbours (fixed), Leiden at resolution 1.0 (`STATE_RES`, adjustable). The notebook prints the number of states and warns if it is outside 15-25 (check: the actual count on your data is not verified).
- Spatial neighbours: 30 per cell (`K_NEIGHBORS`, adjustable), computed separately per `batch`, excluding the cell itself.
- Composition: fraction of neighbours in each state, then CLR with pseudocount 0.01 (`TRANSFORM`, adjustable: "clr" or "sqrt"). Optional own-state one-hot with weight 0.5 (`SELF_WEIGHT`, adjustable, default off).
- Niche clustering: Gaussian mixture, diagonal covariance, 5 initialisations, k from 4 to 10. k is chosen without labels as the maximum of the mean of three min-max scaled scores: BIC elbow, silhouette (5,000-cell sample), and bootstrap ARI (5 subsamples of 80%). The expert `Region` column is never used for selection.
- Minimum niche size: niches below 0.5% of cells (`MIN_NICHE_FRAC`, adjustable) are merged into the niche with the nearest mixture mean. Niches are renumbered by size.
- Markers: one-vs-rest Wilcoxon on log-normalised raw counts, top 10 genes per niche and per state.
- Reporting: ARI, NMI, silhouette and per-niche majority region and purity against `Region`, after selection only. The final configuration is rerun with seeds 0, 1 and 42 (`ROBUST_SEEDS`, adjustable) at the selected k; mean and sd are stored in `metrics.json`. The main run uses `SEED` = 0 (adjustable).
- Smoke test: `SMOKE_TEST` (adjustable, default False) runs on a random subset of `SMOKE_N` = 2,000 cells (adjustable) and writes to a folder with the suffix `_smoke`.

The prompt-runner notebook (`m1_prompt_runner.ipynb`) sends the niches to a model for labelling. Niche ids are shuffled with seed 7 and shown as letters, states as S1...Sn. Four templates are used, each repeated 5 times (`N_RUNS`, adjustable) with `models/gemini-3.5-flash` (`MODEL`, adjustable), temperature 1.0 (`TEMPERATURE`, adjustable) and `maxOutputTokens` 8192. Every template requires a final fenced JSON array with region, label, confidence and justification.

- Baseline zero-shot: top 10 marker genes per anonymous region.
- Tissue context: adds a tissue sentence (`TISSUE_CONTEXT`, adjustable; default "human tumour tissue profiled with NanoString CosMx SMI, 960-gene panel"), a one-time state legend (top 5 genes per state), and each region's top 5 states as percent of its neighbourhood.
- With log2FC: adds log2FC next to each gene and fold-enrichment next to each state.
- Chain-of-thought: same content as the log2FC template, with step-by-step reasoning requested (name dominant states, infer composition, infer niche) before the JSON.

A check stops the run if any prompt contains the word "Region", "banksy", or an expert region name. `DRY_RUN` (adjustable, default True) prints the four prompts and makes no API call. Existing raw response files are skipped on rerun. A 429 response stops the run cleanly and prints the remaining calls.

## Inputs

| File name | Used by | Required or optional | What it contains | Where to place it in Colab |
|---|---|---|---|---|
| `global_z0.h5ad` | niche notebook | Required | CosMx SMI AnnData: raw counts in `X`, `obs["Region"]`, `obs["batch"]`, `obsm["spatial_global"]` | `/content/global_z0.h5ad` (`DATA_PATH`) |
| `m1_composition_outputs.zip` | prompt runner | Required, unless the four files below already exist in `IN_DIR`; if missing, the notebook opens an upload dialog (check: dialog saves to `/content/`) | Zip made by the niche notebook, files at the zip root | `/content/m1_composition_outputs.zip` (`ZIP_PATH`); unzipped into `/content/outputs/m1_composition/` (`IN_DIR`) |
| `niche_markers_long.csv` | prompt runner | Required | Top-10 genes per niche: niche, rank, gene, log2FC, score, padj | `/content/outputs/m1_composition/` (`IN_DIR`), from the zip |
| `niche_composition.csv` | prompt runner | Required | Top states per niche: niche, state, frac_in_niche, frac_global, fold_enrichment, rank | `/content/outputs/m1_composition/` (`IN_DIR`), from the zip |
| `state_markers.csv` | prompt runner | Required | Top-10 genes per state: state, rank, gene, log2FC | `/content/outputs/m1_composition/` (`IN_DIR`), from the zip |
| `niche_summary.csv` | prompt runner | Required | Per niche: niche, n_cells, and summary columns | `/content/outputs/m1_composition/` (`IN_DIR`), from the zip |
| `GEMINI_API_KEY` (Colab secret) | prompt runner | Required only when `DRY_RUN=False` | Gemini API key, read with `google.colab.userdata.get`; turn on notebook access for the secret in the Colab Secrets panel | Colab secrets panel, not a file path |

## Outputs

Niche notebook, written to `/content/outputs/m1_composition/` (`OUT_DIR`; with `SMOKE_TEST=True`, `/content/outputs/m1_composition_smoke/`):

| File name | What it contains | Used downstream by |
|---|---|---|
| `labels.csv` | Index = cell id; niche, Region, cx_g, cy_g, batch, state | Reporting and later scoring |
| `states.csv` | cell, state | Reference |
| `niche_markers_long.csv` | niche, rank, gene, log2FC, score, padj | Prompt runner |
| `niche_markers_wide.csv` | Rank by niche table of gene names | Reference |
| `niche_summary.csv` | niche, n_cells, frac_cells, majority_region, purity, mean_posterior | Prompt runner (niche ids, n_cells); reporting |
| `crosstab_vs_region.csv` | Niche by Region cell counts | Reporting and later scoring of labels |
| `niche_composition.csv` | niche, state, frac_in_niche, frac_global, fold_enrichment, rank | Prompt runner |
| `state_markers.csv` | state, rank, gene, log2FC | Prompt runner |
| `metrics.json` | n_niches, ARI, NMI, silhouette, n_states, stability, seed robustness (mean and sd), a fixed reference row for comparison, k-selection record | Reporting |
| `run_config.json` | CONFIG values, library versions, runtime | Reference |
| `niche_vs_truth.png` | Spatial scatter of expert Region next to niches | Reporting |
| `k_selection_candidates.csv` | k, bic, silhouette, stability, bic_elbow, combined | Reference |
| `k_selection_curves.png` | BIC, silhouette and stability curves over k | Reference |
| `seed_robustness.csv` | seed, n_states, n_niches, ARI, NMI | Reporting |

Prompt-runner notebook, written to `/content/outputs/m1_composition_prompts/` (`RESULTS_DIR`):

| File name | What it contains | Used downstream by |
|---|---|---|
| `results_m1_composition.csv` | method, template, run, model, model_version, niche_letter, niche_id, n_cells, label, confidence, justification, parse_ok, finish_reason, raw_file | Analysis of the labels (not included in these notebooks) |
| `niche_letter_key.csv` | niche_letter, niche_id, n_cells | Decoding letters back to niches |
| `state_legend_key.csv` | state_id, state_label (S1...Sn) | Decoding state labels |
| `run_config.json` | Model, temperature, repeats, template settings, observed model versions | Reference |
| `prompts/T1.txt` to `T4.txt` | The four full prompts as sent | Audit |
| `raw/m1_composition_T{1-4}_run{1-5}.json` | Per call: template, run, temperature, finish_reason, text, full API response | Rebuilds the results CSV; resume support |

Zip files:

- Niche notebook: `/content/m1_composition_outputs.zip` (zip of `OUT_DIR`, downloaded by the last cell). This is the zip to upload into the prompt runner. A smoke-test run writes a zip with the same name.
- Prompt runner: `/content/m1_prompt_results.zip` (zip of `RESULTS_DIR`, downloaded by the last cell).
