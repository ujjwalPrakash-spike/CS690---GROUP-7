# Consensus niche discovery and LLM niche labelling on CosMx SMI

## What we implemented

A niche here is a group of neighbouring cells that many different spatially aware clusterings place together. A single BANKSY run depends on its seed and on the spatial weight (lambda), so its clusters can change between runs. We run several BANKSY configurations plus a scVI/CellCharter clustering, record how often each pair of neighbouring cells is grouped together, and cluster that agreement graph. Each niche also gets a stability score. The niche notebook is `m2_phase1.ipynb`. The prompt runner (`m2_prompt_runner.ipynb`) then asks an LLM to name each niche from its marker genes.

Processing steps in the niche notebook (values marked "adjustable" are in the CONFIG cell):

- Load the CosMx SMI file, drop `NegPrb` probes, keep cells with a Region label, copy `spatial_global` to `cx_g`/`cy_g`, keep raw counts in a layer, then normalise to 1e4 and log1p.
- Run 9 BANKSY base partitions: lambda in {0.2, 0.5, 0.8} (adjustable) x seeds {0, 1, 42} (adjustable); `K_GEOM`=30 (adjustable), resolution 0.3 (adjustable), 50 PCs, Harmony on `batch`, Leiden with `num_nn`=50 and `partition_seed`=1234. numpy and torch are seeded before PCA and before Harmony.
- Run CellCharter as one more base partition (`USE_CELLCHARTER`=True, adjustable): scVI on raw counts with `batch` as batch key (`n_latent`=10, up to 200 epochs with early stopping), spatial kNN k=15, 3 aggregation layers, ClusterAutoK over 3-12 clusters with max 10 runs; the best k is used. All of these are adjustable. If install or run fails, it is skipped and recorded in `run_config.json`.
- Optionally add an earlier composition-based niche labelling as a further partition (`USE_M1_PARTITION`=False, adjustable).
- Save each partition to `base_partitions.csv` right after it finishes; saved partitions are skipped on rerun.
- Build a sparse co-association graph on a per-batch spatial kNN graph with k=50 (adjustable). Edge weight is the fraction of base partitions that put both cells in the same cluster.
- Run weighted Leiden (RBConfiguration partition, 10 iterations, seed 0). Resolutions 0.1 to 1.0 in steps of 0.1 are candidates (adjustable). For each, 10 bootstrap subsamples of 80% of cells (both adjustable) are reclustered and pairwise ARI on overlaps is averaged.
- Select the resolution without using Region labels: highest mean bootstrap ARI among resolutions giving 4 to 12 niches (adjustable), counting only clusters of at least 0.5% of cells (adjustable). If none qualifies, the closest to that range is used and the fallback is recorded.
- Merge niches below 0.5% of cells into their most strongly connected neighbour niche. Niches are renamed "0", "1", ... by size.
- Compute per-cell stability (mean co-association weight to same-niche neighbours), per-niche mean and minimum stability, and bootstrap Jaccard.
- Compute top-10 one-vs-rest Wilcoxon markers per niche from log-normalised raw counts.
- Report ARI, NMI and majority-region purity against the expert Region labels, per-partition ARI, silhouette (50-PC expression PCA, 5000 cells) and Leiden seed agreement (2 extra seeds). These are reported only and are not used for selection.
- `SMOKE_TEST`=True (adjustable) uses a random 2,000-cell subset and 3 base partitions, and writes to a folder ending in `_smoke`.
- `SEED`=0 is adjustable; `BANKSY_PCS`=50, `BANKSY_NUM_NN`=50 and `TOP_N_MARKERS`=10 are fixed in CONFIG.

Prompt runner: niches are shuffled with seed 7 and shown as anonymous letters (A, B, ...). Region names and "BANKSY" are checked for and blocked from every prompt. There are four templates. Baseline zero-shot gives the top-10 genes per region only. Tissue context adds a tissue sentence (`TISSUE_CONTEXT`, adjustable, wording unconfirmed (check)), each region's cell count and percentage, and its stability score described as agreement across N clustering runs (N read from `base_partitions.csv`). With log2FC adds log2FC for each gene. Chain-of-thought uses the same content as with log2FC and asks for cell types, evidence and then one label before the answer. Every template must end with a fenced JSON array (region, label, confidence, justification). Each template is run 5 times (adjustable) on `models/gemini-3.5-flash` (adjustable; availability (check)) at temperature 1.0 (adjustable) with a 8192-token output limit.

## Inputs

