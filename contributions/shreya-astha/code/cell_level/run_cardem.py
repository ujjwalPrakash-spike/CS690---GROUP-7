"""Label-free niche annotation from LLM-written region cards.

No clustering and no labelled reference: Gemini writes a card for every region (expected cell-type mix
around a cell, plus marker genes from the panel). Three ways to use the cards are compared:

  M1  cosine to the nearest card, then majority smoothing
  M2  tempered multinomial likelihood + MAP-EM with the card as a Dirichlet prior, Gemini review of the
      most uncertain cells, Potts smoothing (tau=10, lambda=0.5, beta=1 fixed in advance)
  M3  CardEM: M2 plus a marker-gene view, tau from the design effect, lambda chosen by anchoring,
      a rename check by Gemini, review ranked by card-run disagreement and entropy, and an
      edge-aware Potts step with beta from the pseudo-likelihood

Expert labels are only used for scoring and for the comparison rows.

    python run_cardem.py --dataset starmap [--offline]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score

import common as cm

CARD_RUNS = 3
REVIEW_FRAC = 0.20
BATCH = 15
EPS = 1e-3
LAMBDAS = [4, 2, 1, 0.5, 0.25, 0.1, 0.05]
BETAS = np.arange(0, 8.01, 0.25)

TISSUE = {"starmap": "mouse cortex (STARmap, 4 cortical layers)",
          "merfish": "mouse hypothalamic preoptic region (MERFISH, Bregma -0.14)"}
REGION_INFO = {"starmap": "Layer 1, Layer 2/3, Layer 5, Layer 6 "
                          "(cortical layers; there is no white matter in this section)",
               "merfish": cm.MERFISH_REGIONS}


def cosine(A, B):
    return A @ B.T / (np.linalg.norm(A, axis=1, keepdims=True) * np.linalg.norm(B, axis=1) + 1e-9)


def entropy(G):
    return -(G * np.log(G + 1e-12)).sum(1)


def norm_card(Q):
    Q = np.asarray(Q, float) + EPS
    return Q / Q.sum(1, keepdims=True)


class CardModel:
    def __init__(self, dataset, sec, llm):
        self.ds, self.sec, self.llm = dataset, sec, llm
        self.regions = cm.regions_of(sec)
        self.K, self.N = len(self.regions), len(sec)
        self.types = sec.types
        self.genes = list(sec.expr.columns)
        self.F = sec.comp.values

        # expression: library-size normalise, log1p, z-score, then average over each neighbourhood
        X = sec.expr.values.astype(float)
        X = np.log1p(X / np.maximum(X.sum(1, keepdims=True), 1) * 1e4)
        self.Z = (X - X.mean(0)) / (X.std(0) + 1e-9)
        r, c = sec.graph(self_loops=True)
        Win = sparse.csr_matrix((np.ones(len(r)), (r, c)), shape=(self.N, self.N))
        self.Zbar = sparse.diags(1 / Win.sum(axis=1).A1) @ Win @ self.Z
        off = r != c
        self.r, self.c = r[off], c[off]
        W = sparse.csr_matrix((np.ones(off.sum()), (self.r, self.c)), shape=(self.N, self.N))
        self.W = sparse.diags(1 / np.maximum(W.sum(axis=1).A1, 1)) @ W

    def name(self, z):
        return pd.Series(np.array(self.regions)[z], index=self.sec.cells)

    # ---------------------------------------------------------------- cards
    def card_prompt(self):
        return (f"You are an expert neuroanatomist. Tissue: {TISSUE[self.ds]}.\n"
                f"Regions: {REGION_INFO[self.ds]}.\n"
                f"Cell types measured: {', '.join(self.types)}.\n"
                f"Genes measured (panel): {', '.join(self.genes)}.\n\n"
                "For each region give\n"
                f'(a) "mix": the cell-type composition of a typical neighbourhood (all cells within about '
                f"{self.sec.radius} um), fractions summing to 1,\n"
                "    0 for absent types, using your anatomy knowledge only;\n"
                '(b) "markers": 5 to 10 genes FROM THE PANEL that are more highly expressed in this region '
                "than in the other listed regions.\n\n"
                'Answer ONLY with JSON: {"<region>": {"mix": {"<cell type>": fraction, ...}, '
                '"markers": ["gene", ...]}, ...}\n'
                f"Use exactly these region names: {', '.join(self.regions)}; "
                f"these cell-type names: {', '.join(self.types)}.")

    def get_cards(self):
        path = os.path.join(cm.CACHE, f"{self.ds}_cards.json")
        runs = json.load(open(path))["runs"] if os.path.exists(path) else []
        while len(runs) < CARD_RUNS:
            d = cm.parse_json(self.llm.ask(self.card_prompt(), max_tokens=10000))
            if d is None:
                break
            runs.append(d)
            json.dump({"runs": runs}, open(path, "w"), indent=1)
        if not runs:
            raise SystemExit("No cards: run once with a Gemini key, or check cache/.")
        self.card_runs, marker_runs = [], []
        for d in runs:
            card = pd.DataFrame(0.0, index=self.regions, columns=self.types)
            markers = {r: [] for r in self.regions}
            for reg, v in d.items():
                r = cm.to_region(reg, self.regions)
                if r == "unknown" or not isinstance(v, dict):
                    continue
                for t, x in (v.get("mix") or {}).items():
                    if t in card.columns:
                        try:
                            card.loc[r, t] = float(x)
                        except (TypeError, ValueError):
                            pass
                markers[r] = [g for g in (v.get("markers") or []) if g in self.genes]
            self.card_runs.append(card.div(card.sum(axis=1).replace(0, 1), axis=0))
            marker_runs.append(markers)
        self.cards = sum(self.card_runs) / len(self.card_runs)
        self.markers = {r: sorted({g for m in marker_runs for g in m[r]}) for r in self.regions}
        self.Q0 = self.cards.loc[self.regions].values
        pairs = [(a, b) for i, a in enumerate(self.card_runs) for b in self.card_runs[i + 1:]]
        self.stability = np.mean([np.diag(cosine(a.values, b.values)).mean() for a, b in pairs]) if pairs else np.nan
        # marker score of a cell for region r: mean neighbourhood z-expression of r's markers
        self.SM = np.column_stack([
            self.Zbar[:, [self.genes.index(g) for g in self.markers[r]]].mean(1) if self.markers[r]
            else np.zeros(self.N) for r in self.regions])

    # ---------------------------------------------------------------- MAP-EM
    def em(self, Q, lam=0.5, tau=10.0, genes=False, adapt_tau=False, iters=100):
        F, SM, K, N = self.F, self.SM, self.K, self.N
        Q = norm_card(Q)
        P, pi = Q.copy(), np.full(K, 1 / K)
        mu = sd = None

        def posterior(P, pi, tau, mu, sd):
            L = tau * F @ np.log(P).T + np.log(pi)
            if genes and mu is not None:
                L = L + np.stack([(-0.5 * ((SM - mu[k]) / sd[k]) ** 2 - np.log(sd[k])).sum(1) for k in range(K)], 1)
            L -= L.max(1, keepdims=True)
            G = np.exp(L)
            return G / G.sum(1, keepdims=True)

        G = posterior(P, pi, tau, None, None)
        alpha = lam * N / K  # prior strength, in pseudo-cells per region
        z_old = None
        for _ in range(iters):
            w = G.sum(0) + 1e-9
            P = norm_card((alpha * Q + G.T @ F) / (alpha + w)[:, None])
            pi = (G.sum(0) + 1) / (N + K)
            if genes:
                mu = (G.T @ SM) / w[:, None]
                sd = np.sqrt(np.stack([(G[:, k:k + 1] * (SM - mu[k]) ** 2).sum(0) / w[k] for k in range(K)]) + 1e-3)
            if adapt_tau:
                # a neighbourhood fraction has variance p(1-p)/tau, so tau = binomial variance / observed variance
                obs_var = sum((G[:, k:k + 1] * (F - P[k]) ** 2).sum(0) for k in range(K)) / N
                bin_var = sum(pi[k] * P[k] * (1 - P[k]) for k in range(K))
                tau = float(np.clip(bin_var.sum() / max(obs_var.sum(), 1e-9), 1, 200))
            G = posterior(P, pi, tau, mu, sd)
            z = G.argmax(1)
            if z_old is not None and np.mean(z != z_old) < 1e-3:
                break
            z_old = z
        return G, P, tau

    def potts(self, G, beta, W):
        logG, z = np.log(G + 1e-12), G.argmax(1)
        for _ in range(10):
            z_new = (logG + beta * (W @ np.eye(self.K)[z])).argmax(1)
            if np.all(z_new == z):
                break
            z = z_new
        return z

    def pseudo_ll(self, z, beta, W):
        S = beta * (W @ np.eye(self.K)[z])
        S -= S.max(1, keepdims=True)
        return (S[np.arange(self.N), z] - np.log(np.exp(S).sum(1))).sum()

    def best_beta(self, z, W):
        return max(BETAS, key=lambda b: self.pseudo_ll(z, b, W))

    def edge_weights(self):
        """Neighbours whose mix differs a lot (Jensen-Shannon) pull less during smoothing."""
        a, b = self.F[self.r], self.F[self.c]
        m = 0.5 * (a + b)
        d = 0.5 * (a * np.log((a + 1e-9) / (m + 1e-9))).sum(1) + 0.5 * (b * np.log((b + 1e-9) / (m + 1e-9))).sum(1)
        W = sparse.csr_matrix((np.exp(-d / (np.median(d) + 1e-9)), (self.r, self.c)), shape=(self.N, self.N))
        return sparse.diags(1 / np.maximum(W.sum(axis=1).A1, 1e-9)) @ W

    # ---------------------------------------------------------------- Gemini review of uncertain cells
    def describe(self, i):
        row = self.sec.comp.iloc[i].sort_values(ascending=False)
        top = np.array(self.genes)[np.argsort(-self.Zbar[i])[:6]]
        return ", ".join(f"{t} {v:.0%}" for t, v in row.items() if v >= 0.05) + f" | high genes nearby: {', '.join(top)}"

    def review_prompt(self, rows):
        card_text = "\n".join(
            f"- {r}: " + ", ".join(f"{t} {v:.0%}" for t, v in self.cards.loc[r].sort_values(ascending=False).items()
                                   if v >= 0.05)
            + (f"; markers: {', '.join(self.markers[r][:8])}" if self.markers[r] else "") for r in self.regions)
        cells = "\n".join(f"cell_{k + 1}: {self.describe(i)}" for k, i in enumerate(rows))
        return (f"Tissue: {TISSUE[self.ds]}. Regions: {REGION_INFO[self.ds]}.\n"
                f"Reference cards (expected neighbourhood and marker genes of each region):\n{card_text}\n\n"
                f"Each cell below is described by the cell types within {self.sec.radius} um of it "
                "and the genes most enriched around it.\n"
                f"These cells are ambiguous. Choose exactly one region per cell from: {', '.join(self.regions)}.\n\n"
                f"{cells}\n\n"
                f'Answer ONLY with JSON like {{"cell_1": "{self.regions[0]}", "cell_2": "{self.regions[-1]}"}}.')

    def review(self, cells):
        """One cached answer per cell, shared by every method and ablation."""
        path = os.path.join(cm.CACHE, f"{self.ds}_review.csv")
        cache = cm.read_answers(path)
        ids = self.sec.cells
        todo = [i for i in cells if ids[i] not in cache]
        for b in range(0, len(todo), BATCH):
            rows = todo[b:b + BATCH]
            text = self.llm.ask(self.review_prompt(rows), max_tokens=4000)
            if text is None:
                break
            got = cm.parse_cells(text)
            for k, i in enumerate(rows):
                r = cm.to_region(got.get(k + 1, ""), self.regions)
                if r != "unknown":
                    cache[ids[i]] = r
            cm.write_answers(cache, path)
        return {i: cache[ids[i]] for i in cells if ids[i] in cache}

    def apply_review(self, G, answers):
        G = G.copy()
        for i, r in answers.items():
            G[i] = 0.1 / self.K
            G[i, self.regions.index(r)] += 0.9
        return G

    # ---------------------------------------------------------------- rename check
    def rename_check(self, P):
        path = os.path.join(cm.CACHE, f"{self.ds}_rename.json")
        if os.path.exists(path):
            d = json.load(open(path))
        else:
            fmt = lambda row: ", ".join(f"{t} {v:.0%}" for t, v in pd.Series(row, index=self.types)
                                        .sort_values(ascending=False).items() if v >= 0.05)
            text = (f"Tissue: {TISSUE[self.ds]}. Regions: {REGION_INFO[self.ds]}.\n"
                    "For each region you first predicted a neighbourhood composition. "
                    "Fitting a model to the real tissue refined it.\n"
                    "Does each refined composition still fit its region name? If two regions were swapped, say so.\n\n"
                    + "\n".join(f"{r}:\n  your card: {fmt(self.Q0[k])}\n  refined:   {fmt(P[k])}"
                                for k, r in enumerate(self.regions))
                    + "\n\nAnswer ONLY with JSON mapping each region name to the region name its REFINED card "
                      f'really is,\ne.g. {{"{self.regions[0]}": "{self.regions[0]}", ...}}. '
                      f"Use only: {', '.join(self.regions)}.")
            d = cm.parse_json(self.llm.ask(text, max_tokens=2000, temperature=0.0)) or {}
            if d:
                json.dump(d, open(path, "w"), indent=1)
        perm = []
        for k, r in enumerate(self.regions):
            new = cm.to_region(d.get(r, r), self.regions)
            perm.append(self.regions.index(new) if new in self.regions else k)
        renamed = sorted(perm) == list(range(self.K)) and perm != list(range(self.K))
        return (np.argsort(perm) if renamed else None), renamed


def comparison_rows(model, ds, sec, add):
    regions, F = model.regions, model.F
    if ds == "starmap":
        refs = [cm.load_starmap(b) for b in ("BZ9", "BZ14")]
        comp = pd.concat([r.comp for r in refs]).reindex(columns=sec.types, fill_value=0)
        truth = pd.concat([r.truth for r in refs])
        expert = cosine(F, comp.groupby(truth.values).mean().loc[regions].values).argmax(1)
    else:
        half = (sec.xy[:, 0] > np.median(sec.xy[:, 0])).astype(int)
        expert = np.zeros(model.N, int)
        for h in (0, 1):
            proto = sec.comp[half != h].groupby(sec.truth[half != h].values).mean().reindex(regions).fillna(0)
            expert[half == h] = cosine(F[half == h], proto.values).argmax(1)
    add("Expert cards, cosine nearest (needs labels)", model.name(expert))
    km = KMeans(model.K, n_init=10, random_state=0).fit_predict(F)
    tab = pd.crosstab(km, sec.truth.values)
    ri, ci = linear_sum_assignment(-tab.values)
    add("k-means, best possible naming", pd.Series(km, index=sec.cells).map(
        dict(zip(tab.index[ri], tab.columns[ci]))).fillna("unnamed"))
    add("Majority region", pd.Series(sec.truth.value_counts().index[0], index=sec.cells))
    return expert, km


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["starmap", "merfish"], required=True)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    ds = args.dataset

    sec = cm.load(ds, with_expr=True)
    model = CardModel(ds, sec, cm.Gemini(offline=args.offline))
    model.get_cards()
    regions, K, N = model.regions, model.K, model.N
    n_review = int(REVIEW_FRAC * N)
    print(f"{ds}: {N} cells, {K} regions, {len(model.types)} cell types, {len(model.genes)} genes; "
          f"card stability {model.stability:.2f}")

    rows, preds = [], {}

    def add(name, labels, note=""):
        rows.append(dict(dataset=ds, method=name, **cm.scores(sec.truth, labels), note=note))
        preds[name] = labels

    # M1
    raw = cosine(model.F, model.Q0).argmax(1)
    add("M1 cosine + majority vote", cm.majority_smooth(model.name(raw), sec))

    # M2
    G2, P2, _ = model.em(model.Q0, lam=0.5, tau=10.0)
    rev2 = model.review(np.argsort(-entropy(G2))[:n_review])
    add("M2 EM + review + Potts", model.name(model.potts(model.apply_review(G2, rev2), 1.0, model.W)),
        "tau=10, lambda=0.5, beta=1")

    # M3: lambda is the smallest prior strength at which no refined card swaps identity with another region's
    # LLM card and no region is left (almost) empty
    def anchored(G, P):
        _, b = linear_sum_assignment(-cosine(P, model.Q0))
        return bool(np.all(b == np.arange(K))) and np.bincount(G.argmax(1), minlength=K).min() >= 0.005 * N

    fits = {lam: model.em(model.Q0, lam=lam, genes=True, adapt_tau=True) for lam in LAMBDAS}
    ok = [lam for lam in LAMBDAS if anchored(*fits[lam][:2])]
    lam3 = min(ok) if ok else max(LAMBDAS)
    G3, P3, tau3 = fits[lam3]
    order, renamed = model.rename_check(P3)
    if renamed:
        G3, P3 = G3[:, order], P3[order]

    # two kinds of doubt: data ambiguity (entropy) and disagreement between card runs
    if len(model.card_runs) > 1:
        z_runs = np.stack([model.em(norm_card(c.loc[regions].values), lam=lam3, genes=True, adapt_tau=True)[0]
                           .argmax(1) for c in model.card_runs])
        disagree = (z_runs != z_runs[0]).any(0).astype(float)
    else:
        disagree = np.zeros(N)
    H3 = entropy(G3)
    doubt = H3 / (H3.max() + 1e-9) + disagree
    rev3 = model.review(np.argsort(-doubt)[:n_review])
    G3r = model.apply_review(G3, rev3)
    WE = model.edge_weights()
    beta3 = model.best_beta(G3r.argmax(1), WE)
    z3 = model.potts(G3r, beta3, WE)
    add("M3 CardEM", model.name(z3), f"lambda={lam3}, tau={tau3:.1f}, beta={beta3}, renamed={renamed}")
    print(f"CardEM settings: lambda={lam3}, tau={tau3:.1f}, beta={beta3}, renamed={renamed}")

    # ablations reuse the cached review answers, so they need no new Gemini calls
    def variant(genes=True, adapt=True, lam=None, edge=True, auto_beta=True, review=True):
        G, _, _ = model.em(model.Q0, lam=lam3 if lam is None else lam, tau=10.0, genes=genes, adapt_tau=adapt)
        if renamed:
            G = G[:, order]
        if review:
            G = model.apply_review(G, rev3)
        W = WE if edge else model.W
        beta = model.best_beta(G.argmax(1), W) if auto_beta else 1.0
        return model.name(model.potts(G, beta, W))

    add("  CardEM without marker-gene view", variant(genes=False))
    add("  CardEM with fixed tau=10", variant(adapt=False))
    add("  CardEM with fixed lambda=0.5", variant(lam=0.5))
    add("  CardEM with plain Potts", variant(edge=False))
    add("  CardEM with fixed beta=1", variant(auto_beta=False))
    add("  CardEM without Gemini review", variant(review=False))
    expert, km = comparison_rows(model, ds, sec, add)
    cm.report(rows, os.path.join(cm.RESULTS, f"{ds}_cardem_scores.csv"))

    # diagnostics: how close are the cards to the real mean neighbourhoods, and does doubt find errors?
    real = sec.comp.groupby(sec.truth.values).mean().loc[regions].values
    true_idx = np.array([regions.index(t) for t in sec.truth.values])
    real_top = {r: set(np.array(model.genes)[np.argsort(-(model.Z[true_idx == k].mean(0) - model.Z.mean(0)))[:10]])
                for k, r in enumerate(regions)}
    err = (G3.argmax(1) != true_idx).astype(int)
    auc = (lambda s: roc_auc_score(err, s)) if 0 < err.sum() < N else (lambda s: np.nan)
    diag = pd.DataFrame({
        "cosine_llm_card": np.diag(cosine(model.Q0, real)),
        "cosine_m2_refined": np.diag(cosine(P2, real)),
        "cosine_cardem_refined": np.diag(cosine(P3, real)),
        "llm_markers_in_true_top10": [len(set(model.markers[r]) & real_top[r]) for r in regions],
    }, index=regions)
    diag = diag.assign(card_stability=model.stability, auroc_entropy=auc(H3), auroc_disagreement=auc(disagree),
                       auroc_combined=auc(doubt), lam=lam3, tau=tau3, beta=beta3, renamed=renamed)
    diag.to_csv(os.path.join(cm.RESULTS, f"{ds}_cardem_diagnostics.csv"))
    print(diag.round(2).to_string())

    # per-cell output for the statistics and figures
    idx = lambda labels: np.array([regions.index(x) if x in regions else -1 for x in labels])
    np.savez(os.path.join(cm.RESULTS, f"{ds}_cardem_cells.npz"),
             cells=np.array(sec.cells), xy=sec.xy, truth=true_idx, regions=np.array(regions),
             types=np.array(model.types), F=model.F, SM=model.SM, raw=raw,
             m1=idx(preds["M1 cosine + majority vote"]), m2=idx(preds["M2 EM + review + Potts"]), m3=z3,
             g3=G3.argmax(1), g3r=G3r.argmax(1), entropy=H3, err=err, reviewed=np.array(sorted(rev3)),
             Q0=model.Q0, P2=P2, P3=P3, real=real, expert=expert, km=km)


if __name__ == "__main__":
    main()
