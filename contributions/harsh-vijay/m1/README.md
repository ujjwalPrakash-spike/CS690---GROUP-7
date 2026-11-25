# M1: Composition niches from neighbourhood cell-state fractions, with LLM niche labelling

How to run the .ipynb files:

## 1. Phase 1: `m1_phase1.ipynb`

**Files to upload**
- `global_z0.h5ad`: required. If missing, the load cell fails with FileNotFoundError and nothing runs.
- The h5ad must have `obs["Region"]`, `obs["batch"]` and `obsm["spatial_global"]`. If any is missing, the load cell fails with KeyError.

**Target location**
- `/content/global_z0.h5ad`, set by `DATA_PATH`.
- `OUT_DIR` is `/content/outputs/m1_composition`. The notebook creates it.

**Folder tree before Run all**
```
/content/
└── global_z0.h5ad
```

**Secrets and settings**
- Colab secrets: none.
- Runtime: CPU is enough. The code never requests a GPU (check).
- Restart the runtime after cell 1 (the pip install), then run from cell 2.

**What it produces**
- Folder: `/content/outputs/m1_composition/`
- Files:
  - `labels.csv`, `states.csv`
  - `niche_markers_long.csv`, `niche_markers_wide.csv`
  - `niche_summary.csv`, `crosstab_vs_region.csv`
  - `niche_composition.csv`, `state_markers.csv`
  - `metrics.json`, `run_config.json`
  - `niche_vs_truth.png`
  - `k_selection_candidates.csv`, `k_selection_curves.png`
  - `seed_robustness.csv`
- Zip to download: `/content/m1_composition_outputs.zip` (the last cell downloads it automatically).
- With `SMOKE_TEST=True`, outputs go to `/content/outputs/m1_composition_smoke/`. The zip name is the same, so a smoke zip overwrites a real one.

## 2. Prompt runner: `m1_prompt_runner.ipynb`

**Files to upload**
- `m1_composition_outputs.zip` (from phase 1): required unless the folder below already holds the four files. If both are missing, the notebook opens an upload prompt (saves to `/content/`, check).
- The four files the runner reads from the zip:
  - `niche_markers_long.csv`
  - `niche_composition.csv`
  - `state_markers.csv`
  - `niche_summary.csv`
  If any is missing, the load cell fails when reading it.
- The zip must have those files at its root. The phase-1 zip does. A hand-made zip with a subfolder will fail (check).

**Target location**
- `/content/m1_composition_outputs.zip`, set by `ZIP_PATH`.
- It is unzipped into `/content/outputs/m1_composition/`, set by `IN_DIR`.
- `RESULTS_DIR` is `/content/outputs/m1_composition_prompts`. The notebook creates it.

**Folder tree before Run all** (new session)
```
/content/
└── m1_composition_outputs.zip
```
Same session as phase 1: nothing to upload, because `/content/outputs/m1_composition/` already exists.

**Secrets and settings**
- Colab secret `GEMINI_API_KEY`, with "Notebook access" ON. It is read only when `DRY_RUN=False`, so a dry run needs no secret.
- Runtime: CPU. No install cell, no restart.

**What it produces**
- Folder: `/content/outputs/m1_composition_prompts/`
- Files:
  - `results_m1_composition.csv`
  - `niche_letter_key.csv`, `state_legend_key.csv`, `run_config.json`
  - `prompts/T1.txt` to `T4.txt`
  - `raw/m1_composition_T{1-4}_run{1-5}.json`
- Zip to download: `/content/m1_prompt_results.zip` (the last cell downloads it automatically).

## 3. Handoff

- **Same session:** upload nothing.
- **New session:** upload `m1_composition_outputs.zip` to `/content/`. The notebook unzips it into `IN_DIR` on its own.
- **Unzipped folder instead:** put the four files directly in `/content/outputs/m1_composition/` and skip the zip.
- Only the four files listed above are read; the rest of the phase-1 outputs are ignored.
