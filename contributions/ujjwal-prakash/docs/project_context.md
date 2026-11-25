# Project Context: Computational Genomics CS690 - Spatial Transcriptomics Niche Annotation

## 1. Executive Summary & Scientific Motivation

In spatial transcriptomics (ST), computational clustering (e.g., via BANKSY, CellCharter, or PROST) segments tissue into discrete spatial domains or "niches". A persistent bottleneck in spatial genomics pipelines is **niche annotation**: assigning reliable biological or anatomical identities (such as cortical laminae or specialized cellular microenvironments) to these spatial clusters. Traditionally, this requires labor-intensive expert review of differential marker genes.

Recent efforts have benchmarked large language models (LLMs) for zero-shot biological labeling from top marker genes. However, empirical findings show:
1. **Unconstrained LLMs frequently hallucinate or fail:** Without anatomical constraints or external evidence, models produce single-cell classifications (e.g., predicting *"Secretory Epithelial Cells"* for cortical Layer 2) or misclassify layers due to dominant marker overlap (e.g., predicting *"Layer 5"* for Layer 3 due to neurofilament chains *NEFL*, *NEFM*, *NEFH*).
2. **Current NicheAgent relies on closed-world prototypes:** The existing Python-based NicheAgent framework solves confident hallucinations by evaluating Euclidean distance margins against pre-curated "NicheCards" representing known canonical marker centroids, using the LLM merely to arbitrate low-margin cases. Consequently, it cannot generalize to novel tissues, uncurated niches, or transitional biological states.

**Proposed Research Contribution:**
We design and benchmark a **Web-Augmented NicheAgent** implemented in **TypeScript** using **LangGraph.js**. Instead of hardcoding closed-world prototypes, the agent dynamically evaluates uncertainty, autonomously queries real-time external biological knowledge bases (MyGene.info, Enrichr gene-set enrichment), evaluates the credibility of retrieved biological facts, and refines its predictions through bounded iterative reasoning.

---

## 2. Dataset & Upstream Analysis

The empirical benchmark centers on the canonical **10x Visium Human Dorsolateral Prefrontal Cortex (DLPFC)** dataset, specifically **sample 151673** (Maynard et al., *Nature Neuroscience* 2021; 3,611–3,639 spots, 33,538 genes):
- **Ground Truth Laminae:** 7 expert-curated anatomical zones: **Layer 1**, **Layer 2**, **Layer 3**, **Layer 4**, **Layer 5**, **Layer 6**, and **White Matter (WM)**.
- **Upstream Spatial Clustering:** Two distinct unsupervised algorithms run on sample 151673:
  1. **BANKSY** (incorporates cellular gene expression and spatial neighborhood mean gradients) $\to$ 6 primary spatial niches.
  2. **CellCharter** (variational autoencoder latent embeddings pooled over spatial neighbors) $\to$ 6 primary spatial niches.
- **Marker Extraction:** For each niche cluster, a two-sided Wilcoxon rank-sum test (one-vs-rest) identified the top 10 selective marker genes based on adjusted $p$-value and log fold-change.

### Authentic Niche Composition & Marker Sets

#### A. BANKSY Spatial Niches (Sample 151673)
- **Niche 0:** Top markers: `ENC1, CAMK2N1, HPCAL1, HOPX, MT-CO1, MT-ND1, MT-CYB, SERPINE2, MT-ATP6, OLFM1`.
  - *Ground Truth Composition:* 545 spots Layer 3 (70.4%), 213 spots Layer 2 (27.5%), 16 spots Layer 1 (2.1%). **Majority: Layer 3 (with Layer 2 transition)**.
- **Niche 1:** Top markers: `MBP, DIRAS2, PLP1, KRT17, SLC17A7, SYT1, GPM6A, CPE, TMSB10, SCGB2A2`.
  - *Ground Truth Composition:* 628 spots Layer 6 (83.0%), 103 spots Layer 5 (13.6%), 24 spots WM (3.2%). **Majority: Layer 6**.
