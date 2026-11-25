# Shreya Astha (240997): code for CS690 Group 3, "Can LLMs Name a Niche?"

What is in this zip:

| Folder | What it does |
|---|---|
| `code/label_scoring/` | Exact / Partial / Miss scoring of LLM answers that name a niche: ChatGPT vs Claude on DLPFC, and Rahul's Gemini CosMx prompts |
| `code/cell_level/` | Methods that label every cell without clustering: LLMiniST, NicheAgent-style and CardEM (our method), plus evaluation and figures |
| `code/prompts/` | The three DLPFC prompts and the BANKSY / CellCharter marker lists |
| `code/SCORING.md` | How the answers and cells are scored |

## Quick start (no API key needed)

```
cd code
pip install -r requirements.txt
cd cell_level
python fetch_data.py                      # downloads STARmap and MERFISH into data/
python run_cardem.py --dataset starmap --offline
python run_llminist.py --dataset starmap --offline
python run_nicheagent_style.py --dataset starmap --offline
python evaluate.py
python make_figures.py
cd ../label_scoring
python score_labels.py
```

`--offline` reuses the saved Gemini answers in `cell_level/cache/`, so every table and figure reproduces
without a key. Expected STARmap accuracy: CardEM 0.937, NicheAgent-style 0.943, LLMiniST 0.891.

Full instructions (all datasets, expected numbers, live Gemini runs, folder layout): `code/README.md`.
