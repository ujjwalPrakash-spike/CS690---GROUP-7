"""Shared pieces for the cell-level runs: data loading, neighbourhoods, Gemini calls and scoring."""
import json
import os
import re
import time

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial import cKDTree
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(HERE, "cache")
RESULTS = os.path.join(HERE, "results")
MODEL = "gemini-flash-lite-latest"

LAYER = {1: "Layer 1", 2: "Layer 2/3", 3: "Layer 5", 4: "Layer 6"}
# readable names for the STARmap cell types, used in every prompt
STARMAP_TYPES = {
    "Astro": "astrocytes", "Endo": "endothelial cells", "L5-1": "L5 pyramidal neurons (L5-1)",
    "Lhx6": "Lhx6 interneurons", "NPY": "NPY interneurons", "Oligo": "oligodendrocytes",
    "Reln": "Reln cells", "SST": "SST interneurons", "Smc": "smooth muscle cells", "VIP": "VIP interneurons",
    "eL2/3": "excitatory L2/3 neurons", "eL5-2": "excitatory L5 neurons (eL5-2)",
    "eL5-3": "excitatory L5 neurons (eL5-3)", "eL6-1": "excitatory L6 neurons (eL6-1)",
    "eL6-2": "excitatory L6 neurons (eL6-2)",
}
MERFISH_REGIONS = ("BST = bed nucleus of the stria terminalis, MPA = medial preoptic area, "
                   "MPN = medial preoptic nucleus, PV = periventricular region, "
                   "PVH = paraventricular hypothalamic nucleus, PVT = paraventricular thalamic nucleus, "
                   "V3 = third ventricle, fx = fornix (fiber tract)")


class Section:
    """One tissue section: cell types, positions, expert regions and (optionally) expression."""

    def __init__(self, name, cell_type, xy, truth, expr=None, radius=100):
        self.name = name
        self.cell_type = cell_type
        self.xy = xy
        self.truth = truth
        self.expr = expr
        self.radius = radius
        self.cells = cell_type.index
        self.types = sorted(cell_type.unique())
        self.neighbours = cKDTree(xy).query_ball_point(xy, r=radius)  # includes the cell itself
        onehot = pd.get_dummies(cell_type).reindex(columns=self.types, fill_value=0).astype(float)
        self.comp = pd.DataFrame(np.vstack([onehot.values[n].mean(0) for n in self.neighbours]),
                                 index=self.cells, columns=self.types)

    def __len__(self):
        return len(self.cells)

    def describe(self, i, min_frac=0.05):
        row = self.comp.iloc[i].sort_values(ascending=False)
        return ", ".join(f"{t} {v:.0%}" for t, v in row.items() if v >= min_frac)

    def graph(self, self_loops=False):
        rows = np.concatenate([[i] * len(n) for i, n in enumerate(self.neighbours)])
        cols = np.concatenate(self.neighbours)
        keep = np.ones(len(rows), bool) if self_loops else rows != cols
        return rows[keep], cols[keep]


def load_starmap(sample="BZ5", with_expr=False):
    folder = os.path.join(DATA, "starmap", sample)
    ct = pd.read_csv(os.path.join(folder, "celltype.csv"), index_col=0)["c"]
    pos = pd.read_csv(os.path.join(folder, "pos.csv"), index_col=0).loc[ct.index]
    truth = pd.read_csv(os.path.join(folder, "domain.csv"), index_col=0)["z"].loc[ct.index].astype(int).map(LAYER)
    expr = pd.read_csv(os.path.join(folder, "data.csv"), index_col=0).loc[ct.index] if with_expr else None
    return Section(f"starmap_{sample}", ct.map(STARMAP_TYPES), pos[["x", "y"]].values, truth, expr, radius=700)


