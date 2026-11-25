"""Send the T1-T4 prompts to Gemini through the API, 5 repeats each, and save every answer.

Two arms, both on the CosMx SMI lung slice:
  gt      markers of the 8 expert regions, blinded to A-H (oracle partition: no clustering error)
  banksy  markers of the 7 BANKSY niches, relabelled A-G

    python run_gemini.py --arm gt
    python run_gemini.py --arm banksy
    python run_gemini.py --arm gt --dry-run     # only write the prompts, no API calls

Needs GEMINI_API_KEY in the environment (Google AI Studio). The free tier allows about 20 calls a day,
so a run stops at the daily cap; run it again the next day and it skips answers that already exist.
Writes responses/<arm>/<arm>__<model>__<template>__run<k>.txt, the prompts as _prompts_<arm>.json,
and run_index.csv (finish reason and the model version the API reports for each call).
"""
import argparse
import json
import os
import pathlib
import random
import sys
import time

import pandas as pd
import requests

from common import RESULTS
from prompt_templates import TEMPLATES

TABLES = pathlib.Path(RESULTS) / "CosMX"   # gt tables from smi_oracle_markers.py, Banksy_SMI.xlsx from smi_banksy.py
RESPONSES = pathlib.Path(__file__).resolve().parent / "responses"

# We requested gemini-3.5-flash, but the API reported gemini-3.6-flash as the serving model for every
# call, so that is the model named here. 3.6 ignores sampling parameters such as temperature, so none
# are sent; variability is measured across the 5 repeats instead.
MODEL = "models/gemini-3.6-flash"
REPEATS = 5
URL = "https://generativelanguage.googleapis.com/v1/{model}:generateContent"


def load_tables(arm):
    """Top-10 marker genes and log2FC per group, columns already named A, B, ..."""
    if arm == "gt":
        top10 = pd.read_csv(TABLES / "gt_top10_blinded.csv")
        lfc = pd.read_csv(TABLES / "gt_log2fc_blinded.csv")
    else:
        # Banksy_SMI.xlsx is written by smi_banksy.py; niches 0-6 become A-G
        top10 = pd.read_excel(TABLES / "Banksy_SMI.xlsx", sheet_name="top10_genes")
        lfc = pd.read_excel(TABLES / "Banksy_SMI.xlsx", sheet_name="log2FC")
        top10.columns = [chr(65 + i) for i in range(top10.shape[1])]
        lfc.columns = top10.columns
    return top10, lfc


def build_prompts(top10, lfc):
    """Fill the templates. They are written for 8 groups (A-H); fix the count for other arms.

    Known quirk, kept so the prompts match what was actually sent: the first replace below never
    matches (CONTEXT says "8 spatially distinct regions of one tissue section, labelled A-H"), so in
    the BANKSY arm T2-T4 still say "8 ... regions, labelled A-H" above a 7-column table. Only T1's
    "Number of regions" line is corrected to 7 (A-G).
    """
    n, last = top10.shape[1], top10.columns[-1]
    prompts = {}
    for name, t in TEMPLATES.items():
        t = (t.replace("8 spatially distinct regions, labelled A-H", f"{n} spatially distinct regions, labelled A-{last}")
              .replace("**Number of regions:** 8 (A-H)", f"**Number of regions:** {n} (A-{last})"))
        prompts[name] = t.format(TABLE=top10.to_markdown(index=False), FC_TABLE=lfc.to_markdown(index=False))
    return prompts


def ask(prompt, key, model=MODEL, tries=8):
    """One call. Returns (text, finish reason, model version reported by the API).
    Retries on network errors and 500/503; exits cleanly on 429 (daily quota)."""
    for attempt in range(tries):
        try:
            r = requests.post(URL.format(model=model), headers={"x-goog-api-key": key},
                              json={"contents": [{"parts": [{"text": prompt}]}],
                                    "generationConfig": {"maxOutputTokens": 8192}},
                              timeout=300)
        except requests.RequestException as e:
            print(f"  {type(e).__name__}, retrying")
            time.sleep(10)
            continue
        if r.status_code == 429:
            sys.exit("429: daily quota reached. Run again tomorrow; finished answers are kept.")
        if r.status_code in (500, 503):
            time.sleep(2 ** attempt + random.random())
            continue
        r.raise_for_status()
        j = r.json()
        c = j["candidates"][0]
        return c["content"]["parts"][0]["text"], c.get("finishReason"), j.get("modelVersion")
    raise RuntimeError("gave up after repeated server errors")


def run_arm(arm, dry_run=False):
    out = RESPONSES / arm
    out.mkdir(parents=True, exist_ok=True)
    prompts = build_prompts(*load_tables(arm))
    blob = json.dumps(prompts, indent=1)
    assert "BANKSY" not in blob.upper()           # the method is never named in a prompt
    (out / f"_prompts_{arm}.json").write_text(blob)
    if dry_run:
        print("wrote", out / f"_prompts_{arm}.json")
        return

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("Set GEMINI_API_KEY first.")
    tag = MODEL.split("/")[-1]
    idx = out / "run_index.csv"
    records = pd.read_csv(idx).to_dict("records") if idx.exists() else []
    for tname, ptext in prompts.items():
        for rep in range(1, REPEATS + 1):
            fn = out / f"{arm}__{tag}__{tname}__run{rep}.txt"
            if fn.exists():                        # resume after the daily cap
                continue
            txt, finish, version = ask(ptext, key)
            fn.write_text(txt)
            records.append(dict(arm=arm, template=tname, run=rep, finish=finish,
                                model_version=version, chars=len(txt)))
            pd.DataFrame(records).to_csv(idx, index=False)
            print(fn.name, finish, version, len(txt))
            time.sleep(5)                          # stay under the per-minute limit
    print(len(list(out.glob("*.txt"))), "answers in", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["gt", "banksy"], required=True)
    ap.add_argument("--dry-run", action="store_true", help="write the prompts without calling the API")
    args = ap.parse_args()
    run_arm(args.arm, args.dry_run)
