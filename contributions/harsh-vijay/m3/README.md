# Identity and program evidence for labelling spatial niches on CosMx SMI

## What we implemented

A niche here is a fixed group of cells taken from an existing BANKSY clustering (7 niches). The clustering is not changed. What changes is the evidence used to describe each niche. Plain BANKSY expression clustering describes a niche with its top one-vs-rest marker genes, which tend to be dominated by genes expressed almost everywhere. This approach splits the evidence in three: identity genes (what the cells are, with ubiquitous genes removed), program genes (what the niche is doing, tested within matched cell states so cell-type differences do not dominate), and ligand-receptor pairs (signals the niche receives from neighbouring niches).

The niche notebook (`m3_phase1.ipynb`) runs these steps in order. Values marked (adjustable) are set in its CONFIG cell. Unmarked values are fixed in the notebook.

- Load the SMI data, drop `NegPrb` probes, keep cells with an expert `Region`, store raw counts, normalise to 10,000 counts per cell and apply log1p. Seed 0 (adjustable).
- Load niche labels from the `banksy` column of `banksy_smi_labels.csv`. If the file is absent, recompute BANKSY with k_geom 30, lambda 0.8, 50 PCs, Harmony on `batch`, Leiden resolution 0.3, num_nn 50 and partition seed 1234. Either way, stop unless there are exactly 7 niches.
- Standard markers: one-vs-rest Wilcoxon on log-normalised counts, top 10 per niche (adjustable).
- Identity markers: drop genes expressed in at least 60% of cells in every niche (adjustable), then re-rank and keep the top 10 per niche with `pct_in` and `pct_out`.
- Cell states: log-normalised expression, scaled with max value 10 (adjustable), PCA with 50 components (adjustable), Harmony on `batch`, kNN with 30 neighbours (adjustable), Leiden. The resolution is picked from 0.5, 0.75, 1.0, 1.5, 2.0 (adjustable) as the one whose state count is closest to 20 within 15 to 25 (adjustable). Expert labels are not used.
- Program markers: exclude the top 20 identity genes of every state (adjustable). For each niche and each state with at least 50 cells inside and 50 outside the niche (adjustable), run Wilcoxon niche versus rest within the state. Combine states per gene with a weighted Stouffer z (weight is the square root of the smaller cell count). Keep the top 10 positive genes. If a FOV or sample column with at least 6 units exists (adjustable), the test runs on pseudobulks of at least 10 cells (adjustable) with at least 3 per side (adjustable). Otherwise it runs on cells, which is anti-conservative, and this is recorded.
- Ligand-receptor evidence: OmniPath pairs where both genes are single-gene entries in the panel. `squidpy.gr.ligrec` with 1000 permutations (adjustable), threshold 0.1 (adjustable), Benjamini-Hochberg correction and p < 0.05 (adjustable). The top 5 pairs per receiving niche are kept (adjustable). A timeout of 1800 s (adjustable) or any ligrec error switches to a neighbour-based score (kNN with 30 neighbours, genes expressed in at least 10% of cells; both adjustable), which leaves `pval` empty.
- Stability: 5 bootstrap subsamples of 80% of cells (both adjustable). Each niche gets the mean Jaccard overlap of its identity top 10 with the full-data list.
- Reporting: ARI, NMI, purity and majority region against the expert `Region`, plus silhouette on the expression PCs. These are reported only. Nothing is selected with them.
- `SMOKE_TEST` (default False, adjustable) runs everything on a random subset of `SMOKE_N` = 2000 cells (adjustable) with reduced thresholds.

The prompt runner (`m3_prompt_runner.ipynb`) anonymises niches as letters, shuffled with seed 7, and builds four prompt templates. The baseline zero-shot template gives only the identity top-10 genes. The tissue-context template adds one tissue-context line (adjustable, default "human tumour tissue profiled with NanoString CosMx SMI, 960-gene panel") and the program top-10 genes. The log2FC template adds log2FC values for identity and program genes and the ligand-receptor pairs (top 5 per niche, with the sender niche as a letter and the score). The chain-of-thought template has the same content and asks for step-by-step reasoning first: identity genes to cell types, program genes and pairs to functional state, then the niche label. Every template ends with a fenced JSON array of `region`, `label`, `confidence`, `justification`. Each template is run 5 times (adjustable) on `models/gemini-3.5-flash` (adjustable) at temperature 1.0 (adjustable) with 8192 max output tokens. `DRY_RUN` defaults to True, which only prints and saves the prompts. Before any prompt is saved, it is checked for the word `Region`, `BANKSY` and any expert region name.

## Inputs