| File name | Used by | Required or optional | What it contains | Where to place it in Colab (path and CONFIG variable) |
|---|---|---|---|---|
| `global_z0.h5ad` | niche notebook | Required | CosMx SMI AnnData; the code needs `obs["Region"]`, `obs["batch"]`, `obsm["spatial_global"]`; counts in `X` are assumed raw (check) | `/content/global_z0.h5ad` (`DATA_PATH`) |
| `labels.csv` from an earlier composition-based niche run | niche notebook | Optional, read only if `USE_M1_PARTITION`=True | Cell ids as index, column `niche` | `/content/outputs/m1_composition/labels.csv` (`M1_PATH`) |
| `base_partitions.csv` | niche notebook (resume) | Optional | Cell x run partition labels from an earlier run; must match the current cells | `/content/outputs/m2_consensus/base_partitions.csv` (`OUT_DIR`) |
| `niche_markers_long.csv` | prompt runner | Required | niche, rank, gene, log2FC, score, padj | `/content/outputs/m2_consensus/` (`IN_DIR`) |
| `niche_summary.csv` | prompt runner | Required | niche, n_cells, frac_cells, majority_region, purity, mean_stability | `/content/outputs/m2_consensus/` (`IN_DIR`) |
| `niche_stability.csv` | prompt runner | Required | niche, n_cells, mean_stability, min_stability, bootstrap_jaccard | `/content/outputs/m2_consensus/` (`IN_DIR`) |
| `base_partitions.csv` | prompt runner | Required | Header only is read, to count the base partitions | `/content/outputs/m2_consensus/` (`IN_DIR`) |
| `crosstab_vs_region.csv` | prompt runner | Required | Header only is read, to get expert region names for the prompt check | `/content/outputs/m2_consensus/` (`IN_DIR`) |
| `m2_consensus.zip` | prompt runner | Alternative to the five files above | Zip of the niche notebook output; extracted into `IN_DIR`. If `ZIP_PATH` is empty and the files are missing, an upload prompt opens | Any path; set `ZIP_PATH` (default empty) or upload when prompted |
| Colab secret `GEMINI_API_KEY` | prompt runner | Required only when `DRY_RUN`=False | Gemini API key; turn "Notebook access" on | Colab Secrets panel |

Runtime notes: the niche notebook is meant for a Colab GPU runtime. Restart the runtime after its install cell, then run from the CONFIG cell. The prompt runner needs no install and no restart; CPU is enough. `DRY_RUN` is True by default and prints the four prompts without calling the API.

## Outputs

Niche notebook, written to `/content/outputs/m2_consensus/` (`OUT_DIR`; a `_smoke` suffix is added when `SMOKE_TEST`=True):

| File name | What it contains (key columns) | Used downstream by |
|---|---|---|
| `labels.csv` | Cell id index; niche, Region, cx_g, cy_g, batch, cell_stability | Reporting |
| `niche_markers_long.csv` | niche, rank, gene, log2FC, score, padj (top 10 per niche) | Prompt runner |
| `niche_markers_wide.csv` | Rank x niche table of gene names | Reporting |
| `niche_summary.csv` | niche, n_cells, frac_cells, majority_region, purity, mean_stability | Prompt runner |
| `niche_stability.csv` | niche, n_cells, mean_stability, min_stability, bootstrap_jaccard | Prompt runner |
| `crosstab_vs_region.csv` | Niche x expert Region cell counts | Prompt runner (header only) |
| `base_partitions.csv` | Cell x run labels; columns `banksy_lam<lambda>_seed<seed>`, `cellcharter_autok`, optionally `m1_composition` | Prompt runner (column count); resume |
| `resolution_curve.csv` | resolution, n_clusters_raw, n_niches, mean_boot_ari, eligible, selected | Reporting |
| `resolution_curve.png` | Plot of the resolution curve | Reporting |
| `metrics.json` | n_niches, ARI, NMI, silhouette, per-niche purity, stability, selection record, per-partition ARI/NMI, merge log, fixed reference values | Reporting |
| `run_config.json` | CONFIG values, seed, library versions, partition names, runtime, GPU flag, CellCharter status, notes | Reporting |
| `niche_vs_truth.png` | Side-by-side spatial plot of expert Region and niches | Reporting |

Prompt runner, written to `/content/outputs/m2_consensus_llm/` (`RUN_DIR`):

| File name | What it contains (key columns) | Used downstream by |
|---|---|---|
| `results_m2_consensus.csv` | method, template, run, model, model_version, niche_letter, niche_id, n_cells, label, confidence, justification, parse_ok, finish_reason, raw_file | Label scoring (not part of these notebooks) |
| `niche_letter_key.csv` | niche_letter, niche_id, n_cells | Decoding letters in results |
| `prompt_T1.txt` to `prompt_T4.txt` | The exact prompt text sent for each template | Audit |
| `raw/<template>_run<N>.json` | template, run, model, model_version, temperature, finish_reason, text, usage; existing files are skipped on rerun | `results_m2_consensus.csv`; resume |
| `run_config.json` | CONFIG values, input folder used, partition count, model versions, letter-to-niche map, prompt hashes, parse rate per template | Reporting |

A dry run writes only `niche_letter_key.csv` and the prompt files. `results_m2_consensus.csv` and `run_config.json` are written only when `DRY_RUN`=False.

Zip files:

- Niche notebook: `/content/outputs/m2_consensus.zip` (`/content/outputs/m2_consensus_smoke.zip` for a smoke test). It is downloaded by the last cell. This is the file to upload into the prompt runner (the smoke zip is only for testing).
- Prompt runner: `/content/outputs/m2_consensus_llm.zip`, downloaded by its last cell.