- **Niche 2:** Top markers: `NEFL, NEFM, NEFH, SNCG, MT-CO2, SCN1B, TUBA1B, MT-CO3, MT-ATP6, NDUFA4`.
  - *Ground Truth Composition:* 441 spots Layer 3 (68.4%), 177 spots Layer 4 (27.4%), 27 spots Layer 5 (4.2%). **Majority: Layer 3 (L3/L4 boundary)**.
- **Niche 3:** Top markers: `TMSB10, PCP4, SNAP25, TUBA1B, TUBB2A, SYT1, STMN1, SNCB, STMN2, SYN2`.
  - *Ground Truth Composition:* 542 spots Layer 5 (90.9%), 41 spots Layer 4 (6.9%), 13 spots Layer 6 (2.2%). **Majority: Layer 5**.
- **Niche 4:** Top markers: `PLP1, MBP, CRYAB, CNP, GFAP, MOBP, TF, PTGDS, S100B, FTH1`.
  - *Ground Truth Composition:* 489 spots WM (90.6%), 51 spots Layer 6 (9.4%). **Majority: White Matter (WM)**.
- **Niche 5:** Top markers: `MALAT1, CST3, CLU, MT-ND2, MT-ND1, COX6C, SLC1A2, MT-ND3, MT-ND5, GFAP`.
  - *Ground Truth Composition:* 255 spots Layer 1 (85.3%), 40 spots Layer 2 (13.4%), 3 spots Layer 3 (1.0%). **Majority: Layer 1**.

#### B. CellCharter Spatial Niches (Sample 151673)
- **Niche 0:** Top markers: `DIRAS2, SYT1, TMSB10, MBP, SLC17A7, SNAP25, CHN1, GPM6A, DKK3, KRT17`.
  - *Ground Truth Composition:* 554 spots Layer 6 (72.2%), 213 spots Layer 5 (27.8%). **Majority: Layer 6**.
- **Niche 1:** Top markers: `MBP, PLP1, CNP, GFAP, CRYAB, MOBP, TF, PTGDS, S100B, FTH1`.
  - *Ground Truth Composition:* 513 spots WM (79.0%), 136 spots Layer 6 (21.0%). **Majority: White Matter (WM)**.
- **Niche 2:** Top markers: `NEFL, TUBA1B, SNAP25, PCP4, TMSB10, SNCG, NEFM, UCHL1, STMN2, NDUFA4`.
  - *Ground Truth Composition:* 426 spots Layer 5 (46.7%), 320 spots Layer 3 (35.0%), 165 spots Layer 4 (18.1%). **Majority: Layer 5 (diffuse deep-layer cluster)**.
- **Niche 3:** Top markers: `MALAT1, CST3, CLU, MT-ND1, MT-ND2, SLC1A2, MT-ND3, COX6C, MT3, MT-ND5`.
  - *Ground Truth Composition:* 267 spots Layer 1 (74.4%), 92 spots Layer 2 (25.6%). **Majority: Layer 1**.
- **Niche 4:** Top markers: `ENC1, HOPX, HPCAL1, CAMK2N1, MT-CO1, SERPINE2, CCK, OLFM1, CYP46A1, MT-CYB`.
  - *Ground Truth Composition:* 382 spots Layer 3 (76.4%), 118 spots Layer 2 (23.6%). **Majority: Layer 3**.
- **Niche 5:** Top markers: `MT-ATP6, ENC1, MT-CO1, MT-ND1, MT-CYB, HOPX, YWHAH, MT-CO2, MT-CO3, OLFM1`.
  - *Ground Truth Composition:* 287 spots Layer 3 (67.8%), 53 spots Layer 4 (12.5%), 43 spots Layer 2 (10.2%), 34 spots Layer 5 (8.0%). **Majority: Layer 3 (metabolically active upper-middle layer)**.

---

## 3. Analysis of Existing Work vs. Proposed Contribution