def load_merfish(with_expr=False):
    import anndata
    ad = anndata.read_h5ad(os.path.join(DATA, "merfish.h5ad"))
    obs = ad.obs[ad.obs["domain"].notna()].copy()
    # "OD Mature 2" -> "OD Mature"; cells without a usable class are dropped
    ct = obs["cell_class"].astype(str).str.replace(r"\s+\d+$", "", regex=True)
    ct = ct[~ct.str.lower().isin(["ambiguous", "nan", "unknown"])]
    sub = ad[ct.index]
    expr = None
    if with_expr:
        X = sub.X.toarray() if sparse.issparse(sub.X) else np.asarray(sub.X)
        expr = pd.DataFrame(X, index=ct.index, columns=[str(g) for g in sub.var_names])
    truth = obs.loc[ct.index, "domain"].astype(str)
    return Section("merfish", ct, sub.obsm["spatial"][:, :2], truth, expr, radius=100)


def load(dataset, with_expr=False):
    if dataset == "starmap":
        return load_starmap("BZ5", with_expr)
    if dataset == "merfish":
        return load_merfish(with_expr)
    raise ValueError(dataset)


def regions_of(sec):
    if sec.name.startswith("starmap"):
        return list(LAYER.values())
    return sorted(sec.truth.unique())


def to_region(text, regions):
    text = str(text).strip().strip('"')
    for r in sorted(regions, key=len, reverse=True):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(r)}(?![A-Za-z0-9/])", text):
            return r
    return "unknown"


def parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


def parse_cells(text):
    """{"cell_1": "...", ...} -> {1: "...", ...}; works on truncated answers too."""
    return {int(k): v for k, v in re.findall(r'"cell_(\d+)"\s*:\s*"([^"]+)"', text or "")}


class Gemini:
    """Thin wrapper around google-genai. With offline=True every call is refused, so only cached answers are used."""

    def __init__(self, offline=False, model=MODEL, pause=1.0):
        self.offline = offline
        self.model = model
        self.pause = pause
        self.client = None
        if not offline:
            from google import genai
            key = os.environ.get("GOOGLE_API_KEY")
            if not key:
                raise SystemExit("Set GOOGLE_API_KEY, or run with --offline to reuse the saved answers.")
            self.client = genai.Client(api_key=key)

    def ask(self, prompt, max_tokens=4000, temperature=1.0):
        if self.offline:
            return None
        for _ in range(6):
            try:
                r = self.client.models.generate_content(
                    model=self.model, contents=prompt,
                    config={"temperature": temperature, "max_output_tokens": max_tokens})
                time.sleep(self.pause)
                return r.text or ""
            except Exception as e:  # rate limits on the free tier are common, so wait and retry
                msg = str(e)
                if "404" in msg or "NOT_FOUND" in msg:
                    raise SystemExit(f"Model {self.model} is not available for this key.")
                time.sleep(60 if "429" in msg or "RESOURCE_EXHAUSTED" in msg else 10)
        return None


def read_answers(path):
    if os.path.exists(path):
        return pd.read_csv(path, index_col=0)["answer"].astype(str).to_dict()
    return {}


def write_answers(answers, path):
    out = pd.Series(answers, name="answer")
    out.index.name = "cell"
    out.to_frame().to_csv(path)


def majority_smooth(labels, sec):
    """A cell takes the most common label around it when more than half of its neighbours agree."""
    pos = {c: i for i, c in enumerate(sec.cells)}
    out = labels.copy()
    for c in labels.index:
        around = labels.reindex(sec.cells[sec.neighbours[pos[c]]]).dropna().value_counts()
        if len(around) and around.iloc[0] / around.sum() > 0.5:
            out[c] = around.index[0]
    return out


def scores(truth, pred):
    truth, pred = np.asarray(truth), np.asarray(pred)
    return dict(accuracy=float(np.mean(truth == pred)),
                ARI=float(adjusted_rand_score(truth, pred)),
                NMI=float(normalized_mutual_info_score(truth, pred)))


def report(rows, path):
    df = pd.DataFrame(rows)
    df[["accuracy", "ARI", "NMI"]] = df[["accuracy", "ARI", "NMI"]].round(3)
    df.to_csv(path, index=False)
    print(df.to_string(index=False))
    return df
