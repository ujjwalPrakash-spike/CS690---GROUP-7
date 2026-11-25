# M3: Identity and program evidence for labelling spatial niches on CosMx SMI

How to run the .ipynb files:

## Phase-1: `m3_phase1.ipynb`

**1. Files to upload**
- `global_z0.h5ad`: required. If it is missing, `load_smi` fails in the load cell.
- `banksy_smi_labels.csv`: optional. It needs the cell id as the first column and a column named `banksy`. If it is missing, BANKSY is recomputed with k_geom=30, λ=0.8, res=0.3, seed=0, which is slower and needs the Banksy_py install. If the ids don't match the h5ad cell ids, an assert stops the run (check).

**2. Target location in Colab**
- `/content/global_z0.h5ad`, set by `DATA_PATH`.
- `/content/banksy_smi_labels.csv`, set by `BASELINE_LABELS_PATH`.
- Outputs go to `/content/outputs/m3_identity_program`, set by `OUT_DIR`.

**3. Folder tree before Run all**
```
/content/
├── global_z0.h5ad
└── banksy_smi_labels.csv      (optional)
```

**4. Secrets and settings**
- Secrets: none.
- Runtime: GPU (T4 is enough). The spec says GPU is available; CPU should also work (check).
- Run cell 1 (pip install), then Runtime → Restart session, then run from the CONFIG cell onward. The restart is needed for `pandas>=2.3`.
- Leave `SMOKE_TEST=False` for the full run.

**5. What it produces**
- Folder: `/content/outputs/m3_identity_program/`.
- §5 files: `labels.csv`, `niche_markers_long.csv`, `niche_markers_wide.csv`, `niche_summary.csv`, `crosstab_vs_region.csv`, `metrics.json`, `run_config.json`, `niche_vs_truth.png`.
- Method 3 files: `identity_markers.csv`, `program_markers.csv`, `niche_LR.csv`.
- Extras: `ubiquity_filter.csv`, `state_resolution_curve.csv`, `state_identity_top20.csv`, `program_diagnostics.csv`, `identity_bootstrap.csv`.
- Download: `/content/m3_identity_program.zip`. The last cell downloads it automatically.

**6. Handoff**
- Use the whole `m3_identity_program.zip`.
- The runner only needs four files from it: `identity_markers.csv`, `program_markers.csv`, `niche_LR.csv` and `niche_summary.csv`.
- `labels.csv` is optional there (see the runner's section 1).

## Prompt runner: `m3_prompt_runner.ipynb`

**1. Files to upload**
- `m3_identity_program.zip` (the phase-1 zip): required unless the phase-1 folder is already in the same session. If the files are missing and the zip isn't at `ZIP_PATH`, the notebook opens an upload dialog. If you cancel it, it fails.
- Inside the zip, these four files are required:
  - `identity_markers.csv`
  - `program_markers.csv`
  - `niche_LR.csv`
  - `niche_summary.csv`
- `labels.csv` is optional. It is only used to add the actual Region names to the leakage assert, and it is skipped if absent.

**2. Target location in Colab**
- The zip goes at `/content/m3_identity_program.zip`, set by `ZIP_PATH`. It is extracted into `/content/outputs/m3_identity_program/`, set by `IN_DIR`.
- Outputs go to `/content/outputs/m3_prompt_runner/`, set by `RUN_DIR`.

**3. Folder tree before Run all**

Fresh session:
```
/content/
└── m3_identity_program.zip
```
Same session as phase-1 (nothing to upload):
```
/content/
└── outputs/
    └── m3_identity_program/
        ├── identity_markers.csv
        ├── program_markers.csv
        ├── niche_LR.csv
        ├── niche_summary.csv
        └── (other phase-1 files)
```

**4. Secrets and settings**
- Secret: `GEMINI_API_KEY`, with the "Notebook access" toggle ON. It is only read when `DRY_RUN=False`.
- Runtime: CPU is enough.
- No restart step.
- `DRY_RUN=True` is the default, so the first run only prints the 4 prompts and writes `prompts/T1.txt`–`T4.txt`. Set it to `False` for the real run.

**5. What it produces**
- Folder: `/content/outputs/m3_prompt_runner/`.
- Files: `results_m3_identity_program.csv`, `niche_letter_key.csv`, `run_config.json`, `raw/` (one JSON per template and run) and `prompts/`.
- Download: `/content/m3_prompt_runner_results.zip`. The last cell downloads it, and it is skipped if no results exist yet.

**6. Handoff**
- Two ways, same result:
  - **Same session:** upload nothing; the folder is already at `IN_DIR`.
  - **New session:** upload `m3_identity_program.zip` to `/content/` (drag into the Files panel) before Run all. It is extracted into `IN_DIR` automatically, and a zip with a top-level subfolder is handled too.
- Restarting the session keeps `/content`. "Disconnect and delete runtime" wipes it, so re-upload the zip after that.