### What Has Been Completed So Far
1. **Unsupervised Spatial Clustering:** Completed for sample 151673 with cross-tabulation against authentic Maynard annotations.
2. **Preliminary LLM Prompting:** Explored across ChatGPT, Claude, and Gemini with varying prompt styles (raw markers vs tissue-conditioned vs JSON).
3. **Python Prototype of NicheAgent:** Implemented 12-phase pipeline with closed-world NicheCards, prototype margin arbitration, and spatial neighborhood graph majority voting. Demonstrated reduction of confident hallucinations to 0.0%, but restricted to pre-compiled cortical card sets.

### What Is Missing (The Research Gap)
- **Generalization beyond closed-world cards:** If applied to non-cortical tissue or unknown cancer niches, prototype matching fails.
- **External Biological Evidence Grounding:** Unconstrained LLMs lack grounded validation for marker specificity. For example, neurofilament subunits (*NEFL*, *NEFM*, *NEFH*) are expressed in both pyramidal neurons of Layer 3 and large Betz cells of Layer 5; without querying gene annotation or pathway databases, LLMs collapse to Layer 5.
- **Stateful Iterative Reasoning:** Prior implementations prompt the LLM once. A scientific agent should form a preliminary hypothesis, recognize ambiguity (e.g. low margin or co-presence of conflicting markers), query targeted biological APIs, re-evaluate evidence, and formulate a refined prediction.

---

## 4. Architectural Vision for Web-Augmented NicheAgent

The Web-Augmented NicheAgent is built using **TypeScript** and **LangGraph.js**, operating over a strongly-typed graph state:

```
  ┌───────────────────────┐
  │   Input Validation    │  (Zod validation of marker genes, expression stats, tissue)
  └───────────┬───────────┘
              ▼
  ┌───────────────────────┐
  │   Initial Predictor   │  (Zero-shot Gemini call: initial prediction + confidence + reasoning)
  └───────────┬───────────┘
              ▼
  ┌───────────────────────┐
  │ Uncertainty Assessor  │  (Diagnose low confidence, marker discordance, or mitochondrial noise)
  └───────────┬───────────┘
              │
      Needs Retrieval?
      ├── No  ──────────┐
      └── Yes           │
          ▼             │
  ┌──────────────────┐  │
  │ Biological       │  │  (Fetch from MyGene.info gene summaries,
  │ Retriever        │  │   Enrichr pathway / GO cellular component)
  └───────┬──────────┘  │
          ▼             │
  ┌──────────────────┐  │
  │ Evidence         │  │  (Evaluate retrieved facts against tissue priors;
  │ Evaluator        │  │   check for laminar markers vs non-specific housekeeping)
  └───────┬──────────┘  │
          ▼             │
  ┌──────────────────┐  │
  │ Prediction       │  │  (Synthesize evidence; revise prediction; loop if ambiguous, max 2)
  │ Reviser          │  │
  └───────┬──────────┘  │
          │             │
          └──────┬──────┘
                 ▼
     ┌───────────────────────┐
     │ Final Response Formatter
     └───────────────────────┘
```

### Scientific Rigor & Anti-Leakage Guardrails
1. **No Ground Truth Leakage:** Neither ground-truth layer labels nor sample IDs (e.g., "151673") are ever passed to retrieval queries.
2. **Provenance Tracking:** Every piece of retrieved evidence must retain exact API provenance (URLs, database keys, pathway accession IDs).
3. **Strict Loop Bounds:** Bounded to a maximum of 2 retrieval iterations to prevent runaway execution and control API costs.
4. **Controlled Evaluation:** Comparison across three identical conditions:
   - **Condition A (Baseline Gemini):** Raw marker genes + tissue context.
   - **Condition B (One-Shot RAG):** Retrieve biological summaries once, supply with markers to Gemini.
   - **Condition C (Iterative RAG):** Initial prediction $\to$ Uncertainty check $\to$ Targeted retrieval $\to$ Evidence evaluation $\to$ Prediction revision.