| File | Used by | Required or optional | Contents | Where to place it |
|---|---|---|---|---|
| `global_z0.h5ad` | niche notebook | required | CosMx SMI AnnData with `obs["Region"]`, `obs["batch"]`, `obsm["spatial_global"]`; raw counts in `X` (check) | `/content/global_z0.h5ad`, set by `DATA_PATH` |
| `banksy_smi_labels.csv` | niche notebook | optional; if absent BANKSY is recomputed | cell id as first column, a `banksy` column with niche labels; ids must match the h5ad cell ids (check) | `/content/banksy_smi_labels.csv`, set by `BASELINE_LABELS_PATH` |
| `m3_identity_program.zip` | prompt runner | required unless the niche output folder is already in the session | the zip written by the niche notebook | `/content/m3_identity_program.zip`, set by `ZIP_PATH`; extracted to `/content/outputs/m3_identity_program`, set by `IN_DIR`. If neither exists, the notebook opens an upload dialog |
| `identity_markers.csv`, `program_markers.csv`, `niche_LR.csv`, `niche_summary.csv` | prompt runner | required | niche notebook outputs, columns listed under Outputs | inside `IN_DIR` (from the zip) |
| `labels.csv` | prompt runner | optional | only the `Region` column is read, to add real region names to the leakage check | inside `IN_DIR` (from the zip) |
| `GEMINI_API_KEY` | prompt runner | required when `DRY_RUN` is False | Colab secret with "Notebook access" turned on | Colab Secrets panel |

The niche notebook downloads ligand-receptor pairs from OmniPath at run time and needs internet access (check). It installs its packages in its first cell and needs a runtime restart afterwards. Neither notebook has been run end to end on the full data or the live API (check).

## Outputs

Niche notebook, written to `/content/outputs/m3_identity_program/` (`OUT_DIR`):

| File | Contents | Used downstream by |
|---|---|---|
| `labels.csv` | `cell_id` index; `niche`, `Region`, `cx_g`, `cy_g`, `batch`, `state` | prompt runner (optional, region names for the leakage check); reporting |
| `niche_markers_long.csv` | `niche`, `rank`, `gene`, `log2FC`, `score`, `padj`; standard top 10 per niche | comparison with identity markers; not read by the prompt runner |
| `niche_markers_wide.csv` | rank by niche table of the standard top-10 gene names | reference |
| `niche_summary.csv` | `niche`, `n_cells`, `frac_cells`, `majority_region`, `purity`, `stability` | prompt runner (`n_cells`); reporting |
| `crosstab_vs_region.csv` | niche by expert `Region` cell counts | reporting; mapping niches to regions when scoring labels |
| `metrics.json` | `n_niches`, `ARI`, `NMI`, silhouette, stability, state-resolution candidates, ubiquity filter counts, program diagnostics, ligand-receptor status | reporting |
| `run_config.json` | all CONFIG values, smoke-adjusted values, label source, DE unit and column, package versions, runtime | record |
| `niche_vs_truth.png` | side-by-side spatial scatter, expert region and niche | reporting |
| `identity_markers.csv` | `niche`, `rank`, `gene`, `log2FC`, `score`, `padj`, `pct_in`, `pct_out` | prompt runner |
| `program_markers.csv` | `niche`, `rank`, `gene`, `z`, `padj`, `log2FC`, `n_states` | prompt runner |
| `niche_LR.csv` | `niche` (receiver), `ligand`, `receptor`, `source_niche`, `mean_score`, `pval` | prompt runner |
| `ubiquity_filter.csv` | `niche`, `n_ubiquitous_genes_total`, `n_removed_from_top_list`, `removed_genes` | reporting |
| `state_resolution_curve.csv` | `resolution`, `n_states` | record |
| `state_identity_top20.csv` | `state`, `rank`, `gene`, `log2FC`, `score`, `padj` | record |
| `program_diagnostics.csv` | `niche`, `n_states_used`, `de_unit` | record |
| `identity_bootstrap.csv` | `niche`, `boot`, `jaccard` | record |

Prompt runner, written to `/content/outputs/m3_prompt_runner/` (`RUN_DIR`):

| File | Contents | Used downstream by |
|---|---|---|
| `results_m3_identity_program.csv` | `method`, `template`, `run`, `model`, `model_version`, `niche_letter`, `niche_id`, `n_cells`, `label`, `confidence`, `justification`, `parse_ok`, `finish_reason`, `raw_file` | scoring of labels against expert regions, done outside these notebooks (check) |
| `niche_letter_key.csv` | `niche_letter`, `niche_id` | decoding letters back to niches |
| `run_config.json` | all CONFIG values, endpoint, model versions observed, temperature, stop reason, pending calls | record |
| `raw/<template>_run<n>.json` | response text, finish reason, model version, usage | results table; a call is skipped when its file exists |
| `prompts/<template>.txt` | full prompt text for each template | audit |

Zip files:

- Niche notebook: `/content/m3_identity_program.zip`, the contents of `OUT_DIR` at the zip root. This is the file uploaded into the prompt runner.
- Prompt runner: `/content/m3_prompt_runner_results.zip`, the contents of `RUN_DIR`. It is created only if the results CSV exists.
